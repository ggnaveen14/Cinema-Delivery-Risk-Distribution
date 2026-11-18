import os
import sys
import io
import json
import sqlite3

# Ensure project root is always in Python module search path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename

from config import (
    FLASK_CONFIG, DATA_DIR, MODELS_DIR, SAMPLE_DATASET_PATH,
    REQUIRED_COLUMNS, RISK_MAPPING
)
from database import (
    init_db, save_dataframe_to_db, load_active_dataframe,
    get_active_dataset_info, log_prediction
)
from ml.data_generator import generate_synthetic_cinema_dataset, save_sample_excel
from ml.preprocessor import CinemaDataPreprocessor
from ml.classifier import CinemaRiskClassifier
from ml.ensemble import CinemaEnsembleClassifier
from ml.regressor import CinemaRecoveryRegressor
from ml.clustering import CinemaDeliveryClusterer
from ml.hmm_model import CinemaHMMAnalyzer
from ml.optimizer import CinemaDeliveryOptimizer
from reports.excel_report import generate_excel_report
from reports.pdf_report import generate_pdf_report

app = Flask(__name__)
app.config["SECRET_KEY"] = FLASK_CONFIG["SECRET_KEY"]
app.config["MAX_CONTENT_LENGTH"] = FLASK_CONFIG["MAX_CONTENT_LENGTH"]

# ML Model Singletons
classifier_engine = CinemaRiskClassifier()
ensemble_engine = CinemaEnsembleClassifier()
regressor_engine = CinemaRecoveryRegressor()
clustering_engine = CinemaDeliveryClusterer()
hmm_engine = CinemaHMMAnalyzer()
preprocessor_engine = CinemaDataPreprocessor()

CACHED_ANALYTICS = {
    "classification": {},
    "ensemble": {},
    "regression": {},
    "clustering": {},
    "hmm": {},
    "recommendations": []
}

def bootstrap_application():
    init_db()
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    df = load_active_dataframe()
    if df.empty:
        print("[CinemaPredict] Initializing default synthetic cinema dataset...")
        save_sample_excel()
        raw_df = generate_synthetic_cinema_dataset()
        cleaned_df, _ = preprocessor_engine.clean_and_prepare(raw_df)
        save_dataframe_to_db(cleaned_df, "sample_cinema_delivery.xlsx", is_synthetic=True)
        df = cleaned_df

    train_all_models(df)

def train_all_models(df: pd.DataFrame):
    print(f"[CinemaPredict] Training ML models on {len(df)} records across {df['cinema_screen'].nunique()} screens...")
    global CACHED_ANALYTICS

    try:
        class_metrics = classifier_engine.train_and_evaluate(df)
        CACHED_ANALYTICS["classification"] = class_metrics
    except Exception as e:
        print(f"[ERROR] Classifier training: {e}")

    try:
        ensemble_metrics = ensemble_engine.train_and_evaluate(df)
        CACHED_ANALYTICS["ensemble"] = ensemble_metrics
    except Exception as e:
        print(f"[ERROR] Ensemble training: {e}")

    try:
        reg_metrics = regressor_engine.train_and_evaluate(df)
        CACHED_ANALYTICS["regression"] = reg_metrics
    except Exception as e:
        print(f"[ERROR] Regressor training: {e}")

    try:
        cluster_results = clustering_engine.fit_and_analyze(df)
        CACHED_ANALYTICS["clustering"] = cluster_results
    except Exception as e:
        print(f"[ERROR] Clustering analysis: {e}")

    try:
        hmm_results = hmm_engine.fit_and_evaluate(df)
        CACHED_ANALYTICS["hmm"] = hmm_results
    except Exception as e:
        print(f"[ERROR] HMM analysis: {e}")

    try:
        recs = CinemaDeliveryOptimizer.generate_recommendations(df)
        CACHED_ANALYTICS["recommendations"] = recs
    except Exception as e:
        print(f"[ERROR] Recommendations generation: {e}")

    print("[CinemaPredict] ML models training and analytics caching complete.")

# -------------------------------------------------------------
# PAGE ROUTE
# -------------------------------------------------------------
@app.route("/")
def index():
    active_dataset = get_active_dataset_info()
    return render_template("index.html", dataset_info=active_dataset)

