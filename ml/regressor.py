import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from config import MODELS_DIR

REGRESSION_FEATURES = [
    "dcp_corruption_pct",
    "broken_kdm",
    "kdm_decryption_failure",
    "firmware_update_required",
    "abs_sound_sync_error_ms",
    "network_delay_ms",
    "dcp_file_size_gb",
    "server_load"
]

class CinemaRecoveryRegressor:
    def __init__(self):
        self.models = {
            "Linear Regression": LinearRegression(),
            "Random Forest Regressor": RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
            "Support Vector Regression": SVR(kernel="rbf", C=10.0, epsilon=0.2),
            "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
        }
        self.fitted_models = {}
        self.scaler = StandardScaler()
        self.metrics = {}
        self.best_model_name = "Gradient Boosting Regressor"
        self.test_comparison_data = {}

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df_feat = df.copy()

        if "broken_kdm" not in df_feat.columns:
            df_feat["broken_kdm"] = ((df_feat["kdm_available"] == 0) | (df_feat["kdm_decryptable"] == 0)).astype(int)

        if "kdm_decryption_failure" not in df_feat.columns:
            df_feat["kdm_decryption_failure"] = (df_feat["kdm_decryptable"] == 0).astype(int)

        if "abs_sound_sync_error_ms" not in df_feat.columns:
            df_feat["abs_sound_sync_error_ms"] = df_feat["sound_sync_error_ms"].abs()

        if "dcp_file_size_gb" not in df_feat.columns:
            np.random.seed(42)
            df_feat["dcp_file_size_gb"] = np.random.uniform(90.0, 210.0, size=len(df_feat)).round(1)

        if "server_load" not in df_feat.columns:
            df_feat["server_load"] = np.clip(
                (df_feat["network_delay_ms"] / 5.0) + (df_feat["dcp_corruption_pct"] * 1.5) + 20.0,
                10.0, 98.0
            ).round(1)

        return df_feat

    def train_and_evaluate(self, df: pd.DataFrame):
        df_feat = self._prepare_features(df)

        X = df_feat[REGRESSION_FEATURES]
        y = df_feat["recovery_time_min"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42
        )

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        self.metrics = {}
        best_r2 = -999.0
        best_preds = None

        for name, reg in self.models.items():
            if name in ["Linear Regression", "Support Vector Regression"]:
                reg.fit(X_train_scaled, y_train)
                y_pred = reg.predict(X_test_scaled)
            else:
                reg.fit(X_train, y_train)
                y_pred = reg.predict(X_test)

            mae = float(mean_absolute_error(y_test, y_pred))
            rmse = float(root_mean_squared_error(y_test, y_pred))
            r2 = float(r2_score(y_test, y_pred))

            self.fitted_models[name] = reg
            self.metrics[name] = {
                "mae": round(mae, 2),
                "rmse": round(rmse, 2),
                "r2_score": round(r2, 4),
                "accuracy_pct": round(max(0.0, r2) * 100, 2)
            }

            if r2 > best_r2:
                best_r2 = r2
                self.best_model_name = name
                best_preds = y_pred

        sample_indices = range(min(40, len(y_test)))
        y_test_list = [round(float(v), 1) for v in y_test.iloc[sample_indices].values]
        best_pred_list = [round(float(v), 1) for v in best_preds[sample_indices]]

        self.test_comparison_data = {
            "indices": list(sample_indices),
            "actual": y_test_list,
            "predicted": best_pred_list,
            "model_name": self.best_model_name
        }

        gb = self.fitted_models["Gradient Boosting Regressor"]
        importances = gb.feature_importances_.tolist()
        feat_importances = [
            {"feature": feat, "importance": round(imp * 100, 2)}
            for feat, imp in sorted(zip(REGRESSION_FEATURES, importances), key=lambda x: x[1], reverse=True)
        ]

        self.metrics["feature_importances"] = feat_importances
        self.metrics["best_model"] = self.best_model_name
        self.metrics["comparison_sample"] = self.test_comparison_data

        self.save_models()
        return self.metrics

    def predict_recovery_time(self, input_data: dict, model_name: str = None) -> dict:
        if not self.fitted_models:
            self.load_models()

        if model_name is None or model_name not in self.fitted_models:
            model_name = self.best_model_name

        reg = self.fitted_models[model_name]

        dcp_corr = float(input_data.get("dcp_corruption_pct", 0.0))
        broken_kdm = int(input_data.get("broken_kdm", 0))
        kdm_dec_fail = int(input_data.get("kdm_decryption_failure", 0))
        firmware = int(input_data.get("firmware_update_required", 0))
        sound_sync = abs(float(input_data.get("sound_sync_error_ms", 0.0)))
        net_delay = float(input_data.get("network_delay_ms", 45.0))
        file_size = float(input_data.get("dcp_file_size_gb", 140.0))
        server_load = float(input_data.get("server_load", 35.0))

        row = {
            "dcp_corruption_pct": dcp_corr,
            "broken_kdm": broken_kdm,
            "kdm_decryption_failure": kdm_dec_fail,
            "firmware_update_required": firmware,
            "abs_sound_sync_error_ms": sound_sync,
            "network_delay_ms": net_delay,
            "dcp_file_size_gb": file_size,
            "server_load": server_load
        }

        X_inst = pd.DataFrame([row])[REGRESSION_FEATURES]

        if model_name in ["Linear Regression", "Support Vector Regression"]:
            X_inst_scaled = self.scaler.transform(X_inst)
            pred_time = float(reg.predict(X_inst_scaled)[0])
        else:
            pred_time = float(reg.predict(X_inst)[0])

        pred_time = max(8.0, round(pred_time, 1))

        breakdowns = []
        warnings = []

        if broken_kdm == 1 or kdm_dec_fail == 1:
            warnings.append(
                "CRITICAL KDM ISSUE: KDM cannot decrypt the encrypted DCP. "
                "Immediate intervention required: Contact KDM delivery distributor/laboratory for key reissue."
            )
            breakdowns.append({"problem": "Broken KDM / Decryption Failure", "estimated_impact": "45 - 90 mins", "severity": "HIGH"})

        if dcp_corr > 2.0:
            est_mxf_time = round(dcp_corr * (file_size / 80.0) * 1.5, 1)
            warnings.append(f"DCP Corruption Detected: {dcp_corr}% corrupted packets. MXF reel hash re-validation and delta transfer required.")
            breakdowns.append({"problem": "DCP Hash Re-verification & Reel Re-transfer", "estimated_impact": f"{est_mxf_time} mins", "severity": "MEDIUM" if dcp_corr < 10 else "HIGH"})

        if firmware == 1:
            warnings.append("Firmware Update Required: Server / Media Block firmware update and security handshake needed.")
            breakdowns.append({"problem": "Security Block Firmware Patch & Reboot", "estimated_impact": "40 - 75 mins", "severity": "MEDIUM"})

        if sound_sync > 30.0:
            warnings.append(f"Sound Synchronization Error: Audio offset is {sound_sync} ms (exceeds SMPTE +/-20ms standard).")
            breakdowns.append({"problem": "Audio/Video Buffer Alignment & Calibration", "estimated_impact": "15 - 35 mins", "severity": "LOW" if sound_sync < 60 else "MEDIUM"})

        if not breakdowns:
            breakdowns.append({"problem": "Routine Pipeline Verification", "estimated_impact": "10 - 15 mins", "severity": "LOW"})

        return {
            "model_used": model_name,
            "predicted_recovery_time_min": pred_time,
            "breakdowns": breakdowns,
            "warnings": warnings,
            "inputs": row
        }

    def save_models(self):
        os.makedirs(MODELS_DIR, exist_ok=True)
        dump_path = os.path.join(MODELS_DIR, "regression_bundle.joblib")
        joblib.dump({
            "models": self.fitted_models,
            "scaler": self.scaler,
            "metrics": self.metrics,
            "best_model_name": self.best_model_name,
            "comparison_sample": self.test_comparison_data
        }, dump_path)

    def load_models(self):
        dump_path = os.path.join(MODELS_DIR, "regression_bundle.joblib")
        if os.path.exists(dump_path):
            bundle = joblib.load(dump_path)
            self.fitted_models = bundle["models"]
            self.scaler = bundle["scaler"]
            self.metrics = bundle["metrics"]
            self.best_model_name = bundle.get("best_model_name", "Gradient Boosting Regressor")
            self.test_comparison_data = bundle.get("comparison_sample", {})
            return True
        return False
