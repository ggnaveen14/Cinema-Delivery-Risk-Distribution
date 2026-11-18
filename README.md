# CinemaPredict – Predictive Optimization of Digital Cinema Content Delivery Using Machine Learning

> **AI-Powered Digital Cinema Delivery Intelligence**  
> *A comprehensive Machine Learning Decision-Support System for DCI Theater Management Systems (TMS) and Cinema Network Operations Centers (NOC).*

---

## 1. Project Overview

**CinemaPredict** is a full-stack predictive optimization platform designed to monitor digital cinema content delivery, identify operational bottlenecks, forecast showtime risks, and minimize recovery time using machine learning.

In modern theatrical distribution, movie content is packaged into **Digital Cinema Packages (DCP)** and encrypted with SMPTE-standard AES-128 cryptographic keys known as **Key Delivery Messages (KDM)**. If distributor licensing payments lapse, KDMs expire, or network transport corruption occurs, auditoriums face showtime cancellations and substantial box-office revenue loss. 

CinemaPredict addresses this challenge by applying supervised classification, ensemble learning, unsupervised failure clustering, and sequential Hidden Markov Models (HMM) to operational delivery telemetry.

---

## 2. Key Architecture & Features

### A. Cinema Operations Dashboard
- **7 Operational KPI Cards:** Total Screens, Total Deliveries, KDM Availability %, DCP Corruption Incidents, Firmware Update Alerts, Sound Sync Errors, and Critical Incidents.
- **Interactive Telemetry Visualizations (Plotly.js):**
  - Weekly KDM Availability vs. Payment Compliance
  - Cinema Delivery Risk Distribution (NORMAL / WARNING / CRITICAL Donut)
  - DCP Corruption & Packet Loss Trends vs Recovery Time
  - Monthly Delivery Performance Projection (4-week batches)
- **Weekly KDM Monitoring Table:** Filterable table tracking weekly distributor payments, KDM issuance status, license expiry, certificate decryptability, and delivery risk.

### B. Machine Learning Modules
1. **Cinema Delivery Risk Classification (Supervised):**
   - **Algorithms:** Random Forest Classifier, Support Vector Machine (SVM), Logistic Regression, and Decision Tree.
   - **Features:** Weekly payment status, KDM availability, KDM expiry, KDM decryptability, DCP corruption %, and network delay.
   - **Outputs:** Evaluation benchmarks (Accuracy, Precision, Recall, Weighted F1), 3x3 Confusion Matrix Heatmap, Feature Importances, and an Interactive Real-Time Manual Inference Calculator.
2. **Ensemble Learning Module:**
   - **Algorithms:** Random Forest, Bagging Classifier, Soft-Voting Classifier, and Gradient Boosting Classifier.
   - **Visualizations:** Accuracy comparison bar chart, Precision vs. Recall balance, and Ensemble Confusion Matrix.
3. **Recovery Time Prediction (Regression):**
   - **Algorithms:** Gradient Boosting Regressor, Random Forest Regressor, Support Vector Regression (SVR), and Linear Regression.
   - **Target:** Expected recovery time in minutes (`recovery_time_min`).
   - **Visualizations:** MAE, RMSE, $R^2$ Score, Actual vs. Predicted scatter plot, and Interactive Recovery Time Estimator with issue breakdown (broken KDMs, DCP hash corruption, firmware patches, sound buffer alignment).
4. **Failure Pattern Analysis (K-Means Clustering):**
   - **Algorithms:** Unsupervised K-Means with PCA 2D spatial reduction.
   - **Visualizations:**
     - Graph 1: Elbow Method (Inertia vs $K=2..10$ with optimal $K$ highlight).
     - Graph 2: Silhouette Score Analysis.
     - Graph 3: 2D PCA Cluster Scatter Visualization ($PC_1$ vs $PC_2$ with cluster legends).
     - Graph 4: Cluster Profile Comparison Radar and Bar Charts with dynamic failure pattern interpretations.
