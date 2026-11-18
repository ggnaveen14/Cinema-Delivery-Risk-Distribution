import sqlite3
import pandas as pd
import json
import datetime
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import DATABASE_PATH

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        row_count INTEGER NOT NULL,
        is_synthetic INTEGER DEFAULT 1,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cinema_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_id INTEGER,
        cinema_screen TEXT NOT NULL,
        time_step INTEGER NOT NULL,
        payment_completed INTEGER NOT NULL,
        kdm_available INTEGER NOT NULL,
        kdm_decryptable INTEGER NOT NULL,
        kdm_expired INTEGER NOT NULL,
        dcp_corruption_pct REAL NOT NULL,
        firmware_update_required INTEGER NOT NULL,
        sound_sync_error_ms REAL NOT NULL,
        network_delay_ms REAL NOT NULL,
        recovery_time_min REAL NOT NULL,
        delivery_risk TEXT NOT NULL,
        simulated_state TEXT DEFAULT 'Stable Delivery',
        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prediction_type TEXT NOT NULL,
        inputs_json TEXT NOT NULL,
        result_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def save_dataframe_to_db(df: pd.DataFrame, filename: str, is_synthetic: bool = True) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE datasets SET is_active = 0")
    cursor.execute(
        "INSERT INTO datasets (filename, row_count, is_synthetic, is_active) VALUES (?, ?, ?, 1)",
        (filename, len(df), 1 if is_synthetic else 0)
    )
    dataset_id = cursor.lastrowid

    cursor.execute("DELETE FROM cinema_records")

    records = []
    for _, row in df.iterrows():
        records.append((
            dataset_id,
            str(row["cinema_screen"]),
            int(row["time_step"]),
            int(row["payment_completed"]),
            int(row["kdm_available"]),
            int(row["kdm_decryptable"]),
            int(row["kdm_expired"]),
            float(row["dcp_corruption_pct"]),
            int(row["firmware_update_required"]),
            float(row["sound_sync_error_ms"]),
            float(row["network_delay_ms"]),
            float(row["recovery_time_min"]),
            str(row.get("delivery_risk", "NORMAL")),
            str(row.get("simulated_state", "Stable Delivery"))
        ))

    cursor.executemany("""
        INSERT INTO cinema_records (
            dataset_id, cinema_screen, time_step, payment_completed,
            kdm_available, kdm_decryptable, kdm_expired, dcp_corruption_pct,
            firmware_update_required, sound_sync_error_ms, network_delay_ms,
            recovery_time_min, delivery_risk, simulated_state
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)

    conn.commit()
    conn.close()
    return dataset_id

def load_active_dataframe() -> pd.DataFrame:
    conn = get_connection()
    query = """
    SELECT cinema_screen, time_step, payment_completed, kdm_available,
           kdm_decryptable, kdm_expired, dcp_corruption_pct, firmware_update_required,
           sound_sync_error_ms, network_delay_ms, recovery_time_min, delivery_risk, simulated_state
    FROM cinema_records
    ORDER BY cinema_screen, time_step
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_active_dataset_info():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def log_prediction(pred_type: str, inputs: dict, result: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO predictions (prediction_type, inputs_json, result_json) VALUES (?, ?, ?)",
        (pred_type, json.dumps(inputs), json.dumps(result))
    )
    conn.commit()
    conn.close()
