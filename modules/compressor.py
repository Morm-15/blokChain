"""
Cluster-Aware Compression Engine
=================================
Core Idea:
  1. Assign each transaction to a DBSCAN cluster
  2. Sort/group data BY cluster label (similar data together)
  3. Compress with zstd or gzip — similar data compresses MUCH better
  4. Build a Cluster Index (cluster_id → byte offset) for instant lookup

Why cluster-sorted compression is superior:
  • Compression algorithms (LZ77, Huffman…) exploit LOCAL repetition.
    Grouping similar transactions maximises that repetition → higher ratio.
  • Indexed storage: to find a value or address, check the index →
    decompress only 1-2 cluster blocks instead of the whole file.

Serialization: We use Parquet (binary columnar) which is the standard
format for blockchain analytics — it exploits column-level encoding
(dictionary, RLE, delta) and shows the biggest difference between
random-order and cluster-sorted compression.
"""

import io
import gzip
import time
import zstandard as zstd
import numpy as np
import pandas as pd
import streamlit as st

# Columns that carry meaningful blockchain data for compression
COMP_COLS = [
    "hash", "nonce", "transaction_index",
    "from_address", "to_address",
    "value", "gas", "gas_price",
    "receipt_gas_used", "receipt_cumulative_gas_used",
    "block_number", "block_hash", "block_timestamp",
    "input", "from_scam", "to_scam",
    "from_category", "to_category",
]


# ── Serialisation helpers ─────────────────────────────────────────────
def _df_to_bytes(df: pd.DataFrame) -> bytes:
    """
    Serialise a DataFrame to Parquet bytes (binary columnar format).
    Parquet uses dictionary + RLE encoding per column — consecutive
    similar values (e.g. same gas_price in a cluster) compress far better.
    We use NO internal Parquet compression so zstd/gzip can do its work.
    """
    # Keep only the blockchain columns that exist in this df
    cols = [c for c in COMP_COLS if c in df.columns]
    buf = io.BytesIO()
    df[cols].to_parquet(buf, index=False, compression=None, engine="pyarrow")
    return buf.getvalue()


def _bytes_to_df(b: bytes) -> pd.DataFrame:
    """Deserialise Parquet bytes back to DataFrame."""
    return pd.read_parquet(io.BytesIO(b), engine="pyarrow")


def _bytes_size(b: bytes) -> int:
    return len(b)


# ══════════════════════════════════════════════════════════════════════
#  COMPRESSION METHODS
# ══════════════════════════════════════════════════════════════════════

def compress_zstd(data: bytes, level: int = 3) -> bytes:
    cctx = zstd.ZstdCompressor(level=level)
    return cctx.compress(data)

def decompress_zstd(data: bytes) -> bytes:
    dctx = zstd.ZstdDecompressor()
    return dctx.decompress(data)

def compress_gzip(data: bytes, level: int = 6) -> bytes:
    return gzip.compress(data, compresslevel=level)

def decompress_gzip(data: bytes) -> bytes:
    return gzip.decompress(data)


# ══════════════════════════════════════════════════════════════════════
#  STRATEGY A — BASELINE: compress raw (random order)
# ══════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def compress_baseline(df: pd.DataFrame, method: str = "zstd") -> dict:
    """
    Compress the full dataset in RANDOMLY SHUFFLED order.
    This is the baseline — NO clustering applied.
    We shuffle to simulate a node storing transactions as they arrive
    without any ordering. Shows worst-case scenario that DBSCAN improves.
    """
    shuffled = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    raw = _df_to_bytes(shuffled)
    raw_size = _bytes_size(raw)

    t0 = time.perf_counter()
    if method == "zstd":
        compressed = compress_zstd(raw)
    else:
        compressed = compress_gzip(raw)
    comp_time = time.perf_counter() - t0

    comp_size = _bytes_size(compressed)

    return {
        "method":       method,
        "strategy":     "baseline_random",
        "raw_size":     raw_size,
        "comp_size":    comp_size,
        "ratio":        raw_size / comp_size,
        "pct_saved":    (1 - comp_size / raw_size) * 100,
        "comp_time_s":  comp_time,
        "n_blocks":     1,
        "index":        None,
    }


