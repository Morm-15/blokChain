"""
Feature engineering for DBSCAN clustering.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import streamlit as st


FEATURE_COLS = [
    "value_eth",
    "gas_price_gwei",
    "gas_ratio",
    "is_contract_call",
    "tx_size_bytes",
    "scam_score",
]

FEATURE_DESCRIPTIONS = {
    "en": {
        "value_eth":        ("💰 Value (ETH)",        "Transaction amount in Ether"),
        "gas_price_gwei":   ("⛽ Gas Price (Gwei)",   "Price per gas unit in Gwei"),
        "gas_ratio":        ("📊 Gas Ratio",           "receipt_gas_used / gas_limit — efficiency of gas usage"),
        "is_contract_call": ("🤖 Contract Call",       "1 if transaction calls a smart contract, 0 otherwise"),
        "tx_size_bytes":    ("📦 TX Size (bytes)",     "Estimated storage size of the transaction"),
        "scam_score":       ("🚨 Scam Score",          "0 = clean, 1 = one party flagged, 2 = both flagged"),
    },
    "ar": {
        "value_eth":        ("💰 القيمة (ETH)",        "مبلغ المعاملة بالإيثر"),
        "gas_price_gwei":   ("⛽ سعر الغاز (Gwei)",  "سعر وحدة الغاز بـ Gwei"),
        "gas_ratio":        ("📊 نسبة الغاز",          "receipt_gas_used / gas_limit — كفاءة استخدام الغاز"),
        "is_contract_call": ("🤖 استدعاء عقد",         "1 إذا كانت المعاملة تستدعي عقداً ذكياً، 0 غير ذلك"),
        "tx_size_bytes":    ("📦 حجم المعاملة (بايت)","الحجم التقديري لتخزين المعاملة"),
        "scam_score":       ("🚨 درجة الاحتيال",       "0 = نظيف، 1 = طرف واحد مُعلَّم، 2 = كلاهما مُعلَّم"),
    },
    "tr": {
        "value_eth":        ("💰 Değer (ETH)",         "Ether cinsinden işlem tutarı"),
        "gas_price_gwei":   ("⛽ Gas Fiyatı (Gwei)",  "Gwei cinsinden gas birimi fiyatı"),
        "gas_ratio":        ("📊 Gas Oranı",           "receipt_gas_used / gas_limit — gas kullanım verimliliği"),
        "is_contract_call": ("🤖 Kontrat Çağrısı",    "Akıllı kontrat çağırıyorsa 1, değilse 0"),
        "tx_size_bytes":    ("📦 TX Boyutu (bayt)",    "İşlemin tahmini depolama boyutu"),
        "scam_score":       ("🚨 Dolandırıcılık Skoru","0 = temiz, 1 = bir taraf işaretli, 2 = ikisi de işaretli"),
    },
}


@st.cache_data(show_spinner=False)
def build_features(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Scale features and reduce to 2D/3D via PCA.
    Returns (X_scaled, pca_2d, pca_3d)
    """
    X_raw = df[FEATURE_COLS].fillna(0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    pca2 = PCA(n_components=2, random_state=42)
    pca3 = PCA(n_components=3, random_state=42)

    coords_2d = pca2.fit_transform(X_scaled)
    coords_3d = pca3.fit_transform(X_scaled)

    return X_scaled, coords_2d, coords_3d


@st.cache_data(show_spinner=False)
def get_pca_variance(df: pd.DataFrame) -> np.ndarray:
    """Return explained variance ratio for first 6 PCs."""
    X_raw = df[FEATURE_COLS].fillna(0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)
    pca = PCA(n_components=min(6, X_scaled.shape[1]), random_state=42)
    pca.fit(X_scaled)
    return pca.explained_variance_ratio_


def get_feature_descriptions(lang: str = "en") -> dict:
    return FEATURE_DESCRIPTIONS.get(lang, FEATURE_DESCRIPTIONS["en"])
