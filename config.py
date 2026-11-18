import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATABASE_PATH = os.path.join(BASE_DIR, "cinemapredict.db")

SAMPLE_DATASET_PATH = os.path.join(DATA_DIR, "sample_cinema_delivery.xlsx")

REQUIRED_COLUMNS = [
    "cinema_screen",
    "time_step",
    "payment_completed",
    "kdm_available",
    "kdm_decryptable",
    "kdm_expired",
    "dcp_corruption_pct",
    "firmware_update_required",
    "sound_sync_error_ms",
    "network_delay_ms",
    "recovery_time_min",
    "simulated_state"
]

NUMERIC_COLUMNS = [
    "time_step",
    "payment_completed",
    "kdm_available",
    "kdm_decryptable",
    "kdm_expired",
    "dcp_corruption_pct",
    "firmware_update_required",
    "sound_sync_error_ms",
    "network_delay_ms",
    "recovery_time_min"
]

RISK_MAPPING = {
    0: "NORMAL",
    1: "WARNING",
    2: "CRITICAL"
}

STATE_NAMES = ["Stable Delivery", "Degraded Delivery", "Critical Delivery"]

FLASK_CONFIG = {
    "SECRET_KEY": "cinemapredict-secret-key-pbl-2026",
    "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,
    "UPLOAD_EXTENSIONS": [".xlsx", ".xls", ".csv"]
}
