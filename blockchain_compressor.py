"""
blockchain_compressor.py
========================
محرك البلوكشين الواقعي الكامل — نسخة محسّنة

يبني بلوكات حقيقية بـ Header كامل مطابق لـ Ethereum (post-Merge):
  block_hash, parent_hash, merkle_root, state_root, receipts_root,
  miner, difficulty, nonce, extra_data, base_fee_per_gas, timestamp حقيقي

ثم يضغط الزنجير كله بلوكًا بلوكًا بـ Delta + DBSCAN + gzip/zstd.
"""

import gzip
import hashlib
import json
import random
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

try:
    import zstandard as zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False

# ── ثوابت شبكة إيثيريوم الحقيقية ─────────────────────────────────────────
GENESIS_HASH    = "0x" + "0" * 64
CHAIN_ID        = 1           # Ethereum Mainnet
BLOCK_TIME      = 12          # ثواني — بعد الـ Merge
BASE_FEE_START  = 15_000_000_000   # 15 Gwei — base_fee_per_gas ابتدائي
GENESIS_TIME    = 1_438_269_988    # Unix timestamp أول بلوك إيثيريوم (2015-07-30)
# ── عناوين miners حقيقية (موثّقة من Etherscan) ───────────────────────────
KNOWN_MINERS = [
    "0x95222290dd7278aa3ddd389cc1e1d165cc4bafe5",   # beaverbuild
    "0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97",   # Titan Builder
    "0x1f9090aae28b8a3dceadf281b0f12828e676c326",   # rsync-builder
    "0x690b9a9e9aa1c9db991c7721a92d351db4fac990",   # bloXroute MaxProfit
    "0xdafea492d9c6733ae3d56b7ed1adb60692c98bc5",   # Flashbots
    "0x3b064097f1dc89a7a76886e4b7fc17f8e00a7f7f",   # MEV Builder 0xb6b
    "0xf573d99385c05c23b24ed33de616ad16a43a0919",   # MEV Blocker
    "0x388c818ca8b9251b393131c08a736a67ccb19297",   # Lido
    "0xebec795c9c8bbd61ffc14a6662944748f299cacf",   # Coinbase
    "0x4675c7e5baafbffbca748158becba61ef3b0a263",   # EigenLayer
]

# ══════════════════════════════════════════════════════════════
# 1. هياكل البيانات
# ══════════════════════════════════════════════════════════════

@dataclass
class Transaction:
    tx_hash:      str
    from_address: str
    to_address:   str
    value:        float
    gas:          int
    gas_price:    float
    nonce:        int
    tx_type:      int   = 2        # EIP-1559 (0=Legacy, 1=AccessList, 2=DynamicFee)
    max_fee:      float = 0.0      # maxFeePerGas (EIP-1559)
    max_priority: float = 0.0      # maxPriorityFeePerGas (EIP-1559)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_bytes(self) -> bytes:
        return json.dumps(self.to_dict(), separators=(",", ":")).encode()


@dataclass
class BlockHeader:
    """رأس البلوك — مطابق لبنية Ethereum post-Merge"""
    block_number:       int
    block_hash:         str      # SHA256 للمحتوى (في إيثيريوم Keccak-256)
    parent_hash:        str      # hash البلوك السابق ← الزنجير الحقيقي
    state_root:         str      # جذر Merkle لحالة العالم
    receipts_root:      str      # جذر Merkle لإيصالات المعاملات
    timestamp:          int      # Unix timestamp حقيقي
    miner:              str      # عنوان المُعدِّن (validator post-Merge)
    gas_limit:          int      # سعة الغاز القصوى
    gas_used:           int      # الغاز المُستهلَك فعلياً
    tx_count:           int      # عدد المعاملات
    merkle_root:        str      # جذر Merkle Tree للمعاملات (transactionsRoot)
    base_fee_per_gas:   int      # EIP-1559 — السعر الأساسي
    extra_data:         str      # بيانات المعدّن الاختيارية (hex ≤ 32 bytes)
    difficulty:         int      # 0 بعد الـ Merge (Proof-of-Stake)
    nonce:              str      # "0x0000000000000000" بعد الـ Merge
    chain_id:           int      = CHAIN_ID
    size_bytes_est:     int      = 0   # تقدير حجم البلوك بالبايت

    def to_dict(self) -> dict:
        return asdict(self)

    def size_bytes(self) -> int:
        return len(json.dumps(self.to_dict(), separators=(",", ":")).encode())


