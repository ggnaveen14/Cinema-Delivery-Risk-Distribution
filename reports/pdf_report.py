import io
import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)

def generate_pdf_report(df: pd.DataFrame, class_metrics: dict, reg_metrics: dict,
                         cluster_results: dict, hmm_results: dict, recommendations: list) -> io.BytesIO:
    """
    Generates an executive-grade PDF analytics report using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    navy_dark = colors.HexColor("#0A192F")
    gold_accent = colors.HexColor("#D4AF37")
    slate_gray = colors.HexColor("#475569")
    light_bg = colors.HexColor("#F8FAFC")
    border_color = colors.HexColor("#CBD5E1")
    crit_bg = colors.HexColor("#FEE2E2")
    warn_bg = colors.HexColor("#FEF3C7")

    # Typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=navy_dark
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=gold_accent
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=navy_dark,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=slate_gray
    )

    bold_body_style = ParagraphStyle(
        "BoldBody_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=navy_dark
    )

    cell_style = ParagraphStyle(
        "Cell_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.black
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("CinemaPredict", title_style))
    story.append(Paragraph("AI-POWERED DIGITAL CINEMA DELIVERY INTELLIGENCE &bull; OPERATIONAL DIAGNOSTIC REPORT", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=2, color=gold_accent, spaceAfter=10))

    # Meta banner
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_p = Paragraph(
        f"<b>Generated:</b> {timestamp_str} | <b>Monitored Screens:</b> {df['cinema_screen'].nunique() if not df.empty else 0} | "
        f"<b>Total Monitored Delivery Runs:</b> {len(df)} | <b>Mode:</b> Production Decision-Support",
        body_style
    )
    story.append(meta_p)
    story.append(Spacer(1, 10))

    # 2. Executive Operational KPI Summary
    story.append(Paragraph("1. Executive Operational KPI Summary", h1_style))
    
    kpis = [
        ["Total Screens Monitored", str(df["cinema_screen"].nunique() if not df.empty else 0),
         "KDM Availability Rate", f"{df['kdm_available'].mean() * 100:.1f}%" if not df.empty else "N/A"],
        ["Total Delivery Operations", str(len(df)),
         "KDM Decryptability Rate", f"{df['kdm_decryptable'].mean() * 100:.1f}%" if not df.empty else "N/A"],
        ["DCP Packet Corruptions (>2%)", str(int((df["dcp_corruption_pct"] > 2.0).sum()) if not df.empty else 0),
         "Critical Delivery Flags", str(int((df["delivery_risk"] == "CRITICAL").sum()) if "delivery_risk" in df.columns else 0)],
        ["Firmware Update Incidents", str(int((df["firmware_update_required"] == 1).sum()) if not df.empty else 0),
         "Sound Sync Drift Incidents", str(int((df["sound_sync_error_ms"].abs() > 20.0).sum()) if not df.empty else 0)],
        ["Avg Recovery Time", f"{df['recovery_time_min'].mean():.1f} min" if not df.empty else "N/A",
         "Weekly Payment Compliance", f"{df['payment_completed'].mean() * 100:.1f}%" if not df.empty else "N/A"]
    ]

    kpi_table = Table(kpis, colWidths=[2.2 * inch, 1.2 * inch, 2.2 * inch, 1.4 * inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), light_bg),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (-1, -1), navy_dark),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # 3. Machine Learning Classification & Regression Benchmarks
    story.append(Paragraph("2. Machine Learning Algorithm Benchmarks", h1_style))

    # Classification table
    cls_data = [["Classification Model", "Accuracy", "Precision", "Recall", "F1-Score", "Evaluation Status"]]
    for model_name, m in class_metrics.items():
        if isinstance(m, dict) and "accuracy" in m:
            is_best = (model_name == class_metrics.get("best_model"))
            status_text = "Optimal Selected" if is_best else "Benchmarked"
            cls_data.append([
                model_name,
                f"{m.get('accuracy', 0):.2f}%",
                f"{m.get('precision', 0):.2f}%",
                f"{m.get('recall', 0):.2f}%",
                f"{m.get('f1_score', 0):.2f}%",
                status_text
            ])

    cls_table = Table(cls_data, colWidths=[2.0 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 1.4 * inch])
    cls_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), navy_dark),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(Paragraph("<b>A. Cinema Delivery Risk Classification (NORMAL / WARNING / CRITICAL)</b>", body_style))
    story.append(Spacer(1, 3))
    story.append(cls_table)
    story.append(Spacer(1, 8))

    # Regression table
    reg_data = [["Regression Model", "MAE (min)", "RMSE (min)", "R² Score", "Variance (%)", "Evaluation Status"]]
    for model_name, m in reg_metrics.items():
        if isinstance(m, dict) and "mae" in m:
            is_best = (model_name == reg_metrics.get("best_model"))
            status_text = "Optimal Selected" if is_best else "Benchmarked"
            reg_data.append([
                model_name,
                f"{m.get('mae', 0):.2f}",
                f"{m.get('rmse', 0):.2f}",
                f"{m.get('r2_score', 0):.4f}",
                f"{m.get('accuracy_pct', 0):.1f}%",
                status_text
            ])

    reg_table = Table(reg_data, colWidths=[2.0 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 1.4 * inch])
    reg_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), navy_dark),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(Paragraph("<b>B. Recovery Time Prediction (Expected Minutes to Resolve)</b>", body_style))
    story.append(Spacer(1, 3))
    story.append(reg_table)
    story.append(Spacer(1, 14))

    # 4. K-Means Delivery Failure Clusters
    story.append(Paragraph("3. K-Means Delivery Failure Pattern Analysis", h1_style))
    story.append(Paragraph(
        f"<b>Selected Optimal Clusters (K):</b> {cluster_results.get('elbow_data', {}).get('selected_k', 4)} | "
        f"<b>Peak Silhouette Score:</b> {cluster_results.get('silhouette_data', {}).get('best_silhouette', 'N/A')}",
        body_style
    ))
    story.append(Spacer(1, 4))

    clust_rows = [["ID", "Identified Operational Pattern", "Share", "Avg Corruption", "KDM Fail %", "Latency", "Firmware %"]]
    for c in cluster_results.get("cluster_profiles", []):
        m = c.get("means", {})
        clust_rows.append([
            str(c.get("cluster_id")),
            Paragraph(c.get("label"), cell_style),
            f"{c.get('percentage')}%",
            f"{m.get('dcp_corruption_pct')}%",
            f"{m.get('kdm_failure_rate_pct')}%",
            f"{m.get('network_delay_ms')} ms",
            f"{m.get('firmware_update_pct')}%"
        ])

    clust_table = Table(clust_rows, colWidths=[0.4 * inch, 2.7 * inch, 0.7 * inch, 0.9 * inch, 0.7 * inch, 0.8 * inch, 0.8 * inch])
    clust_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), navy_dark),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(clust_table)
    story.append(Spacer(1, 14))

    # Page break for HMM and Recommendations
    story.append(PageBreak())

    # 5. Hidden Markov Model Sequence Dynamics
    story.append(Paragraph("4. Hidden Markov Model Operational Dynamics (hmmlearn)", h1_style))
    hmm_perf = hmm_results.get("performance", {})
    story.append(Paragraph(
        f"<b>Train Log-Likelihood:</b> {hmm_perf.get('train_log_likelihood')} ({hmm_perf.get('train_ll_per_obs')} /obs) | "
        f"<b>Test Log-Likelihood:</b> {hmm_perf.get('test_log_likelihood')} ({hmm_perf.get('test_ll_per_obs')} /obs) | "
        f"<b>Train Sequences:</b> {hmm_perf.get('train_screens_count')} screens | <b>Holdout Test:</b> {hmm_perf.get('test_screens_count')} screens",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Transition matrix table
    tmat = hmm_results.get("transition_matrix", {})
    states = tmat.get("states", ["STABLE", "DEGRADED", "CRITICAL"])
    matrix = tmat.get("matrix", [])

    hmm_table_data = [["From \\ To State"] + states]
    for row_idx, s_from in enumerate(states):
        row_vals = [s_from]
        for col_idx in range(len(states)):
            val = matrix[row_idx][col_idx] if row_idx < len(matrix) and col_idx < len(matrix[row_idx]) else 0
            row_vals.append(f"{val * 100:.1f}%")
        hmm_table_data.append(row_vals)

    hmm_table = Table(hmm_table_data, colWidths=[2.0 * inch, 1.6 * inch, 1.6 * inch, 1.6 * inch])
    hmm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), navy_dark),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(Paragraph("<b>State Transition Probability Matrix (Temporal Degradation / Recovery)</b>", body_style))
    story.append(Spacer(1, 3))
    story.append(hmm_table)
    story.append(Spacer(1, 14))

    # 6. Prioritized Predictive Advisory & Action Plan
    story.append(Paragraph("5. Prioritized Predictive Advisory & Action Plan", h1_style))
    story.append(Paragraph("Actionable engineering recommendations generated by model inference and KDM business rules:", body_style))
    story.append(Spacer(1, 4))

    rec_rows = [["Screen", "Severity", "Category", "Identified Operational Issue & Recommended Action", "Recovery"]]
    top_recs = recommendations[:10] # Top 10 recommendations for report clarity
    for r in top_recs:
        combined_text = f"<b>{r.get('issue')}</b><br/>{r.get('action')}"
        rec_rows.append([
            r.get("screen"),
            r.get("severity"),
            r.get("category"),
            Paragraph(combined_text, cell_style),
            f"{r.get('expected_recovery_time_min'):.0f}m"
        ])

    rec_table = Table(rec_rows, colWidths=[0.8 * inch, 0.9 * inch, 1.4 * inch, 3.2 * inch, 0.7 * inch])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), navy_dark),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (4, 0), (4, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 14))

    # Footer note
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=6))
    notice_p = Paragraph(
        "<b>Notice:</b> CinemaPredict is a decision-support advisory system designed for digital cinema network operations. "
        "Cryptographic KDM keys must be requested and generated through authorized distribution partners and SMPTE security authorities.",
        ParagraphStyle("Notice", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=7, leading=9, textColor=slate_gray)
    )
    story.append(notice_p)

    doc.build(story)
    buffer.seek(0)
    return buffer
