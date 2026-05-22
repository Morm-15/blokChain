"""
app.py - Blockchain Decision Support System (DSS)
Optimized for storage efficiency, signature aggregation, and academic presentation.
"""
import warnings
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from blockchain_compressor import (
    Blockchain, MerkleTree, DeltaEncoder, TxClusterer, HAS_ZSTD
)
from i18n import make_t

warnings.filterwarnings("ignore")

# ── PAGE CONFIGURATION ────────────────────────────────────────────
st.set_page_config(
    page_title="Blockchain DSS & Compressor | graduation project",
    page_icon="⛓️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM GLASSMORPHIC STYLING (CSS) ──────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&family=IBM+Plex+Mono:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Cairo', sans-serif !important;
}
code, pre, [class*="mono"] {
    font-family: 'IBM Plex Mono', monospace !important;
}
.stApp {
    background-color: #090d16 !important;
    background-image: radial-gradient(at 5% 5%, rgba(0, 242, 254, 0.08) 0px, transparent 40%),
                      radial-gradient(at 95% 95%, rgba(16, 185, 129, 0.08) 0px, transparent 40%) !important;
    color: #e2e8f0 !important;
}

/* Glassmorphic Panel styling */
.glass-panel {
    background: rgba(13, 22, 40, 0.6) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(0, 242, 254, 0.12) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    margin-bottom: 24px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.glass-panel:hover {
    border-color: rgba(0, 242, 254, 0.25) !important;
    box-shadow: 0 8px 32px 0 rgba(0, 242, 254, 0.08) !important;
}

/* Academic Banner */
.hero {
    background: linear-gradient(135deg, rgba(9, 22, 46, 0.85) 0%, rgba(13, 36, 72, 0.65) 100%) !important;
    border: 1px solid rgba(0, 242, 254, 0.2) !important;
    border-radius: 20px !important;
    padding: 36px 44px !important;
    margin-bottom: 30px !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.45), inset 0 1px 1px rgba(255, 255, 255, 0.05) !important;
}
.hero h1 {
    color: #ffffff !important;
    background: linear-gradient(120deg, #ffffff, #00f2fe, #10b981) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    margin: 0 0 12px 0 !important;
    font-size: 2.2rem !important;
    font-weight: 900 !important;
    letter-spacing: -0.5px;
}
.hero p {
    color: #94a3b8 !important;
    margin: 0 !important;
    font-size: 1.02rem !important;
    line-height: 1.8 !important;
}
.hero-meta {
    font-size: 0.82rem !important;
    color: #64748b !important;
    margin-top: 15px !important;
    display: flex;
    gap: 15px;
    align-items: center;
    border-top: 1px solid rgba(148, 163, 184, 0.1);
    padding-top: 15px;
}
.htag {
    display: inline-block;
    border-radius: 30px;
    padding: 4px 14px;
    font-size: .75rem;
    font-weight: 600;
    margin: 12px 6px 0 0;
}
.htag-g { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #10b981; }
.htag-b { background: rgba(0, 242, 254, 0.1); border: 1px solid rgba(0, 242, 254, 0.3); color: #00f2fe; }
.htag-o { background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); color: #f59e0b; }

/* KPI Display cards */
.kpi {
    background: rgba(13, 22, 40, 0.65) !important;
    backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(0, 242, 254, 0.1) !important;
    border-radius: 14px !important;
    padding: 20px 14px !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
}
.kpi:hover {
    transform: translateY(-5px) !important;
    border-color: rgba(0, 242, 254, 0.3) !important;
    box-shadow: 0 10px 30px rgba(0, 242, 254, 0.15) !important;
}
.kv {
    font-size: 1.6rem !important;
    font-weight: 900 !important;
    color: #00f2fe !important;
    text-shadow: 0 0 15px rgba(0, 242, 254, 0.25) !important;
}
.kv-g { color: #10b981 !important; text-shadow: 0 0 15px rgba(16, 185, 129, 0.25) !important; }
.kv-o { color: #f59e0b !important; text-shadow: 0 0 15px rgba(245, 158, 11, 0.25) !important; }
.kl { font-size: .82rem; color: #94a3b8; margin-top: 8px; font-weight: 600; }
.ks { font-size: .72rem; color: #64748b; margin-top: 4px; }

/* Block cards */
.bc {
    background: rgba(13, 22, 40, 0.55) !important;
    border: 1px solid rgba(0, 242, 254, 0.1) !important;
    border-left: 4px solid #00f2fe !important;
    border-radius: 12px !important;
    padding: 16px 18px !important;
    margin: 10px 0 !important;
    transition: all 0.25s ease !important;
}
.bc:hover {
    border-left-color: #10b981 !important;
    border-color: rgba(16, 185, 129, 0.25) !important;
    box-shadow: 0 4px 20px rgba(16, 185, 129, 0.1) !important;
    transform: translateX(4px) !important;
}
.bn { color: #00f2fe; font-weight: 700; font-size: 1rem; margin-bottom: 6px; }
.bh { color: #64748b; font-size: 0.72rem; margin-top: 3px; font-family: 'IBM Plex Mono', monospace; }
.bi { color: #cbd5e1; font-size: 0.8rem; margin-top: 8px; line-height: 1.8; }
.br { color: #10b981; font-weight: 700; }

/* Dynamic Tipbox styling */
.tip {
    background: rgba(15, 23, 42, 0.45) !important;
    border: 1px solid rgba(148, 163, 184, 0.12) !important;
    border-left: 4px solid #00f2fe !important;
    border-radius: 10px !important;
    padding: 14px 20px !important;
    margin-bottom: 20px !important;
}
.tip-g { border-left-color: #10b981 !important; }
.tip-o { border-left-color: #f59e0b !important; }
.tip-h { font-weight: 700; font-size: .9rem; color: #00f2fe; margin-bottom: 4px; }
.tip-g .tip-h { color: #10b981 !important; }
.tip-o .tip-h { color: #f59e0b !important; }
.tip-t { font-size: .83rem; color: #94a3b8; line-height: 1.7; }
.tip-t b { color: #ffffff; }

/* Row Statistics */
.nstat {
    background: rgba(13, 22, 40, 0.5) !important;
    border: 1px solid rgba(148, 163, 184, 0.1) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    text-align: center !important;
}
.nstat-v { font-size: 1.15rem; font-weight: 700; color: #c084fc; font-family: 'IBM Plex Mono', monospace; }
.nstat-l { font-size: .75rem; color: #94a3b8; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ── DATA LOADING ───────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_df():
    df = pd.read_csv("Dataset.csv")
    cols = ["hash", "from_address", "to_address", "value", "gas", "gas_price", "block_number", "nonce"]
    exist = [c for c in cols if c in df.columns]
    df = df[exist].dropna(subset=["gas_price", "gas", "block_number"])
    df = df[(df["gas_price"] > 0) & (df["gas"] > 0)]
    return df.sort_values("block_number").reset_index(drop=True)

@st.cache_resource(show_spinner=False)
def get_chain(n_tx: int):
    _df = load_df().head(n_tx)
    _chain = Blockchain()
    _chain.build_from_df(_df)
    return _chain

# ── LANGUAGE SELECTION & i18n ───────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "ar"

t = make_t(st.session_state.lang)

st.sidebar.markdown(f"**{t('lang_label')}**")
lc1, lc2, lc3 = st.sidebar.columns(3)
if lc1.button(t("btn_ar"), use_container_width=True):
    st.session_state.lang = "ar"
    st.rerun()
if lc2.button(t("btn_tr"), use_container_width=True):
    st.session_state.lang = "tr"
    st.rerun()
if lc3.button(t("btn_en"), use_container_width=True):
    st.session_state.lang = "en"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(f"## {t('sidebar_title')}")

# ── DATASET STATS WIDGET ────────────────────────────────────────
_df_info = load_df()
_nb_real  = int(_df_info["block_number"].nunique())
_ntx_real = len(_df_info)
_avg_real = round(_ntx_real / _nb_real, 1) if _nb_real else 0
st.sidebar.markdown(f"""
<div style="background:rgba(13, 22, 40, 0.65); border:1px solid rgba(0, 242, 254, 0.15); border-left:4px solid #10b981;
            border-radius:10px; padding:12px 16px; margin-bottom:10px;">
  <div style="color:#00f2fe; font-weight:700; font-size:.9rem; margin-bottom:8px;">
      {t('dataset_info_title')}
  </div>
  <div style="color:#94a3b8; font-size:.83rem; line-height:1.8;">
    📄 {t('dataset_total_txs')}: <b style="color:#10b981; font-family:'IBM Plex Mono';">{_ntx_real:,}</b><br>
    🔗 {t('dataset_uniq_blks')}: <b style="color:#10b981; font-family:'IBM Plex Mono';">{_nb_real:,}</b><br>
    📊 {t('dataset_avg_tx')}: <b style="color:#10b981; font-family:'IBM Plex Mono';">{_avg_real}</b>
  </div>
</div>
""", unsafe_allow_html=True)

# ── CONTROLS & SLIDERS ──────────────────────────────────────────
_tx_options = [300, 500, 1_000, 2_000, 5_000, 10_000, 20_000, 50_000]
if _ntx_real not in _tx_options:
    _tx_options.append(_ntx_real)
_tx_options = sorted(set(v for v in _tx_options if v <= _ntx_real))

n_tx_total = st.sidebar.select_slider(
    t("n_tx_total_lbl"),
    options=_tx_options,
    value=min(5_000, _tx_options[-1]),
    format_func=lambda v: f"{v:,} tx",
    help=t("n_tx_total_help")
)
st.sidebar.markdown("---")
st.sidebar.markdown(f"### {t('comp_section')}")
methods     = ["gzip", "zstd"] if HAS_ZSTD else ["gzip"]
comp_method = st.sidebar.selectbox(t("comp_method"), methods)
use_delta   = st.sidebar.toggle(t("delta_toggle"),   value=True)
use_cluster = st.sidebar.toggle(t("cluster_toggle"), value=True)

st.sidebar.markdown(f"### {t('dbscan_section')}")
eps_val  = st.sidebar.slider(t("eps_lbl"),      0.1, 3.0, 0.6, 0.1)
min_samp = st.sidebar.slider(t("minsamp_lbl"),  2,   10,  3,   1)

st.sidebar.markdown("---")
st.sidebar.markdown(f"### {t('network_section')}")
show_chain_graph = st.sidebar.toggle(t("chain_graph_toggle"), value=True)
show_merkle      = st.sidebar.toggle(t("merkle_toggle"),      value=True)

if not HAS_ZSTD:
    st.sidebar.info(t("zstd_tip"))

# ── HEADER BANNER (ACADEMIC BANNER) ─────────────────────────────
st.markdown(f"""
<div class="hero">
  <div style="font-size:0.85rem; font-weight:700; color:#10b981; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">
    {t('academic_meta')}
  </div>
  <h1>{t('academic_title')}</h1>
  <p>{t('hero_sub')}</p>
  <div style="margin-top: 15px;">
    <span class="htag htag-g">Ethereum PoS</span>
    <span class="htag htag-b">EIP-1559</span>
    <span class="htag htag-o">DBSCAN</span>
    <span class="htag htag-g">Delta Encoding</span>
    <span class="htag htag-b">Merkle Tree</span>
    <span class="htag htag-o">{comp_method.upper()}</span>
  </div>
</div>""", unsafe_allow_html=True)

# ── RUN SIMULATION & COMPRESSION ────────────────────────────────
with st.spinner(t("spinner_build")):
    chain = get_chain(n_tx_total)
with st.spinner(t("spinner_compress")):
    results = chain.compress_chain(
        method=comp_method, use_delta=use_delta,
        use_clustering=use_cluster, eps=eps_val, min_samples=min_samp
    )
    summary = chain.chain_summary(results)

res_df = pd.DataFrame(results)

# ── STANDARD METRICS ROW (KPI CARDS) ────────────────────────────
st.markdown(f"### ⚙️ {t('sidebar_title')}")
c1, c2, c3, c4, c5, c6 = st.columns(6)
kpis = [
    (c1, str(summary["n_blocks"]),             t("kpi_blocks"),  "",                  "kv"),
    (c2, f"{summary['total_tx']:,}",            t("kpi_txs"),    "",                  "kv"),
    (c3, f"{summary['total_raw_kb']:,.1f} KB",  t("kpi_raw"),    "",                  "kv"),
    (c4, f"{summary['total_comp_kb']:,.1f} KB", t("kpi_comp"),   "",                  "kv-g"),
    (c5, f"{summary['chain_ratio_pct']}%",      t("kpi_ratio"),  t("kpi_ratio_sub"), "kv-g"),
    (c6, f"{summary['saved_kb']:,.1f} KB",      t("kpi_saved"),  "",                  "kv-o"),
]
for col, val, lbl, sub, cls in kpis:
    col.markdown(f'<div class="kpi"><div class="{cls}">{val}</div>'
                 f'<div class="kl">{lbl}</div><div class="ks">{sub}</div></div>',
                 unsafe_allow_html=True)

# ── ACADEMIC OPTIMIZATIONS METRICS ROW ──────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"### {t('opt_stats_title')}")
oc1, oc2, oc3, oc4, oc5 = st.columns(5)
opt_kpis = [
    (oc1, f"{summary['total_opt_comp_kb']:,.1f} KB",  t("opt_compressed_size"), "", "kv-g"),
    (oc2, f"{summary['opt_chain_ratio_pct']}%",       t("opt_saving_pct"), t("kpi_ratio_sub"), "kv-g"),
    (oc3, f"{summary['opt_saved_kb']:,.1f} KB",       t("opt_saved_kb"), "", "kv-o"),
    (oc4, f"{summary['ecdsa_sig_bytes_kb'] - summary['bls_sig_bytes_kb']:,.1f} KB", t("sig_saved_kb"), f"ECDSA: {summary['ecdsa_sig_bytes_kb']}KB | BLS: {summary['bls_sig_bytes_kb']}KB", "kv"),
    (oc5, f"{summary['field_comp_saved_kb']:,.1f} KB", t("field_saved_kb"), "", "kv"),
]
for col, val, lbl, sub, cls in opt_kpis:
    col.markdown(f'<div class="kpi"><div class="{cls}">{val}</div>'
                 f'<div class="kl">{lbl}</div><div class="ks">{sub}</div></div>',
                 unsafe_allow_html=True)

# ── GENERAL BLOCKCHAIN STATS ────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
_avg_fee = summary.get("avg_base_fee_gwei", 0)
_avg_gas = summary.get("avg_gas_used", 0)
_dur     = summary.get("chain_duration_h", 0)
nc1, nc2, nc3, nc4 = st.columns(4)
_nstats = [
    (nc1, f"{_avg_fee:.4f} Gwei",  t("nstat_basefee")),
    (nc2, f"{_avg_gas:,.0f}",       t("nstat_avggas")),
    (nc3, f"12s",                   t("nstat_blocktime")),
    (nc4, f"{_dur:.1f}h",           t("nstat_duration")),
]
for col, val, lbl in _nstats:
    col.markdown(f'<div class="nstat"><div class="nstat-v">{val}</div>'
                 f'<div class="nstat-l">{lbl}</div></div>',
                 unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ══ BLOCKCHAIN CUMULATIVE SIZE GROWTH (PLOTLY) ═════════════════
st.markdown(t("section_growth"))
st.markdown(f"""
<div class="tip">
  <div class="tip-h">{t('tip_growth_h')}</div>
  <div class="tip-t">{t('tip_growth')}</div>
</div>
""", unsafe_allow_html=True)

fig_growth = go.Figure()
fig_growth.add_trace(go.Scatter(
    x=res_df["block_number"], y=res_df["cumulative_raw_kb"],
    mode='lines+markers', name=t("chart_raw"),
    line=dict(color='#ef5350', width=2.5),
    marker=dict(size=4)
))
fig_growth.add_trace(go.Scatter(
    x=res_df["block_number"], y=res_df["cumulative_comp_kb"],
    mode='lines+markers', name=t("chart_comp"),
    line=dict(color='#00f2fe', width=2.5),
    marker=dict(size=4)
))
fig_growth.add_trace(go.Scatter(
    x=res_df["block_number"], y=res_df["cumulative_opt_comp_kb"],
    mode='lines+markers', name=t("opt_compressed_size"),
    line=dict(color='#10b981', width=2.5),
    marker=dict(size=4)
))
fig_growth.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Cairo"),
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(showgrid=True, gridcolor="#1a2a40", title=t("chart_blk_x")),
    yaxis=dict(showgrid=True, gridcolor="#1a2a40", title=t("chart_y_kb")),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=400
)
st.plotly_chart(fig_growth, use_container_width=True)

# ══ SINGLE-BLOCK COMPRESSION RATIOS (PLOTLY) ══════════════════
st.markdown(t("section_ratio"))
st.markdown(f"""
<div class="tip tip-g">
  <div class="tip-h">{t('tip_ratio_h')}</div>
  <div class="tip-t">{t('tip_ratio')}</div>
</div>
""", unsafe_allow_html=True)

fig_scatter = px.scatter(
    res_df, x="block_number", y="ratio_pct", size="tx_count", color="ratio_pct",
    color_continuous_scale=[[0, "#ef5350"], [0.5, "#f59e0b"], [1.0, "#10b981"]],
    hover_data=["tx_count", "raw_bytes", "compressed_bytes"],
    labels={
        "block_number": t("chart_blk_x"),
        "ratio_pct": t("chart_ratio_lbl"),
        "tx_count": t("chart_tx_y")
    }
)
fig_scatter.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Cairo"),
    margin=dict(l=20, r=20, t=30, b=20),
    xaxis=dict(showgrid=True, gridcolor="#1a2a40"),
    yaxis=dict(showgrid=True, gridcolor="#1a2a40"),
)
fig_scatter.add_hline(
    y=summary["avg_ratio_pct"], line_dash="dash", line_color="#f59e0b",
    annotation_text=f"Avg: {summary['avg_ratio_pct']}%", annotation_font_color="#f59e0b"
)
st.plotly_chart(fig_scatter, use_container_width=True)

# ══ HEATMAP GRID DENSITY (PLOTLY) ═════════════════════════════
st.markdown(t("section_heatmap"))
cols = 20
rows = (len(res_df) // cols) + (1 if len(res_df) % cols != 0 else 0)
z_data = np.full((rows, cols), np.nan)
text_data = np.full((rows, cols), "", dtype=object)

for i, r in res_df.iterrows():
    row_idx = i // cols
    col_idx = i % cols
    z_data[row_idx, col_idx] = r["ratio_pct"]
    text_data[row_idx, col_idx] = f"Block: {r['block_number']}<br>Ratio: {r['ratio_pct']}%<br>TXs: {r['tx_count']}"

fig_hm = go.Figure(data=go.Heatmap(
    z=z_data, text=text_data, hoverinfo="text",
    colorscale=[[0, "#ef5350"], [0.5, "#f59e0b"], [1.0, "#10b981"]],
    showscale=True, xgap=3, ygap=3,
))
fig_hm.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Cairo"),
    xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
    yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, autorange="reversed"),
    margin=dict(l=10, r=10, t=10, b=10),
    height=max(150, rows * 25)
)
st.plotly_chart(fig_hm, use_container_width=True)

st.markdown("---")

# ══ TOPOLOGY BLOCKCHAIN GRAPH (PLOTLY) ════════════════════════
if show_chain_graph and len(chain.blocks) > 0:
    st.markdown(t("section_chain"))
    st.markdown(f"""
    <div class="tip tip-o">
      <div class="tip-h">{t('tip_chain_h')}</div>
      <div class="tip-t">{t('tip_chain')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    _MAX_GRAPH = 500
    show_n = min(len(res_df), _MAX_GRAPH)
    df_graph = res_df.head(show_n).copy()
    
    df_graph['y_pos'] = -(df_graph.index // 20)
    df_graph['x_pos'] = df_graph.index % 20
    df_graph.loc[df_graph['y_pos'] % 2 != 0, 'x_pos'] = 19 - df_graph.loc[df_graph['y_pos'] % 2 != 0, 'x_pos']
    
    fig_chain = px.scatter(
        df_graph, x="x_pos", y="y_pos", size="tx_count", color="ratio_pct",
        color_continuous_scale=[[0, "#ef5350"], [0.5, "#f59e0b"], [1.0, "#10b981"]], text="block_number",
        hover_data=["tx_count", "ratio_pct", "time_ms", "n_clusters"]
    )
    fig_chain.add_trace(go.Scatter(
        x=df_graph['x_pos'], y=df_graph['y_pos'],
        mode='lines', line=dict(color='rgba(0, 242, 254, 0.25)', width=2),
        hoverinfo='skip', showlegend=False
    ))
    fig_chain.update_traces(textposition='top center', textfont=dict(size=9, color='white'))
    fig_chain.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=10, r=10, t=30, b=10),
        height=max(200, (abs(df_graph['y_pos'].min()) + 1) * 60)
    )
    st.plotly_chart(fig_chain, use_container_width=True)
    st.markdown("---")

# ══ INSPECTION CARDS ══════════════════════════════════════════
st.markdown(t("section_cards"))
_MAX_CARDS    = 15
_cards_blks   = chain.blocks[:_MAX_CARDS]
_cards_remain = len(chain.blocks) - _MAX_CARDS
if _cards_remain > 0:
    if st.session_state.lang == "ar":
        st.caption(f"📍 يعرض أول **{_MAX_CARDS}** بلوك — المتبقي **{_cards_remain:,}** يظهر في الجدول التفصيلي أدناه")
    elif st.session_state.lang == "tr":
        st.caption(f"📍 İlk **{_MAX_CARDS}** blok gösteriliyor — Kalan **{_cards_remain:,}** alttaki detaylı tabloda listelenmiştir")
    else:
        st.caption(f"📍 Showing first **{_MAX_CARDS}** blocks — Remaining **{_cards_remain:,}** are listed in the detailed table below")

rows_grid = [_cards_blks[i:i+3] for i in range(0, len(_cards_blks), 3)]
for row_blks in rows_grid:
    cols_ui = st.columns(3)
    for col_ui, blk in zip(cols_ui, row_blks):
        _bidx = chain.blocks.index(blk)
        r = results[_bidx]
        tx_cnt  = r['tx_count']
        avg_gas = (blk.header.gas_used // tx_cnt) if tx_cnt else 0
        col_ui.markdown(f"""
<div class="bc">
  <div class="bn">⛓️ Block #{blk.header.block_number}</div>
  <div class="bh">🔗 hash: {blk.header.block_hash[:22]}…</div>
  <div class="bh">↖️ parent: {blk.header.parent_hash[:22]}…</div>
  <div class="bh">🌳 merkle: {blk.header.merkle_root[:22]}…</div>
  <div class="bi">
    📦 {t('blk_tx')}: <b>{tx_cnt}</b> | ⛽ {t('blk_gas')}: {blk.header.gas_used:,}<br>
    📊 avg gas/tx: {avg_gas:,}<br>
    📏 {t('blk_raw')}: {r['raw_bytes']:,} B | 🗄️ {t('blk_comp')}: {r['compressed_bytes']:,} B<br>
    🛠️ {t('opt_compressed_size')}: <b>{r['optimized_compressed_bytes']:,} B</b><br>
    <span class="br">✅ {t('blk_ratio_lbl')}: {r['ratio_pct']}% | Optimized: {r['optimized_ratio_pct']}%</span>
  </div>
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ══ MERKLE TREE (PLOTLY INTERACTIVE) ══════════════════════════
if show_merkle and chain.blocks:
    _blk_nums = [b.header.block_number for b in chain.blocks]
    _col_mh, _col_ms = st.columns([3, 2])
    with _col_mh:
        st.markdown(t("section_merkle"))
    with _col_ms:
        _sel_blk = st.selectbox(
            t("merkle_block_select"),
            options=_blk_nums,
            index=0,
            key="merkle_blk_sel"
        )
    merkle_blk = next((b for b in chain.blocks if b.header.block_number == _sel_blk), chain.blocks[0])
    s_txs = merkle_blk.transactions[:min(16, len(merkle_blk.transactions))]
    
    st.markdown(f"""
    <div class="tip tip-g">
      <div class="tip-h">{t('tip_merkle_h')}</div>
      <div class="tip-t">{t('tip_merkle')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if len(s_txs) < 2:
        st.warning("⚠️ This block has only 1 transaction. Merkle tree cannot be visualised.")
    else:
        root, tree_levels = MerkleTree.build(s_txs)
        if tree_levels:
            def make_plotly_merkle_tree(tree_levels):
                L = len(tree_levels)
                coords = {}
                n_leaves = len(tree_levels[0])
                for ni in range(n_leaves):
                    coords[f"L0N{ni}"] = (ni - (n_leaves - 1) / 2, 0)
                for li in range(1, L):
                    level = tree_levels[li]
                    for ni in range(len(level)):
                        c1_id = f"L{li-1}N{2*ni}"
                        c2_id = f"L{li-1}N{2*ni+1}"
                        if c1_id in coords:
                            x1, y1 = coords[c1_id]
                            if c2_id in coords:
                                x2, y2 = coords[c2_id]
                                x = (x1 + x2) / 2
                            else:
                                x = x1
                        else:
                            x = ni - (len(level) - 1) / 2
                        coords[f"L{li}N{ni}"] = (x, li)
                
                edge_x = []
                edge_y = []
                node_x = []
                node_y = []
                node_text = []
                node_hover = []
                node_color = []
                
                for li in range(L):
                    level = tree_levels[li]
                    for ni in range(len(level)):
                        nid = f"L{li}N{ni}"
                        if nid not in coords:
                            continue
                        x, y = coords[nid]
                        node_x.append(x)
                        node_y.append(y)
                        h_val = level[ni]
                        node_text.append(h_val[:6] + "…")
                        node_hover.append(f"Level {li} | Index {ni}<br>Full Hash: {h_val}")
                        if li == L - 1:
                            node_color.append("#10b981") # root green
                        elif li == 0:
                            node_color.append("#00f2fe") # leaf cyan
                        else:
                            node_color.append("#f59e0b") # branch gold
                        
                        if li > 0:
                            c1_id = f"L{li-1}N{2*ni}"
                            c2_id = f"L{li-1}N{2*ni+1}"
                            if c1_id in coords:
                                cx, cy = coords[c1_id]
                                edge_x.extend([x, cx, None])
                                edge_y.extend([y, cy, None])
                            if c2_id in coords:
                                cx, cy = coords[c2_id]
                                edge_x.extend([x, cx, None])
                                edge_y.extend([y, cy, None])
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=1.5, color="rgba(148, 163, 184, 0.4)"),
                    hoverinfo='skip', mode='lines'
                ))
                fig.add_trace(go.Scatter(
                    x=node_x, y=node_y, mode='markers+text', hoverinfo='text',
                    text=node_text, textposition="top center", hovertext=node_hover,
                    marker=dict(color=node_color, size=24, line=dict(width=2, color="#090d16")),
                    textfont=dict(color="#ffffff", size=9)
                ))
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=max(320, L * 65 + 50),
                    showlegend=False
                )
                return fig

            st.plotly_chart(make_plotly_merkle_tree(tree_levels), use_container_width=True)
            st.info(f"{t('merkle_root_lbl')} `{root}`")
    st.markdown("---")

# ══ DELTA ENCODING VISUALIZATION (PLOTLY) ══════════════════════
st.markdown(t("section_delta"))
st.markdown(f"""
<div class="tip tip-o">
  <div class="tip-h">{t('tip_delta_h')}</div>
  <div class="tip-t">{t('tip_delta')}</div>
</div>
""", unsafe_allow_html=True)

mid_blk = chain.blocks[len(chain.blocks)//2] if chain.blocks else None
if mid_blk and len(mid_blk.transactions) > 1:
    s_txs2  = mid_blk.transactions[:min(80, len(mid_blk.transactions))]
    gp_vals = [tx.gas_price for tx in s_txs2]
    gp_dlts = [0]+[gp_vals[i]-gp_vals[i-1] for i in range(1,len(gp_vals))]
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        fig_abs = go.Figure()
        fig_abs.add_trace(go.Scatter(
            x=list(range(len(gp_vals))), y=gp_vals,
            mode='lines+markers', name='Gas Price',
            line=dict(color='#00f2fe', width=2),
            marker=dict(size=4)
        ))
        fig_abs.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Cairo"),
            xaxis=dict(showgrid=True, gridcolor="#1a2a40", title=t("delta_tx_x")),
            yaxis=dict(showgrid=True, gridcolor="#1a2a40", title=t("delta_gp_y")),
            title=dict(text=f"{t('delta_full')} (Block #{mid_blk.header.block_number})", font=dict(size=14, color="#ffffff")),
            margin=dict(l=20, r=20, t=45, b=20),
            height=320
        )
        st.plotly_chart(fig_abs, use_container_width=True)
        
    with col_d2:
        fig_diff = go.Figure()
        colors = ['#10b981' if d >= 0 else '#ef5350' for d in gp_dlts]
        fig_diff.add_trace(go.Bar(
            x=list(range(len(gp_dlts))), y=gp_dlts,
            marker_color=colors, name='Delta'
        ))
        fig_diff.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Cairo"),
            xaxis=dict(showgrid=True, gridcolor="#1a2a40", title=t("delta_tx_x")),
            yaxis=dict(showgrid=True, gridcolor="#1a2a40", title=t("delta_d_y")),
            title=dict(text=t("delta_diff"), font=dict(size=14, color="#ffffff")),
            margin=dict(l=20, r=20, t=45, b=20),
            height=320
        )
        st.plotly_chart(fig_diff, use_container_width=True)

    if use_delta:
        dr = DeltaEncoder.measure(s_txs2)
        ca, cb, cc = st.columns(3)
        ca.metric(t("delta_raw_m"),  f"{dr['raw_size']:,} B")
        cb.metric(t("delta_enc_m"),  f"{dr['encoded_size']:,} B")
        cc.metric(t("delta_save_m"), f"{dr['saving_pct']}%")

st.markdown("---")

# ══ DETAILED BLOCK DATA TABLE ═════════════════════════════════
st.markdown(t("section_table"))
disp = res_df[[
    "block_number", "tx_count", "header_size", "raw_bytes", "compressed_bytes", "optimized_compressed_bytes",
    "ratio_pct", "optimized_ratio_pct", "cumulative_raw_kb", "cumulative_comp_kb", "cumulative_opt_comp_kb",
    "n_clusters", "time_ms"
]].copy()

disp.columns = [
    t("tbl_blknum"), t("tbl_tx"), t("tbl_hdr"), t("tbl_raw"), t("tbl_comp"), t("opt_compressed_size"),
    t("tbl_ratio"), t("opt_saving_pct"), t("tbl_cum_raw"), t("tbl_cum_comp"), "Opt Cum (KB)",
    t("tbl_clusters"), t("tbl_time")
]
st.dataframe(disp, use_container_width=True, hide_index=True)

col_dl, _ = st.columns([1.5, 3])
with col_dl:
    csv_data = disp.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label=t("export_btn"),
        data=csv_data,
        file_name="blockchain_optimization_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.caption(t("export_caption"))

st.markdown("---")

# ══ CRYPTOGRAPHIC INTEGRITY VERIFICATION ═══════════════════════
st.markdown(t("section_verify"))
st.markdown(f"""
<div class="tip tip-g">
  <div class="tip-h">{t('tip_verify_h')}</div>
  <div class="tip-t">{t('tip_verify')}</div>
</div>
""", unsafe_allow_html=True)

verify_result = chain.verify_chain()
cv1, cv2 = st.columns([3, 1])
with cv2:
    st.metric(t("verify_checked"), verify_result["checked"])
with cv1:
    if verify_result["valid"]:
        st.success(t("verify_ok"))
    else:
        st.error(t("verify_fail"))
        for err in verify_result["errors"]:
            st.code(err, language=None)

st.markdown("---")

# ══ LATEX ACADEMIC FORMULATIONS SECTION ════════════════════════
st.markdown(f"### {t('latex_formulas')}")
exp_latex = st.expander("🎓 Open Mathematical Formulations | عرض النماذج الرياضية الأكاديمية", expanded=False)
with exp_latex:
    st.markdown("""
    #### 1. EIP-1559 Dynamic Base Fee Adjustment Formula
    Under EIP-1559, the base fee per gas ($F$) dynamically updates depending on block congestion. If gas used exceeds the target ($G_{\\text{limit}}/2$), fee increases, else it decreases:
    
    $$F_{t+1} = F_t \\cdot \\left(1 + \\frac{1}{8} \\cdot \\frac{G_{\\text{used}} - G_{\\text{target}}}{G_{\\text{target}}}\\right)$$
    
    #### 2. Delta Encoding and Numeric Reduction
    Delta encoding replaces absolute transaction integers (nonces, gas prices, values) with consecutive differences, dramatically lowering input entropy:
    
    $$D_i = X_i - X_{i-1}, \\quad \\text{where } D_0 = X_0$$
    
    This concentrates frequencies near zero, maximizing Lempel-Ziv-Welch or DEFLATE (zstandard/gzip) dictionary matching.
    
    #### 3. DBSCAN Density-Based Spatial Clustering
    We cluster transaction parameters ($\\{Gas Price, Value, Gas\\}$) in standardized space to locate dense subsets of execution flows:
    
    $$N_\\epsilon(p) = \\{q \\in \\mathcal{D} \\mid \\text{dist}(p, q) \\le \\epsilon\\}$$
    
    If $|N_\\epsilon(p)| \\ge \\text{MinPts}$, node $p$ is marked as core, grouping transactions together before compression.
    
    #### 4. Cryptographic Signature Aggregation (ECDSA vs. BLS)
    Standard signatures store separate ECDSA proofs per transaction ($N \\times 65$ bytes). BLS aggregates all signatures into a single proof:
    
    $$\\sigma_{\\text{agg}} = \\prod_{i=1}^N \\sigma_i \\quad \\implies \\quad S_{\\text{agg}} = 96 \\text{ bytes} \\quad (O(1))$$
    
    The net space saved in bytes is:
    
    $$\\Delta S_{\\text{sig}} = (65 \\cdot N) - 96 \\text{ bytes}$$
    
    #### 5. Field Serialization Savings (RLP / Varint Encoding)
    Replacing fixed-width integers with Recursive Length Prefix (RLP) or Variable-length integers (Varint) reduces field headers:
    
    $$\\Delta S_{\\text{field}} \\approx 40 \\cdot N \\text{ bytes}$$
    """)

st.markdown("---")

# ══ THESIS REPORT EXPORTER WIDGET ══════════════════════════════
st.markdown(f"### {t('thesis_exporter')}")
st.info(t("thesis_desc"))

tab_ar, tab_tr, tab_en = st.tabs(["🇸🇦 المسودة العربية", "🇹🇷 Türkçe Taslak", "🇬🇧 English Draft"])

with tab_en:
    english_thesis = f"""# Thesis Chapter: Experimental Results & Storage Optimization Analysis

## 1. Project Title
**Decision Support System for Blockchain Storage Optimization and Ledger Size Reduction**

## 2. Abstract
As blockchain networks scale, ledger size inflation presents a significant challenge to node synchronization, decentralization, and hardware costs. This graduation thesis presents a comprehensive storage optimization framework and Decision Support System (DSS) tailored to compress and optimize blockchain transaction histories. 

By applying standard dynamic fee transaction sorting (EIP-1559) and combining Delta Encoding with spatial density clustering using DBSCAN, we successfully group similar transaction signatures and parameters to achieve higher compression ratios under standard compression algorithms ({comp_method}). 

To push the theoretical limits of ledger size reduction, we further integrated models for BLS Signature Aggregation and RLP/Varint Field Serialization. The simulation processed {summary['total_tx']} transactions across {summary['n_blocks']} blocks. The raw ledger size of {summary['total_raw_kb']:.1f} KB was reduced to {summary['total_comp_kb']:.1f} KB under standard compression (a saving of {summary['chain_ratio_pct']}%). With signature aggregation and field optimization enabled, the ledger was compressed to {summary['total_opt_comp_kb']:.1f} KB, achieving an overall optimization of {summary['opt_chain_ratio_pct']}% (saving {summary['opt_saved_kb']:.1f} KB). These findings confirm the viability of off-chain clustering combined with cryptographic aggregation as a standard layer-1 or layer-2 storage optimization paradigm.

## 3. Results Summary Table
| Metric | Standard Value | Optimized Value | Improvement (%) |
| :--- | :---: | :---: | :---: |
| Ledger Size | {summary['total_raw_kb']:.1f} KB | {summary['total_opt_comp_kb']:.1f} KB | {summary['opt_chain_ratio_pct']}% |
| Signature Space | {summary['ecdsa_sig_bytes_kb']:.1f} KB | {summary['bls_sig_bytes_kb']:.1f} KB | {round((1 - summary['bls_sig_bytes_kb']/summary['ecdsa_sig_bytes_kb'])*100, 2) if summary['ecdsa_sig_bytes_kb'] > 0 else 0}% |
| Field Overhead Savings | 0 KB | {summary['field_comp_saved_kb']:.1f} KB | 100% |
"""
    st.code(english_thesis, language="markdown")

with tab_ar:
    arabic_thesis = f"""# فصل الأطروحة: النتائج التجريبية وتحليل تحسين التخزين

## 1. عنوان المشروع
**نظام دعم القرار لتقليل حجم البلوكشين وتخزينها الأمثل**

## 2. الملخص
مع توسع شبكات البلوكشين، يمثل تضخم حجم دفتر الحسابات (Ledger) تحدياً كبيراً لمزامنة العقد، واللامركزية، وتكاليف الأجهزة. تقدم أطروحة التخرج هذه إطار عمل شاملاً لتحسين التخزين ونظام دعم القرار (DSS) المصمم لتقليل وضغط تواريخ معاملات البلوكشين.

من خلال تطبيق الفرز الديناميكي للمعاملات بناءً على أسعار الغاز (EIP-1559) ودمج ترميز الدلتا (Delta Encoding) مع التجميع المكاني الكثيف باستخدام DBSCAN، نجحنا في تجميع توقيعات ومعاملات المعاملات المتشابهة لتحقيق معدلات ضغط أعلى تحت خوارزميات الضغط القياسية ({comp_method}).

لتجاوز الحدود النظرية لتقليل حجم دفتر الحسابات، قمنا بدمج نماذج تجميع التوقيعات (BLS Signature Aggregation) وتحسين حقول التسلسل RLP/Varint. قامت المحاكاة بمعالجة {summary['total_tx']} معاملة موزعة على {summary['n_blocks']} بلوك. تم تقليص حجم دفتر الحسابات الخام من {summary['total_raw_kb']:.1f} KB إلى {summary['total_comp_kb']:.1f} KB تحت الضغط القياسي (توفير بنسبة {summary['chain_ratio_pct']}%). ومع تفعيل تجميع التوقيعات وتحسين الحقول، انخفض حجم دفتر الحسابات إلى {summary['total_opt_comp_kb']:.1f} KB، محققاً تحسيناً كلياً بنسبة {summary['opt_chain_ratio_pct']}% (توفير {summary['opt_saved_kb']:.1f} KB). تؤكد هذه النتائج جدوى دمج التجميع خارج الشبكة (off-chain clustering) مع التجميع التشفيري كأداة قياسية لتحسين التخزين في الطبقة الأولى أو الثانية.

## 3. جدول ملخص النتائج
| المقياس | القيمة القياسية | القيمة المحسّنة | نسبة التحسن (%) |
| :--- | :---: | :---: | :---: |
| حجم دفتر الحسابات | {summary['total_raw_kb']:.1f} KB | {summary['total_opt_comp_kb']:.1f} KB | {summary['opt_chain_ratio_pct']}% |
| مساحة التوقيعات | {summary['ecdsa_sig_bytes_kb']:.1f} KB | {summary['bls_sig_bytes_kb']:.1f} KB | {round((1 - summary['bls_sig_bytes_kb']/summary['ecdsa_sig_bytes_kb'])*100, 2) if summary['ecdsa_sig_bytes_kb'] > 0 else 0}% |
| توفير ترميز الحقول | 0 KB | {summary['field_comp_saved_kb']:.1f} KB | 100% |
"""
    st.code(arabic_thesis, language="markdown")

with tab_tr:
    turkish_thesis = f"""# Tez Bölümü: Deneysel Sonuçlar ve Depolama Optimizasyonu Analizi

## 1. Proje Başlığı
**Blokzincir Boyut Azaltma ve Depolama Optimizasyonu Karar Destek Sistemi**

## 2. Özet
Blokzincir ağları büyüdükçe, defter (ledger) boyutunun şişmesi düğüm senkronizasyonu, merkeziyetsizlik ve donanım maliyetleri açısından ciddi bir sorun teşkil etmektedir. Bu mezuniyet tezi, blokzincir işlem geçmişlerini sıkıştırmak ve optimize etmek amacıyla geliştirilmiş kapsamlı bir depolama optimizasyon çerçevesi ve Karar Destek Sistemi (DSS) sunmaktadır.

EIP-1559 standartlarına göre gas ücreti öncelikli paketleme yapılmış ve Delta Kodlama (Delta Encoding) ile DBSCAN yoğunluk tabanlı kümeleme algoritmaları entegre edilmiştir. Bu sayede benzer imzalar ve işlem parametreleri gruplanarak standart sıkıştırma algoritmaları ({comp_method}) altında daha yüksek sıkıştırma oranları elde edilmiştir.

Defter boyutu azaltmanın teorik sınırlarını zorlamak amacıyla, BLS İmza Toplulaştırma (BLS Signature Aggregation) ve RLP/Varint Alan Serileştirme modelleri entegre edilmiştir. Simülasyon kapsamında {summary['n_blocks']} blokta toplam {summary['total_tx']} işlem işlenmiştir. {summary['total_raw_kb']:.1f} KB olan ham defter boyutu standart sıkıştırma ile {summary['total_comp_kb']:.1f} KB değerine düşürülmüştür (yüzde {summary['chain_ratio_pct']} tasarruf). İmza toplulaştırma ve alan optimizasyonu etkinleştirildiğinde ise defter boyutu {summary['total_opt_comp_kb']:.1f} KB değerine düşerek yüzde {summary['opt_chain_ratio_pct']} optimizasyon (toplam {summary['opt_saved_kb']:.1f} KB depolama tasarrufu) sağlanmıştır. Bu bulgular, zincir dışı kümeleme ve kriptografik toplulaştırmanın birinci veya ikinci katman depolama optimizasyonlarında kullanılabilirliğini kanıtlamaktadır.

## 3. Sonuçlar Özet Tablosu
| Metrik | Standart Değer | Optimize Değer | İyileştirme (%) |
| :--- | :---: | :---: | :---: |
| Defter Boyutu | {summary['total_raw_kb']:.1f} KB | {summary['total_opt_comp_kb']:.1f} KB | {summary['opt_chain_ratio_pct']}% |
| İmza Alanı | {summary['ecdsa_sig_bytes_kb']:.1f} KB | {summary['bls_sig_bytes_kb']:.1f} KB | {round((1 - summary['bls_sig_bytes_kb']/summary['ecdsa_sig_bytes_kb'])*100, 2) if summary['ecdsa_sig_bytes_kb'] > 0 else 0}% |
| Alan Optimizasyonu Tasarrufu | 0 KB | {summary['field_comp_saved_kb']:.1f} KB | 100% |
"""
    st.code(turkish_thesis, language="markdown")

st.markdown("---")

# ══ FINAL SUMMARY SUCCESS MESSAGE ═════════════════════════════
st.markdown(t("section_final"))
col_a, col_b = st.columns(2)
with col_a:
    st.markdown(t("before_comp"))
    st.metric(t("total_raw_m"),  f"{summary['total_raw_kb']:,.1f} KB",
              f"= {summary['total_raw_mb']:.4f} MB")
    st.metric(t("n_blocks_m"),   summary["n_blocks"])
    st.metric(t("total_tx_m"),   f"{summary['total_tx']:,}")
with col_b:
    st.markdown(t("after_comp"))
    st.metric(t("total_comp_m"), f"{summary['total_comp_kb']:,.1f} KB",
              f"- {summary['saved_kb']:,.1f} KB {t('saved_m_lbl')}")
    st.metric(t("chain_ratio_m"), f"{summary['chain_ratio_pct']}%")
    st.metric(t("avg_ratio_m"),   f"{summary['avg_ratio_pct']}%")

st.success(t("success_msg",
    n_blocks=summary["n_blocks"],
    total_tx=summary["total_tx"],
    raw=summary["total_raw_kb"],
    comp=summary["total_comp_kb"],
    ratio=summary["chain_ratio_pct"],
    saved=summary["saved_kb"]
))