# ══════════════════════════════════════════════════════════════════════
#  STRATEGY B — CLUSTER-SORTED: compress after DBSCAN grouping
# ══════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def compress_cluster_sorted(
    df: pd.DataFrame,
    labels: np.ndarray,
    method: str = "zstd",
) -> dict:
    """
    Sort the DataFrame by cluster label FIRST, then compress the whole thing.
    Cluster index maps cluster_id → (start_row, end_row) in sorted data.
    Benefit: entropy within contiguous similar rows is much lower → better ratio.
    """
    tmp = df.copy()
    tmp["_cluster"] = labels

    # Sort: noise (-1) last, then by cluster id
    tmp_sorted = tmp.sort_values("_cluster").reset_index(drop=True)

    # Build row-level cluster index
    cluster_index = {}
    for cid, grp in tmp_sorted.groupby("_cluster"):
        cluster_index[int(cid)] = {
            "start_row": int(grp.index[0]),
            "end_row":   int(grp.index[-1]),
            "count":     len(grp),
        }

    # Compress sorted data
    export = tmp_sorted.drop(columns=["_cluster"])
    raw = _df_to_bytes(export)
    raw_size = _bytes_size(raw)

    t0 = time.perf_counter()
    if method == "zstd":
        compressed = compress_zstd(raw)
    else:
        compressed = compress_gzip(raw)
    comp_time = time.perf_counter() - t0

    comp_size = _bytes_size(compressed)

    return {
        "method":         method,
        "strategy":       "cluster_sorted",
        "raw_size":       raw_size,
        "comp_size":      comp_size,
        "ratio":          raw_size / comp_size,
        "pct_saved":      (1 - comp_size / raw_size) * 100,
        "comp_time_s":    comp_time,
        "n_blocks":       1,
        "index":          cluster_index,
        "sorted_df":      tmp_sorted,
    }


# ══════════════════════════════════════════════════════════════════════
#  STRATEGY C — PER-CLUSTER BLOCKS: each cluster = own compressed block
# ══════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def compress_per_cluster(
    df: pd.DataFrame,
    labels: np.ndarray,
    method: str = "zstd",
) -> dict:
    """
    Compress each cluster into its OWN compressed block.
    Index maps cluster_id → byte offset in the concatenated blob.
    
    Search benefit: decompress ONLY the one block that contains what you need.
    Trade-off: slightly worse ratio for tiny clusters (less context).
    """
    tmp = df.copy()
    tmp["_cluster"] = labels

    cluster_ids = sorted(tmp["_cluster"].unique())

    blocks       = []      # list of compressed bytes
    block_index  = {}      # cluster_id → {offset, size, count}
    raw_total    = 0
    comp_total   = 0
    per_cluster_stats = []

    t0 = time.perf_counter()
    offset = 0
    for cid in cluster_ids:
        grp = tmp[tmp["_cluster"] == cid].drop(columns=["_cluster"])
        raw = _df_to_bytes(grp)
        raw_sz = _bytes_size(raw)

        if method == "zstd":
            comp = compress_zstd(raw)
        else:
            comp = compress_gzip(raw)
        comp_sz = _bytes_size(comp)

        blocks.append(comp)
        block_index[int(cid)] = {
            "offset":    offset,
            "comp_size": comp_sz,
            "raw_size":  raw_sz,
            "count":     len(grp),
            "ratio":     raw_sz / comp_sz if comp_sz > 0 else 1,
        }
        per_cluster_stats.append({
            "cluster_id": int(cid),
            "n_txs":      len(grp),
            "raw_kb":     raw_sz / 1024,
            "comp_kb":    comp_sz / 1024,
            "ratio":      round(raw_sz / comp_sz, 2) if comp_sz > 0 else 1,
            "pct_saved":  round((1 - comp_sz/raw_sz)*100, 1) if raw_sz > 0 else 0,
        })
        offset     += comp_sz
        raw_total  += raw_sz
        comp_total += comp_sz

    comp_time = time.perf_counter() - t0
    blob = b"".join(blocks)

    return {
        "method":              method,
        "strategy":            "per_cluster_blocks",
        "raw_size":            raw_total,
        "comp_size":           comp_total,
        "ratio":               raw_total / comp_total if comp_total else 1,
        "pct_saved":           (1 - comp_total / raw_total) * 100 if raw_total else 0,
        "comp_time_s":         comp_time,
        "n_blocks":            len(cluster_ids),
        "index":               block_index,
        "blob":                blob,
        "per_cluster_stats":   pd.DataFrame(per_cluster_stats),
    }


# ══════════════════════════════════════════════════════════════════════
#  SEARCH SIMULATION
# ══════════════════════════════════════════════════════════════════════

def simulate_search_random(
    compressed_blob: bytes,
    df: pd.DataFrame,
    query_address: str,
    method: str = "zstd",
) -> dict:
    """
    Simulate searching for an address in a RANDOM-order compressed file.
    Must decompress the entire file, then scan all rows.
    """
    t0 = time.perf_counter()

    if method == "zstd":
        raw = decompress_zstd(compressed_blob)
    else:
        raw = decompress_gzip(compressed_blob)

    result_df = _bytes_to_df(raw)
    hits = result_df[
        (result_df["from_address"] == query_address) |
        (result_df["to_address"]   == query_address)
    ]
    elapsed = time.perf_counter() - t0

    return {
        "strategy":         "random_baseline",
        "search_time_s":    elapsed,
        "rows_decompressed": len(result_df),
        "rows_scanned":      len(result_df),
        "hits":              len(hits),
        "blocks_opened":     1,
        "bytes_decompressed": len(raw),
    }


