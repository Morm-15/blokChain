"""
tx_batcher.py ― Blockchain Storage Optimization & Size Reduction Engine
========================================================================
This module models and simulates blockchain block packing and data compression.
It replaces complex clustering algorithms with real-world priority-based (Gas Price)
block filling, focusing on metrics such as compression ratio, space savings, and signature aggregation.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple

class TransactionBatcher:
    """
    Simulates blockchain storage optimization techniques on transactions:
    - Signature Aggregation (ECDSA 65 bytes -> BLS 96 bytes per block)
    - Field Serialization Compression (Variable-length integers / RLP)
    - Block-Level Compression (Zstd / Snappy)
    """
    
    def __init__(self, block_gas_limit: int = 15_000_000):
        self.block_gas_limit = block_gas_limit

    def calculate_tx_sizes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates simulated transaction sizes based on real-world blockchain metrics.
        - A standard transaction (e.g., Ether transfer, gas_limit = 21,000) is about 110 bytes.
        - Larger gas limits represent contract interactions with variable payload sizes.
        - ECDSA signature size is 65 bytes.
        """
        df_copy = df.copy()
        
        # Base size model: 110 bytes base for 21000 gas, plus 0.005 bytes per gas unit above 21000.
        # Add a tiny deterministic noise based on the index to make the data feel real.
        np.random.seed(42)
        noise = np.random.normal(0, 5, len(df_copy))
        
        sizes = 110 + (df_copy["gas_limit"] - 21000).clip(lower=0) * 0.005 + noise
        df_copy["uncompressed_size_bytes"] = np.round(sizes.clip(lower=110)).astype(int)
        
        # ECDSA signature is 65 bytes of the total uncompressed size.
        df_copy["ecdsa_sig_bytes"] = 65
        
        # Field compression saves about 40 bytes per transaction by compressing fixed 256-bit fields
        # (gas price, limit, nonce) into variable-length integers (varints).
        df_copy["field_compressed_size_bytes"] = np.round(
            (df_copy["uncompressed_size_bytes"] - 65 - 40).clip(lower=15)
        ).astype(int)
        
        return df_copy

    def pack_block(self, df_mempool: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """
        Simulates packing transactions from the mempool into a block using priority fee (gas_price).
        Returns:
            packed_txs (pd.DataFrame): Transactions successfully placed in the block.
            remaining_mempool (pd.DataFrame): Leftover transactions.
            stats (Dict): Storage statistics for the packed block.
        """
        # Ensure sizes are calculated
        if "uncompressed_size_bytes" not in df_mempool.columns:
            df_mempool = self.calculate_tx_sizes(df_mempool)
            
        # Sort mempool strictly by Gas Price (descending) as in real-world networks (miner priority)
        sorted_mempool = df_mempool.sort_values("gas_price", ascending=False).reset_index(drop=True)
        
        packed_indices = []
        total_gas = 0
        total_revenue_gwei = 0.0
        
        for idx, row in sorted_mempool.iterrows():
            gas_needed = int(row["gas_limit"])
            if total_gas + gas_needed <= self.block_gas_limit:
                total_gas += gas_needed
                total_revenue_gwei += float(row["gas_price"]) * gas_needed / 1e9
                packed_indices.append(idx)
            else:
                # Continue trying to pack smaller transactions (Greedy Knapsack for gas limit)
                continue
                
        packed_txs = sorted_mempool.loc[packed_indices].copy().reset_index(drop=True)
        remaining_mempool = sorted_mempool.drop(index=packed_indices).reset_index(drop=True)
        
        n_tx = len(packed_txs)
        if n_tx == 0:
            return packed_txs, remaining_mempool, self._empty_stats()
            
        # --- Storage Metrics Calculation ---
        # 1. Uncompressed Block: Sum of raw transaction sizes (includes 65 bytes ECDSA signature per tx)
        uncompressed_size = int(packed_txs["uncompressed_size_bytes"].sum())
        
        # 2. Optimized (Signature Aggregated + Field Compressed) Block:
        # - Remove 65-byte ECDSA signatures from each transaction.
        # - Add 96-byte BLS aggregated signature for the entire block.
        # - Use field-compressed sizes for headers.
        field_compressed_tx_sum = packed_txs["field_compressed_size_bytes"].sum()
        optimized_size = int(field_compressed_tx_sum + 96)
        
        # 3. Fully Compressed Block (Zstandard applied on optimized data, simulating a 35% general compression)
        compressed_size = int(np.round(optimized_size * 0.65))
        
        # 4. Compression metrics
        compression_ratio = uncompressed_size / compressed_size if compressed_size > 0 else 1.0
        space_saving_pct = (1.0 - (compressed_size / uncompressed_size)) * 100.0 if uncompressed_size > 0 else 0.0
        bytes_saved = uncompressed_size - compressed_size
        
        stats = {
            "tx_count": n_tx,
            "gas_used": total_gas,
            "gas_efficiency": round((total_gas / self.block_gas_limit) * 100.0, 2),
            "miner_revenue_gwei": round(total_revenue_gwei, 4),
            "uncompressed_size_kb": round(uncompressed_size / 1024.0, 3),
            "optimized_size_kb": round(optimized_size / 1024.0, 3),
            "compressed_size_kb": round(compressed_size / 1024.0, 3),
            "compression_ratio": round(compression_ratio, 2),
            "space_saving_pct": round(space_saving_pct, 2),
            "bytes_saved_kb": round(bytes_saved / 1024.0, 3)
        }
        
        return packed_txs, remaining_mempool, stats

    def simulate_multi_block(self, df_mempool: pd.DataFrame, n_blocks: int = 5) -> pd.DataFrame:
        """
        Simulates storage growth and size savings over multiple blocks.
        """
        remaining = self.calculate_tx_sizes(df_mempool)
        blocks_data = []
        
        cumulative_uncompressed = 0.0
        cumulative_compressed = 0.0
        cumulative_saved = 0.0
        
        for block_num in range(1, n_blocks + 1):
            if remaining.empty:
                break
                
            packed, remaining, stats = self.pack_block(remaining)
            
            if stats["tx_count"] == 0:
                break
                
            cumulative_uncompressed += stats["uncompressed_size_kb"]
            cumulative_compressed += stats["compressed_size_kb"]
            cumulative_saved += stats["bytes_saved_kb"]
            
            blocks_data.append({
                "block": block_num,
                "tx_count": stats["tx_count"],
                "gas_used": stats["gas_used"],
                "gas_efficiency_%": stats["gas_efficiency"],
                "uncompressed_size_kb": stats["uncompressed_size_kb"],
                "compressed_size_kb": stats["compressed_size_kb"],
                "bytes_saved_kb": stats["bytes_saved_kb"],
                "compression_ratio": stats["compression_ratio"],
                "space_saving_%": stats["space_saving_pct"],
                "cum_uncompressed_kb": round(cumulative_uncompressed, 3),
                "cum_compressed_kb": round(cumulative_compressed, 3),
                "cum_saved_kb": round(cumulative_saved, 3)
            })
            
        return pd.DataFrame(blocks_data)

    def _empty_stats(self) -> Dict:
        return {
            "tx_count": 0,
            "gas_used": 0,
            "gas_efficiency": 0.0,
            "miner_revenue_gwei": 0.0,
            "uncompressed_size_kb": 0.0,
            "optimized_size_kb": 0.0,
            "compressed_size_kb": 0.0,
            "compression_ratio": 1.0,
            "space_saving_pct": 0.0,
            "bytes_saved_kb": 0.0
        }
