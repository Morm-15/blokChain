# ⛓️ Blockchain Cluster-Aware Compression

> **Bitirme Projesi** — Yapay Zeka Destekli Blockchain Boyutu Küçültme  
> DBSCAN Kümeleme + Zstandard/Gzip Sıkıştırma + İndeksli Arama

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)](https://streamlit.io)
[![DBSCAN](https://img.shields.io/badge/ML-DBSCAN-purple)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🚀 Canlı Demo

**[▶ Uygulamayı Aç](https://your-app.streamlit.app)**

---

## 📋 Proje Özeti

Bu proje, Ethereum blockchain işlem verilerini **makine öğrenimi (DBSCAN)** ile davranışsal kümelere ayırarak sıkıştırma verimliliğini ve arama hızını artırmaktadır.

### Ana Fikir

```
Veri (71K işlem)
    ↓  DBSCAN Kümeleme
    ↓  Kümeye Göre Sırala   ← Benzer satırları yanyana getir
    ↓  Parquet Serileştirme
    ↓  Zstd/Gzip Sıkıştırma ← Düşük entropi → Yüksek oran
    ↓  Küme İndeksi Oluştur
    ↓  O(1) İndeksli Arama  ← Sadece 1 blok aç!
```

### Sonuçlar

| Strateji              | Sıkıştırma Oranı | Arama Hızı          |
|-----------------------|-----------------|----------------------|
| Temel (rastgele)      | ~2.14×           | 🐢 Tam tarama        |
| Kümeye Göre Sıralı    | ~2.27× (+%6)    | ⚡ Satır aralığı     |
| Küme Başına Blok      | ~2.12×           | 🚀 O(1) blok erişimi |

---

## 🖥️ Uygulama Sayfaları

| Sayfa | İçerik |
|-------|--------|
| 📊 Genel Bakış | Veri seti istatistikleri, zaman çizelgesi |
| 🔬 DBSCAN Analizi | Küme haritası, K-Distance grafiği |
| 🗜️ Sıkıştırma Motoru | 3 strateji karşılaştırması, küme indeksi |
| 🔍 Arama Kıyaslaması | Gerçek adres sorgusu, hızlanma göstergesi |
| 📦 Blok Analizi | Blok başına boyut analizi |
| 📈 Performans Metrikleri | ε duyarlılık analizi, tam rapor |
| 🆚 Algoritma Karşılaştırması | DBSCAN vs K-Means, Elbow yöntemi, dolandırıcılık tespiti |
| 📥 Dışa Aktar | .zst dosyası, JSON indeksi, HTML raporu |

---

## ⚙️ Kurulum

### Gereksinimler

- Python 3.11+
- `Dataset.csv` (proje kök dizinine koyun)

### Yerel Çalıştırma

```bash
# Repoyu klonla
git clone https://github.com/your-username/blockzincir.git
cd blockzincir

# Bağımlılıkları yükle
pip install -r requirements.txt

# Dataset.csv'yi kök dizine koy
# Uygulamayı başlat
streamlit run app.py
```

---

## ☁️ Streamlit Cloud'da Yayınlama

1. **GitHub'a yükle** (Dataset.csv dahil)
2. [share.streamlit.io](https://share.streamlit.io) adresine git
3. GitHub reposunu bağla
4. `app.py` seç → **Deploy!**

---

## 📁 Proje Yapısı

```
blockzincir/
├── app.py                    # Ana uygulama (8 sayfa)
├── Dataset.csv               # Ethereum işlem verisi (71K işlem)
├── requirements.txt          # Python bağımlılıkları
├── rapor_hoca.html           # Türkçe akademik rapor
├── .streamlit/
│   └── config.toml           # Streamlit ayarları
└── modules/
    ├── data_loader.py        # Veri yükleme
    ├── feature_engineering.py # Özellik mühendisliği
    ├── dbscan_model.py       # DBSCAN kümeleme
    ├── kmeans_model.py       # K-Means karşılaştırma
    ├── compressor.py         # Sıkıştırma motoru
    ├── report_generator.py   # HTML rapor üretici
    └── translations.py       # EN/AR/TR çeviriler
```

---

## 🔬 Teknoloji Yığını

- **Streamlit** — Web arayüzü
- **scikit-learn** — DBSCAN, K-Means, PCA
- **Zstandard** — Hızlı kayıpsız sıkıştırma  
- **Apache Parquet** — Sütun tabanlı serileştirme
- **Plotly** — İnteraktif görselleştirme
- **Pandas / NumPy** — Veri işleme

---

## 📄 Lisans

MIT © 2026
