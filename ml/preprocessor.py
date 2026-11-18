import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
from config import REQUIRED_COLUMNS, NUMERIC_COLUMNS

class CinemaDataPreprocessor:
    def __init__(self):
        self.validation_errors = []

    def validate_columns(self, df: pd.DataFrame) -> Tuple[bool, list]:
        df_cols = [c.strip().lower() for c in df.columns]
        # Allow simulated_state to be derived if missing
        required = [col for col in REQUIRED_COLUMNS if col != "simulated_state"]
        missing = [col for col in required if col.lower() not in df_cols]
        if missing:
            return False, missing
        return True, []

    def clean_and_prepare(self, raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df = raw_df.copy()
        initial_rows = len(df)
        df.columns = [c.strip().lower() for c in df.columns]

        missing_counts = df.isnull().sum().to_dict()
        total_missing = int(df.isnull().sum().sum())

        if "cinema_screen" in df.columns and "time_step" in df.columns:
            duplicates_removed = int(df.duplicated(subset=["cinema_screen", "time_step"]).sum())
            df = df.drop_duplicates(subset=["cinema_screen", "time_step"], keep="last")
        else:
            duplicates_removed = int(df.duplicated().sum())
            df = df.drop_duplicates(keep="last")

        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                if df[col].isnull().any():
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val if not pd.isna(median_val) else 0)

        if "cinema_screen" in df.columns:
            df["cinema_screen"] = df["cinema_screen"].astype(str).str.strip()

        # Derive delivery_risk
        if "delivery_risk" not in df.columns or df["delivery_risk"].isnull().any():
            df["delivery_risk"] = df.apply(self._derive_risk, axis=1)
        else:
            df["delivery_risk"] = df["delivery_risk"].astype(str).str.upper().str.strip()
            valid_risks = {"NORMAL", "WARNING", "CRITICAL"}
            df["delivery_risk"] = df.apply(
                lambda row: row["delivery_risk"] if row["delivery_risk"] in valid_risks else self._derive_risk(row),
                axis=1
            )

        # Derive simulated_state if missing
        if "simulated_state" not in df.columns or df["simulated_state"].isnull().any():
            risk_to_state = {
                "NORMAL": "Stable Delivery",
                "WARNING": "Degraded Delivery",
                "CRITICAL": "Critical Delivery"
            }
            df["simulated_state"] = df["delivery_risk"].map(risk_to_state)

        final_rows = len(df)
        stats = {
            "initial_rows": initial_rows,
            "final_rows": final_rows,
            "duplicates_removed": duplicates_removed,
            "missing_values_detected": total_missing,
            "missing_per_column": missing_counts,
            "unique_screens": int(df["cinema_screen"].nunique()) if "cinema_screen" in df.columns else 0,
            "weeks_span": int(df["time_step"].max()) if "time_step" in df.columns else 0,
            "risk_distribution": df["delivery_risk"].value_counts().to_dict()
        }

        return df, stats

    @staticmethod
    def _derive_risk(row) -> str:
        kdm_avail = row.get("kdm_available", 1)
        kdm_dec = row.get("kdm_decryptable", 1)
        kdm_exp = row.get("kdm_expired", 0)
        dcp_corr = row.get("dcp_corruption_pct", 0)
        pay_comp = row.get("payment_completed", 1)
        net_delay = row.get("network_delay_ms", 50)
        firmware = row.get("firmware_update_required", 0)
        sound_sync = abs(row.get("sound_sync_error_ms", 0))

        if kdm_avail == 0 or kdm_dec == 0 or kdm_exp == 1 or dcp_corr > 15.0:
            return "CRITICAL"
        elif (pay_comp == 0 or net_delay > 180.0 or firmware == 1 or
              sound_sync > 35.0 or dcp_corr > 2.5):
            return "WARNING"
        return "NORMAL"