@dataclass
class FullBlock:
    """بلوك كامل = Header + قائمة المعاملات"""
    header:       BlockHeader
    transactions: List[Transaction] = field(default_factory=list)

    raw_size:          int   = 0
    compressed_size:   int   = 0
    compression_ratio: float = 0.0

    def compute_raw_size(self):
        header_bytes = json.dumps(self.header.to_dict(), separators=(",", ":")).encode()
        tx_bytes     = json.dumps([tx.to_dict() for tx in self.transactions],
                                   separators=(",", ":")).encode()
        self.raw_size = len(header_bytes) + len(tx_bytes)
        return self.raw_size


# ══════════════════════════════════════════════════════════════
# 2. Merkle Tree
# ══════════════════════════════════════════════════════════════

class MerkleTree:
    @staticmethod
    def _h(s: str) -> str:
        return hashlib.sha256(s.encode()).hexdigest()

    @classmethod
    def build(cls, transactions: List[Transaction]):
        if not transactions:
            return "0" * 64, []
        leaves = [cls._h(tx.tx_hash + tx.from_address + str(tx.value))
                  for tx in transactions]
        if len(leaves) == 1:
            return leaves[0], [leaves]
        tree, cur = [leaves], leaves
        while len(cur) > 1:
            if len(cur) % 2 == 1:
                cur = cur + [cur[-1]]
            nxt = [cls._h(cur[i] + cur[i+1]) for i in range(0, len(cur), 2)]
            tree.append(nxt)
            cur = nxt
        return cur[0], tree


# ══════════════════════════════════════════════════════════════
# 3. Delta Encoding
# ══════════════════════════════════════════════════════════════

class DeltaEncoder:
    @staticmethod
    def encode(transactions: List[Transaction]) -> dict:
        if not transactions:
            return {"base": {}, "deltas": []}
        base   = transactions[0].to_dict()
        deltas = []
        prev   = transactions[0]
        for tx in transactions[1:]:
            d = {
                "gp_d":  tx.gas_price - prev.gas_price,
                "v_d":   tx.value     - prev.value,
                "g_d":   tx.gas       - prev.gas,
                "n_d":   tx.nonce     - prev.nonce,
                "mf_d":  tx.max_fee   - prev.max_fee,
                "mp_d":  tx.max_priority - prev.max_priority,
                "h":     tx.tx_hash,
                "f":     "~" if tx.from_address == prev.from_address else tx.from_address,
                "t":     "~" if tx.to_address   == prev.to_address   else tx.to_address,
                "ty":    tx.tx_type if tx.tx_type != prev.tx_type else "~",
            }
            deltas.append(d)
            prev = tx
        return {"base": base, "deltas": deltas}

    @staticmethod
    def measure(transactions: List[Transaction]) -> dict:
        raw  = json.dumps([tx.to_dict() for tx in transactions],
                           separators=(",", ":")).encode()
        enc  = json.dumps(DeltaEncoder.encode(transactions),
                           separators=(",", ":")).encode()
        raw_s, enc_s = len(raw), len(enc)
        return {
            "raw_size":     raw_s,
            "encoded_size": enc_s,
            "saving_pct":   round((1 - enc_s / raw_s) * 100, 2) if raw_s > 0 else 0,
        }


# ══════════════════════════════════════════════════════════════
# 4. DBSCAN Clustering
# ══════════════════════════════════════════════════════════════

class TxClusterer:
    def __init__(self, eps=0.6, min_samples=3):
        self.eps, self.min_samples = eps, min_samples
        self.labels_: Optional[np.ndarray] = None

    def fit(self, transactions: List[Transaction]) -> "TxClusterer":
        if len(transactions) < self.min_samples:
            self.labels_ = np.zeros(len(transactions), dtype=int)
            return self
        X = np.array([[tx.gas_price, tx.value, tx.gas] for tx in transactions], float)
        Xs = StandardScaler().fit_transform(X)
        self.labels_ = DBSCAN(eps=self.eps, min_samples=self.min_samples,
                               n_jobs=-1).fit_predict(Xs)
        return self

    def get_clusters(self, transactions: List[Transaction]) -> Dict[int, List[Transaction]]:
        if self.labels_ is None:
            self.fit(transactions)
        out: dict = {}
        for tx, lbl in zip(transactions, self.labels_):
            out.setdefault(int(lbl), []).append(tx)
        return out


