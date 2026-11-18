import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import joblib
import numpy as np
import pandas as pd
from hmmlearn import hmm
from sklearn.preprocessing import StandardScaler
from config import MODELS_DIR

HMM_FEATURES = [
    "payment_completed",
    "kdm_available",
    "kdm_decryptable",
    "dcp_corruption_pct",
    "firmware_update_required",
    "sound_sync_error_ms",
    "network_delay_ms"
]

STATE_NAMES = ["Stable Delivery", "Degraded Delivery", "Critical Delivery"]
STATE_COLORS = ["#10b981", "#f59e0b", "#ef4444"]

class CinemaHMMAnalyzer:
    def __init__(self, n_components: int = 3):
        self.n_components = n_components
        self.model = None
        self.scaler = StandardScaler()
        self.results = {}
        self.state_mapping = {}

    def fit_and_evaluate(self, df: pd.DataFrame):
        df_sorted = df.sort_values(by=["cinema_screen", "time_step"]).copy()
        screens = df_sorted["cinema_screen"].unique().tolist()

        np.random.seed(42)
        shuffled_screens = screens.copy()
        np.random.shuffle(shuffled_screens)
        split_idx = max(1, int(len(shuffled_screens) * 0.75))
        train_screens = set(shuffled_screens[:split_idx])
        test_screens = set(shuffled_screens[split_idx:])

        X_all = df_sorted[HMM_FEATURES].values
        self.scaler.fit(X_all)

        train_seqs = []
        train_lengths = []
        for scr in train_screens:
            sub = df_sorted[df_sorted["cinema_screen"] == scr]
            if len(sub) > 0:
                train_seqs.append(self.scaler.transform(sub[HMM_FEATURES].values))
                train_lengths.append(len(sub))

        test_seqs = []
        test_lengths = []
        for scr in test_screens:
            sub = df_sorted[df_sorted["cinema_screen"] == scr]
            if len(sub) > 0:
                test_seqs.append(self.scaler.transform(sub[HMM_FEATURES].values))
                test_lengths.append(len(sub))

        X_train = np.vstack(train_seqs) if train_seqs else self.scaler.transform(X_all)
        lengths_train = train_lengths if train_lengths else [len(X_all)]

        X_test = np.vstack(test_seqs) if test_seqs else X_train
        lengths_test = test_lengths if test_lengths else lengths_train

        self.model = hmm.GaussianHMM(
            n_components=self.n_components,
            covariance_type="diag",
            n_iter=150,
            random_state=42,
            min_covar=1e-3
        )
        self.model.fit(X_train, lengths_train)

        train_ll = float(self.model.score(X_train, lengths_train))
        test_ll = float(self.model.score(X_test, lengths_test))

        train_ll_per_obs = round(train_ll / sum(lengths_train), 3)
        test_ll_per_obs = round(test_ll / sum(lengths_test), 3)

        scaled_means = self.model.means_
        orig_means = self.scaler.inverse_transform(scaled_means)

        risk_scores = []
        for i in range(self.n_components):
            m = orig_means[i]
            pay, kdm_av, kdm_dec, dcp_c, fw, sound, net = m
            score = (1.0 - kdm_av) * 50.0 + (1.0 - kdm_dec) * 50.0 + dcp_c * 2.0 + fw * 20.0 + (net / 10.0)
            risk_scores.append((score, i))

        risk_scores.sort(key=lambda x: x[0])
        sorted_indices = [idx for _, idx in risk_scores]

        raw_startprob = self.model.startprob_[sorted_indices]
        startprob = (raw_startprob / raw_startprob.sum()).tolist()

        raw_transmat = self.model.transmat_[sorted_indices, :][:, sorted_indices]
        transmat = (raw_transmat / raw_transmat.sum(axis=1, keepdims=True)).tolist()

        reordered_means = orig_means[sorted_indices]

        # Viterbi decoding over all records to compute empirical emission matrix heatmap
        index_remap = {orig_idx: new_idx for new_idx, orig_idx in enumerate(sorted_indices)}
        all_scaled = self.scaler.transform(X_all)
        viterbi_all = [index_remap[s] for s in self.model.predict(all_scaled)]
        df_sorted["inferred_state"] = viterbi_all

        # Compute Emission Matrix: Probability of observations given state
        obs_categories = [
            "KDM Available",
            "KDM Decryptable",
            "DCP Valid (<2% Loss)",
            "Low Network Delay (<100ms)",
            "Audio In-Sync (<20ms)",
            "Firmware Current",
            "Payment Completed"
        ]

        emission_matrix_rows = []
        for st_id in range(self.n_components):
            st_sub = df_sorted[df_sorted["inferred_state"] == st_id]
            if len(st_sub) > 0:
                p_kdm = float((st_sub["kdm_available"] == 1).mean())
                p_dec = float((st_sub["kdm_decryptable"] == 1).mean())
                p_dcp = float((st_sub["dcp_corruption_pct"] <= 2.0).mean())
                p_net = float((st_sub["network_delay_ms"] <= 100.0).mean())
                p_aud = float((st_sub["sound_sync_error_ms"].abs() <= 20.0).mean())
                p_fw = float((st_sub["firmware_update_required"] == 0).mean())
                p_pay = float((st_sub["payment_completed"] == 1).mean())
            else:
                p_kdm, p_dec, p_dcp, p_net, p_aud, p_fw, p_pay = 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5

            emission_matrix_rows.append([
                round(p_kdm, 3), round(p_dec, 3), round(p_dcp, 3),
                round(p_net, 3), round(p_aud, 3), round(p_fw, 3), round(p_pay, 3)
            ])

        emissions_summary = []
        for new_idx, state_name in enumerate(STATE_NAMES):
            means_vec = reordered_means[new_idx]
            emissions_summary.append({
                "state_id": new_idx,
                "state_name": state_name,
                "color": STATE_COLORS[new_idx],
                "means": {
                    "payment_completed_pct": round(float(means_vec[0]) * 100, 1),
                    "kdm_available_pct": round(float(means_vec[1]) * 100, 1),
                    "kdm_decryptable_pct": round(float(means_vec[2]) * 100, 1),
                    "dcp_corruption_pct": round(float(means_vec[3]), 2),
                    "firmware_update_pct": round(float(means_vec[4]) * 100, 1),
                    "sound_sync_error_ms": round(float(abs(means_vec[5])), 1),
                    "network_delay_ms": round(float(means_vec[6]), 1)
                }
            })

        screen_timelines = {}
        sample_screens = screens[:8]

        for scr in sample_screens:
            sub = df_sorted[df_sorted["cinema_screen"] == scr]
            X_scr = self.scaler.transform(sub[HMM_FEATURES].values)
            raw_viterbi = self.model.predict(X_scr)
            remapped_viterbi = [index_remap[s] for s in raw_viterbi]

            timeline_records = []
            for (_, row), st in zip(sub.iterrows(), remapped_viterbi):
                timeline_records.append({
                    "week": int(row["time_step"]),
                    "state_id": st,
                    "state_name": STATE_NAMES[st],
                    "color": STATE_COLORS[st],
                    "kdm_available": int(row["kdm_available"]),
                    "dcp_corruption_pct": float(row["dcp_corruption_pct"]),
                    "recovery_time_min": float(row["recovery_time_min"])
                })
            screen_timelines[scr] = timeline_records

        self.results = {
            "initial_state_probabilities": [
                {"state": STATE_NAMES[i], "probability": round(float(p), 4), "color": STATE_COLORS[i]}
                for i, p in enumerate(startprob)
            ],
            "transition_matrix": {
                "states": STATE_NAMES,
                "matrix": [[round(float(val), 4) for val in row] for row in transmat]
            },
            "emission_matrix": {
                "states": STATE_NAMES,
                "observations": obs_categories,
                "matrix": emission_matrix_rows
            },
            "emission_profiles": emissions_summary,
            "performance": {
                "train_log_likelihood": round(train_ll, 2),
                "test_log_likelihood": round(test_ll, 2),
                "train_ll_per_obs": train_ll_per_obs,
                "test_ll_per_obs": test_ll_per_obs,
                "train_screens_count": len(train_screens),
                "test_screens_count": len(test_screens),
                "train_sequences_length": sum(lengths_train),
                "test_sequences_length": sum(lengths_test)
            },
            "screen_timelines": screen_timelines,
            "available_timeline_screens": sample_screens
        }

        self.save_models()
        return self.results

    def save_models(self):
        os.makedirs(MODELS_DIR, exist_ok=True)
        dump_path = os.path.join(MODELS_DIR, "hmm_bundle.joblib")
        joblib.dump({
            "model": self.model,
            "scaler": self.scaler,
            "results": self.results
        }, dump_path)

    def load_models(self):
        dump_path = os.path.join(MODELS_DIR, "hmm_bundle.joblib")
        if os.path.exists(dump_path):
            bundle = joblib.load(dump_path)
            self.model = bundle["model"]
            self.scaler = bundle["scaler"]
            self.results = bundle["results"]
            return True
        return False
