import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from config import MODELS_DIR

CLUSTERING_FEATURES = [
    "payment_completed",
    "kdm_available",
    "kdm_decryptable",
    "kdm_expired",
    "dcp_corruption_pct",
    "firmware_update_required",
    "sound_sync_error_ms",
    "network_delay_ms"
]

class CinemaDeliveryClusterer:
    def __init__(self, n_clusters: int = 4):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2, random_state=42)
        self.kmeans = None
        self.results = {}

    def fit_and_analyze(self, df: pd.DataFrame, max_k: int = 10):
        """Runs full K-Means pipeline: Elbow curve, Silhouette, PCA, and dynamic cluster profiling."""
        X = df[CLUSTERING_FEATURES].copy()
        # Take absolute value of sound sync error for magnitude analysis
        X["abs_sound_sync_error_ms"] = X["sound_sync_error_ms"].abs()
        features_to_scale = [f for f in CLUSTERING_FEATURES if f != "sound_sync_error_ms"] + ["abs_sound_sync_error_ms"]

        X_scaled = self.scaler.fit_transform(X[features_to_scale])

        # 1. Elbow Method & Silhouette Score across K=2 to 10
        k_values = list(range(2, min(max_k + 1, len(df) - 1)))
        inertias = []
        silhouettes = []

        best_k = 4
        best_sil = -1.0

        for k in k_values:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            km.fit(X_scaled)
            inertias.append(round(float(km.inertia_), 2))
            sil = float(silhouette_score(X_scaled, km.labels_))
            silhouettes.append(round(sil, 4))
            if sil > best_sil:
                best_sil = sil
                best_k = k

        # Choose best K (prefer 4 or 5 if silhouette is close, for meaningful failure modes)
        self.n_clusters = best_k
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        labels = self.kmeans.fit_predict(X_scaled)

        # 2. PCA 2D Visualization
        pca_coords = self.pca.fit_transform(X_scaled)
        pca_df = pd.DataFrame(pca_coords, columns=["pc1", "pc2"])
        pca_df["cluster"] = labels
        pca_df["cinema_screen"] = df["cinema_screen"].values
        pca_df["time_step"] = df["time_step"].values

        # Explained variance ratio
        var_ratio = [round(float(v) * 100, 2) for v in self.pca.explained_variance_ratio_]

        # 3. Cluster Profiling & Dynamic Labeling based on actual feature means
        df_clustered = df.copy()
        df_clustered["cluster"] = labels
        df_clustered["abs_sound_sync"] = df_clustered["sound_sync_error_ms"].abs()

        cluster_profiles = []
        overall_means = {
            "dcp_corruption_pct": float(df_clustered["dcp_corruption_pct"].mean()),
            "kdm_failure_rate": float(((df_clustered["kdm_available"] == 0) | (df_clustered["kdm_decryptable"] == 0)).mean()),
            "network_delay_ms": float(df_clustered["network_delay_ms"].mean()),
            "firmware_update_rate": float(df_clustered["firmware_update_required"].mean()),
            "sound_sync_error_ms": float(df_clustered["abs_sound_sync"].mean())
        }

        for c in range(self.n_clusters):
            c_df = df_clustered[df_clustered["cluster"] == c]
            size = len(c_df)
            pct = round((size / len(df_clustered)) * 100, 1)

            c_dcp = float(c_df["dcp_corruption_pct"].mean())
            c_kdm_fail = float(((c_df["kdm_available"] == 0) | (c_df["kdm_decryptable"] == 0)).mean())
            c_net = float(c_df["network_delay_ms"].mean())
            c_firmware = float(c_df["firmware_update_required"].mean())
            c_sound = float(c_df["abs_sound_sync"].mean())

            # Dynamic identification based on largest z-score / deviation
            elevated = []
            if c_kdm_fail > overall_means["kdm_failure_rate"] * 1.8:
                elevated.append("KDM Decryption & Key Distribution Failures")
            if c_dcp > overall_means["dcp_corruption_pct"] * 2.0:
                elevated.append("DCP Package Packet Corruption")
            if c_net > overall_means["network_delay_ms"] * 1.5:
                elevated.append("High Network Delivery Latency")
            if c_firmware > overall_means["firmware_update_rate"] * 1.8:
                elevated.append("Firmware Maintenance Requirement")
            if c_sound > overall_means["sound_sync_error_ms"] * 1.8:
                elevated.append("Audio/Visual Sync Drift")

            if not elevated:
                label = f"Cluster {c}: Stable / Nominal Delivery Operations"
                desc = "Screens exhibit standard low corruption, valid KDMs, and optimal network timing."
            else:
                label = f"Cluster {c}: Dominant " + " & ".join(elevated[:2])
                desc = f"Characterized by elevated {', '.join(elevated).lower()}."

            cluster_profiles.append({
                "cluster_id": c,
                "label": label,
                "description": desc,
                "size": size,
                "percentage": pct,
                "means": {
                    "dcp_corruption_pct": round(c_dcp, 2),
                    "kdm_failure_rate_pct": round(c_kdm_fail * 100, 1),
                    "network_delay_ms": round(c_net, 1),
                    "firmware_update_pct": round(c_firmware * 100, 1),
                    "sound_sync_error_ms": round(c_sound, 1)
                }
            })

        # Downsample PCA data for UI responsiveness (max 300 points)
        sample_size = min(300, len(pca_df))
        sampled_pca = pca_df.sample(n=sample_size, random_state=42) if len(pca_df) > sample_size else pca_df

        self.results = {
            "elbow_data": {
                "k_values": k_values,
                "inertias": inertias,
                "selected_k": self.n_clusters
            },
            "silhouette_data": {
                "k_values": k_values,
                "silhouettes": silhouettes,
                "best_silhouette": round(best_sil, 4)
            },
            "pca_visualization": {
                "explained_variance_ratio": var_ratio,
                "points": sampled_pca.to_dict(orient="records")
            },
            "cluster_profiles": cluster_profiles,
            "overall_averages": {k: round(v, 2) for k, v in overall_means.items()}
        }

        self.save_models()
        return self.results

    def save_models(self):
        os.makedirs(MODELS_DIR, exist_ok=True)
        dump_path = os.path.join(MODELS_DIR, "clustering_bundle.joblib")
        joblib.dump({
            "kmeans": self.kmeans,
            "scaler": self.scaler,
            "pca": self.pca,
            "results": self.results,
            "n_clusters": self.n_clusters
        }, dump_path)

    def load_models(self):
        dump_path = os.path.join(MODELS_DIR, "clustering_bundle.joblib")
        if os.path.exists(dump_path):
            bundle = joblib.load(dump_path)
            self.kmeans = bundle["kmeans"]
            self.scaler = bundle["scaler"]
            self.pca = bundle["pca"]
            self.results = bundle["results"]
            self.n_clusters = bundle["n_clusters"]
            return True
        return False
