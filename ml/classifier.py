import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder, StandardScaler
from config import MODELS_DIR

CLASSIFIER_FEATURES = [
    "payment_completed",
    "kdm_available",
    "kdm_expired",
    "kdm_decryptable",
    "dcp_corruption_pct",
    "network_delay_ms",
    "server_load",
    "screen_encoded"
]

TARGET_CLASSES = ["NORMAL", "WARNING", "CRITICAL"]

class CinemaRiskClassifier:
    def __init__(self):
        self.models = {
            "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42),
            "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
            "Decision Tree": DecisionTreeClassifier(max_depth=5, random_state=42),
            "Support Vector Machine": SVC(kernel="rbf", probability=True, random_state=42)
        }
        self.fitted_models = {}
        self.scaler = StandardScaler()
        self.screen_encoder = LabelEncoder()
        self.metrics = {}
        self.best_model_name = "Random Forest"

    def _prepare_features(self, df: pd.DataFrame, fit_encoders: bool = True) -> pd.DataFrame:
        df_feat = df.copy()

        if "server_load" not in df_feat.columns:
            df_feat["server_load"] = np.clip(
                (df_feat["network_delay_ms"] / 5.0) + (df_feat["dcp_corruption_pct"] * 1.5) + 20.0,
                10.0, 98.0
            ).round(1)

        if fit_encoders:
            self.screen_encoder.fit(df_feat["cinema_screen"].astype(str))
            df_feat["screen_encoded"] = self.screen_encoder.transform(df_feat["cinema_screen"].astype(str))
        else:
            known_classes = set(self.screen_encoder.classes_)
            df_feat["screen_encoded"] = df_feat["cinema_screen"].astype(str).apply(
                lambda s: self.screen_encoder.transform([s])[0] if s in known_classes else 0
            )

        return df_feat

    def train_and_evaluate(self, df: pd.DataFrame):
        df_feat = self._prepare_features(df, fit_encoders=True)

        X = df_feat[CLASSIFIER_FEATURES]
        y = df_feat["delivery_risk"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        self.metrics = {}
        best_f1 = -1.0

        for name, clf in self.models.items():
            if name in ["Logistic Regression", "Support Vector Machine"]:
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

        rf = self.fitted_models["Random Forest"]
        importances = rf.feature_importances_.tolist()
        feat_importance_dict = [
            {"feature": feat, "importance": round(imp * 100, 2)}
            for feat, imp in sorted(zip(CLASSIFIER_FEATURES, importances), key=lambda x: x[1], reverse=True)
        ]

        self.metrics["feature_importances"] = feat_importance_dict
        self.metrics["best_model"] = self.best_model_name
        self.save_models()
        return self.metrics

    def predict_single(self, input_data: dict, model_name: str = None) -> dict:
        if not self.fitted_models:
            self.load_models()

        if model_name is None or model_name not in self.fitted_models:
            model_name = self.best_model_name

        clf = self.fitted_models[model_name]

        screen_str = str(input_data.get("cinema_screen", "SCR-01"))
        if screen_str in self.screen_encoder.classes_:
            screen_enc = int(self.screen_encoder.transform([screen_str])[0])
        else:
            screen_enc = 0

        row = {
            "payment_completed": int(input_data.get("payment_completed", 1)),
            "kdm_available": int(input_data.get("kdm_available", 1)),
            "kdm_expired": int(input_data.get("kdm_expired", 0)),
            "kdm_decryptable": int(input_data.get("kdm_decryptable", 1)),
            "dcp_corruption_pct": float(input_data.get("dcp_corruption_pct", 0.0)),
            "network_delay_ms": float(input_data.get("network_delay_ms", 50.0)),
            "server_load": float(input_data.get("server_load", 35.0)),
            "screen_encoded": screen_enc
        }

        X_inst = pd.DataFrame([row])[CLASSIFIER_FEATURES]

        if model_name in ["Logistic Regression", "Support Vector Machine"]:
            X_inst_scaled = self.scaler.transform(X_inst)
            prediction = clf.predict(X_inst_scaled)[0]
            probs = clf.predict_proba(X_inst_scaled)[0]
        else:
            prediction = clf.predict(X_inst)[0]
            probs = clf.predict_proba(X_inst)[0]

        prob_dict = {cls: round(float(prob) * 100, 2) for cls, prob in zip(clf.classes_, probs)}

        reasons = []
        if row["kdm_available"] == 0:
            reasons.append("KDM is not available on cinema server (Content cannot be decrypted).")
        if row["kdm_decryptable"] == 0 and row["kdm_available"] == 1:
            reasons.append("KDM certificate mismatch or corrupt key block detected.")
        if row["kdm_expired"] == 1:
            reasons.append("KDM validity license window has expired.")
        if row["payment_completed"] == 0:
            reasons.append("Weekly distributor licensing payment is pending.")
        if row["dcp_corruption_pct"] > 5.0:
            reasons.append(f"DCP file corruption elevated ({row['dcp_corruption_pct']}%).")
        if row["network_delay_ms"] > 180.0:
            reasons.append(f"High network latency ({row['network_delay_ms']} ms) risking multicast ingest.")

        if not reasons:
            reasons.append("All operational KDM and transport parameters are within healthy thresholds.")

        return {
            "model_used": model_name,
            "predicted_risk": prediction,
            "probabilities": prob_dict,
            "explanations": reasons,
            "inputs": input_data
        }

    def save_models(self):
        os.makedirs(MODELS_DIR, exist_ok=True)
        dump_path = os.path.join(MODELS_DIR, "classification_bundle.joblib")
        joblib.dump({
            "models": self.fitted_models,
            "scaler": self.scaler,
            "screen_encoder": self.screen_encoder,
            "metrics": self.metrics,
            "best_model_name": self.best_model_name
        }, dump_path)

    def load_models(self):
        dump_path = os.path.join(MODELS_DIR, "classification_bundle.joblib")
        if os.path.exists(dump_path):
            bundle = joblib.load(dump_path)
            self.fitted_models = bundle["models"]
            self.scaler = bundle["scaler"]
            self.screen_encoder = bundle["screen_encoder"]
            self.metrics = bundle["metrics"]
            self.best_model_name = bundle.get("best_model_name", "Random Forest")
            return True
        return False
