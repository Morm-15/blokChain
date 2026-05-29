"""
BlockchAIn Cluster-Aware Compression — Streamlit App  v2.0
8 Pages · EN/AR/TR · DBSCAN vs K-Means · Download · Report
"""
import io, time, warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Blockchain Cluster Compression",
    page_icon="⛓️", layout="wide",
    initial_sidebar_state="expanded",
)

from modules.translations        import t, TRANSLATIONS
from modules.data_loader         import load_data, get_summary_stats, get_block_stats
from modules.feature_engineering import build_features, get_feature_descriptions, FEATURE_COLS
from modules.dbscan_model        import (run_dbscan, get_cluster_stats,
                                         compute_kdistance, compute_silhouette, eps_sensitivity)
from modules.kmeans_model        import (run_kmeans, kmeans_silhouette,
                                         get_kmeans_cluster_stats, sweep_k)
from modules.compressor          import (compress_baseline, compress_cluster_sorted,
                                         compress_per_cluster, simulate_search_random,
                                         simulate_search_cluster_index,
                                         human_size, build_comparison_table, _df_to_bytes,
                                         compress_zstd, compress_gzip,
                                         compare_compression_levels,
                                         export_compressed_file, export_cluster_index_json)
from modules.report_generator    import generate_html_report

# ── Palette ───────────────────────────────────────────────────────────
BG=    "#0d1117"; CARD=  "#161b22"; CARD2= "#1c2128"
VIOLET="#7c3aed"; CYAN=  "#06b6d4"; AMBER= "#f59e0b"
GREEN= "#22c55e"; RED=   "#ef4444"; PINK=  "#ec4899"
TEXT=  "#e6edf3"; MUTED= "#8b949e"; BORDER="#30363d"
PAL=[VIOLET,CYAN,AMBER,GREEN,RED,PINK,"#14b8a6","#f97316","#8b5cf6","#3b82f6","#84cc16","#a78bfa"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
html,body,[data-testid="stAppViewContainer"]{{background:{BG};color:{TEXT};font-family:'Inter',sans-serif;}}
[data-testid="stSidebar"]{{background:{CARD};border-right:1px solid {BORDER};}}
[data-testid="stSidebar"] *{{color:{TEXT}!important;}}
[data-testid="stHeader"]{{background:transparent;}}
#MainMenu,footer,header{{visibility:hidden;}}
.hero{{background:linear-gradient(135deg,#1a0535 0%,#0c2341 55%,#001a1a 100%);
  border:1px solid {BORDER};border-radius:16px;padding:2.2rem 2.8rem;margin-bottom:1.8rem;
  position:relative;overflow:hidden;}}
.hero::before{{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 15% 50%,rgba(124,58,237,.18) 0%,transparent 60%),
             radial-gradient(ellipse at 85% 50%,rgba(6,182,212,.12) 0%,transparent 60%);}}
.hero-title{{font-size:2rem;font-weight:800;
  background:linear-gradient(90deg,{VIOLET},{CYAN},{AMBER});
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0 0 .35rem;position:relative;}}
.hero-sub{{color:{MUTED};font-size:.95rem;position:relative;}}
.badge{{display:inline-block;background:rgba(124,58,237,.22);border:1px solid rgba(124,58,237,.45);
  color:#c4b5fd;border-radius:20px;padding:.18rem .75rem;font-size:.73rem;font-weight:600;margin-right:.4rem;position:relative;}}
.badge-c{{background:rgba(6,182,212,.18);border-color:rgba(6,182,212,.4);color:#a5f3fc;}}
.badge-a{{background:rgba(245,158,11,.18);border-color:rgba(245,158,11,.4);color:#fde68a;}}
.mc{{background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:1.3rem 1.1rem;
  text-align:center;position:relative;overflow:hidden;transition:border-color .2s,transform .2s;}}
.mc:hover{{border-color:{VIOLET};transform:translateY(-2px);}}
.mc::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,{VIOLET},{CYAN});border-radius:12px 12px 0 0;}}
.mv{{font-size:1.9rem;font-weight:800;color:{TEXT};line-height:1;
  margin-bottom:.25rem;font-family:'JetBrains Mono',monospace;}}
.ml{{font-size:.73rem;color:{MUTED};font-weight:600;text-transform:uppercase;letter-spacing:.05em;}}
.sh{{display:flex;align-items:center;gap:.6rem;margin:1.8rem 0 .9rem;
  padding-bottom:.65rem;border-bottom:1px solid {BORDER};}}
.sh h2{{font-size:1.2rem;font-weight:700;color:{TEXT};margin:0;}}
.sh-b{{background:rgba(124,58,237,.18);border:1px solid rgba(124,58,237,.38);
  color:#c4b5fd;border-radius:6px;padding:.12rem .45rem;font-size:.7rem;font-weight:700;}}
.ib{{background:rgba(6,182,212,.08);border:1px solid rgba(6,182,212,.25);
  border-left:4px solid {CYAN};border-radius:8px;padding:.9rem 1.1rem;
  margin-bottom:1.1rem;color:#cffafe;font-size:.88rem;line-height:1.65;}}
.wb{{background:rgba(245,158,11,.08);border:1px solid rgba(245,158,11,.25);
  border-left:4px solid {AMBER};border-radius:8px;padding:.9rem 1.1rem;
  margin-bottom:1.1rem;color:#fef3c7;font-size:.88rem;line-height:1.65;}}
.sb{{background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.25);
  border-left:4px solid {GREEN};border-radius:8px;padding:.9rem 1.1rem;
  margin-bottom:1.1rem;color:#dcfce7;font-size:.88rem;line-height:1.65;}}
.cs{{background:{CARD2};border:1px solid {BORDER};border-radius:10px;
  padding:.9rem 1.1rem;margin-bottom:.6rem;display:flex;align-items:flex-start;gap:.9rem;}}
.cn{{background:linear-gradient(135deg,{VIOLET},{CYAN});color:white;font-weight:800;
  font-size:.82rem;width:26px;height:26px;border-radius:50%;display:flex;
  align-items:center;justify-content:center;flex-shrink:0;font-family:'JetBrains Mono',monospace;}}
.ct{{color:{TEXT};font-size:.88rem;line-height:1.6;margin:0;}}
.cr{{display:flex;align-items:center;justify-content:space-between;
  background:{CARD2};border:1px solid {BORDER};border-radius:8px;
  padding:.65rem 1rem;margin-bottom:.4rem;transition:border-color .2s;}}
.cr:hover{{border-color:{VIOLET};}}
.cr-l{{font-size:.83rem;color:{MUTED};min-width:180px;}}
.cr-v{{font-family:'JetBrains Mono',monospace;font-size:.88rem;color:{TEXT};font-weight:600;}}
.dl-card{{background:{CARD};border:1px solid {BORDER};border-radius:14px;padding:1.4rem 1.6rem;margin-bottom:1.2rem;}}
.dl-card-title{{font-size:1rem;font-weight:700;color:{TEXT};margin-bottom:.4rem;}}
.dl-card-desc{{font-size:.84rem;color:{MUTED};margin-bottom:.9rem;line-height:1.6;}}
.stButton>button{{background:linear-gradient(135deg,{VIOLET},#5b21b6);color:white;
  border:none;border-radius:8px;font-weight:600;padding:.55rem 1.4rem;
  transition:opacity .2s,transform .2s;width:100%;}}
.stButton>button:hover{{opacity:.9;transform:translateY(-1px);}}
div[data-baseweb="select"]>div{{background:{CARD2};border:1px solid {BORDER};color:{TEXT};border-radius:8px;}}
::-webkit-scrollbar{{width:6px;height:6px;}}
::-webkit-scrollbar-track{{background:{BG};}}
::-webkit-scrollbar-thumb{{background:{BORDER};border-radius:3px;}}
::-webkit-scrollbar-thumb:hover{{background:{VIOLET};}}

/* ── Force sidebar always expanded ── */
[data-testid="stSidebar"] {{
    display: block !important;
    visibility: visible !important;
    min-width: 244px !important;
    max-width: 320px !important;
    transform: none !important;
    opacity: 1 !important;
}}
[data-testid="stSidebar"][aria-expanded="false"] {{
    display: block !important;
    transform: none !important;
    min-width: 244px !important;
}}
/* Hide the collapse arrow on desktop */
@media (min-width: 768px) {{
    [data-testid="collapsedControl"] {{ display: none !important; }}
    button[kind="header"] {{ display: none !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ── State ─────────────────────────────────────────────────────────────
def _init():
    for k,v in dict(lang="en", eps=0.5, min_samples=5, comp_method="zstd",
                    labels=None, exec_time=None, baseline=None,
                    sorted_res=None, per_cluster_res=None,
                    search_done=False, search_random=None,
                    search_idx=None, search_addr=None, page=None,
                    km_labels=None, km_time=None, km_sil=None,
                    km_ratio=None, km_k=15).items():
        if k not in st.session_state: st.session_state[k] = v
_init()

def tx(k): return t(k, st.session_state.lang)

# ── RTL Support — يُطبَّق تلقائياً عند اختيار العربية ────────────────
def _apply_rtl(lang: str):
    if lang == "ar":
        st.markdown("""
<style>
/* ── RTL: قلب اتجاه النص بالكامل ── */
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="block-container"],
section.main > div,
.main .block-container {
    direction: rtl !important;
    text-align: right !important;
}

/* Sidebar RTL */
[data-testid="stSidebar"] > div {
    direction: rtl !important;
    text-align: right !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] p {
    direction: rtl !important;
    text-align: right !important;
}

/* Streamlit widgets labels */
label, .stMarkdown, .stText, p, h1, h2, h3, h4, li {
    direction: rtl !important;
    text-align: right !important;
    font-family: 'Segoe UI', 'Tahoma', 'Arial', sans-serif !important;
}

/* عناصر الـ info boxes  */
.ib, .wb, .sb {
    direction: rtl !important;
    text-align: right !important;
    border-left: none !important;
    border-right: 4px solid;
    padding-right: 1.1rem !important;
    padding-left: .9rem !important;
}
.ib { border-right-color: #06b6d4 !important; }
.wb { border-right-color: #f59e0b !important; }
.sb { border-right-color: #22c55e !important; }

/* Step cards */
.cs {
    direction: rtl !important;
    flex-direction: row-reverse !important;
}

/* Metric cards */
.mc, .mv, .ml {
    direction: rtl !important;
    text-align: center !important;
}

/* cr rows */
.cr {
    direction: rtl !important;
    flex-direction: row-reverse !important;
}
.cr-l { text-align: right !important; }
.cr-v { text-align: left !important; font-family: 'JetBrains Mono', monospace !important; }

/* Selectbox / radio labels */
[data-baseweb="select"] * ,
[data-baseweb="radio"] * {
    direction: rtl !important;
    text-align: right !important;
}

/* Buttons */
.stButton > button {
    direction: rtl !important;
}

/* Hero */
.hero-title, .hero-sub {
    direction: rtl !important;
    text-align: right !important;
}

/* Horizontal radio nav: keep centered */
[data-testid="stHorizontalBlock"] label {
    text-align: center !important;
}

/* Dataframe headers */
.stDataFrame { direction: rtl !important; }

/* Expander */
[data-testid="stExpander"] summary,
[data-testid="stExpander"] div {
    direction: rtl !important;
    text-align: right !important;
}
</style>
""", unsafe_allow_html=True)
    else:
        # Reset to LTR for EN and TR
        st.markdown("""
<style>
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="block-container"],
section.main > div,
.main .block-container,
[data-testid="stSidebar"] > div,
label, .stMarkdown, p, h1, h2, h3 {
    direction: ltr !important;
    text-align: left !important;
}
.ib, .wb, .sb {
    border-left: 4px solid;
    border-right: none !important;
    padding-left: 1.1rem !important;
    padding-right: .9rem !important;
}
.ib { border-left-color: #06b6d4 !important; }
.wb { border-left-color: #f59e0b !important; }
.sb { border-left-color: #22c55e !important; }
.cs { flex-direction: row !important; }
.cr { flex-direction: row !important; }
</style>
""", unsafe_allow_html=True)


def plo(h=400):
    return dict(height=h,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=TEXT,family="Inter"),
                xaxis=dict(gridcolor=BORDER,zerolinecolor=BORDER),
                yaxis=dict(gridcolor=BORDER,zerolinecolor=BORDER),
                legend=dict(bgcolor="rgba(0,0,0,0)",bordercolor=BORDER),
                margin=dict(l=50,r=20,t=45,b=45))

def mc(label, val, delta="", dc=""):
    dh = f'<div style="font-size:.78rem;font-weight:600;margin-top:.35rem;color:{dc};">{delta}</div>' if delta else ""
    return f'<div class="mc"><div class="mv">{val}</div><div class="ml">{label}</div>{dh}</div>'

def sh(title, badge=""):
    bh = f'<span class="sh-b">{badge}</span>' if badge else ""
    st.markdown(f'<div class="sh"><h2>{title}</h2>{bh}</div>', unsafe_allow_html=True)

def ib(text, kind="i"):
    cls={"i":"ib","w":"wb","s":"sb"}.get(kind,"ib")
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)

def cs(num, text):
    st.markdown(f'<div class="cs"><div class="cn">{num}</div><div class="ct">{text}</div></div>',
                unsafe_allow_html=True)

def cr(label, val, color=TEXT):
    st.markdown(f'<div class="cr"><span class="cr-l">{label}</span>'
                f'<span class="cr-v" style="color:{color};">{val}</span></div>',
                unsafe_allow_html=True)

def dl_card(title, desc, download_widget_fn):
    st.markdown(f'<div class="dl-card"><div class="dl-card-title">{title}</div>'
                f'<div class="dl-card-desc">{desc}</div></div>', unsafe_allow_html=True)
    download_widget_fn()

# ── Load data ─────────────────────────────────────────────────────────
with st.spinner(tx("loading")):
    df        = load_data()
    stats     = get_summary_stats(df)
    blk_stats = get_block_stats(df)
    X_scaled, coords_2d, _ = build_features(df)

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    lang_map = {"🇬🇧 English":"en","🇸🇦 العربية":"ar","🇹🇷 Türkçe":"tr"}
    chosen = st.selectbox(tx("language_label"), list(lang_map.keys()),
                          index=["en","ar","tr"].index(st.session_state.lang))
    if lang_map[chosen] != st.session_state.lang:
        st.session_state.lang = lang_map[chosen]
        # No st.rerun() — avoids sidebar collapse on Streamlit Cloud


    st.markdown("---")
    st.markdown(f'<div style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:{MUTED}">⚙️ {tx("sidebar_params")}</div>', unsafe_allow_html=True)
    eps      = st.slider(tx("eps_label"), 0.1, 2.0, st.session_state.eps, 0.05, help=tx("eps_help"))
    min_samp = st.slider(tx("min_samples_label"), 2, 30, st.session_state.min_samples, 1, help=tx("min_samples_help"))

    st.markdown(f'<div style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:{MUTED};margin-top:.8rem">🗜️ {tx("comp_method_label")}</div>', unsafe_allow_html=True)
    comp_method = st.radio("_cm", ["zstd","gzip"],
        format_func=lambda x: ("⚡ Zstandard (zstd)" if x=="zstd" else "🏛️ Gzip"),
        index=0, label_visibility="collapsed")

    st.markdown("---")
    if st.button(f"▶ {tx('run_btn')}", use_container_width=True):
        for k in ["labels","baseline","sorted_res","per_cluster_res","search_done",
                  "search_random","search_idx","km_labels","km_time","km_sil","km_ratio"]:
            st.session_state[k] = None
        st.session_state.search_done = False
        st.session_state.eps         = eps
        st.session_state.min_samples = min_samp
        st.session_state.comp_method = comp_method

    st.markdown(f'<div style="text-align:center;margin-top:1.5rem;color:{MUTED};font-size:.7rem;">'
                f'⛓️ Blockchain Cluster Compression<br>'
                f'<span style="color:{VIOLET}">DBSCAN + {comp_method}</span></div>',
                unsafe_allow_html=True)

# ── Run DBSCAN ────────────────────────────────────────────────────────
if st.session_state.labels is None:
    with st.spinner(tx("processing")):
        labels, etime = run_dbscan(X_scaled, st.session_state.eps, st.session_state.min_samples)
        st.session_state.labels    = labels
        st.session_state.exec_time = etime
else:
    labels = st.session_state.labels
    etime  = st.session_state.exec_time

n_clusters = len(set(labels) - {-1})
n_noise    = int((labels == -1).sum())
method     = st.session_state.comp_method

# ── Run Compression ───────────────────────────────────────────────────
if st.session_state.baseline is None:
    with st.spinner(tx("processing")):
        st.session_state.baseline        = compress_baseline(df, method)
        st.session_state.sorted_res      = compress_cluster_sorted(df, labels, method)
        st.session_state.per_cluster_res = compress_per_cluster(df, labels, method)

baseline   = st.session_state.baseline
sorted_res = st.session_state.sorted_res
per_res    = st.session_state.per_cluster_res

# ── Hero ──────────────────────────────────────────────────────────────
lang = st.session_state.lang
_apply_rtl(lang)   # ← RTL/LTR تبديل تلقائي حسب اللغة

st.markdown(f"""
<div class="hero">
  <div><span class="badge">DBSCAN</span>
       <span class="badge badge-c">{method.upper()}</span>
       <span class="badge badge-a">{"Cluster-Aware Compression" if lang=="en" else ("ضغط ذكي بالتجميع" if lang=="ar" else "Küme Tabanlı Sıkıştırma")}</span></div>
  <h1 class="hero-title">{tx('app_title')}</h1>
  <p class="hero-sub">{tx('app_subtitle')}</p>
  <div style="margin-top:.9rem;display:flex;gap:2.2rem;flex-wrap:wrap;">
    <div style="font-size:.83rem;color:{MUTED}">🔬 {"Clusters" if lang=="en" else ("تجمعات" if lang=="ar" else "Kümeler")}: <b style="color:#c4b5fd">{n_clusters}</b></div>
    <div style="font-size:.83rem;color:{MUTED}">📦 Baseline: <b style="color:#fca5a5">{baseline['ratio']:.2f}×</b></div>
    <div style="font-size:.83rem;color:{MUTED}">🚀 {"Cluster-Sorted" if lang=="en" else ("مرتّب" if lang=="ar" else "Küme")}: <b style="color:#6ee7b7">{sorted_res['ratio']:.2f}×</b></div>
    <div style="font-size:.83rem;color:{MUTED}">⏱ DBSCAN: <b style="color:#a5f3fc">{etime:.2f}s</b></div>
    <div style="font-size:.83rem;color:{MUTED}">💾 {"Saved" if lang=="en" else ("موفَّر" if lang=="ar" else "Kazanılan")}: <b style="color:#fcd34d">{sorted_res['pct_saved']:.1f}%</b></div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Page Nav ──────────────────────────────────────────────────────────
pages = [tx("page_overview"), tx("page_dbscan"), tx("page_compression"),
         tx("page_search"),   tx("page_blocks"),  tx("page_metrics"),
         tx("page_algo_cmp"), tx("page_export")]

if st.session_state.page not in pages:
    st.session_state.page = pages[0]

page = st.radio("_nav", pages, index=pages.index(st.session_state.page),
                horizontal=True, label_visibility="collapsed")
st.session_state.page = page
st.markdown(f"<hr style='border-color:{BORDER};margin:.4rem 0 1.8rem'>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════
if page == tx("page_overview"):
    sh(tx("overview_title"), "Dataset")
    ib(tx("overview_desc"))

    c1,c2,c3,c4 = st.columns(4)
    for col,(l,v) in zip([c1,c2,c3,c4],[
        (tx("total_txs"),    f"{stats['total_txs']:,}"),
        (tx("total_blocks"), f"{stats['total_blocks']:,}"),
        (tx("total_size"),   human_size(stats['total_size_mb']*1_048_576)),
        (tx("scam_rate"),    f"{stats['scam_rate']:.1f}%"),
    ]):
        with col: st.markdown(mc(l,v), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c5,c6,c7,c8 = st.columns(4)
    for col,(l,v) in zip([c5,c6,c7,c8],[
        (tx("scam_txs"),       f"{stats['scam_count']:,}"),
        (tx("normal_txs"),     f"{stats['normal_count']:,}"),
        (tx("unique_senders"), f"{stats['unique_senders']:,}"),
        (tx("avg_gas"),        f"{stats['avg_gas']:,.0f}"),
    ]):
        with col: st.markdown(mc(l,v), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    sh(tx("section_timeline"))
    daily = df.groupby("date").agg(tx_count=("hash","count"),scam_count=("is_scam","sum")).reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["date"],y=daily["tx_count"],
        name=tx("total_txs"),fill="tozeroy",line=dict(color=CYAN,width=2),fillcolor="rgba(6,182,212,.12)"))
    fig.add_trace(go.Scatter(x=daily["date"],y=daily["scam_count"],
        name=tx("scam_txs"),fill="tozeroy",line=dict(color=RED,width=2),fillcolor="rgba(239,68,68,.12)"))
    fig.update_layout(**plo(330))
    st.plotly_chart(fig, use_container_width=True)

    l2,r2 = st.columns(2)
    with l2:
        sh(tx("section_scam_dist"))
        fig_p = go.Figure(go.Pie(
            labels=[tx("scam_txs"),tx("normal_txs")],
            values=[stats["scam_count"],stats["normal_count"]],
            marker_colors=[RED,GREEN],hole=.55,textinfo="label+percent",textfont_size=13))
        fig_p.update_layout(**plo(300))
        st.plotly_chart(fig_p, use_container_width=True)
    with r2:
        sh(tx("section_gas_dist"))
        fig_g = go.Figure(go.Histogram(x=df["receipt_gas_used"].clip(0,300_000),
            nbinsx=60,marker_color=VIOLET,opacity=.85))
        fig_g.update_layout(**plo(300))
        st.plotly_chart(fig_g, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE 2 — DBSCAN ANALYSIS
# ═══════════════════════════════════════════════════════════════════
elif page == tx("page_dbscan"):
    sh(tx("dbscan_title"), "DBSCAN")
    ib(tx("dbscan_desc"))

    with st.expander(f"📖 {tx('dbscan_how_title')}", expanded=False):
        st.markdown(tx("dbscan_how_desc"))

    sh(tx("features_used"))
    feat_desc = get_feature_descriptions(st.session_state.lang)
    for col_name in FEATURE_COLS:
        label, desc = feat_desc[col_name]
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:1rem;padding:.65rem 1rem;'
            f'background:{CARD2};border:1px solid {BORDER};border-radius:8px;margin-bottom:.35rem;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:.8rem;color:{CYAN};min-width:170px;">{label}</span>'
            f'<span style="color:{MUTED};font-size:.84rem;">{desc}</span></div>',
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    sil = compute_silhouette(X_scaled, labels)
    sil_str = f"{sil:.3f}" if sil else "N/A"
    for col,(l,v) in zip(st.columns(4),[
        (tx("total_clusters"),str(n_clusters)),
        (tx("noise_count"),   f"{n_noise:,}"),
        (tx("silhouette"),    sil_str),
        ("ε / min_samples",   f"{st.session_state.eps} / {st.session_state.min_samples}"),
    ]):
        with col: st.markdown(mc(l,v), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    sh(tx("cluster_scatter"))
    unique_c = sorted(set(labels))
    color_map={str(c):RED if c==-1 else PAL[i%len(PAL)] for i,c in enumerate(unique_c)}
    idx_s = np.random.choice(len(coords_2d), min(8000,len(coords_2d)), replace=False)
    ps_c  = labels[idx_s].astype(str)
    ps_x  = coords_2d[idx_s,0]; ps_y = coords_2d[idx_s,1]
    fig_sc = go.Figure()
    for cv in sorted(set(ps_c)):
        m  = ps_c==cv
        nm = tx("noise_label") if cv=="-1" else f"Cluster {cv}"
        fig_sc.add_trace(go.Scatter(x=ps_x[m],y=ps_y[m],mode="markers",name=nm,
            marker=dict(size=4 if cv!="-1" else 3,color=color_map.get(cv,"#888"),
                        opacity=.75 if cv!="-1" else .4,line=dict(width=0))))
    fig_sc.update_layout(**plo(460))
    st.plotly_chart(fig_sc, use_container_width=True)

    sh(tx("cluster_table"))
    cst = get_cluster_stats(df, labels)
    cst["cluster_id"] = cst["cluster_id"].apply(lambda x: tx("noise_label") if x==-1 else f"#{x}")
    cst.columns = [tx("cluster_id"),tx("cluster_count"),tx("cluster_avg_gas"),
                   tx("cluster_avg_value"),tx("cluster_scam_pct"),"Bytes"]
    cst[tx("cluster_avg_gas")]   = cst[tx("cluster_avg_gas")].apply(lambda x: f"{x:,.0f}")
    cst[tx("cluster_avg_value")] = cst[tx("cluster_avg_value")].apply(lambda x: f"{x:.4f}")
    cst[tx("cluster_scam_pct")] = cst[tx("cluster_scam_pct")].apply(lambda x: f"{x:.1f}%")
    cst["Bytes"] = cst["Bytes"].apply(human_size)
    st.dataframe(cst, use_container_width=True, height=290)

    sh(tx("kdist_title"))
    ib(tx("kdist_desc"))
    kd = compute_kdistance(X_scaled, k=st.session_state.min_samples)
    fig_kd = go.Figure()
    fig_kd.add_trace(go.Scatter(y=kd,mode="lines",line=dict(color=CYAN,width=2),
        fill="tozeroy",fillcolor="rgba(6,182,212,.1)"))
    fig_kd.add_hline(y=st.session_state.eps,line=dict(color=AMBER,dash="dash",width=2),
        annotation_text=f"ε={st.session_state.eps}",annotation_font_color=AMBER)
    fig_kd.update_layout(**plo(330))
    st.plotly_chart(fig_kd, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE 3 — COMPRESSION ENGINE
# ═══════════════════════════════════════════════════════════════════
elif page == tx("page_compression"):
    sh(tx("comp_title"), method.upper())
    ib(tx("comp_concept"))

    if baseline is None or sorted_res is None or per_res is None:
        ib("⚠️ " + (
            "Please press **▶ Run** in the sidebar to compute compression results."
            if lang=="en" else
            "اضغط على **▶ تشغيل** في الشريط الجانبي لحساب نتائج الضغط."
            if lang=="ar" else
            "Sıkıştırma sonuçlarını hesaplamak için kenar çubuğundaki **▶ Çalıştır** düğmesine basın."
        ), "w")
        st.stop()

    with st.expander(f"📖 {tx('comp_how_title')}", expanded=True):
        for i,k in enumerate(["comp_step1","comp_step2","comp_step3","comp_step4","comp_step5"],1):
            cs(i, tx(k))

    st.markdown("<br>", unsafe_allow_html=True)
    sh(tx("comp_strategy_cmp"))

    def strategy_card(label, sub, ratio, comp_size, pct_saved, search_txt, border_color, highlight=False):
        border = f"2px solid {border_color}" if highlight else f"1px solid {BORDER}"
        glow   = f"box-shadow:0 0 20px rgba(124,58,237,.25);" if highlight else ""
        return f"""
        <div style="background:{CARD};border:{border};border-radius:14px;
             padding:1.4rem;text-align:center;border-top:3px solid {border_color};{glow}">
          <div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.07em;
               color:{border_color};font-weight:700;margin-bottom:.4rem;">{label}</div>
          <div style="font-size:.72rem;color:{MUTED};margin-bottom:.8rem;">{sub}</div>
          <div style="font-size:2.4rem;font-weight:800;color:{border_color};
               font-family:'JetBrains Mono',monospace;">{ratio:.2f}×</div>
          <div style="font-size:.75rem;color:{MUTED};">{"Compression Ratio" if lang=="en" else ("نسبة الضغط" if lang=="ar" else "Sıkıştırma Oranı")}</div>
          <hr style="border-color:{BORDER};margin:.8rem 0;">
          <div style="font-size:1rem;font-weight:700;color:{TEXT};">{human_size(comp_size)}</div>
          <div style="margin-top:.5rem;font-size:.85rem;color:{GREEN};font-weight:600;">▼ {pct_saved:.1f}%</div>
          <div style="margin-top:.4rem;font-size:.75rem;color:{MUTED};">{tx("comp_search_cap")} {search_txt}</div>
        </div>"""

    c1,c2,c3 = st.columns(3)
    with c1:
        st.markdown(strategy_card(tx("comp_baseline_label"),tx("comp_baseline_sub"),
            baseline['ratio'],baseline['comp_size'],baseline['pct_saved'],tx("comp_search_full"),RED),unsafe_allow_html=True)
    with c2:
        st.markdown(strategy_card(tx("comp_sorted_label"),tx("comp_sorted_sub"),
            sorted_res['ratio'],sorted_res['comp_size'],sorted_res['pct_saved'],tx("comp_search_row"),CYAN,True),unsafe_allow_html=True)
    with c3:
        st.markdown(strategy_card(tx("comp_percluster_label"),tx("comp_percluster_sub"),
            per_res['ratio'],per_res['comp_size'],per_res['pct_saved'],tx("comp_search_idx"),VIOLET),unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    sh(tx("comp_ratio_chart"))
    strat_labels = [tx("comp_baseline"), tx("comp_sorted"), tx("comp_percluster")]
    ratios  = [baseline['ratio'], sorted_res['ratio'], per_res['ratio']]
    fig_bar = go.Figure(go.Bar(x=strat_labels, y=ratios, marker_color=[RED,CYAN,VIOLET],
        text=[f"{r:.2f}×" for r in ratios], textposition="outside",
        textfont=dict(size=15,color=TEXT,family="JetBrains Mono")))
    fig_bar.add_hline(y=baseline['ratio'],line=dict(color=RED,dash="dash",width=1.5),
        annotation_text=f"Baseline {baseline['ratio']:.2f}×",annotation_font_color=RED)
    fig_bar.update_layout(**plo(360)); fig_bar.update_yaxes(title_text=tx("comp_ratio_y"))
    st.plotly_chart(fig_bar, use_container_width=True)

    sh(tx("comp_size_chart"))
    size_labels=[tx("comp_original"),tx("comp_baseline"),tx("comp_sorted"),tx("comp_percluster")]
    raw_mb  = baseline["raw_size"]/1_048_576
    sizes_mb=[raw_mb,baseline["comp_size"]/1_048_576,sorted_res["comp_size"]/1_048_576,per_res["comp_size"]/1_048_576]
    fig_sz=go.Figure(go.Bar(x=size_labels,y=sizes_mb,marker_color=[MUTED,RED,CYAN,VIOLET],
        text=[f"{v:.2f} MB" for v in sizes_mb],textposition="outside",
        textfont=dict(size=13,color=TEXT,family="JetBrains Mono")))
    fig_sz.update_layout(**plo(340)); fig_sz.update_yaxes(title_text=tx("comp_size_y"))
    st.plotly_chart(fig_sz, use_container_width=True)

    sh(tx("comp_block_detail"), f"{per_res['n_blocks']} blocks")
    pc_df = per_res["per_cluster_stats"].copy()
    pc_df["cluster_id"]=pc_df["cluster_id"].apply(lambda x: tx("noise_label") if x==-1 else f"#{x}")
    pc_df["raw_kb"]=pc_df["raw_kb"].apply(lambda x:f"{x:.1f} KB")
    pc_df["comp_kb"]=pc_df["comp_kb"].apply(lambda x:f"{x:.1f} KB")
    pc_df.columns=[tx("comp_cluster_col"),tx("comp_txs_col"),tx("comp_raw_col"),
                   tx("comp_comp_col"),tx("comp_ratio_col"),tx("comp_saved_col")]
    st.dataframe(pc_df, use_container_width=True, height=300)

    sh(tx("comp_index_title"), "Index")
    ib(tx("comp_index_desc"))
    idx_rows=[]
    for cid,info in sorted(per_res["index"].items()):
        idx_rows.append({tx("comp_cluster_col"):tx("noise_label") if cid==-1 else f"#{cid}",
                         tx("comp_txs_col"):info["count"],
                         tx("comp_offset_col"):f"{info['offset']:,} B",
                         tx("comp_block_size_col"):human_size(info["comp_size"]),
                         tx("comp_ratio_col"):f"{info['ratio']:.2f}×"})
    st.dataframe(pd.DataFrame(idx_rows), use_container_width=True, height=280)

# ═══════════════════════════════════════════════════════════════════
# PAGE 4 — SEARCH BENCHMARK
# ═══════════════════════════════════════════════════════════════════
elif page == tx("page_search"):
    sh(tx("search_title"), "Benchmark")
    ib(tx("search_desc"))

    if per_res is None:
        ib("⚠️ " + (
            "Please press **▶ Run** in the sidebar first."
            if lang=="en" else
            "اضغط على **▶ تشغيل** في الشريط الجانبي أولاً."
            if lang=="ar" else
            "Önce kenar çubuğundaki **▶ Çalıştır** düğmesine basın."
        ), "w")
        st.stop()

    with st.expander(f"📖 {tx('search_why_title')}", expanded=False):
        for i,k in enumerate(["search_why1","search_why2","search_why3","search_why4"],1):
            cs(i, tx(k))

    st.markdown("<br>", unsafe_allow_html=True)
    sh(tx("search_addr_title"))
    scam_addr   = df[df["is_scam"]==1]["from_address"].value_counts().head(20).index.tolist()
    normal_addr = df[df["is_scam"]==0]["from_address"].value_counts().head(20).index.tolist()

    ct,cp = st.columns([1,3])
    with ct:
        addr_type = st.selectbox(tx("search_addr_type"),
            [tx("search_scam"),tx("search_normal"),tx("search_custom")])
    with cp:
        if addr_type == tx("search_scam"):
            query_addr = st.selectbox("__",scam_addr,label_visibility="collapsed",
                format_func=lambda x: x[:22]+"…")
        elif addr_type == tx("search_normal"):
            query_addr = st.selectbox("__",normal_addr,label_visibility="collapsed",
                format_func=lambda x: x[:22]+"…")
        else:
            query_addr = st.text_input(tx("search_enter"),
                value="0x304cc179719bc5b05418d6f7f6783abe45d83090")

    run_search = st.button(tx("search_run_btn"), use_container_width=False)
    if run_search: st.session_state.search_done = False

    if run_search or st.session_state.search_done:
        if not st.session_state.search_done:
            with st.spinner(tx("search_running")):
                raw_all = _df_to_bytes(df)
                b_blob  = compress_zstd(raw_all) if method=="zstd" else compress_gzip(raw_all)
                sr = simulate_search_random(b_blob, df, query_addr, method)
                si = simulate_search_cluster_index(per_res, df, labels, query_addr, method)
                st.session_state.search_random = sr
                st.session_state.search_idx    = si
                st.session_state.search_done   = True
                st.session_state.search_addr   = query_addr

        sr  = st.session_state.search_random
        si  = st.session_state.search_idx
        qa  = st.session_state.search_addr or query_addr
        spd = sr["search_time_s"]/si["search_time_s"] if si["search_time_s"]>0 else 999
        dr  = (1-si["rows_decompressed"]/max(sr["rows_decompressed"],1))*100

        ib(f'🔍 {tx("search_result_info")}: <code>{qa[:28]}…</code> — '
           f'<b style="color:{GREEN}">{spd:.1f}× {tx("search_faster")}</b> · '
           f'{si["pct_data_read"]:.1f}% {tx("search_touched")}', "s")

        l,r = st.columns(2)
        with l:
            st.markdown(f'<div style="background:{CARD};border:1px solid {RED};border-radius:12px;padding:1.4rem;">'
                        f'<div style="font-size:.78rem;font-weight:700;text-transform:uppercase;color:{RED};margin-bottom:.8rem;">{tx("search_baseline_lbl")}</div>',
                        unsafe_allow_html=True)
            cr(tx("search_time"),f'{sr["search_time_s"]:.3f}s',RED)
            cr(tx("search_rows_decomp"),f'{sr["rows_decompressed"]:,}')
            cr(tx("search_blocks_opened"),str(sr["blocks_opened"]))
            cr(tx("search_results"),str(sr["hits"]))
            cr(tx("search_data_pct"),"100%",RED)
            st.markdown("</div>",unsafe_allow_html=True)
        with r:
            st.markdown(f'<div style="background:{CARD};border:2px solid {VIOLET};border-radius:12px;padding:1.4rem;box-shadow:0 0 16px rgba(124,58,237,.2);">'
                        f'<div style="font-size:.78rem;font-weight:700;text-transform:uppercase;color:{VIOLET};margin-bottom:.8rem;">{tx("search_idx_lbl")}</div>',
                        unsafe_allow_html=True)
            cr(tx("search_time"),f'{si["search_time_s"]:.3f}s ({spd:.1f}×)',GREEN)
            cr(tx("search_rows_decomp"),f'{si["rows_decompressed"]:,} (-{dr:.0f}%)',GREEN)
            cr(tx("search_blocks_opened"),f'{si["blocks_opened"]} / {per_res["n_blocks"]}',VIOLET)
            cr(tx("search_results"),str(si["hits"]))
            cr(tx("search_data_pct"),f'{si["pct_data_read"]:.1f}%',GREEN)
            st.markdown("</div>",unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        sh(tx("search_speedup_title"))
        fig_g = go.Figure(go.Indicator(mode="gauge+number+delta",value=spd,
            number={"suffix":"×","font":{"size":46,"color":GREEN}},
            delta={"reference":1,"suffix":"×"},
            gauge={"axis":{"range":[0,max(spd*1.2,20)]},
                   "bar":{"color":GREEN},
                   "steps":[{"range":[0,5],"color":"rgba(239,68,68,.2)"},
                             {"range":[5,15],"color":"rgba(245,158,11,.2)"},
                             {"range":[15,200],"color":"rgba(34,197,94,.2)"}]},
            title={"text":tx("search_speedup_label"),"font":{"color":TEXT}}))
        fig_g.update_layout(paper_bgcolor="rgba(0,0,0,0)",font=dict(color=TEXT,family="Inter"),
                            height=300,margin=dict(l=40,r=40,t=60,b=20))
        st.plotly_chart(fig_g, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════
# PAGE 5 — BLOCK ANALYSIS
# ═══════════════════════════════════════════════════════════════════
elif page == tx("page_blocks"):
    sh(tx("blocks_title"), "Blocks")
    ib(tx("blocks_desc"))
    ratio = sorted_res["ratio"]
    top20 = blk_stats.nlargest(20,"total_size").sort_values("total_size",ascending=True).copy()
    top20["comp_size"]=top20["total_size"]/ratio
    fig_top=go.Figure()
    fig_top.add_trace(go.Bar(y=top20["block_number"].astype(str),x=top20["total_size"]/1024,
        name=tx("total_size"),orientation="h",marker_color=VIOLET,opacity=.9))
    fig_top.add_trace(go.Bar(y=top20["block_number"].astype(str),x=top20["comp_size"]/1024,
        name=f'After {method.upper()} ({ratio:.2f}×)',orientation="h",marker_color=GREEN,opacity=.85))
    fig_top.update_layout(**plo(500),barmode="overlay")
    fig_top.update_xaxes(title_text="KB")
    sh(tx("top_blocks"))
    st.plotly_chart(fig_top, use_container_width=True)

    sh(tx("block_timeline"))
    srt=blk_stats.sort_values("block_number").copy()
    srt["comp_size"]=srt["total_size"]/ratio
    fig_btl=go.Figure()
    fig_btl.add_trace(go.Scatter(x=srt["block_number"],y=srt["total_size"]/1024,
        mode="lines",name=tx("total_size"),line=dict(color=VIOLET,width=1.5),
        fill="tozeroy",fillcolor="rgba(124,58,237,.1)"))
    fig_btl.add_trace(go.Scatter(x=srt["block_number"],y=srt["comp_size"]/1024,
        mode="lines",name=f'After {method.upper()}',
        line=dict(color=GREEN,width=1.5),fill="tozeroy",fillcolor="rgba(34,197,94,.1)"))
    fig_btl.update_layout(**plo(360))
    fig_btl.update_yaxes(title_text="KB")
    st.plotly_chart(fig_btl, use_container_width=True)

    sh(tx("block_select"))
    sel=st.selectbox("__b",sorted(df["block_number"].unique()),label_visibility="collapsed")
    bl_df=df[df["block_number"]==sel]
    bl_row=blk_stats[blk_stats["block_number"]==sel]
    if not bl_row.empty:
        r=bl_row.iloc[0]
        for col,(l,v) in zip(st.columns(4),[
            (tx("block_txs"),f"{int(r['tx_count'])}"),
            (tx("block_size"),human_size(int(r["total_size"]))),
            (f'After {method.upper()}',human_size(int(r["total_size"]/ratio))),
            (tx("block_scam_count"),f"{int(r['scam_count'])}"),
        ]):
            with col: st.markdown(mc(l,v),unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    show=["hash","from_address","to_address","value_eth","gas_price_gwei","is_scam","tx_size_bytes"]
    disp=bl_df[show].copy()
    disp["hash"]=disp["hash"].apply(lambda x: x[:18]+"…")
    disp["from_address"]=disp["from_address"].apply(lambda x: x[:14]+"…")
    disp["to_address"]=disp["to_address"].apply(lambda x: x[:14]+"…")
    st.dataframe(disp, use_container_width=True, height=320)

# ═══════════════════════════════════════════════════════════════════
# PAGE 6 — PERFORMANCE METRICS
# ═══════════════════════════════════════════════════════════════════
elif page == tx("page_metrics"):
    import psutil, os
    sh(tx("metrics_title"), "Metrics")
    ib(tx("metrics_desc"))

    # ── Guard: make sure compression has been computed ─────────────
    if baseline is None or sorted_res is None or per_res is None:
        ib(
            "⚠️ " + (
                "Please press the **▶ Run** button in the sidebar first to compute DBSCAN clustering and compression results."
                if lang == "en" else
                "من فضلك اضغط على زر **▶ تشغيل** في الشريط الجانبي أولاً لحساب التجميع ونتائج الضغط."
                if lang == "ar" else
                "Lütfen önce kenar çubuğundaki **▶ Çalıştır** düğmesine basın."
            ),
            "w"
        )
        st.stop()

    mem_mb = psutil.Process(os.getpid()).memory_info().rss / 1_048_576

    for col,(l,v) in zip(st.columns(4),[
        (tx("metrics_dbscan_time"), f"{etime:.2f}s"  if etime  else "—"),
        (tx("metrics_memory"),      f"{mem_mb:.0f} MB"),
        (tx("metrics_rows"),        f"{len(df):,}"),
        (tx("metrics_blocks"),      str(per_res.get("n_blocks", "—"))),
    ]):
        with col: st.markdown(mc(l,v), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    sh(tx("metrics_cmp_table"))
    try:
        tbl = build_comparison_table([baseline, sorted_res, per_res])
        tbl["Strategy"] = tbl["Strategy"].map({
            "baseline_random":   tx("comp_baseline_label"),
            "cluster_sorted":    tx("comp_sorted_label"),
            "per_cluster_blocks":tx("comp_percluster_label"),
        })
        st.dataframe(tbl, use_container_width=True, hide_index=True)
    except Exception as e:
        ib(f"⚠️ Table error: {e}", "w")

    sh(tx("metrics_eps_title"))
    ib(tx("metrics_eps_desc"))
    eps_vals = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5]
    try:
        with st.spinner(tx("processing")):
            sens = eps_sensitivity(X_scaled, eps_vals, st.session_state.min_samples)
        fig_sens = make_subplots(specs=[[{"secondary_y": True}]])
        fig_sens.add_trace(go.Scatter(x=sens["eps"], y=sens["n_clusters"],
            name=tx("total_clusters"), mode="lines+markers",
            line=dict(color=VIOLET, width=2.5), marker=dict(size=8)), secondary_y=False)
        fig_sens.add_trace(go.Scatter(x=sens["eps"], y=sens["n_noise"],
            name=tx("noise_count"), mode="lines+markers",
            line=dict(color=RED, width=2.5, dash="dot"), marker=dict(size=8)), secondary_y=True)
        fig_sens.add_vline(x=st.session_state.eps,
            line=dict(color=AMBER, dash="dash", width=2),
            annotation_text=f"ε={st.session_state.eps}",
            annotation_font_color=AMBER)
        fig_sens.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT, family="Inter"), height=360,
            legend=dict(bgcolor="rgba(0,0,0,0)"), margin=dict(l=50,r=50,t=50,b=50))
        fig_sens.update_yaxes(title_text=tx("total_clusters"), secondary_y=False, gridcolor=BORDER)
        fig_sens.update_yaxes(title_text=tx("noise_count"), secondary_y=True)
        st.plotly_chart(fig_sens, use_container_width=True)
    except Exception as e:
        ib(f"⚠️ Sensitivity chart error: {e}", "w")

    sh(tx("metrics_summary"))
    try:
        improvement = (sorted_res['ratio'] / baseline['ratio'] - 1) * 100 if baseline['ratio'] else 0
        summary = [
            (tx("total_txs"),            f"{len(df):,}"),
            (tx("total_blocks"),         f"{df['block_number'].nunique():,}"),
            (tx("total_size"),           human_size(baseline["raw_size"])),
            (tx("comp_baseline_label"),  human_size(baseline["comp_size"])),
            (tx("comp_sorted_label"),    human_size(sorted_res["comp_size"])),
            (tx("comp_percluster_label"),human_size(per_res["comp_size"])),
            ("Baseline Ratio",           f"{baseline['ratio']:.3f}×"),
            ("Cluster-Sorted Ratio",     f"{sorted_res['ratio']:.3f}×"),
            ("Improvement",              f"+{improvement:.1f}%"),
            (tx("metrics_blocks"),       str(per_res.get("n_blocks","—"))),
            (tx("total_clusters"),       str(n_clusters)),
            (tx("noise_count"),          f"{n_noise:,}"),
            ("Epsilon (ε)",              str(st.session_state.eps)),
            ("min_samples",              str(st.session_state.min_samples)),
            (tx("metrics_dbscan_time"),  f"{etime:.2f}s" if etime else "—"),
            (tx("comp_method_label"),    method.upper()),
            (tx("metrics_memory"),       f"{mem_mb:.0f} MB"),
        ]
        st.dataframe(
            pd.DataFrame(summary, columns=[tx("metric"), tx("value_col")]),
            use_container_width=True, hide_index=True, height=560)
        ib(tx("metrics_grad_note"), "s")
    except Exception as e:
        ib(f"⚠️ Summary error: {e}", "w")


# ═══════════════════════════════════════════════════════════════════
# PAGE 7 — ALGORITHM COMPARISON (DBSCAN vs K-Means)
# ═══════════════════════════════════════════════════════════════════
elif page == tx("page_algo_cmp"):
    sh(tx("algo_title"), "DBSCAN vs K-Means")
    ib(tx("algo_desc"))

    with st.expander(f"📖 {tx('algo_why_dbscan')}", expanded=True):
        for i,k in enumerate(["algo_why1","algo_why2","algo_why3","algo_why4"],1):
            cs(i, tx(k))

    st.markdown("<br>", unsafe_allow_html=True)
    c_k, c_btn = st.columns([2,1])
    with c_k:
        km_k = st.slider(tx("algo_k_slider"), 3, 30, st.session_state.km_k, 1)
        st.session_state.km_k = km_k
    with c_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        run_km = st.button(tx("algo_run_btn"), use_container_width=True)

    if run_km:
        st.session_state.km_labels = None
        st.session_state.km_ratio  = None

    if st.session_state.km_labels is None:
        with st.spinner(tx("algo_running")):
            km_labels, km_time = run_kmeans(X_scaled, n_clusters=st.session_state.km_k)
            km_sil  = kmeans_silhouette(X_scaled, km_labels)
            # Compute K-Means cluster-sorted compression ratio
            km_res  = compress_cluster_sorted(df, km_labels, method)
            st.session_state.km_labels = km_labels
            st.session_state.km_time   = km_time
            st.session_state.km_sil    = km_sil
            st.session_state.km_ratio  = km_res["ratio"]

    km_labels = st.session_state.km_labels
    km_time   = st.session_state.km_time
    km_sil    = st.session_state.km_sil
    km_ratio  = st.session_state.km_ratio
    dbscan_sil= compute_silhouette(X_scaled, labels) or 0.0

    # ── Side-by-side scatter ──────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    ls, rs = st.columns(2)
    with ls:
        sh(tx("algo_scatter_dbscan"), "DBSCAN")
        idx_s=np.random.choice(len(coords_2d),min(5000,len(coords_2d)),replace=False)
        fig_d=go.Figure()
        for cv in sorted(set(labels[idx_s].astype(str))):
            m=labels[idx_s].astype(str)==cv
            nm=tx("noise_label") if cv=="-1" else f"Cluster {cv}"
            col=RED if cv=="-1" else PAL[int(cv)%len(PAL) if cv!="-1" else 0]
            fig_d.add_trace(go.Scatter(x=coords_2d[idx_s,0][m],y=coords_2d[idx_s,1][m],
                mode="markers",name=nm,marker=dict(size=3,color=col,opacity=.7,line=dict(width=0)),showlegend=False))
        fig_d.update_layout(**plo(340))
        st.plotly_chart(fig_d, use_container_width=True)

    with rs:
        sh(tx("algo_scatter_km"), "K-Means")
        fig_k=go.Figure()
        for cv in sorted(set(km_labels[idx_s])):
            m=km_labels[idx_s]==cv
            fig_k.add_trace(go.Scatter(x=coords_2d[idx_s,0][m],y=coords_2d[idx_s,1][m],
                mode="markers",name=f"Cluster {cv}",
                marker=dict(size=3,color=PAL[cv%len(PAL)],opacity=.7,line=dict(width=0)),showlegend=False))
        fig_k.update_layout(**plo(340))
        st.plotly_chart(fig_k, use_container_width=True)

    # ── Head-to-head table ───────────────────────────────────────
    sh(tx("algo_cmp_table"))
    dbscan_wins = sorted_res['ratio'] >= km_ratio
    if lang == "ar":
        noise_y="✅ تلقائي"; noise_n="❌ لا يوجد"; k_y="✅ لا"; k_n="❌ نعم"
    elif lang == "tr":
        noise_y="✅ Otomatik"; noise_n="❌ Yok"; k_y="✅ Hayır"; k_n="❌ Evet"
    else:
        noise_y="✅ Automatic"; noise_n="❌ None"; k_y="✅ No"; k_n="❌ Yes (must set K)"

    rows_cmp=[
        {"algo":f"{'🏆 ' if dbscan_wins else ''}DBSCAN",
         tx("algo_cmp_clusters"):n_clusters,
         tx("algo_cmp_noise"):noise_y,
         tx("algo_cmp_k_req"):k_y,
         tx("algo_cmp_time"):f"{etime:.2f}s",
         tx("algo_cmp_sil"):f"{dbscan_sil:.3f}",
         tx("algo_cmp_ratio"):f"{sorted_res['ratio']:.3f}×",
         tx("algo_cmp_saved"):f"{sorted_res['pct_saved']:.1f}%"},
        {"algo":f"{'🏆 ' if not dbscan_wins else ''}K-Means (K={km_k})",
         tx("algo_cmp_clusters"):km_k,
         tx("algo_cmp_noise"):noise_n,
         tx("algo_cmp_k_req"):k_n,
         tx("algo_cmp_time"):f"{km_time:.2f}s",
         tx("algo_cmp_sil"):f"{km_sil:.3f}",
         tx("algo_cmp_ratio"):f"{km_ratio:.3f}×",
         tx("algo_cmp_saved"):f"{(1-1/km_ratio)*100:.1f}%"},
    ]
    st.dataframe(pd.DataFrame(rows_cmp).rename(columns={"algo":tx("algo_cmp_algo")}),
                 use_container_width=True, hide_index=True)

    # ── Ratio bar chart ──────────────────────────────────────────
    sh(tx("algo_ratio_chart"))
    fig_cmp=go.Figure(go.Bar(
        x=["DBSCAN","K-Means","Baseline"],
        y=[sorted_res['ratio'],km_ratio,baseline['ratio']],
        marker_color=[VIOLET if dbscan_wins else CYAN,
                      CYAN if dbscan_wins else VIOLET, RED],
        text=[f"{sorted_res['ratio']:.2f}×",f"{km_ratio:.2f}×",f"{baseline['ratio']:.2f}×"],
        textposition="outside",textfont=dict(size=16,color=TEXT,family="JetBrains Mono")))
    fig_cmp.add_hline(y=baseline['ratio'],line=dict(color=RED,dash="dash",width=1.5),
        annotation_text="Baseline",annotation_font_color=RED)
    fig_cmp.update_layout(**plo(380))
    fig_cmp.update_yaxes(title_text=tx("algo_cmp_ratio"))
    st.plotly_chart(fig_cmp, use_container_width=True)

    if dbscan_wins:
        ib(f"✅ DBSCAN {tx('algo_cmp_winner')} — {tx('algo_cmp_ratio')}: "
           f"<b style='color:{GREEN}'>{sorted_res['ratio']:.2f}×</b> vs K-Means "
           f"<b style='color:{AMBER}'>{km_ratio:.2f}×</b>", "s")
    else:
        ib(f"⚠️ K-Means {tx('algo_cmp_winner')} for this K. Try adjusting ε for DBSCAN.", "w")

    # ── Elbow method ────────────────────────────────────────────
    sh(tx("algo_elbow_title"))
    ib(tx("algo_elbow_desc"))
    with st.spinner(tx("processing")):
        elbow=sweep_k(X_scaled, list(range(3,21)))
    fig_el=make_subplots(specs=[[{"secondary_y":True}]])
    fig_el.add_trace(go.Scatter(x=elbow["k"],y=elbow["inertia"],name="Inertia",
        mode="lines+markers",line=dict(color=AMBER,width=2.5),marker=dict(size=7)),secondary_y=False)
    fig_el.add_trace(go.Scatter(x=elbow["k"],y=elbow["silhouette"],name=tx("silhouette"),
        mode="lines+markers",line=dict(color=CYAN,width=2.5,dash="dot"),marker=dict(size=7)),secondary_y=True)
    fig_el.add_vline(x=km_k,line=dict(color=VIOLET,dash="dash",width=2),
        annotation_text=f"K={km_k}",annotation_font_color=VIOLET)
    fig_el.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT,family="Inter"),height=340,
        legend=dict(bgcolor="rgba(0,0,0,0)"),margin=dict(l=50,r=50,t=40,b=40))
    fig_el.update_xaxes(title_text="K",gridcolor=BORDER)
    fig_el.update_yaxes(title_text="Inertia",secondary_y=False,gridcolor=BORDER)
    fig_el.update_yaxes(title_text=tx("silhouette"),secondary_y=True)
    st.plotly_chart(fig_el, use_container_width=True)

    # ── Fraud detection via noise ────────────────────────────────
    sh(tx("algo_noise_title"), "Fraud")
    ib(tx("algo_noise_desc"))
    noise_mask = labels == -1
    noise_scam_pct  = df[noise_mask]["is_scam"].mean()*100 if noise_mask.sum()>0 else 0
    normal_scam_pct = df[~noise_mask]["is_scam"].mean()*100

    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(mc(tx("noise_count"),f"{n_noise:,}"),unsafe_allow_html=True)
    with c2: st.markdown(mc(tx("algo_noise_scam_pct"),f"{noise_scam_pct:.1f}%",
                             delta=f"+{noise_scam_pct-normal_scam_pct:.1f}% vs clusters",dc=RED),
                         unsafe_allow_html=True)
    with c3: st.markdown(mc(tx("algo_noise_normal_pct"),f"{normal_scam_pct:.1f}%"),unsafe_allow_html=True)

    fig_fraud=go.Figure(go.Bar(
        x=[tx("noise_label"),f'Clusters ({n_clusters})'],
        y=[noise_scam_pct, normal_scam_pct],
        marker_color=[RED,GREEN],
        text=[f"{noise_scam_pct:.1f}%",f"{normal_scam_pct:.1f}%"],
        textposition="outside",textfont=dict(size=15,color=TEXT,family="JetBrains Mono")))
    fig_fraud.update_layout(**plo(340)); fig_fraud.update_yaxes(title_text="Scam %")
    st.plotly_chart(fig_fraud, use_container_width=True)
    ib(tx("algo_noise_insight"), "s")

# ═══════════════════════════════════════════════════════════════════
# PAGE 8 — EXPORT & DOWNLOAD
# ═══════════════════════════════════════════════════════════════════
elif page == tx("page_export"):
    sh(tx("export_title"), "⬇️")
    ib(tx("export_desc"))

    # ── 1. Download compressed file ───────────────────────────────
    sh(tx("export_zst_title"))
    ib(tx("export_zst_desc").format(method=method.upper()))

    strat_choice = st.selectbox(tx("export_zst_strategy"),
        ["cluster_sorted","baseline"],
        format_func=lambda x: tx("comp_sorted_label") if x=="cluster_sorted" else tx("comp_baseline_label"))

    with st.spinner(f"{tx('processing')}…"):
        comp_bytes = export_compressed_file(df, labels, method=method, strategy=strat_choice)
        comp_ratio = (df["tx_size_bytes"].sum()) / len(comp_bytes)
        comp_pct   = (1 - len(comp_bytes)/df["tx_size_bytes"].sum())*100

    ext = "zst" if method=="zstd" else "gz"
    fname = f"blockchain_cluster_{strat_choice}_{method}.parquet.{ext}"

    ib(tx("export_zst_info").format(
        size=human_size(len(comp_bytes)),
        ratio=f"{comp_ratio:.2f}",
        saved=f"{comp_pct:.1f}"), "s")

    st.download_button(label=tx("export_zst_btn"), data=comp_bytes,
                       file_name=fname, mime="application/octet-stream",
                       use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 2. Download cluster index ────────────────────────────────
    sh(tx("export_idx_title"))
    ib(tx("export_idx_desc"))
    idx_json = export_cluster_index_json(per_res)
    st.download_button(label=tx("export_idx_btn"), data=idx_json,
                       file_name="cluster_index.json", mime="application/json",
                       use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 3. Download HTML report ──────────────────────────────────
    sh(tx("export_report_title"))
    ib(tx("export_report_desc"))

    km_r  = st.session_state.km_ratio  or 0.0
    km_t  = st.session_state.km_time   or 0.0
    km_s  = st.session_state.km_sil    or 0.0
    db_s  = compute_silhouette(X_scaled, labels) or 0.0

    html_report = generate_html_report(
        stats=stats, baseline=baseline, sorted_res=sorted_res, per_res=per_res,
        n_clusters=n_clusters, n_noise=n_noise, etime=etime,
        km_ratio=km_r, km_time=km_t, km_sil=km_s, dbscan_sil=db_s,
        method=method, lang=st.session_state.lang)

    st.download_button(label=tx("export_report_btn"),
                       data=html_report.encode("utf-8"),
                       file_name=f"blockchain_compression_report_{lang}.html",
                       mime="text/html", use_container_width=True)

    ib(f"💡 {'Open the downloaded HTML in your browser → Ctrl+P → Save as PDF.' if lang=='en' else 'افتح ملف HTML في المتصفح → Ctrl+P → حفظ كـ PDF.' if lang=='ar' else 'İndirilen HTML dosyasını tarayıcıda açın → Ctrl+P → PDF olarak kaydet.'}")        

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 4. Compression levels benchmark ─────────────────────────
    sh(tx("export_levels_title"))
    ib(tx("export_levels_desc"))

    if st.button(tx("export_levels_run"), use_container_width=False):
        with st.spinner(tx("export_levels_running")):
            raw_sorted = _df_to_bytes(df.assign(_c=labels).sort_values("_c").drop(columns=["_c"]))
            lvl_df = compare_compression_levels(raw_sorted)

        lvl_df["raw_mb"] = df["tx_size_bytes"].sum()/1_048_576
        lvl_df["comp_mb"] = lvl_df["comp_size"]/1_048_576

        fig_lvl = go.Figure()
        for algo, clr in [("zstd", VIOLET), ("gzip", CYAN)]:
            sub = lvl_df[lvl_df["algo"]==algo]
            fig_lvl.add_trace(go.Scatter(x=sub["method"], y=sub["ratio"],
                mode="lines+markers+text", name=algo.upper(),
                line=dict(color=clr,width=2.5), marker=dict(size=9),
                text=[f"{r:.2f}×" for r in sub["ratio"]], textposition="top center",
                textfont=dict(color=TEXT,size=11)))
        fig_lvl.add_hline(y=baseline["ratio"],line=dict(color=RED,dash="dash",width=1.5),
            annotation_text=f"Baseline {baseline['ratio']:.2f}×",annotation_font_color=RED)
        fig_lvl.update_layout(**plo(380))
        fig_lvl.update_yaxes(title_text=tx("algo_cmp_ratio"))
        st.plotly_chart(fig_lvl, use_container_width=True)

        disp_lvl = lvl_df[[tx("export_col_method") if False else "method","ratio","pct_saved","time_s","comp_mb"]].copy()
        disp_lvl.columns=[tx("export_col_method"),tx("export_col_ratio"),
                           tx("export_col_saved"),tx("export_col_time"),tx("export_col_size")]
        disp_lvl[tx("export_col_ratio")]  = disp_lvl[tx("export_col_ratio")].apply(lambda x: f"{x:.2f}×")
        disp_lvl[tx("export_col_saved")]  = disp_lvl[tx("export_col_saved")].apply(lambda x: f"{x:.1f}%")
        disp_lvl[tx("export_col_time")]   = disp_lvl[tx("export_col_time")].apply(lambda x: f"{x:.3f}s")
        disp_lvl[tx("export_col_size")]   = disp_lvl[tx("export_col_size")].apply(lambda x: f"{x:.2f} MB")
        st.dataframe(disp_lvl, use_container_width=True, hide_index=True)

        best = lvl_df.loc[lvl_df["ratio"].idxmax()]
        ib(f"🏆 {'Best level' if lang=='en' else 'أفضل مستوى' if lang=='ar' else 'En iyi seviye'}: "
           f"<b style='color:{GREEN}'>{best['method'].upper()}</b> — "
           f"{best['ratio']:.2f}× — {best['pct_saved']:.1f}% saved — {best['time_s']:.2f}s", "s")
