"""
Blockchain size reduction simulation module.
"""
import numpy as np
import pandas as pd
import streamlit as st

STRATEGIES = ["strategy_noise", "strategy_scam", "strategy_both", "strategy_aggregate"]


def compute_reduction(
    df: pd.DataFrame,
    labels: np.ndarray,
    strategy: str,
) -> dict:
    """
    Apply the selected pruning strategy and compute before/after sizes.

    Parameters
    ----------
    df       : Full dataframe with tx_size_bytes, is_scam, cluster columns
    labels   : DBSCAN labels (-1 = noise)
    strategy : One of strategy_noise | strategy_scam | strategy_both | strategy_aggregate

    Returns dict with all reduction metrics.
    """
    tmp = df.copy()
    tmp["cluster"] = labels
    tmp["is_noise"] = (labels == -1).astype(int)

    total_before      = int(tmp["tx_size_bytes"].sum())
    total_txs_before  = len(tmp)

    # ── Flag which rows to remove ─────────────────────────────────────
    if strategy == "strategy_noise":
        mask_remove = tmp["is_noise"] == 1
    elif strategy == "strategy_scam":
        mask_remove = tmp["is_scam"] == 1
    elif strategy == "strategy_both":
        mask_remove = (tmp["is_noise"] == 1) | (tmp["is_scam"] == 1)
    elif strategy == "strategy_aggregate":
        # Keep one representative per cluster (smallest index), remove duplicates
        # Noise points are also removed
        cluster_keep = tmp[tmp["cluster"] >= 0].groupby("cluster").head(1).index
        mask_remove  = ~tmp.index.isin(cluster_keep)
    else:
        mask_remove = pd.Series(False, index=tmp.index)

    # ── Per-removal-type counts ───────────────────────────────────────
    noise_removed = int((tmp["is_noise"] == 1).sum())
    scam_removed  = int((tmp["is_scam"] == 1).sum())
    both_removed  = int(((tmp["is_noise"] == 1) | (tmp["is_scam"] == 1)).sum())

    removed        = tmp[mask_remove]
    kept           = tmp[~mask_remove]

    total_after    = int(kept["tx_size_bytes"].sum())
    bytes_saved    = total_before - total_after
    pct_saved      = (bytes_saved / total_before * 100) if total_before else 0

    txs_removed    = int(mask_remove.sum())
    txs_kept       = len(kept)

    # ── Per-block stats ───────────────────────────────────────────────
    block_before = tmp.groupby("block_number")["tx_size_bytes"].sum().rename("before")
    block_after  = kept.groupby("block_number")["tx_size_bytes"].sum().rename("after")
    block_df = pd.concat([block_before, block_after], axis=1).fillna(0).reset_index()
    block_df["saved"]   = block_df["before"] - block_df["after"]
    block_df["pct_saved"] = (block_df["saved"] / block_df["before"].replace(0, np.nan) * 100).fillna(0)
    block_df = block_df.sort_values("block_number")

    # ── Removal breakdown for waterfall chart ─────────────────────────
    if strategy == "strategy_noise":
        breakdown = {"Noise / Outliers": int(removed["tx_size_bytes"].sum())}
    elif strategy == "strategy_scam":
        breakdown = {"Scam Transactions": int(removed["tx_size_bytes"].sum())}
    elif strategy == "strategy_both":
        noise_only = removed[removed["is_noise"] == 1]
        scam_only  = removed[removed["is_scam"] == 1]
        breakdown  = {
            "Noise / Outliers":   int(noise_only["tx_size_bytes"].sum()),
            "Scam Transactions":  int(scam_only["tx_size_bytes"].sum()),
        }
    else:  # aggregate
        noise_part    = removed[removed["is_noise"] == 1]
        cluster_part  = removed[removed["cluster"] >= 0]
        breakdown = {
            "Noise / Outliers":        int(noise_part["tx_size_bytes"].sum()),
            "Cluster Aggregated":      int(cluster_part["tx_size_bytes"].sum()),
        }

    return {
        "total_before":    total_before,
        "total_after":     total_after,
        "bytes_saved":     bytes_saved,
        "pct_saved":       pct_saved,
        "txs_removed":     txs_removed,
        "txs_kept":        txs_kept,
        "noise_removed":   noise_removed,
        "scam_removed":    scam_removed,
        "both_removed":    both_removed,
        "block_df":        block_df,
        "breakdown":       breakdown,
        "kept_df":         kept,
        "removed_df":      removed,
    }


def human_size(n_bytes: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(n_bytes) < 1024:
            return f"{n_bytes:.2f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.2f} PB"
