import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import (
    RandomForestClassifier, BaggingClassifier, VotingClassifier, GradientBoostingClassifier
)
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
from config import MODELS_DIR

ENSEMBLE_FEATURES = [
    "payment_completed",
    "kdm_available",
    "kdm_expired",
    "kdm_decryptable",
    "dcp_corruption_pct",
    "network_delay_ms",
    "firmware_update_required",
    "sound_sync_error_ms"
]

TARGET_CLASSES = ["NORMAL", "WARNING", "CRITICAL"]

class CinemaEnsembleClassifier:
    def __init__(self):
        # Base estimators for voting
        clf_rf = RandomForestClassifier(n_estimators=80, random_state=42)
        clf_lr = LogisticRegression(max_iter=500, random_state=42)
        clf_dt = DecisionTreeClassifier(max_depth=5, random_state=42)

        self.models = {
            "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42),
            "Bagging Classifier": BaggingClassifier(
                estimator=DecisionTreeClassifier(max_depth=6),
                n_estimators=50, random_state=42
            ),
            "Voting Classifier": VotingClassifier(
                estimators=[('rf', clf_rf), ('lr', clf_lr), ('dt', clf_dt)],
                voting='soft'
            ),
            "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
        }
        self.fitted_models = {}
        self.scaler = StandardScaler()
        self.metrics = {}
        self.best_model_name = "Gradient Boosting"

    def train_and_evaluate(self, df: pd.DataFrame):
        X = df[ENSEMBLE_FEATURES].copy()
        y = df["delivery_risk"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        self.metrics = {}
        best_f1 = -1.0

        for name, clf in self.models.items():
            if name in ["Voting Classifier", "Gradient Boosting"]:
                clf.fit(X_train_scaled, y_train)
                y_pred = clf.predict(X_test_scaled)
            else:
                clf.fit(X_train, y_train)
                y_pred = clf.predict(X_test)

            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
            rec = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
            f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

            cm = confusion_matrix(y_test, y_pred, labels=TARGET_CLASSES).tolist()

            self.fitted_models[name] = clf
            self.metrics[name] = {
                "accuracy": round(acc * 100, 2),
                "precision": round(prec * 100, 2),
                "recall": round(rec * 100, 2),
                "f1_score": round(f1 * 100, 2),
                "confusion_matrix": cm,
                "labels": TARGET_CLASSES,
                "classes": clf.classes_.tolist()
            }

            if f1 > best_f1:
                best_f1 = f1
                self.best_model_name = name

        self.metrics["best_model"] = self.best_model_name
        self.save_models()
        return self.metrics

    def save_models(self):
        os.makedirs(MODELS_DIR, exist_ok=True)
        dump_path = os.path.join(MODELS_DIR, "ensemble_bundle.joblib")
        joblib.dump({
            "models": self.fitted_models,
            "scaler": self.scaler,
            "metrics": self.metrics,
            "best_model_name": self.best_model_name
        }, dump_path)

    def load_models(self):
        dump_path = os.path.join(MODELS_DIR, "ensemble_bundle.joblib")
        if os.path.exists(dump_path):
            bundle = joblib.load(dump_path)
            self.fitted_models = bundle["models"]
            self.scaler = bundle["scaler"]
            self.metrics = bundle["metrics"]
            self.best_model_name = bundle.get("best_model_name", "Gradient Boosting")
            return True
        return False
