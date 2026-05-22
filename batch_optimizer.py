import pandas as pd

def assemble_batches(df, block_gas_limit=30_000_000):
    batches = []
    for cluster_id in sorted(df['cluster'].unique()):
        cluster_txs = df[df['cluster'] == cluster_id].sort_values("gas_price", ascending=False)
        current_batch = []
        current_gas = 0
        for _, tx in cluster_txs.iterrows():
            if current_gas + tx["gas_limit"] > block_gas_limit:
                batches.append({"cluster": cluster_id, "tx_count": len(current_batch), "gas_used": current_gas})
                current_batch = []
                current_gas = 0
            current_batch.append(tx)
            current_gas += tx["gas_limit"]
        if current_batch:
            batches.append({"cluster": cluster_id, "tx_count": len(current_batch), "gas_used": current_gas})
    return pd.DataFrame(batches)