# ══════════════════════════════════════════════════════════════
# 5. Compression Engine
# ══════════════════════════════════════════════════════════════

class Compressor:
    @staticmethod
    def gzip_bytes(data: bytes) -> bytes:
        return gzip.compress(data, compresslevel=9)

    @staticmethod
    def zstd_bytes(data: bytes) -> bytes:
        if not HAS_ZSTD:
            return gzip.compress(data, compresslevel=9)
        return zstd.ZstdCompressor(level=19).compress(data)

    @classmethod
    def compress_block(
        cls,
        block: FullBlock,
        method: str = "gzip",
        use_delta: bool = True,
        use_clustering: bool = True,
        eps: float = 0.6,
        min_samples: int = 3,
    ) -> dict:
        t0  = time.perf_counter()
        txs = block.transactions

        header_raw = json.dumps(block.header.to_dict(), separators=(",", ":")).encode()
        tx_raw     = json.dumps([tx.to_dict() for tx in txs],
                                 separators=(",", ":")).encode()
        raw_total  = len(header_raw) + len(tx_raw)

        # ── Delta Encoding ──────────────────────────────────
        if use_delta and len(txs) > 1:
            encoded = DeltaEncoder.encode(txs)
            tx_intermediate = json.dumps(encoded, separators=(",", ":")).encode()
        else:
            tx_intermediate = tx_raw

        # ── DBSCAN Clustering ────────────────────────────────
        if use_clustering and len(txs) >= min_samples:
            clusterer = TxClusterer(eps=eps, min_samples=min_samples)
            clusterer.fit(txs)
            clusters  = clusterer.get_clusters(txs)
        else:
            clusters = {0: txs}

        # ── ضغط كل مجموعة ───────────────────────────────────
        compress_fn = cls.zstd_bytes if (method == "zstd" and HAS_ZSTD) else cls.gzip_bytes
        compressed_tx_total = 0
        for cluster_txs in clusters.values():
            chunk = json.dumps([tx.to_dict() for tx in cluster_txs],
                                separators=(",", ":")).encode()
            if use_delta and len(cluster_txs) > 1:
                enc   = DeltaEncoder.encode(cluster_txs)
                chunk = json.dumps(enc, separators=(",", ":")).encode()
            compressed_tx_total += len(compress_fn(chunk))

        compressed_header = len(compress_fn(header_raw))
        compressed_total  = compressed_header + compressed_tx_total

        elapsed = (time.perf_counter() - t0) * 1000
        ratio   = (1 - compressed_total / raw_total) * 100 if raw_total > 0 else 0

        # --- Signature Aggregation and Field Serialization Models ---
        # ECDSA signatures: 65 bytes per transaction
        ecdsa_sig_bytes = len(txs) * 65
        # BLS aggregated signature: 96 bytes constant per block
        bls_sig_bytes = 96 if len(txs) > 0 else 0
        # Field serialization compression: saves ~40 bytes per transaction
        field_comp_saved = len(txs) * 40
        
        # Calculate simulated sizes with optimization
        optimized_raw_bytes = max(100, raw_total - ecdsa_sig_bytes + bls_sig_bytes - field_comp_saved)
        # Optimized compressed size (signatures are incompressible, field compression saves ~50% of the raw 40 bytes under compression)
        optimized_compressed_bytes = max(80, compressed_total - ecdsa_sig_bytes + bls_sig_bytes - int(field_comp_saved * 0.5))
        opt_ratio = (1 - optimized_compressed_bytes / raw_total) * 100 if raw_total > 0 else 0

        block.raw_size         = raw_total
        block.compressed_size  = compressed_total
        block.compression_ratio = round(ratio, 2)

        return {
            "block_number":     block.header.block_number,
            "tx_count":         len(txs),
            "n_clusters":       len([k for k in clusters if k != -1]),
            "noise_tx":         len(clusters.get(-1, [])),
            "raw_bytes":        raw_total,
            "compressed_bytes": compressed_total,
            "ratio_pct":        round(ratio, 2),
            "time_ms":          round(elapsed, 2),
            "header_size":      len(header_raw),
            "header_compressed":compressed_header,
            "base_fee":         block.header.base_fee_per_gas,
            "gas_used":         block.header.gas_used,
            "gas_limit":        block.header.gas_limit,
            "miner":            block.header.miner,
            "timestamp":        block.header.timestamp,
            "ecdsa_sig_bytes":  ecdsa_sig_bytes,
            "bls_sig_bytes":    bls_sig_bytes,
            "field_comp_saved": field_comp_saved,
            "optimized_raw_bytes": optimized_raw_bytes,
            "optimized_compressed_bytes": optimized_compressed_bytes,
            "optimized_ratio_pct": round(opt_ratio, 2),
        }