# -------------------------------------------------------------
# API: DASHBOARD OVERVIEW & KPIS
# -------------------------------------------------------------
@app.route("/api/dashboard", methods=["GET"])
def get_dashboard_data():
    df = load_active_dataframe()
    if df.empty:
        return jsonify({"error": "No active dataset loaded"}), 400

    dataset_info = get_active_dataset_info() or {}

    total_screens = int(df["cinema_screen"].nunique())
    total_deliveries = len(df)
    kdm_avail_rate = round(float(df["kdm_available"].mean() * 100), 2)
    kdm_dec_rate = round(float(df["kdm_decryptable"].mean() * 100), 2)
    payment_rate = round(float(df["payment_completed"].mean() * 100), 2)

    dcp_corruption_incidents = int((df["dcp_corruption_pct"] > 2.0).sum())
    firmware_alerts = int((df["firmware_update_required"] == 1).sum())
    sound_sync_errors = int((df["sound_sync_error_ms"].abs() > 20.0).sum())
    critical_incidents = int((df["delivery_risk"] == "CRITICAL").sum())
    warning_incidents = int((df["delivery_risk"] == "WARNING").sum())
    normal_incidents = int((df["delivery_risk"] == "NORMAL").sum())
    avg_recovery_time = round(float(df["recovery_time_min"].mean()), 1)

    weekly_agg = df.groupby("time_step").agg({
        "kdm_available": lambda s: round(s.mean() * 100, 1),
        "payment_completed": lambda s: round(s.mean() * 100, 1),
        "dcp_corruption_pct": lambda s: round(s.mean(), 2),
        "recovery_time_min": lambda s: round(s.mean(), 1)
    }).reset_index()

    risk_distribution = {
        "NORMAL": normal_incidents,
        "WARNING": warning_incidents,
        "CRITICAL": critical_incidents
    }

    df["month_group"] = ((df["time_step"] - 1) // 4) + 1
    months = [f"Month {m}" for m in df["month_group"].unique()]
    month_normal = [int((df[df['month_group'] == m]['delivery_risk'] == 'NORMAL').sum()) for m in df['month_group'].unique()]
    month_warning = [int((df[df['month_group'] == m]['delivery_risk'] == 'WARNING').sum()) for m in df['month_group'].unique()]
    month_critical = [int((df[df['month_group'] == m]['delivery_risk'] == 'CRITICAL').sum()) for m in df['month_group'].unique()]

    kdm_table_records = []
    latest_step = df["time_step"].max()
    recent_kdm_df = df[df["time_step"] >= max(1, latest_step - 3)].sort_values(by=["time_step", "cinema_screen"], ascending=[False, True])

    for _, r in recent_kdm_df.head(60).iterrows():
        pay_status = "Completed" if r["payment_completed"] == 1 else "Pending Payment"
        kdm_issued = "Issued" if r["kdm_available"] == 1 else "Withheld / Not Issued"
        kdm_expiry_str = "Expired" if r["kdm_expired"] == 1 else "Valid Active"
        dec_status = "Decrypted OK" if r["kdm_decryptable"] == 1 else "Decryption Failed"
        dcp_status = "Corrupted" if r["dcp_corruption_pct"] > 2.0 else "Valid DCP"
        fw_status = "Update Pending" if r["firmware_update_required"] == 1 else "Up to date"
        sound_status = f"{r['sound_sync_error_ms']}ms Error" if abs(r['sound_sync_error_ms']) > 20.0 else "Synced (<20ms)"

        kdm_table_records.append({
            "week": int(r["time_step"]),
            "cinema_screen": str(r["cinema_screen"]),
            "payment_status": pay_status,
            "kdm_issued": kdm_issued,
            "kdm_expiry": kdm_expiry_str,
            "decryption_status": dec_status,
            "dcp_status": dcp_status,
            "firmware_status": fw_status,
            "sound_status": sound_status,
            "delivery_risk": str(r["delivery_risk"]),
            "dcp_corruption_pct": float(r["dcp_corruption_pct"]),
            "recovery_time_min": float(r["recovery_time_min"])
        })

    return jsonify({
        "dataset_info": dataset_info,
        "kpis": {
            "total_screens": total_screens,
            "total_deliveries": total_deliveries,
            "kdm_availability_rate": kdm_avail_rate,
            "kdm_decryptability_rate": kdm_dec_rate,
            "payment_compliance_rate": payment_rate,
            "dcp_corruption_incidents": dcp_corruption_incidents,
            "firmware_alerts": firmware_alerts,
            "sound_sync_errors": sound_sync_errors,
            "critical_incidents": critical_incidents,
            "avg_recovery_time_min": avg_recovery_time
        },
        "charts": {
            "weekly_timeline": {
                "weeks": [f"W{int(w)}" for w in weekly_agg["time_step"]],
                "kdm_availability": weekly_agg["kdm_available"].tolist(),
                "payment_compliance": weekly_agg["payment_completed"].tolist(),
                "dcp_corruption": weekly_agg["dcp_corruption_pct"].tolist(),
                "avg_recovery_time": weekly_agg["recovery_time_min"].tolist()
            },
            "risk_distribution": risk_distribution,
            "monthly_performance": {
                "months": months,
                "normal": month_normal,
                "warning": month_warning,
                "critical": month_critical
            }
        },
        "recent_kdm_records": kdm_table_records
    })

# -------------------------------------------------------------
# API: CLASSIFICATION MODULE
# -------------------------------------------------------------
@app.route("/api/classification/metrics", methods=["GET"])
def get_classification_metrics():
    if not CACHED_ANALYTICS["classification"]:
        df = load_active_dataframe()
        CACHED_ANALYTICS["classification"] = classifier_engine.train_and_evaluate(df)
    return jsonify(CACHED_ANALYTICS["classification"])

@app.route("/api/classification/predict", methods=["POST"])
def predict_risk_single():
    try:
        data = request.get_json() or {}
        model_name = data.get("model_name", None)
        result = classifier_engine.predict_single(data, model_name=model_name)
        log_prediction("classification", data, result)
        return jsonify({"success": True, "prediction": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# -------------------------------------------------------------
# API: ENSEMBLE LEARNING MODULE
# -------------------------------------------------------------
@app.route("/api/ensemble/metrics", methods=["GET"])
def get_ensemble_metrics():
    if not CACHED_ANALYTICS["ensemble"]:
        df = load_active_dataframe()
        CACHED_ANALYTICS["ensemble"] = ensemble_engine.train_and_evaluate(df)
    return jsonify(CACHED_ANALYTICS["ensemble"])

# -------------------------------------------------------------
# API: REGRESSION MODULE
# -------------------------------------------------------------
@app.route("/api/regression/metrics", methods=["GET"])
def get_regression_metrics():
    if not CACHED_ANALYTICS["regression"]:
        df = load_active_dataframe()
        CACHED_ANALYTICS["regression"] = regressor_engine.train_and_evaluate(df)
    return jsonify(CACHED_ANALYTICS["regression"])

@app.route("/api/regression/predict", methods=["POST"])
def predict_recovery_time_single():
    try:
        data = request.get_json() or {}
        model_name = data.get("model_name", None)
        result = regressor_engine.predict_recovery_time(data, model_name=model_name)
        log_prediction("regression", data, result)
        return jsonify({"success": True, "prediction": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# -------------------------------------------------------------
# API: K-MEANS CLUSTERING
# -------------------------------------------------------------
@app.route("/api/clustering/results", methods=["GET"])
def get_clustering_results():
    if not CACHED_ANALYTICS["clustering"]:
        df = load_active_dataframe()
        CACHED_ANALYTICS["clustering"] = clustering_engine.fit_and_analyze(df)
    return jsonify(CACHED_ANALYTICS["clustering"])

# -------------------------------------------------------------
# API: HIDDEN MARKOV MODEL (HMM)
# -------------------------------------------------------------
@app.route("/api/hmm/results", methods=["GET"])
def get_hmm_results():
    if not CACHED_ANALYTICS["hmm"]:
        df = load_active_dataframe()
        CACHED_ANALYTICS["hmm"] = hmm_engine.fit_and_evaluate(df)
    return jsonify(CACHED_ANALYTICS["hmm"])

# -------------------------------------------------------------
# API: COMPARATIVE PERFORMANCE ANALYSIS
# -------------------------------------------------------------
@app.route("/api/comparison/summary", methods=["GET"])
def get_comparison_summary():
    return jsonify({
        "classification": CACHED_ANALYTICS.get("classification", {}),
        "ensemble": CACHED_ANALYTICS.get("ensemble", {}),
        "regression": CACHED_ANALYTICS.get("regression", {}),
        "clustering": {
            "selected_k": CACHED_ANALYTICS.get("clustering", {}).get("elbow_data", {}).get("selected_k", 4),
            "best_silhouette": CACHED_ANALYTICS.get("clustering", {}).get("silhouette_data", {}).get("best_silhouette", 0.0),
            "inertias": CACHED_ANALYTICS.get("clustering", {}).get("elbow_data", {}).get("inertias", [])
        },
        "hmm": {
            "train_ll": CACHED_ANALYTICS.get("hmm", {}).get("performance", {}).get("train_log_likelihood", 0),
            "test_ll": CACHED_ANALYTICS.get("hmm", {}).get("performance", {}).get("test_log_likelihood", 0),
            "train_ll_per_obs": CACHED_ANALYTICS.get("hmm", {}).get("performance", {}).get("train_ll_per_obs", 0),
            "test_ll_per_obs": CACHED_ANALYTICS.get("hmm", {}).get("performance", {}).get("test_ll_per_obs", 0)
        }
    })

# -------------------------------------------------------------
# API: PREDICTIVE OPTIMIZATION
# -------------------------------------------------------------
@app.route("/api/optimizer/recommendations", methods=["GET"])
def get_optimization_recommendations():
    if not CACHED_ANALYTICS["recommendations"]:
        df = load_active_dataframe()
        CACHED_ANALYTICS["recommendations"] = CinemaDeliveryOptimizer.generate_recommendations(df)
    return jsonify({
        "count": len(CACHED_ANALYTICS["recommendations"]),
        "recommendations": CACHED_ANALYTICS["recommendations"]
    })

# -------------------------------------------------------------
# API: EXCEL DATASET MANAGEMENT & UPLOAD
# -------------------------------------------------------------
@app.route("/api/dataset/preview", methods=["GET"])
def preview_dataset():
    df = load_active_dataframe()
    info = get_active_dataset_info() or {}
    limit = int(request.args.get("limit", 100))
    preview_records = df.head(limit).to_dict(orient="records") if not df.empty else []

    # Descriptive Statistics
    stats = {}
    if not df.empty:
        stats = {
            "dcp_corruption": {"mean": round(df["dcp_corruption_pct"].mean(), 2), "max": round(df["dcp_corruption_pct"].max(), 2)},
            "network_delay": {"mean": round(df["network_delay_ms"].mean(), 1), "max": round(df["network_delay_ms"].max(), 1)},
            "recovery_time": {"mean": round(df["recovery_time_min"].mean(), 1), "max": round(df["recovery_time_min"].max(), 1)},
            "kdm_availability_pct": round(df["kdm_available"].mean() * 100, 1),
            "payment_compliance_pct": round(df["payment_completed"].mean() * 100, 1)
        }

    return jsonify({
        "dataset_info": info,
        "columns": list(df.columns) if not df.empty else [],
        "total_records": len(df),
        "records": preview_records,
        "statistics": stats
    })

@app.route("/api/dataset/upload", methods=["POST"])
def upload_dataset():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".xlsx", ".xls", ".csv"]:
        return jsonify({"success": False, "error": f"Invalid format {ext}. Allowed: .xlsx, .xls, .csv"}), 400

    try:
        if ext == ".csv":
            raw_df = pd.read_csv(file)
        else:
            raw_df = pd.read_excel(file)

        is_valid, missing_cols = preprocessor_engine.validate_columns(raw_df)
        if not is_valid:
            return jsonify({
                "success": False,
                "error": f"Missing required columns: {', '.join(missing_cols)}",
                "required_columns": REQUIRED_COLUMNS
            }), 400

        cleaned_df, cleaning_stats = preprocessor_engine.clean_and_prepare(raw_df)

        dataset_id = save_dataframe_to_db(cleaned_df, filename, is_synthetic=False)
        train_all_models(cleaned_df)

        return jsonify({
            "success": True,
            "message": f"Successfully loaded and preprocessed {len(cleaned_df)} records.",
            "dataset_id": dataset_id,
            "cleaning_stats": cleaning_stats
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to process file: {str(e)}"}), 500

@app.route("/api/dataset/sample/download", methods=["GET"])
def download_sample_dataset():
    if not os.path.exists(SAMPLE_DATASET_PATH):
        save_sample_excel()
    return send_file(
        SAMPLE_DATASET_PATH,
        as_attachment=True,
        download_name="sample_cinema_delivery.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route("/api/dataset/download_processed", methods=["GET"])
def download_processed_dataset():
    df = load_active_dataframe()
    if df.empty:
        return jsonify({"error": "No data available"}), 400

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="CleanedCinemaData", index=False)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="cinemapredict_cleaned_dataset.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -------------------------------------------------------------
# API: REPORT GENERATION (EXCEL & PDF)
# -------------------------------------------------------------
@app.route("/api/reports/download/excel", methods=["GET"])
def download_excel_report():
    df = load_active_dataframe()
    stream = generate_excel_report(
        df=df,
        class_metrics=CACHED_ANALYTICS.get("classification", {}),
        reg_metrics=CACHED_ANALYTICS.get("regression", {}),
        cluster_results=CACHED_ANALYTICS.get("clustering", {}),
        hmm_results=CACHED_ANALYTICS.get("hmm", {}),
        recommendations=CACHED_ANALYTICS.get("recommendations", [])
    )
    return send_file(
        stream,
        as_attachment=True,
        download_name="CinemaPredict_Operational_Report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route("/api/reports/download/pdf", methods=["GET"])
def download_pdf_report():
    df = load_active_dataframe()
    stream = generate_pdf_report(
        df=df,
        class_metrics=CACHED_ANALYTICS.get("classification", {}),
        reg_metrics=CACHED_ANALYTICS.get("regression", {}),
        cluster_results=CACHED_ANALYTICS.get("clustering", {}),
        hmm_results=CACHED_ANALYTICS.get("hmm", {}),
        recommendations=CACHED_ANALYTICS.get("recommendations", [])
    )
    return send_file(
        stream,
        as_attachment=True,
        download_name="CinemaPredict_Operational_Report.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    bootstrap_application()
    app.run(host="127.0.0.1", port=5000, debug=True)