def simulate_search_cluster_index(
    per_cluster_result: dict,
    df: pd.DataFrame,
    labels: np.ndarray,
    query_address: str,
    method: str = "zstd",
) -> dict:
    """
    Simulate searching using the Cluster Index (per-cluster blocks).
    Strategy:
      1. Look up the cluster index to find which cluster(s) the address belongs to.
      2. Decompress ONLY those blocks.
      3. Scan only the decompressed rows.
    This is a simulated O(k) search where k = number of relevant clusters (usually 1-2).
    """
    t0 = time.perf_counter()

    tmp = df.copy()
    tmp["_cluster"] = labels

    # Find which clusters contain this address
    addr_clusters = tmp[
        (tmp["from_address"] == query_address) |
        (tmp["to_address"]   == query_address)
    ]["_cluster"].unique().tolist()

    block_index = per_cluster_result["index"]
    blob        = per_cluster_result["blob"]

    rows_decompressed = 0
    hits              = 0
    blocks_opened     = 0
    bytes_dec         = 0

    # If address not in known clusters, fall back to checking noise block
    if len(addr_clusters) == 0:
        addr_clusters = [-1]  # search noise cluster only

    for cid in addr_clusters:
        info = block_index.get(int(cid))
        if info is None:
            continue
        off  = info["offset"]
        csz  = info["comp_size"]
        comp_block = blob[off: off + csz]

        if method == "zstd":
            raw_block = decompress_zstd(comp_block)
        else:
            raw_block = decompress_gzip(comp_block)

        block_df = _bytes_to_df(raw_block)
        found = block_df[
            (block_df["from_address"] == query_address) |
            (block_df["to_address"]   == query_address)
        ]
        rows_decompressed += len(block_df)
        hits              += len(found)
        blocks_opened     += 1
        bytes_dec         += len(raw_block)

    elapsed = time.perf_counter() - t0

    total_rows = len(df)
    return {
        "strategy":           "cluster_indexed",
        "search_time_s":      elapsed,
        "rows_decompressed":   rows_decompressed,
        "rows_scanned":        rows_decompressed,
        "hits":                hits,
        "blocks_opened":       blocks_opened,
        "bytes_decompressed":  bytes_dec,
        "clusters_targeted":   len(addr_clusters),
        "pct_data_read":       rows_decompressed / total_rows * 100,
    }


# ══════════════════════════════════════════════════════════════════════
#  UTILITIES
# ══════════════════════════════════════════════════════════════════════

def human_size(n_bytes: float) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(n_bytes) < 1024:
            return f"{n_bytes:.2f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.2f} TB"


def build_comparison_table(results: list[dict]) -> pd.DataFrame:
    """Build a comparison DataFrame from multiple compression result dicts."""
    rows = []
    for r in results:
        rows.append({
            "Strategy":       r["strategy"],
            "Method":         r["method"].upper(),
            "Raw Size":       human_size(r["raw_size"]),
            "Compressed":     human_size(r["comp_size"]),
            "Ratio":          f"{r['ratio']:.2f}x",
            "Space Saved %":  f"{r['pct_saved']:.1f}%",
            "Comp Time (s)":  f"{r['comp_time_s']:.3f}",
            "# Blocks":       r["n_blocks"],
            "Searchable":     "✅ Yes" if r["index"] else "❌ No (full scan)",
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════
#  COMPRESSION LEVELS COMPARISON
# ═══════════════════════════════════════════

@st.cache_data(show_spinner=False)
def compare_compression_levels(raw_bytes: bytes) -> pd.DataFrame:
    import time as _t, gzip as _gz
    rows = []
    for lvl in [1, 3, 6, 9, 15, 19]:
        t0 = _t.perf_counter()
        cctx = zstd.ZstdCompressor(level=lvl)
        comp = cctx.compress(raw_bytes)
        elapsed = _t.perf_counter() - t0
        rows.append(dict(method=f"zstd-{lvl}", level=lvl, algo="zstd",
                         comp_size=len(comp), ratio=len(raw_bytes)/len(comp),
                         pct_saved=(1-len(comp)/len(raw_bytes))*100, time_s=elapsed))
    for lvl in [1, 3, 6, 9]:
        t0 = _t.perf_counter()
        comp = _gz.compress(raw_bytes, compresslevel=lvl)
        elapsed = _t.perf_counter() - t0
        rows.append(dict(method=f"gzip-{lvl}", level=lvl, algo="gzip",
                         comp_size=len(comp), ratio=len(raw_bytes)/len(comp),
                         pct_saved=(1-len(comp)/len(raw_bytes))*100, time_s=elapsed))
    return pd.DataFrame(rows)


def export_compressed_file(df, labels, method="zstd", strategy="cluster_sorted"):
    import gzip as _gz
    tmp = df.copy()
    if strategy == "cluster_sorted":
        tmp["_cluster"] = labels
        tmp = tmp.sort_values("_cluster").drop(columns=["_cluster"])
    raw = _df_to_bytes(tmp)
    if method == "zstd":
        cctx = zstd.ZstdCompressor(level=3)
        return cctx.compress(raw)
    return _gz.compress(raw, compresslevel=6)


def export_cluster_index_json(per_cluster_result):
    import json
    clean = {str(k): v for k, v in per_cluster_result["index"].items()}
    return json.dumps(clean, indent=2, ensure_ascii=False).encode("utf-8")