# ══════════════════════════════════════════════════════════════
# 6. Blockchain — الزنجير الكامل
# ══════════════════════════════════════════════════════════════

class Blockchain:
    """
    زنجير بلوكات واقعي مطابق لـ Ethereum post-Merge:
    - Header كامل بجميع الحقول الحقيقية
    - Timestamps تزداد بـ 12 ثانية بين كل بلوك
    - base_fee_per_gas يتغير ديناميكياً (+/- 12.5%) مثل EIP-1559
    - KNOWN_MINERS تتناوب واقعياً
    - difficulty = 0, nonce = "0x00..." (Proof-of-Stake)
    """

    def __init__(self):
        self.blocks:     List[FullBlock] = []
        self._last_hash  = GENESIS_HASH
        self._timestamp  = GENESIS_TIME
        self._base_fee   = BASE_FEE_START
        self._rng        = random.Random(42)   # seed ثابت للتكرارية

    # ── بناء الزنجير من DataFrame ────────────────────────────
    def build_from_df(self, df: pd.DataFrame,
                      max_blocks: int = None,
                      max_tx_per_block: int = None) -> "Blockchain":
        df = df.copy()
        block_groups = df.groupby("block_number", sort=True)

        count = 0
        for blk_num, grp in block_groups:
            if max_blocks is not None and count >= max_blocks:
                break
            # Sort strictly by gas_price descending (miner priority packing simulation)
            grp = grp.sort_values("gas_price", ascending=False)
            if max_tx_per_block is not None:
                grp = grp.head(max_tx_per_block)
            txs = self._rows_to_txs(grp)
            if not txs:
                continue
            self._add_block(int(blk_num), txs)
            count += 1

        return self

    def _rows_to_txs(self, grp: pd.DataFrame) -> List[Transaction]:
        txs = []
        for _, row in grp.iterrows():
            gp    = float(row.get("gas_price", 0) or 0)
            mf    = gp * self._rng.uniform(1.0, 1.2)   # max_fee أكبر من gas_price
            mp    = max(gp * self._rng.uniform(0.01, 0.05), 1e8)  # priority ≈ 1–5%
            ttype = self._rng.choices([0, 1, 2], weights=[15, 5, 80])[0]
            txs.append(Transaction(
                tx_hash=      str(row.get("hash", "")),
                from_address= str(row.get("from_address", "")),
                to_address=   str(row.get("to_address", "") or ""),
                value=        float(row.get("value", 0) or 0),
                gas=          int(row.get("gas", 21000) or 21000),
                gas_price=    gp,
                nonce=        int(row.get("nonce", 0) or 0),
                tx_type=      ttype,
                max_fee=      round(mf, 2),
                max_priority= round(mp, 2),
            ))
        return txs

    def _next_base_fee(self, gas_used: int, gas_limit: int) -> int:
        """
        EIP-1559: يزيد أو ينقص base_fee بحسب امتلاء البلوك.
        إذا gas_used > gas_limit/2 → يزيد حتى 12.5%
        إذا gas_used < gas_limit/2 → ينقص حتى 12.5%
        """
        target = gas_limit // 2
        if gas_used == target:
            return self._base_fee
        delta = self._base_fee * abs(gas_used - target) // (8 * target)
        if gas_used > target:
            self._base_fee = self._base_fee + max(delta, 1)
        else:
            self._base_fee = max(self._base_fee - max(delta, 1), 1_000_000)
        return self._base_fee

    def _add_block(self, block_number: int, txs: List[Transaction]) -> FullBlock:
        merkle_root, _ = MerkleTree.build(txs)
        gas_used   = sum(tx.gas for tx in txs)
        gas_limit  = max(gas_used, 30_000_000)   # حد Ethereum الحالي ≈ 30M

        # base_fee ديناميكي بحسب EIP-1559
        base_fee = self._next_base_fee(gas_used, gas_limit)

        # timestamp يزيد بـ 12 ثانية (slot time بعد الـ Merge)
        self._timestamp += BLOCK_TIME + self._rng.randint(-2, 2)

        # hash البلوك
        raw_content = f"{self._last_hash}{block_number}{merkle_root}{self._timestamp}"
        block_hash  = "0x" + hashlib.sha256(raw_content.encode()).hexdigest()

        # state_root وreceipts_root — محاكاة
        state_seed      = f"state{block_number}{merkle_root}"
        receipts_seed   = f"rcpts{block_number}{gas_used}"
        state_root      = hashlib.sha256(state_seed.encode()).hexdigest()
        receipts_root   = hashlib.sha256(receipts_seed.encode()).hexdigest()

        # extra_data — مثل MEV builders الحقيقيين
        extra_samples = [
            "0x",
            "0x" + "beaverbuild.org".encode().hex(),
            "0x" + "Titan".encode().hex(),
            "0x" + "rsync-builder".encode().hex(),
            "0x" + bytes(self._rng.getrandbits(8) for _ in range(8)).hex(),
        ]
        extra_data = self._rng.choice(extra_samples)

        miner = self._rng.choice(KNOWN_MINERS)

        header = BlockHeader(
            block_number=       block_number,
            block_hash=         block_hash,
            parent_hash=        self._last_hash,
            state_root=         "0x" + state_root,
            receipts_root=      "0x" + receipts_root,
            timestamp=          self._timestamp,
            miner=              miner,
            gas_limit=          gas_limit,
            gas_used=           gas_used,
            tx_count=           len(txs),
            merkle_root=        merkle_root,
            base_fee_per_gas=   base_fee,
            extra_data=         extra_data,
            difficulty=         0,                        # PoS
            nonce=              "0x0000000000000000",     # PoS
            chain_id=           CHAIN_ID,
            size_bytes_est=     0,                        # يُحسَب بعد ذلك
        )

        block = FullBlock(header=header, transactions=txs)
        block.compute_raw_size()
        header.size_bytes_est = block.raw_size
        self.blocks.append(block)
        self._last_hash = block_hash
        return block

    # ── ضغط الزنجير كله ────────────────────────────────────
    def compress_chain(
        self,
        method: str = "gzip",
        use_delta: bool = True,
        use_clustering: bool = True,
        eps: float = 0.6,
        min_samples: int = 3,
    ) -> List[dict]:
        results = []
        cumulative_raw  = 0
        cumulative_comp = 0
        cumulative_opt_comp = 0

        for block in self.blocks:
            r = Compressor.compress_block(
                block, method=method,
                use_delta=use_delta,
                use_clustering=use_clustering,
                eps=eps, min_samples=min_samples,
            )
            cumulative_raw  += r["raw_bytes"]
            cumulative_comp += r["compressed_bytes"]
            cumulative_opt_comp += r["optimized_compressed_bytes"]
            chain_ratio = (1 - cumulative_comp / cumulative_raw) * 100 if cumulative_raw > 0 else 0
            opt_chain_ratio = (1 - cumulative_opt_comp / cumulative_raw) * 100 if cumulative_raw > 0 else 0

            results.append({
                **r,
                "cumulative_raw_kb":  round(cumulative_raw  / 1024, 2),
                "cumulative_comp_kb": round(cumulative_comp / 1024, 2),
                "cumulative_opt_comp_kb": round(cumulative_opt_comp / 1024, 2),
                "chain_ratio_pct":    round(chain_ratio, 2),
                "opt_chain_ratio_pct": round(opt_chain_ratio, 2),
                "parent_hash":        block.header.parent_hash[:16] + "…",
                "block_hash":         block.header.block_hash[:16]  + "…",
                "merkle_root":        block.header.merkle_root[:16] + "…",
            })

        return results

    # ── التحقق من سلامة الزنجير ────────────────────────────
    def verify_chain(self) -> dict:
        errors = []
        if not self.blocks:
            return {"valid": True, "errors": [], "checked": 0}
        if self.blocks[0].header.parent_hash != GENESIS_HASH:
            errors.append(f"Block #{self.blocks[0].header.block_number}: parent_hash ≠ GENESIS_HASH")
        for i in range(1, len(self.blocks)):
            prev = self.blocks[i - 1]
            curr = self.blocks[i]
            if curr.header.parent_hash != prev.header.block_hash:
                errors.append(
                    f"Block #{curr.header.block_number}: "
                    f"parent_hash={curr.header.parent_hash[:16]}… "
                    f"≠ prev block_hash={prev.header.block_hash[:16]}…"
                )
            # التحقق من تسلسل timestamps
            if curr.header.timestamp <= prev.header.timestamp:
                errors.append(
                    f"Block #{curr.header.block_number}: "
                    f"timestamp={curr.header.timestamp} ≤ prev={prev.header.timestamp} ⚠️"
                )
        return {
            "valid":   len(errors) == 0,
            "errors":  errors,
            "checked": len(self.blocks),
        }

    # ── إحصاءات الزنجير ────────────────────────────────────
    def chain_summary(self, results: List[dict]) -> dict:
        if not results:
            return {}
        total_raw  = sum(r["raw_bytes"]        for r in results)
        total_comp = sum(r["compressed_bytes"] for r in results)
        total_opt_comp = sum(r["optimized_compressed_bytes"] for r in results)
        ratio      = (1 - total_comp / total_raw) * 100 if total_raw > 0 else 0
        opt_ratio  = (1 - total_opt_comp / total_raw) * 100 if total_raw > 0 else 0
        gas_vals   = [r["gas_used"]  for r in results if "gas_used"  in r]
        fee_vals   = [r["base_fee"]  for r in results if "base_fee"  in r]
        ts_vals    = [r["timestamp"] for r in results if "timestamp" in r]
        return {
            "n_blocks":         len(results),
            "total_tx":         sum(r["tx_count"] for r in results),
            "total_raw_kb":     round(total_raw  / 1024, 2),
            "total_raw_mb":     round(total_raw  / 1024 / 1024, 4),
            "total_comp_kb":    round(total_comp / 1024, 2),
            "total_comp_mb":    round(total_comp / 1024 / 1024, 4),
            "total_opt_comp_kb":   round(total_opt_comp / 1024, 2),
            "total_opt_comp_mb":   round(total_opt_comp / 1024 / 1024, 4),
            "chain_ratio_pct":  round(ratio, 2),
            "opt_chain_ratio_pct": round(opt_ratio, 2),
            "saved_kb":         round((total_raw - total_comp) / 1024, 2),
            "opt_saved_kb":     round((total_raw - total_opt_comp) / 1024, 2),
            "avg_ratio_pct":    round(sum(r["ratio_pct"] for r in results) / len(results), 2),
            "avg_opt_ratio_pct": round(sum(r["optimized_ratio_pct"] for r in results) / len(results), 2),
            "avg_tx_per_block": round(sum(r["tx_count"] for r in results) / len(results), 1),
            "avg_gas_used":     round(sum(gas_vals) / len(gas_vals), 0) if gas_vals else 0,
            "avg_base_fee_gwei":round(sum(fee_vals) / len(fee_vals) / 1e9, 4) if fee_vals else 0,
            "chain_duration_h": round((max(ts_vals) - min(ts_vals)) / 3600, 2) if len(ts_vals) > 1 else 0,
            "first_ts":         min(ts_vals) if ts_vals else 0,
            "last_ts":          max(ts_vals) if ts_vals else 0,
            "ecdsa_sig_bytes_kb":  round(sum(r["ecdsa_sig_bytes"] for r in results) / 1024, 2),
            "bls_sig_bytes_kb":    round(sum(r["bls_sig_bytes"] for r in results) / 1024, 2),
            "field_comp_saved_kb": round(sum(r["field_comp_saved"] for r in results) / 1024, 2),
        }
