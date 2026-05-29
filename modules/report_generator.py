"""
Report Generator — Styled HTML results report
=====================================================
Generates a comprehensive report of all compression results,
DBSCAN vs K-Means comparison, and performance metrics.
Works in all 3 languages (EN/AR/TR).
"""
import io
import base64
from datetime import datetime
import pandas as pd
from modules.compressor import human_size


# ── Color palette (matches Streamlit app) ────────────────────────────
VIOLET = "#7c3aed"
CYAN   = "#06b6d4"
GREEN  = "#22c55e"
RED    = "#ef4444"
AMBER  = "#f59e0b"
DARK   = "#0d1117"
CARD   = "#161b22"
TEXT   = "#e6edf3"
MUTED  = "#8b949e"
BORDER = "#30363d"


def _b64_svg(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def generate_html_report(
    stats: dict,
    baseline: dict,
    sorted_res: dict,
    per_res: dict,
    n_clusters: int,
    n_noise: int,
    etime: float,
    km_ratio: float,
    km_time: float,
    km_sil: float,
    dbscan_sil: float,
    method: str,
    lang: str = "en",
) -> str:
    """
    Generate a self-contained styled HTML report.
    Returns HTML string ready for download / browser print → PDF.
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Language strings ─────────────────────────────────────────────
    L = {
        "en": {
            "title":       "Blockchain Cluster-Aware Compression — Results Report",
            "subtitle":    "AI-Based Blockchain Size Reduction via Cluster-Aware Compression",
            "generated":   f"Generated: {ts}",
            "pipeline":    "Pipeline: DBSCAN Clustering → Cluster-Sorted Compression → Indexed Search",
            "s1":          "1. Dataset Overview",
            "s2":          "2. DBSCAN Clustering Results",
            "s3":          "3. Compression Strategy Comparison",
            "s4":          "4. DBSCAN vs K-Means Comparison",
            "s5":          "5. Key Findings",
            "total_txs":   "Total Transactions",
            "orig_size":   "Original Size",
            "scam_rate":   "Scam Rate",
            "clusters":    "Clusters Found",
            "noise":       "Noise Points",
            "sil":         "Silhouette Score",
            "dbscan_time": "DBSCAN Time",
            "strategy":    "Strategy",
            "comp_size":   "Compressed Size",
            "ratio":       "Compression Ratio",
            "saved":       "Space Saved",
            "searchable":  "Indexed Search",
            "baseline":    "Baseline (Shuffled)",
            "sorted":      "Cluster-Sorted",
            "percluster":  "Per-Cluster Blocks",
            "yes":         "✅ Yes",
            "no":          "❌ No (full scan)",
            "algo":        "Algorithm",
            "km_clusters": "Clusters",
            "km_noise":    "Noise Handling",
            "km_time":     "Clustering Time",
            "km_ratio":    "Compression Ratio",
            "km_sil":      "Silhouette Score",
            "km_k":        "K required?",
            "dbscan_n":    "DBSCAN",
            "kmeans_n":    "K-Means",
            "km_noise_y":  "✅ Automatic",
            "km_noise_n":  "❌ None",
            "km_k_y":      "✅ No",
            "km_k_n":      "❌ Yes (must set K)",
            "finding1":    f"Cluster-sorted compression improved ratio by {(sorted_res['ratio']/baseline['ratio']-1)*100:.1f}% vs random-order baseline.",
            "finding2":    f"DBSCAN found {n_clusters} behavioural clusters in just {etime:.1f}s using the KDTree-accelerated implementation.",
            "finding3":    f"DBSCAN compression ratio ({sorted_res['ratio']:.2f}×) {'outperforms' if sorted_res['ratio']>km_ratio else 'is comparable to'} K-Means ({km_ratio:.2f}×), with automatic noise handling.",
            "finding4":    f"Per-cluster indexed storage enables searching only 1 of {per_res['n_blocks']} blocks — drastically reducing I/O.",
            "finding5":    f"Total storage reduction: {human_size(baseline['raw_size'])} → {human_size(sorted_res['comp_size'])} ({sorted_res['pct_saved']:.1f}% saved) using {method.upper()}.",
        },
        "ar": {
            "title":       "ضغط البلوك شين الذكي بالتجميع — تقرير النتائج",
            "subtitle":    "تقليل حجم البلوك شين بالذكاء الاصطناعي — ضغط ذكي بالتجميع",
            "generated":   f"تاريخ الإنشاء: {ts}",
            "pipeline":    "خط الأنابيب: تجميع DBSCAN ← ضغط مرتّب ← بحث مفهرس",
            "s1":          "١. نظرة عامة على البيانات",
            "s2":          "٢. نتائج تجميع DBSCAN",
            "s3":          "٣. مقارنة استراتيجيات الضغط",
            "s4":          "٤. مقارنة DBSCAN مقابل K-Means",
            "s5":          "٥. النتائج الرئيسية",
            "total_txs":   "إجمالي المعاملات",
            "orig_size":   "الحجم الأصلي",
            "scam_rate":   "معدل الاحتيال",
            "clusters":    "التجمعات المكتشفة",
            "noise":       "نقاط الضوضاء",
            "sil":         "معامل Silhouette",
            "dbscan_time": "وقت DBSCAN",
            "strategy":    "الاستراتيجية",
            "comp_size":   "الحجم المضغوط",
            "ratio":       "نسبة الضغط",
            "saved":       "المساحة المُوفَّرة",
            "searchable":  "بحث مفهرس",
            "baseline":    "الخط الأساسي (عشوائي)",
            "sorted":      "مرتّب بالتجمع",
            "percluster":  "كتل لكل تجمع",
            "yes":         "✅ نعم",
            "no":          "❌ لا (مسح كامل)",
            "algo":        "الخوارزمية",
            "km_clusters": "التجمعات",
            "km_noise":    "معالجة الضوضاء",
            "km_time":     "وقت التجميع",
            "km_ratio":    "نسبة الضغط",
            "km_sil":      "معامل Silhouette",
            "km_k":        "يحتاج K؟",
            "dbscan_n":    "DBSCAN",
            "kmeans_n":    "K-Means",
            "km_noise_y":  "✅ تلقائي",
            "km_noise_n":  "❌ لا يوجد",
            "km_k_y":      "✅ لا",
            "km_k_n":      "❌ نعم (يجب تحديد K)",
            "finding1":    f"الضغط المرتّب بالتجمع حسّن النسبة بمقدار {(sorted_res['ratio']/baseline['ratio']-1)*100:.1f}% مقارنةً بالخط الأساسي العشوائي.",
            "finding2":    f"اكتشف DBSCAN {n_clusters} تجمعاً سلوكياً في {etime:.1f} ثانية فقط باستخدام تسريع KDTree.",
            "finding3":    f"نسبة ضغط DBSCAN ({sorted_res['ratio']:.2f}×) {'أفضل من' if sorted_res['ratio']>km_ratio else 'مماثلة لـ'} K-Means ({km_ratio:.2f}×) مع معالجة تلقائية للضوضاء.",
            "finding4":    f"التخزين المفهرس يتيح البحث في كتلة واحدة فقط من أصل {per_res['n_blocks']} — تقليل جذري لعمليات الإدخال/الإخراج.",
            "finding5":    f"إجمالي تقليل التخزين: {human_size(baseline['raw_size'])} ← {human_size(sorted_res['comp_size'])} (توفير {sorted_res['pct_saved']:.1f}%) باستخدام {method.upper()}.",
        },
        "tr": {
            "title":       "Blockchain Küme Tabanlı Sıkıştırma — Sonuç Raporu",
            "subtitle":    "Mezuniyet Projesi: Yapay Zeka ile Blockchain Boyutu Küçültme",
            "generated":   f"Oluşturulma: {ts}",
            "pipeline":    "Hat: DBSCAN Kümeleme → Kümeye Göre Sıkıştırma → İndeksli Arama",
            "s1":          "1. Veri Kümesine Genel Bakış",
            "s2":          "2. DBSCAN Kümeleme Sonuçları",
            "s3":          "3. Sıkıştırma Stratejisi Karşılaştırması",
            "s4":          "4. DBSCAN ve K-Means Karşılaştırması",
            "s5":          "5. Temel Bulgular",
            "total_txs":   "Toplam İşlem",
            "orig_size":   "Orijinal Boyut",
            "scam_rate":   "Dolandırıcılık Oranı",
            "clusters":    "Bulunan Küme",
            "noise":       "Gürültü Noktaları",
            "sil":         "Silhouette Skoru",
            "dbscan_time": "DBSCAN Süresi",
            "strategy":    "Strateji",
            "comp_size":   "Sıkıştırılmış Boyut",
            "ratio":       "Sıkıştırma Oranı",
            "saved":       "Kazanılan Alan",
            "searchable":  "İndeksli Arama",
            "baseline":    "Temel (Karıştırılmış)",
            "sorted":      "Kümeye Göre Sıralı",
            "percluster":  "Küme Başına Bloklar",
            "yes":         "✅ Evet",
            "no":          "❌ Hayır (tam tarama)",
            "algo":        "Algoritma",
            "km_clusters": "Kümeler",
            "km_noise":    "Gürültü İşleme",
            "km_time":     "Kümeleme Süresi",
            "km_ratio":    "Sıkıştırma Oranı",
            "km_sil":      "Silhouette Skoru",
            "km_k":        "K gerekli mi?",
            "dbscan_n":    "DBSCAN",
            "kmeans_n":    "K-Means",
            "km_noise_y":  "✅ Otomatik",
            "km_noise_n":  "❌ Yok",
            "km_k_y":      "✅ Hayır",
            "km_k_n":      "❌ Evet (K belirlenmeli)",
            "finding1":    f"Kümeye göre sıralı sıkıştırma, rastgele temel çizgiye göre oranı {(sorted_res['ratio']/baseline['ratio']-1)*100:.1f}% artırdı.",
            "finding2":    f"DBSCAN, KDTree hızlandırması ile {etime:.1f} saniyede {n_clusters} davranışsal küme buldu.",
            "finding3":    f"DBSCAN sıkıştırma oranı ({sorted_res['ratio']:.2f}×), K-Means'ten ({km_ratio:.2f}×) {'daha iyi' if sorted_res['ratio']>km_ratio else 'benzer'}, otomatik gürültü işleme ile.",
            "finding4":    f"İndekslenmiş depolama, {per_res['n_blocks']} bloktan yalnızca 1'ini arayarak G/Ç işlemlerini büyük ölçüde azaltır.",
            "finding5":    f"Toplam depolama küçültme: {human_size(baseline['raw_size'])} → {human_size(sorted_res['comp_size'])} ({sorted_res['pct_saved']:.1f}% kazanıldı) — {method.upper()} ile.",
        },
    }
    T = L.get(lang, L["en"])

    dir_attr = 'dir="rtl"' if lang == "ar" else ""
    font_family = "'Segoe UI', Tahoma, sans-serif"

    rows_comp = [
        (T["baseline"],   human_size(baseline["comp_size"]),   f"{baseline['ratio']:.2f}×",   f"{baseline['pct_saved']:.1f}%",  T["no"]),
        (T["sorted"],     human_size(sorted_res["comp_size"]), f"{sorted_res['ratio']:.2f}×", f"{sorted_res['pct_saved']:.1f}%",T["yes"]),
        (T["percluster"], human_size(per_res["comp_size"]),    f"{per_res['ratio']:.2f}×",    f"{per_res['pct_saved']:.1f}%",   T["yes"]),
    ]

    comp_rows_html = "".join(
        f"<tr><td><b>{r[0]}</b></td><td>{r[1]}</td><td style='color:{GREEN};font-weight:700'>{r[2]}</td>"
        f"<td style='color:{GREEN}'>{r[3]}</td><td>{r[4]}</td></tr>"
        for r in rows_comp
    )

    findings_html = "".join(
        f'<li style="margin:.6rem 0;color:#d1d5db;">{T[f"finding{i}"]}</li>'
        for i in range(1, 6)
    )

    html = f"""<!DOCTYPE html>
<html lang="{lang}" {dir_attr}>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{T['title']}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:{DARK};color:{TEXT};font-family:{font_family};padding:2rem;line-height:1.6;}}
  h1{{font-size:1.7rem;background:linear-gradient(90deg,{VIOLET},{CYAN});
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.4rem;}}
  h2{{font-size:1.1rem;color:{CYAN};border-bottom:1px solid {BORDER};
      padding-bottom:.4rem;margin:1.8rem 0 .9rem;}}
  .sub{{color:{MUTED};font-size:.88rem;margin-bottom:.3rem;}}
  .badge{{display:inline-block;background:rgba(124,58,237,.22);border:1px solid rgba(124,58,237,.45);
          color:#c4b5fd;border-radius:20px;padding:.12rem .65rem;font-size:.72rem;font-weight:600;margin-right:.3rem;}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:.9rem;margin:.9rem 0;}}
  .card{{background:{CARD};border:1px solid {BORDER};border-radius:10px;padding:1rem;text-align:center;}}
  .card-v{{font-size:1.6rem;font-weight:800;color:{CYAN};font-family:monospace;}}
  .card-l{{font-size:.68rem;color:{MUTED};font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-top:.2rem;}}
  table{{width:100%;border-collapse:collapse;margin:.6rem 0;font-size:.88rem;}}
  th{{background:{CARD};color:{CYAN};padding:.6rem .9rem;text-align:left;font-weight:700;font-size:.78rem;text-transform:uppercase;}}
  td{{padding:.55rem .9rem;border-bottom:1px solid {BORDER};color:{TEXT};}}
  tr:hover td{{background:rgba(124,58,237,.07);}}
  .winner{{background:rgba(34,197,94,.08)!important;}}
  .winner td{{color:{GREEN};}}
  ul{{padding-left:1.4rem;}}
  .footer{{margin-top:2.5rem;padding-top:1rem;border-top:1px solid {BORDER};
           color:{MUTED};font-size:.75rem;text-align:center;}}
  @media print{{body{{background:white;color:#111;}}
    h1{{-webkit-text-fill-color:{VIOLET};}}
    .card{{border:1px solid #ccc;}}}}
</style>
</head>
<body>
<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;margin-bottom:1.4rem;">
  <div>
    <div><span class="badge">DBSCAN</span><span class="badge">{method.upper()}</span></div>
    <h1>{T['title']}</h1>
    <p class="sub">{T['subtitle']}</p>
    <p class="sub">{T['pipeline']}</p>
  </div>
  <div style="color:{MUTED};font-size:.8rem;text-align:right;">{T['generated']}</div>
</div>

<h2>{T['s1']}</h2>
<div class="grid">
  <div class="card"><div class="card-v">{stats['total_txs']:,}</div><div class="card-l">{T['total_txs']}</div></div>
  <div class="card"><div class="card-v">{human_size(stats['total_size_mb']*1_048_576)}</div><div class="card-l">{T['orig_size']}</div></div>
  <div class="card"><div class="card-v">{stats['scam_rate']:.1f}%</div><div class="card-l">{T['scam_rate']}</div></div>
  <div class="card"><div class="card-v">{stats['total_blocks']:,}</div><div class="card-l">Blocks</div></div>
</div>

<h2>{T['s2']}</h2>
<div class="grid">
  <div class="card"><div class="card-v">{n_clusters}</div><div class="card-l">{T['clusters']}</div></div>
  <div class="card"><div class="card-v">{n_noise:,}</div><div class="card-l">{T['noise']}</div></div>
  <div class="card"><div class="card-v">{dbscan_sil:.3f}</div><div class="card-l">{T['sil']}</div></div>
  <div class="card"><div class="card-v">{etime:.2f}s</div><div class="card-l">{T['dbscan_time']}</div></div>
</div>

<h2>{T['s3']}</h2>
<table>
  <thead><tr>
    <th>{T['strategy']}</th><th>{T['comp_size']}</th>
    <th>{T['ratio']}</th><th>{T['saved']}</th><th>{T['searchable']}</th>
  </tr></thead>
  <tbody>{comp_rows_html}</tbody>
</table>

<h2>{T['s4']}</h2>
<table>
  <thead><tr>
    <th>{T['algo']}</th><th>{T['km_clusters']}</th><th>{T['km_noise']}</th>
    <th>{T['km_time']}</th><th>{T['km_ratio']}</th><th>{T['km_sil']}</th><th>{T['km_k']}</th>
  </tr></thead>
  <tbody>
    <tr class="winner">
      <td><b>{T['dbscan_n']}</b></td>
      <td>{n_clusters}</td>
      <td>{T['km_noise_y']}</td>
      <td>{etime:.2f}s</td>
      <td style="color:{GREEN};font-weight:700">{sorted_res['ratio']:.3f}×</td>
      <td>{dbscan_sil:.3f}</td>
      <td>{T['km_k_y']}</td>
    </tr>
    <tr>
      <td><b>{T['kmeans_n']}</b></td>
      <td>{n_clusters}</td>
      <td>{T['km_noise_n']}</td>
      <td>{km_time:.2f}s</td>
      <td>{km_ratio:.3f}×</td>
      <td>{km_sil:.3f}</td>
      <td>{T['km_k_n']}</td>
    </tr>
  </tbody>
</table>

<h2>{T['s5']}</h2>
<ul>{findings_html}</ul>

<div class="footer">
  ⛓️ Blockchain Cluster-Aware Compression · DBSCAN + {method.upper()} · {ts}
</div>
</body></html>"""
    return html
