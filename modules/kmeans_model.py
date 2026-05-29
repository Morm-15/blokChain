"""
K-Means Clustering — for comparison with DBSCAN
================================================
Used to demonstrate WHY DBSCAN is better for blockchain compression:
  • K-Means requires knowing K in advance
  • K-Means forces every point into a cluster (no noise handling)
  • K-Means assumes spherical clusters — poor for blockchain patterns
  • DBSCAN finds arbitrary shapes + marks outliers automatically
"""
import time
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.metrics import silhouette_score


@st.cache_data(show_spinner=False)
def run_kmeans(
    X_scaled: np.ndarray,
    n_clusters: int = 15,
    random_state: int = 42,
) -> tuple[np.ndarray, float]:
    """
    Run K-Means on the scaled feature matrix.
    Uses MiniBatchKMeans for speed on large datasets.
    Returns (labels, execution_time_seconds)
    """
    t0 = time.perf_counter()
    km = MiniBatchKMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init=10,
        batch_size=4096,
    )
    labels = km.fit_predict(X_scaled)
    elapsed = time.perf_counter() - t0
    return labels, elapsed


@st.cache_data(show_spinner=False)
def kmeans_silhouette(X_scaled: np.ndarray, labels: np.ndarray) -> float:
    """Compute silhouette score for K-Means labels (sampled for speed)."""
    try:
        idx = np.random.default_rng(42).choice(len(X_scaled),
                                                min(5000, len(X_scaled)),
                                                replace=False)
        return float(silhouette_score(X_scaled[idx], labels[idx]))
    except Exception:
        return 0.0


def get_kmeans_cluster_stats(df: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """Per-cluster statistics for K-Means."""
    tmp = df.copy()
    tmp["_km"] = labels
    rows = []
    for cid, grp in tmp.groupby("_km"):
        rows.append({
            "cluster_id":  int(cid),
            "count":       len(grp),
            "avg_gas":     grp["receipt_gas_used"].mean(),
            "avg_value":   grp["value_eth"].mean(),
            "scam_pct":    grp["is_scam"].mean() * 100,
            "total_bytes": grp["tx_size_bytes"].sum(),
        })
    return pd.DataFrame(rows).sort_values("cluster_id")


@st.cache_data(show_spinner=False)
def sweep_k(
    X_scaled: np.ndarray,
    k_values: list,
) -> pd.DataFrame:
    """
    Try multiple K values and record inertia + silhouette.
    Used in the Elbow Method chart.
    """
    results = []
    for k in k_values:
        km = MiniBatchKMeans(n_clusters=k, random_state=42, n_init=5, batch_size=4096)
        lbl = km.fit_predict(X_scaled)
        try:
            idx = np.random.default_rng(42).choice(len(X_scaled),
                                                    min(3000, len(X_scaled)),
                                                    replace=False)
            sil = float(silhouette_score(X_scaled[idx], lbl[idx]))
        except Exception:
            sil = 0.0
        results.append({
            "k":         k,
            "inertia":   float(km.inertia_),
            "silhouette": sil,
        })
    return pd.DataFrame(results)
