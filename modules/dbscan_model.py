"""
DBSCAN clustering and evaluation module.
"""
import time
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.neighbors import KDTree
from sklearn.metrics import (
    silhouette_score,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
)
from sklearn.neighbors import NearestNeighbors
import streamlit as st


@st.cache_data(show_spinner=False)
def run_dbscan(
    X_scaled: np.ndarray,
    eps: float = 0.5,
    min_samples: int = 5,
    max_sample: int = 20_000,
) -> tuple[np.ndarray, float]:
    """
    Run DBSCAN on scaled feature matrix.
    For large datasets (>max_sample rows) fits on a stratified sample then
    assigns remaining points to the nearest core point cluster via KDTree.
    Returns (labels, execution_time_seconds)
    """
    t0 = time.perf_counter()
    n = len(X_scaled)

    if n <= max_sample:
        db = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean", n_jobs=-1)
        labels = db.fit_predict(X_scaled)
    else:
        # 1. Fit on a random sample
        rng = np.random.default_rng(42)
        sample_idx = rng.choice(n, max_sample, replace=False)
        X_sample   = X_scaled[sample_idx]

        db = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean", n_jobs=-1)
        sample_labels = db.fit_predict(X_sample)

        # 2. Build KDTree of sample core points
        labels = np.full(n, -1, dtype=np.int32)
        labels[sample_idx] = sample_labels

        # Core points in sample (label != -1)
        core_mask = sample_labels != -1
        if core_mask.sum() > 0:
            core_X      = X_sample[core_mask]
            core_labels = sample_labels[core_mask]
            tree = KDTree(core_X, leaf_size=40)

            # Assign remaining points
            rest_mask = np.ones(n, dtype=bool)
            rest_mask[sample_idx] = False
            rest_idx = np.where(rest_mask)[0]

            if len(rest_idx) > 0:
                dist, ind = tree.query(X_scaled[rest_idx], k=1)
                assign_mask = dist[:, 0] <= eps
                labels[rest_idx[assign_mask]] = core_labels[ind[assign_mask, 0]]

    elapsed = time.perf_counter() - t0
    return labels, elapsed


def get_cluster_stats(df: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """Build per-cluster statistics dataframe."""
    tmp = df.copy()
    tmp["cluster"] = labels

    rows = []
    for cid in sorted(tmp["cluster"].unique()):
        sub = tmp[tmp["cluster"] == cid]
        rows.append(
            {
                "cluster_id":    cid,
                "count":         len(sub),
                "avg_gas":       sub["receipt_gas_used"].mean(),
                "avg_value_eth": sub["value_eth"].mean(),
                "scam_pct":      sub["is_scam"].mean() * 100,
                "total_bytes":   sub["tx_size_bytes"].sum(),
            }
        )
    return pd.DataFrame(rows)


def compute_silhouette(X_scaled: np.ndarray, labels: np.ndarray) -> float | None:
    """Return silhouette score (None if only 1 cluster or all noise)."""
    unique = set(labels) - {-1}
    if len(unique) < 2:
        return None
    # Subsample for speed on large datasets
    if len(labels) > 10_000:
        idx = np.random.choice(len(labels), 10_000, replace=False)
        X_sub, l_sub = X_scaled[idx], labels[idx]
        if len(set(l_sub) - {-1}) < 2:
            return None
        return silhouette_score(X_sub, l_sub, sample_size=5000, random_state=42)
    return silhouette_score(X_scaled, labels)


@st.cache_data(show_spinner=False)
def compute_kdistance(X_scaled: np.ndarray, k: int = 5, sample: int = 5000) -> np.ndarray:
    """Return sorted k-distances for the k-distance graph."""
    if len(X_scaled) > sample:
        idx = np.random.choice(len(X_scaled), sample, replace=False)
        X_sub = X_scaled[idx]
    else:
        X_sub = X_scaled
    nbrs = NearestNeighbors(n_neighbors=k, metric="euclidean", n_jobs=-1)
    nbrs.fit(X_sub)
    dists, _ = nbrs.kneighbors(X_sub)
    k_dists = np.sort(dists[:, -1])[::-1]
    return k_dists


def evaluate_fraud_detection(
    df: pd.DataFrame, labels: np.ndarray
) -> dict:
    """
    Compare DBSCAN noise points (label=-1) against ground-truth is_scam labels.
    Returns dict with confusion matrix components and metrics.
    """
    y_true = df["is_scam"].values
    # DBSCAN noise = predicted scam
    y_pred = (labels == -1).astype(int)

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)

    return {
        "y_true":    y_true,
        "y_pred":    y_pred,
        "cm":        cm,
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall":    recall_score(y_true, y_pred, zero_division=0),
        "f1":        f1_score(y_true, y_pred, zero_division=0),
        "accuracy":  accuracy_score(y_true, y_pred),
    }


@st.cache_data(show_spinner=False)
def eps_sensitivity(
    X_scaled: np.ndarray,
    eps_values: list[float],
    min_samples: int = 5,
) -> pd.DataFrame:
    """Run DBSCAN for multiple eps values and return stats."""
    rows = []
    for eps in eps_values:
        labels, _ = run_dbscan(X_scaled, eps=eps, min_samples=min_samples)
        n_clusters = len(set(labels) - {-1})
        n_noise    = (labels == -1).sum()
        rows.append({"eps": eps, "n_clusters": n_clusters, "n_noise": n_noise})
    return pd.DataFrame(rows)
