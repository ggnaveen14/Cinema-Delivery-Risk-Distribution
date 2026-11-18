import io
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def generate_excel_report(df: pd.DataFrame, class_metrics: dict, reg_metrics: dict,
                          cluster_results: dict, hmm_results: dict, recommendations: list) -> io.BytesIO:
    """
    Generates a beautifully formatted multi-sheet Excel report containing all analytics,
    ML benchmarks, operational monitoring records, and actionable recommendations.
    """
    output = io.BytesIO()
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Styles
    navy_fill = PatternFill(start_color="0A192F", end_color="0A192F", fill_type="solid")
    gold_fill = PatternFill(start_color="D4AF37", end_color="D4AF37", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=16, bold=True, color="0A192F")
    bold_font = Font(name="Calibri", size=11, bold=True)
    regular_font = Font(name="Calibri", size=10)
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    # ----------------------------------------------------
    # SHEET 1: Executive Summary & KPIs
    # ----------------------------------------------------
    ws1 = wb.create_sheet(title="Executive Summary")
    ws1.views.sheetView[0].showGridLines = True

    ws1.cell(row=2, column=2, value="CinemaPredict - Digital Cinema Delivery Intelligence").font = title_font
    ws1.cell(row=3, column=2, value="Automated Operational Diagnostic & Machine Learning Benchmark Report").font = Font(name="Calibri", size=11, italic=True, color="64748B")

    # KPI Table
    kpis = [
        ("Total Cinema Screens Monitored", df["cinema_screen"].nunique() if not df.empty else 0),
        ("Total Delivery Operations Recorded", len(df)),
        ("KDM Availability Rate (%)", round((df["kdm_available"].mean() * 100), 2) if not df.empty else 0),
        ("KDM Decryption Success Rate (%)", round((df["kdm_decryptable"].mean() * 100), 2) if not df.empty else 0),
        ("DCP Packet Corruption Incidents", int((df["dcp_corruption_pct"] > 2.0).sum()) if not df.empty else 0),
        ("Firmware Update Maintenance Alerts", int((df["firmware_update_required"] == 1).sum()) if not df.empty else 0),
        ("Sound Sync Tolerance Errors (> 20ms)", int((df["sound_sync_error_ms"].abs() > 20.0).sum()) if not df.empty else 0),
        ("Critical Delivery Risks Flagged", int((df["delivery_risk"] == "CRITICAL").sum()) if "delivery_risk" in df.columns else 0),
        ("Average Predicted Recovery Time (min)", round(df["recovery_time_min"].mean(), 1) if not df.empty else 0),
    ]

    ws1.cell(row=5, column=2, value="Operational Key Performance Indicators (KPIs)").font = bold_font
    ws1.cell(row=6, column=2, value="Metric Description").fill = navy_fill
    ws1.cell(row=6, column=2).font = header_font
    ws1.cell(row=6, column=3, value="Observed Value").fill = navy_fill
    ws1.cell(row=6, column=3).font = header_font
    ws1.cell(row=6, column=3).alignment = center_align

    for i, (k, v) in enumerate(kpis, start=7):
        c1 = ws1.cell(row=i, column=2, value=k)
        c2 = ws1.cell(row=i, column=3, value=v)
        c1.font = regular_font
        c2.font = bold_font
        c2.alignment = center_align
        c1.border = thin_border
        c2.border = thin_border

    # ----------------------------------------------------
    # SHEET 2: ML Model Benchmark Comparisons
    # ----------------------------------------------------
    ws2 = wb.create_sheet(title="ML Model Benchmarks")
    ws2.views.sheetView[0].showGridLines = True

    # Classification Models
    ws2.cell(row=2, column=2, value="1. Cinema Delivery Risk Classification Models").font = title_font
    headers_cls = ["Model Algorithm", "Accuracy (%)", "Precision (%)", "Recall (%)", "F1-Score (%)"]
    for col_idx, h in enumerate(headers_cls, start=2):
        cell = ws2.cell(row=4, column=col_idx, value=h)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = center_align

    r = 5
    for model_name, metrics in class_metrics.items():
        if isinstance(metrics, dict) and "accuracy" in metrics:
            ws2.cell(row=r, column=2, value=model_name).font = bold_font
            ws2.cell(row=r, column=3, value=metrics.get("accuracy", 0)).alignment = center_align
            ws2.cell(row=r, column=4, value=metrics.get("precision", 0)).alignment = center_align
            ws2.cell(row=r, column=5, value=metrics.get("recall", 0)).alignment = center_align
            ws2.cell(row=r, column=6, value=metrics.get("f1_score", 0)).alignment = center_align
            for col_idx in range(2, 7):
                ws2.cell(row=r, column=col_idx).border = thin_border
            r += 1

    # Regression Models
    r += 2
    ws2.cell(row=r, column=2, value="2. Recovery Time Prediction Regression Models").font = title_font
    r += 2
    headers_reg = ["Model Algorithm", "MAE (min)", "RMSE (min)", "R² Score", "Variance Explained (%)"]
    for col_idx, h in enumerate(headers_reg, start=2):
        cell = ws2.cell(row=r, column=col_idx, value=h)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = center_align
    r += 1

    for model_name, metrics in reg_metrics.items():
        if isinstance(metrics, dict) and "mae" in metrics:
            ws2.cell(row=r, column=2, value=model_name).font = bold_font
            ws2.cell(row=r, column=3, value=metrics.get("mae", 0)).alignment = center_align
            ws2.cell(row=r, column=4, value=metrics.get("rmse", 0)).alignment = center_align
            ws2.cell(row=r, column=5, value=metrics.get("r2_score", 0)).alignment = center_align
            ws2.cell(row=r, column=6, value=metrics.get("accuracy_pct", 0)).alignment = center_align
            for col_idx in range(2, 7):
                ws2.cell(row=r, column=col_idx).border = thin_border
            r += 1

    # ----------------------------------------------------
    # SHEET 3: K-Means Failure Pattern Clusters
    # ----------------------------------------------------
    ws3 = wb.create_sheet(title="Failure Clusters")
    ws3.views.sheetView[0].showGridLines = True
    ws3.cell(row=2, column=2, value="K-Means Delivery Failure Cluster Profiles").font = title_font

    cluster_headers = ["Cluster ID", "Identified Pattern Label", "Sample Size", "% of Deliveries",
                       "Avg DCP Corruption (%)", "KDM Failure Rate (%)", "Avg Network Latency (ms)",
                       "Firmware Alert Rate (%)", "Avg Sound Sync Error (ms)"]
    for col_idx, h in enumerate(cluster_headers, start=2):
        cell = ws3.cell(row=4, column=col_idx, value=h)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = center_align

    r = 5
    for c in cluster_results.get("cluster_profiles", []):
        m = c.get("means", {})
        ws3.cell(row=r, column=2, value=c.get("cluster_id")).alignment = center_align
        ws3.cell(row=r, column=3, value=c.get("label")).font = bold_font
        ws3.cell(row=r, column=4, value=c.get("size")).alignment = center_align
        ws3.cell(row=r, column=5, value=f"{c.get('percentage')}%").alignment = center_align
        ws3.cell(row=r, column=6, value=m.get("dcp_corruption_pct")).alignment = center_align
        ws3.cell(row=r, column=7, value=f"{m.get('kdm_failure_rate_pct')}%").alignment = center_align
        ws3.cell(row=r, column=8, value=m.get("network_delay_ms")).alignment = center_align
        ws3.cell(row=r, column=9, value=f"{m.get('firmware_update_pct')}%").alignment = center_align
        ws3.cell(row=r, column=10, value=m.get("sound_sync_error_ms")).alignment = center_align
        for col_idx in range(2, 11):
            ws3.cell(row=r, column=col_idx).border = thin_border
        r += 1

    # ----------------------------------------------------
    # SHEET 4: Hidden Markov Model Results
    # ----------------------------------------------------
    ws4 = wb.create_sheet(title="HMM Sequence Dynamics")
    ws4.views.sheetView[0].showGridLines = True
    ws4.cell(row=2, column=2, value="Hidden Markov Model - Operational State Dynamics").font = title_font

    # Initial Probabilities
    ws4.cell(row=4, column=2, value="Hidden Operational State").fill = navy_fill
    ws4.cell(row=4, column=2).font = header_font
    ws4.cell(row=4, column=3, value="Initial State Probability").fill = navy_fill
    ws4.cell(row=4, column=3).font = header_font

    r = 5
    for item in hmm_results.get("initial_state_probabilities", []):
        ws4.cell(row=r, column=2, value=item.get("state")).font = bold_font
        ws4.cell(row=r, column=3, value=item.get("probability")).alignment = center_align
        ws4.cell(row=r, column=2).border = thin_border
        ws4.cell(row=r, column=3).border = thin_border
        r += 1

    # Transition Matrix
    r += 2
    ws4.cell(row=r, column=2, value="Hidden State Transition Probability Matrix").font = bold_font
    r += 1
    tmat = hmm_results.get("transition_matrix", {})
    states = tmat.get("states", ["STABLE", "DEGRADED", "CRITICAL"])
    matrix = tmat.get("matrix", [])

    ws4.cell(row=r, column=2, value="From \\ To State").fill = navy_fill
    ws4.cell(row=r, column=2).font = header_font
    for c_idx, s in enumerate(states, start=3):
        ws4.cell(row=r, column=c_idx, value=s).fill = navy_fill
        ws4.cell(row=r, column=c_idx).font = header_font
        ws4.cell(row=r, column=c_idx).alignment = center_align
    r += 1

    for row_idx, s_from in enumerate(states):
        ws4.cell(row=r, column=2, value=s_from).font = bold_font
        ws4.cell(row=r, column=2).border = thin_border
        for col_idx, s_to in enumerate(states, start=3):
            val = matrix[row_idx][col_idx - 3] if row_idx < len(matrix) and (col_idx - 3) < len(matrix[row_idx]) else 0
            cell = ws4.cell(row=r, column=col_idx, value=val)
            cell.alignment = center_align
            cell.border = thin_border
        r += 1

    # ----------------------------------------------------
    # SHEET 5: Proactive Operational Recommendations
    # ----------------------------------------------------
    ws5 = wb.create_sheet(title="Predictive Advisory")
    ws5.views.sheetView[0].showGridLines = True
    ws5.cell(row=2, column=2, value="Intelligent Cinema Delivery Optimization Recommendations").font = title_font

    rec_headers = ["Cinema Screen", "Week", "Severity", "Category", "Identified Operational Issue", "Recommended Action", "Est. Recovery (min)"]
    for col_idx, h in enumerate(rec_headers, start=2):
        cell = ws5.cell(row=4, column=col_idx, value=h)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = center_align

    r = 5
    for rec in recommendations:
        ws5.cell(row=r, column=2, value=rec.get("screen")).alignment = center_align
        ws5.cell(row=r, column=3, value=rec.get("week")).alignment = center_align
        sev_cell = ws5.cell(row=r, column=4, value=rec.get("severity"))
        sev_cell.alignment = center_align
        sev_cell.font = bold_font
        if rec.get("severity") == "CRITICAL":
            sev_cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
            sev_cell.font = Font(name="Calibri", size=10, bold=True, color="991B1B")
        elif rec.get("severity") == "WARNING":
            sev_cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
            sev_cell.font = Font(name="Calibri", size=10, bold=True, color="92400E")

        ws5.cell(row=r, column=5, value=rec.get("category")).alignment = left_align
        ws5.cell(row=r, column=6, value=rec.get("issue")).alignment = left_align
        ws5.cell(row=r, column=7, value=rec.get("action")).alignment = left_align
        ws5.cell(row=r, column=8, value=rec.get("expected_recovery_time_min")).alignment = center_align
        for col_idx in range(2, 9):
            ws5.cell(row=r, column=col_idx).border = thin_border
        r += 1

    # ----------------------------------------------------
    # SHEET 6: Full Cinema Operational Records
    # ----------------------------------------------------
    ws6 = wb.create_sheet(title="Operational Records")
    ws6.views.sheetView[0].showGridLines = True
    ws6.cell(row=2, column=2, value="Raw Monitored Cinema Operational Records").font = title_font

    cols = list(df.columns)
    for col_idx, c in enumerate(cols, start=2):
        cell = ws6.cell(row=4, column=col_idx, value=c.upper().replace("_", " "))
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = center_align

    r = 5
    for _, row in df.iterrows():
        for col_idx, c in enumerate(cols, start=2):
            cell = ws6.cell(row=r, column=col_idx, value=row[c])
            cell.font = regular_font
            cell.border = thin_border
            if isinstance(row[c], (int, float)):
                cell.alignment = center_align
        r += 1

    # Auto-adjust column widths for all sheets
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 48)

    wb.save(output)
    output.seek(0)
    return output
