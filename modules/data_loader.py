"""
Data loading and preprocessing module for Blockchain Size Reducer.
"""
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path


# ── Smart dataset path resolution ────────────────────────────────────
# Works locally (C:\final\Dataset.csv) and on deployment (./Dataset.csv)
_HERE = Path(__file__).resolve().parent.parent   # project root

def _find_dataset() -> Path:
    candidates = [
        _HERE / "Dataset.csv",                    # project root (deployment)
        _HERE / "data" / "Dataset.csv",           # data sub-folder
        Path(r"C:\final\Dataset.csv"),            # original local path
        Path("/data/Dataset.csv"),                # Linux/Docker mount
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        "Dataset.csv not found. "
        "Place it in the project root or set DATASET_PATH in data_loader.py"
    )

DATASET_PATH = _find_dataset()


# Estimated bytes per transaction field
FIELD_SIZES = {
    "hash": 32,
    "nonce": 8,
    "transaction_index": 4,
    "from_address": 20,
    "to_address": 20,
    "value": 32,
    "gas": 8,
    "gas_price": 8,
    "receipt_cumulative_gas_used": 8,
    "receipt_gas_used": 8,
    "block_number": 8,
    "block_hash": 32,
    "block_timestamp": 8,
    "from_scam": 1,
    "to_scam": 1,
}
BASE_TX_SIZE = sum(FIELD_SIZES.values())  # ~198 bytes base


@st.cache_data(show_spinner=False)
def load_data(path: str = DATASET_PATH) -> pd.DataFrame:
    """Load and preprocess the Ethereum transactions CSV."""
    df = pd.read_csv(path, low_memory=False)

    # ── Parse timestamps ──────────────────────────────────────────────
    df["block_timestamp"] = pd.to_datetime(df["block_timestamp"], utc=True, errors="coerce")

    # ── Fill categorical nulls ────────────────────────────────────────
    df["from_category"] = df["from_category"].fillna("Normal")
    df["to_category"]   = df["to_category"].fillna("Normal")

    # ── Boolean scam flag ─────────────────────────────────────────────
    df["is_scam"] = ((df["from_scam"] == 1) | (df["to_scam"] == 1)).astype(int)

    # ── ETH value ─────────────────────────────────────────────────────
    df["value_eth"] = df["value"] / 1e18
    df["value_eth"] = df["value_eth"].clip(0, df["value_eth"].quantile(0.999))

    # ── Gas price in Gwei ────────────────────────────────────────────
    df["gas_price_gwei"] = df["gas_price"] / 1e9

    # ── Gas efficiency ratio ──────────────────────────────────────────
    df["gas_ratio"] = df["receipt_gas_used"] / df["gas"].replace(0, np.nan)
    df["gas_ratio"] = df["gas_ratio"].fillna(0).clip(0, 1)

    # ── Is contract call ──────────────────────────────────────────────
    df["is_contract_call"] = (df["input"].astype(str) != "0x").astype(int)

    # ── Input data size ───────────────────────────────────────────────
    df["input_bytes"] = df["input"].astype(str).apply(
        lambda x: max(0, (len(x) - 2) // 2) if x.startswith("0x") else len(x.encode())
    )

    # ── Estimated transaction byte size ──────────────────────────────
    df["tx_size_bytes"] = BASE_TX_SIZE + df["input_bytes"]

    # ── Scam score ────────────────────────────────────────────────────
    df["scam_score"] = df["from_scam"] + df["to_scam"]

    # ── Date column for grouping ──────────────────────────────────────
    df["date"] = df["block_timestamp"].dt.date

    return df


def get_block_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-block statistics."""
    stats = df.groupby("block_number").agg(
        tx_count      = ("hash", "count"),
        total_size    = ("tx_size_bytes", "sum"),
        scam_count    = ("is_scam", "sum"),
        total_gas     = ("receipt_gas_used", "sum"),
        avg_value_eth = ("value_eth", "mean"),
        timestamp     = ("block_timestamp", "first"),
    ).reset_index()
    stats["scam_rate"] = stats["scam_count"] / stats["tx_count"]
    return stats


def get_summary_stats(df: pd.DataFrame) -> dict:
    """Return a dict of key dataset statistics."""
    return {
        "total_txs":        len(df),
        "total_blocks":     df["block_number"].nunique(),
        "total_size_mb":    df["tx_size_bytes"].sum() / 1_048_576,
        "total_size_gb":    df["tx_size_bytes"].sum() / 1_073_741_824,
        "scam_count":       int(df["is_scam"].sum()),
        "normal_count":     int((df["is_scam"] == 0).sum()),
        "scam_rate":        df["is_scam"].mean() * 100,
        "unique_senders":   df["from_address"].nunique(),
        "unique_receivers": df["to_address"].nunique(),
        "avg_gas":          df["receipt_gas_used"].mean(),
        "avg_value_eth":    df["value_eth"].mean(),
        "date_min":         df["block_timestamp"].min(),
        "date_max":         df["block_timestamp"].max(),
    }
