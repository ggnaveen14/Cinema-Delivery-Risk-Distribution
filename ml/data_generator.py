import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np
import pandas as pd
from config import SAMPLE_DATASET_PATH, REQUIRED_COLUMNS

def generate_synthetic_cinema_dataset(num_screens: int = 20, weeks: int = 26, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates realistic, physically-sound digital cinema operational delivery data.
    Includes simulated_state for HMM sequence ground truth evaluation.
    Clearly labeled as SYNTHETIC demonstration data.
    """
    np.random.seed(random_seed)
    records = []

    screen_ids = [f"SCR-{i:02d}" for i in range(1, num_screens + 1)]

    for screen in screen_ids:
        network_base = np.random.uniform(30.0, 65.0)
        firmware_cycle = np.random.randint(10, 24)

        for week in range(1, weeks + 1):
            # 1. Weekly payment status
            payment_completed = 1 if np.random.rand() > 0.12 else 0

            # 2. KDM Availability Rule:
            if payment_completed == 1:
                kdm_available = 1 if np.random.rand() > 0.03 else 0
            else:
                kdm_available = 0 if np.random.rand() > 0.20 else 1

            # 3. KDM Decryptability:
            if kdm_available == 1:
                kdm_decryptable = 1 if np.random.rand() > 0.05 else 0
            else:
                kdm_decryptable = 0

            # 4. KDM Expiry:
            kdm_expired = 1 if np.random.rand() < 0.04 else 0

            # 5. DCP Corruption Percentage:
            if np.random.rand() < 0.09:
                dcp_corruption_pct = round(np.random.uniform(5.0, 38.0), 2)
            else:
                dcp_corruption_pct = round(np.random.uniform(0.0, 1.5), 2)

            # 6. Firmware Update Requirement:
            firmware_update_required = 1 if (week % firmware_cycle == 0 or np.random.rand() < 0.07) else 0

            # 7. Sound Synchronization Error (ms):
            if np.random.rand() < 0.12:
                sound_sync_error_ms = round(np.random.choice([-1, 1]) * np.random.uniform(45.0, 140.0), 1)
            else:
                sound_sync_error_ms = round(np.random.normal(0.0, 8.0), 1)

            # 8. Network Delay (ms):
            if np.random.rand() < 0.10:
                network_delay_ms = round(network_base + np.random.uniform(150.0, 420.0), 1)
            else:
                network_delay_ms = round(network_base + np.random.normal(0.0, 10.0), 1)
                network_delay_ms = max(15.0, network_delay_ms)

            # Compute Recovery Time in Minutes
            recovery = 10.0
            if kdm_available == 0 or kdm_decryptable == 0:
                recovery += np.random.uniform(45.0, 95.0)
            if kdm_expired == 1:
                recovery += np.random.uniform(30.0, 60.0)
            if firmware_update_required == 1:
                recovery += np.random.uniform(40.0, 75.0)
            if dcp_corruption_pct > 2.0:
                recovery += dcp_corruption_pct * 2.1
            if abs(sound_sync_error_ms) > 30.0:
                recovery += abs(sound_sync_error_ms) * 0.22
            recovery += (network_delay_ms * 0.06)
            recovery += np.random.normal(0.0, 4.0)
            recovery_time_min = round(max(8.0, recovery), 1)

            # Risk Category
            if (kdm_available == 0 or kdm_decryptable == 0 or kdm_expired == 1 or dcp_corruption_pct > 15.0):
                delivery_risk = "CRITICAL"
                simulated_state = "Critical Delivery"
            elif (payment_completed == 0 or network_delay_ms > 180.0 or
                  firmware_update_required == 1 or abs(sound_sync_error_ms) > 35.0 or
                  dcp_corruption_pct > 2.5):
                delivery_risk = "WARNING"
                simulated_state = "Degraded Delivery"
            else:
                delivery_risk = "NORMAL"
                simulated_state = "Stable Delivery"

            records.append({
                "cinema_screen": screen,
                "time_step": week,
                "payment_completed": payment_completed,
                "kdm_available": kdm_available,
                "kdm_decryptable": kdm_decryptable,
                "kdm_expired": kdm_expired,
                "dcp_corruption_pct": dcp_corruption_pct,
                "firmware_update_required": firmware_update_required,
                "sound_sync_error_ms": sound_sync_error_ms,
                "network_delay_ms": network_delay_ms,
                "recovery_time_min": recovery_time_min,
                "delivery_risk": delivery_risk,
                "simulated_state": simulated_state
            })

    df = pd.DataFrame(records)
    return df

def save_sample_excel():
    os.makedirs(os.path.dirname(SAMPLE_DATASET_PATH), exist_ok=True)
    df = generate_synthetic_cinema_dataset()
    with pd.ExcelWriter(SAMPLE_DATASET_PATH, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="CinemaDelivery_Data", index=False)
        meta_df = pd.DataFrame([
            {"Key": "Project", "Value": "Predictive Optimization of Digital Cinema Content Delivery Using Machine Learning"},
            {"Key": "Dataset Type", "Value": "Synthetic Demonstration Dataset"},
            {"Key": "Total Records", "Value": len(df)},
            {"Key": "Total Cinema Screens", "Value": df["cinema_screen"].nunique()},
            {"Key": "Weeks Covered", "Value": df["time_step"].max()},
            {"Key": "Notice", "Value": "Synthesized to simulate SMPTE digital cinema delivery failure modes. Does not represent proprietary commercial cinema operations."}
        ])
        meta_df.to_excel(writer, sheet_name="Dataset_Metadata", index=False)
    return SAMPLE_DATASET_PATH

if __name__ == "__main__":
    path = save_sample_excel()
    print(f"Sample dataset saved to {path}")
