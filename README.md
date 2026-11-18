# CinemaPredict – Predictive Optimization of Digital Cinema Content Delivery Using Machine Learning

> **AI-Powered Digital Cinema Delivery Intelligence**  
> A Machine Learning-based decision-support system for digital cinema delivery monitoring, theatre risk analysis, and predictive optimization.

---

## 1. Project Overview

**CinemaPredict** is a full-stack Machine Learning platform designed to monitor digital cinema content delivery, identify operational bottlenecks, predict delivery risks, and minimize recovery time.

The system analyses theatre-level operational data, including Digital Cinema Package (DCP) delivery, Key Delivery Message (KDM) availability, distributor payment status, technical faults, and network delays. It applies machine learning techniques to classify delivery risks, predict recovery time, identify recurring failure patterns, and analyse delivery conditions over time.

## 2. Key Features

- **Cinema Operations Dashboard:** Displays operational KPIs, delivery status, KDM availability, technical incidents, and risk distribution.
- **Cinema Delivery Risk Classification:** Uses Random Forest, SVM, Logistic Regression, and Decision Tree algorithms to classify delivery risks.
- **Ensemble Learning:** Compares ensemble algorithms such as Bagging, Soft Voting, Random Forest, and Gradient Boosting.
- **Recovery Time Prediction:** Estimates recovery time using regression algorithms.
- **Failure Pattern Analysis:** Uses K-Means clustering and PCA to identify recurring operational failure patterns.
- **Sequential State Prediction:** Uses Hidden Markov Models (HMM) to analyse transitions between stable, degraded, and critical delivery conditions.
- **Predictive Alerts:** Generates risk-based alerts and suggested operational actions.
- **Dataset Management:** Supports CSV and Excel uploads, data validation, preprocessing, and model retraining.
- **Report Generation:** Generates downloadable PDF and Excel reports containing performance metrics and operational insights.

## 3. Machine Learning Modules

| Module | Algorithms | Purpose |
|---|---|---|
| Risk Classification | Random Forest, SVM, Logistic Regression, Decision Tree | Classifies cinema delivery risks |
| Ensemble Learning | Bagging, Soft Voting, Gradient Boosting | Compares predictive performance |
| Recovery Prediction | Random Forest Regressor, Gradient Boosting Regressor, SVR, Linear Regression | Predicts recovery time |
| Failure Analysis | K-Means, PCA | Identifies failure patterns |
| Sequential Prediction | Gaussian Hidden Markov Model | Analyses delivery-state transitions |

## 4. Technology Stack

### Frontend
- HTML5
- CSS3
- JavaScript (Vanilla ES6+)
- Plotly.js
- Font Awesome

### Backend
- Python
- Flask
- SQLite

### Machine Learning and Data Science
- Scikit-learn
- Pandas
- NumPy
- hmmlearn

### Report Generation
- OpenPyXL
- ReportLab

## 5. Installation and Execution

### Prerequisites
- Python 3.10 or above
- pip package manager

### Step 1: Navigate to the Project Directory

```bash
cd cinemapredict
```

### Step 2: Install Dependencies

```bash
pip install flask pandas numpy scikit-learn hmmlearn openpyxl reportlab
```

### Step 3: Run the Application

```bash
python run.py
```

Alternatively:

```bash
python app.py
```

### Step 4: Open the Dashboard

Open your browser and visit:

```text
http://127.0.0.1:5000
```

## 6. Project Objectives

- Monitor movie content distribution across multiple cinema theatres.
- Identify technical faults and delivery-related issues.
- Track distributor payment compliance and KDM availability.
- Predict potential delivery delays and operational risks.
- Analyse recurring failure patterns using clustering.
- Estimate recovery time for cinema delivery incidents.
- Support proactive decision-making through predictive analytics.

## 7. Expected Outcome

CinemaPredict aims to provide cinema network operators with a centralized platform to monitor distribution activities, identify high-risk theatres, predict operational problems, and improve digital cinema delivery efficiency.

## 8. Academic Project

- **Project Domain:** Machine Learning, Predictive Analytics, Digital Cinema Management
- **Project Type:** Full-Stack Machine Learning Application
- **Application:** Digital Cinema Delivery Intelligence

---

**CinemaPredict – Making Digital Cinema Delivery Smarter Through Predictive Intelligence.**