5. **Sequential State Prediction (Hidden Markov Models):**
   - **Algorithm:** Gaussian Hidden Markov Model (`hmmlearn.hmm.GaussianHMM`) evaluated on independent chronological screen sequences.
   - **States:** Stable Delivery ($S_0$), Degraded Delivery ($S_1$), and Critical Delivery ($S_2$).
   - **Visualizations:**
     - Graph 1: Initial State Probability Distribution ($\pi$).
     - Graph 2: State Transition Probability Matrix ($A$ Matrix Heatmap).
     - Graph 3: Emission Probability Matrix ($B$ Matrix Heatmap).
     - Graph 4: Inferred Hidden State Timeline across weeks for individual screens (Viterbi Decoding).
     - Graph 5: Training vs. Holdout Testing Log-Likelihood performance metrics.

### C. Predictive Optimization & Advisory
- Proactive alerts categorized by severity (CRITICAL, WARNING).
- Direct operational remediation steps for authorized cinema technicians and KDM distribution agencies (e.g. Deluxe, Technicolor, Qube).

### D. Dataset Management & Ingest
- Drag & Drop upload facility for `.xlsx`, `.xls`, and `.csv` files.
- Automated schema validation against required SMPTE delivery columns:
  `cinema_screen`, `time_step`, `payment_completed`, `kdm_available`, `kdm_decryptable`, `kdm_expired`, `dcp_corruption_pct`, `firmware_update_required`, `sound_sync_error_ms`, `network_delay_ms`, `recovery_time_min`, `simulated_state`.
- Automated missing value imputation, deduplication, and on-the-fly ML retraining.
- Downloadable synthetic demonstration dataset.

### E. Formal Report Generation
- **Excel (.xlsx) Report:** Formatted multi-sheet workbook covering Executive Summary, ML Benchmarks, K-Means Profiles, HMM Sequence Matrices, Predictive Action Items, and Full Telemetry Records.
- **PDF (.pdf) Report:** Executive document with cinema dark theme header, complete metric tables, cluster profiles, and actionable engineering recommendations.

---

## 3. Technology Stack

- **Frontend:** HTML5, CSS3 (Custom Dark Cinema Glassmorphism theme with Electric Cyan, Purple, and Gold highlights), JavaScript (Vanilla ES6+), Plotly.js 2.29, Font Awesome 6.
- **Backend:** Python Flask 3.1, SQLite 3.
- **Machine Learning & Data Science:** Scikit-learn, hmmlearn, Pandas, NumPy.
- **Document & Spreadsheet Generation:** OpenPyXL, ReportLab.

---

## 4. Installation & Local Execution

### Prerequisites
- Python 3.10+ installed on your system.

### Step 1: Clone or Navigate to the Project Directory
```powershell
cd C:\Users\Kavinraj\.gemini\antigravity\scratch\cinemapredict
```

### Step 2: Install Python Dependencies
```powershell
pip install flask pandas numpy scikit-learn hmmlearn openpyxl reportlab
```

### Step 3: Run the Application
```powershell
python run.py
```
*Or:*
```powershell
python app.py
```

### Step 4: Access the Web Dashboard
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 5. College PBL Presentation & Review Guide

When presenting this project for your academic review, highlight:
1. **Genuine Machine Learning Pipelines:** All graphs and model evaluations are calculated from the active dataset in real-time, with zero fabricated or static mock metrics.
2. **KDM Business Rules:** How the model captures the real-world operational dependency between weekly distributor billing compliance and cryptographic KDM license delivery.
3. **Temporal Independence in HMM:** Emphasize that sequences from different cinema screens are evaluated separately to prevent spurious cross-screen transitions.
4. **Ensemble Variance Reduction:** How Gradient Boosting and Soft Voting ensembles outperform individual decision trees and logistic regression on multi-class operational risk targets.
5. **Actionable Predictive Optimization:** How ML inference directly translates into proactive engineering actions (buffer compensation, SHA-256 hash checks, KDM reissuance requests) to protect theatrical showtimes.
