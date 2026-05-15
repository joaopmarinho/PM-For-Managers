"""
app.py — Dashboard de Process Mining Multidimensional
Layout 70/30: esquerda (exploração de dados) / direita (motor de mineração)
"""

import io
import json
import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

# ── allow running from the project root ──────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from engine.data_utils import CATEGORY_COL, prepare_dataframe
from engine.miner import run_apriori
from engine.persistence import (
    delete_dataset,
    list_datasets,
    load_dataset,
    save_dataset,
)

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Process Mining Dashboard",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS — dark glassmorphism theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Google Fonts ─────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & global ───────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* App background */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #111827 50%, #0d1520 100%);
    min-height: 100vh;
}

/* ── Header ───────────────────────────────────── */
.app-header {
    background: linear-gradient(90deg, rgba(99,102,241,0.15), rgba(139,92,246,0.10), rgba(236,72,153,0.08));
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    gap: 1rem;
}
.app-header h1 {
    margin: 0;
    font-size: 1.6rem;
    font-weight: 700;
    background: linear-gradient(90deg, #818cf8, #a78bfa, #e879f9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.app-header p {
    margin: 0;
    font-size: 0.82rem;
    color: #94a3b8;
}

/* ── Panel cards ──────────────────────────────── */
.panel-card {
    background: rgba(15,23,42,0.7);
    border: 1px solid rgba(99,102,241,0.18);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(8px);
}
.panel-title {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #818cf8;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

/* ── Section divider ──────────────────────────── */
.section-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,0.4), transparent);
    margin: 1.25rem 0;
}

/* ── Metric chip ──────────────────────────────── */
.metric-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 0.75rem;
}
.metric-chip {
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 8px;
    padding: 0.45rem 0.9rem;
    font-size: 0.78rem;
    color: #c7d2fe;
}
.metric-chip span {
    font-weight: 700;
    color: #a5b4fc;
}

/* ── Severity badges ──────────────────────────── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-illegal   { background: rgba(239,68,68,0.15);  color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); }
.badge-prohibited{ background: rgba(249,115,22,0.15); color: #fdba74; border: 1px solid rgba(249,115,22,0.3); }
.badge-ignored   { background: rgba(234,179,8,0.15);  color: #fde68a; border: 1px solid rgba(234,179,8,0.3); }
.badge-unexpected{ background: rgba(99,102,241,0.15); color: #c7d2fe; border: 1px solid rgba(99,102,241,0.3); }

/* ── Buttons ──────────────────────────────────── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.35) !important;
}

/* Primary button */
div[data-testid="column"] .stButton > button[kind="primary"],
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    color: white !important;
}

/* ── Dataframe ────────────────────────────────── */
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
}

/* ── Slider ───────────────────────────────────── */
.stSlider [data-baseweb="slider"] {
    margin-top: 0.25rem;
}

/* ── Multiselect tags ─────────────────────────── */
.stMultiSelect [data-baseweb="tag"] {
    background-color: rgba(99,102,241,0.25) !important;
    border-color: rgba(99,102,241,0.4) !important;
}

/* ── Upload zone ──────────────────────────────── */
.stFileUploader {
    border-radius: 12px;
}

/* ── Info/success/warning boxes ───────────────── */
.stAlert {
    border-radius: 10px;
}

/* ── Relevance table rows ─────────────────────── */
.rule-row {
    background: rgba(15,23,42,0.8);
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 10px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.6rem;
    transition: border-color 0.2s;
}
.rule-row:hover {
    border-color: rgba(99,102,241,0.4);
}
.rule-ant {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #a5b4fc;
    margin-bottom: 0.3rem;
}
.rule-arrow {
    color: #475569;
    margin: 0 0.3rem;
}
.rule-cons {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #f1f5f9;
}
.rule-metrics {
    display: flex;
    gap: 0.75rem;
    margin-top: 0.4rem;
    flex-wrap: wrap;
}
.rule-metric {
    font-size: 0.7rem;
    color: #64748b;
}
.rule-metric b {
    color: #94a3b8;
}
.rel-score {
    float: right;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    font-weight: 700;
    font-size: 0.78rem;
    padding: 3px 10px;
    border-radius: 6px;
}

/* ── No-data placeholder ──────────────────────── */
.empty-state {
    text-align: center;
    padding: 2rem 1rem;
    color: #475569;
    font-size: 0.88rem;
}
.empty-state .icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "active_df": None,
        "active_name": None,
        "active_id": None,
        "search_query": "",
        "page_idx": 0,
        "mining_result": None,
        "selected_cols": [],
        "min_support": 0.05,
        "min_confidence": 0.80,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()

PAGE_SIZE = 10

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _severity_badge(category: str) -> str:
    cat_lower = category.lower()
    if "illegal" in cat_lower:
        css = "badge-illegal"
    elif "prohibited" in cat_lower:
        css = "badge-prohibited"
    elif "ignored" in cat_lower:
        css = "badge-ignored"
    else:
        css = "badge-unexpected"
    return f'<span class="badge {css}">{category}</span>'


def _load_default_csv():
    """Pre-load the bundled report.csv if no dataset exists."""
    default = os.path.join(os.path.dirname(__file__), "default_dataset.csv")
    if not os.path.exists(default):
        return
    if list_datasets():
        return  # already have data
    try:
        df = pd.read_csv(default)
        save_dataset("report_default.csv", df)
    except Exception:
        pass


_load_default_csv()


def _set_active(dataset_id: int, name: str):
    df = load_dataset(dataset_id)
    st.session_state.active_df = prepare_dataframe(df)
    st.session_state.active_name = name
    st.session_state.active_id = dataset_id
    st.session_state.page_idx = 0
    st.session_state.search_query = ""
    st.session_state.mining_result = None
    # default col selection
    available = [c for c in df.columns if c != CATEGORY_COL]
    st.session_state.selected_cols = available[:1] if available else []


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="app-header">
    <div>
        <h1>⛏️ Process Mining Dashboard</h1>
        <p>Mineração Multidimensional de Regras de Associação · Algoritmo Apriori · Priorização Likert (Definição 18)</p>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Layout: 70 / 30
# ─────────────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([7, 3], gap="large")

# ═════════════════════════════════════════════════════════════════════════════
# LEFT PANEL  (70%)
# ═════════════════════════════════════════════════════════════════════════════
with col_left:

    # ── Upload ──────────────────────────────────────────────────────────────
    st.markdown('<div class="panel-title">📤 Ingestão de Dados</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Arraste um CSV ou clique para selecionar",
        type=["csv"],
        key="uploader",
        label_visibility="collapsed",
    )
    if uploaded:
        try:
            df_up = pd.read_csv(uploaded)
            ds_id = save_dataset(uploaded.name, df_up)
            st.success(f"✅ **{uploaded.name}** importado com {len(df_up)} linhas.")
            _set_active(ds_id, uploaded.name)
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao importar: {e}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Dataset selector ────────────────────────────────────────────────────
    datasets_meta = list_datasets()

    if not datasets_meta:
        st.markdown(
            '<div class="empty-state"><div class="icon">📂</div>'
            "Nenhum dataset carregado. Faça upload de um CSV acima.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="panel-title">🗄️ Contexto Ativo</div>', unsafe_allow_html=True)

        options_map = {f"{d['filename']} ({d['upload_date']})  [{d['row_count']} linhas]": d["id"]
                       for d in datasets_meta}
        options_list = list(options_map.keys())

        # auto-select first if nothing active
        if st.session_state.active_id is None and datasets_meta:
            _set_active(datasets_meta[0]["id"], datasets_meta[0]["filename"])

        current_key = next(
            (k for k, v in options_map.items() if v == st.session_state.active_id),
            options_list[0],
        )

        col_sel, col_del = st.columns([5, 1])
        with col_sel:
            selected_label = st.selectbox(
                "Dataset ativo",
                options=options_list,
                index=options_list.index(current_key),
                label_visibility="collapsed",
            )
        with col_del:
            if st.button("🗑️", help="Remover dataset", use_container_width=True):
                delete_dataset(options_map[selected_label])
                st.session_state.active_id = None
                st.session_state.active_df = None
                st.rerun()

        new_id = options_map[selected_label]
        if new_id != st.session_state.active_id:
            name = datasets_meta[[d["id"] for d in datasets_meta].index(new_id)]["filename"]
            _set_active(new_id, name)
            st.rerun()

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # ── Data Explorer ────────────────────────────────────────────────────
        df: pd.DataFrame = st.session_state.active_df

        st.markdown('<div class="panel-title">🔍 Data Explorer</div>', unsafe_allow_html=True)

        # Metrics row
        meta = next((d for d in datasets_meta if d["id"] == st.session_state.active_id), {})
        st.markdown(
            f"""
<div class="metric-row">
  <div class="metric-chip">Linhas: <span>{meta.get("row_count","–")}</span></div>
  <div class="metric-chip">Colunas: <span>{len(df.columns)}</span></div>
  <div class="metric-chip">Categorias únicas: <span>{df[CATEGORY_COL].nunique() if CATEGORY_COL in df.columns else "–"}</span></div>
  <div class="metric-chip">Dataset: <span>{meta.get("filename","–")}</span></div>
</div>
""",
            unsafe_allow_html=True,
        )

        # Search
        search = st.text_input(
            "🔎 Filtro global",
            value=st.session_state.search_query,
            placeholder="Buscar em qualquer coluna…",
            key="search_input",
        )
        st.session_state.search_query = search

        # Apply filter
        display_df = df.copy()
        if search:
            mask = display_df.apply(
                lambda col: col.astype(str).str.contains(search, case=False, na=False)
            ).any(axis=1)
            display_df = display_df[mask]

        # Pagination
        total_rows = len(display_df)
        total_pages = max(1, (total_rows + PAGE_SIZE - 1) // PAGE_SIZE)
        page = st.session_state.page_idx
        page = max(0, min(page, total_pages - 1))

        page_df = display_df.iloc[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]

        st.dataframe(
            page_df,
            use_container_width=True,
            height=320,
        )

        # Pagination controls
        p_col1, p_col2, p_col3 = st.columns([1, 3, 1])
        with p_col1:
            if st.button("◀", disabled=page == 0, use_container_width=True):
                st.session_state.page_idx = page - 1
                st.rerun()
        with p_col2:
            st.markdown(
                f'<p style="text-align:center;color:#64748b;font-size:0.8rem;margin-top:0.5rem;">'
                f"Pág. {page + 1} / {total_pages} · {total_rows} linhas"
                f"</p>",
                unsafe_allow_html=True,
            )
        with p_col3:
            if st.button("▶", disabled=page >= total_pages - 1, use_container_width=True):
                st.session_state.page_idx = page + 1
                st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL  (30%)
# ═════════════════════════════════════════════════════════════════════════════
with col_right:

    if st.session_state.active_df is None:
        st.markdown(
            '<div class="empty-state"><div class="icon">⚙️</div>'
            "Carregue um dataset para configurar o motor de mineração.</div>",
            unsafe_allow_html=True,
        )
    else:
        df = st.session_state.active_df
        available_cols = [c for c in df.columns if c != CATEGORY_COL]

        # ── N-dimensional column selector ────────────────────────────────────
        st.markdown('<div class="panel-title">📐 Colunas Antecedentes (N-D)</div>', unsafe_allow_html=True)
        selected = st.multiselect(
            "Selecione as dimensões para o One-Hot Encoding",
            options=available_cols,
            default=st.session_state.selected_cols,
            key="col_selector",
            label_visibility="collapsed",
        )
        st.session_state.selected_cols = selected

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # ── Mining controls ──────────────────────────────────────────────────
        st.markdown('<div class="panel-title">⚙️ Parâmetros de Mineração</div>', unsafe_allow_html=True)

        min_sup = st.slider(
            "Suporte Mínimo",
            min_value=0.01,
            max_value=0.50,
            value=st.session_state.min_support,
            step=0.01,
            format="%.2f",
        )
        st.session_state.min_support = min_sup

        min_conf = st.slider(
            "Confiança Mínima",
            min_value=0.50,
            max_value=1.00,
            value=st.session_state.min_confidence,
            step=0.05,
            format="%.2f",
        )
        st.session_state.min_confidence = min_conf

        if st.button("▶ Executar Mineração", use_container_width=True, type="primary"):
            if not selected:
                st.warning("Selecione ao menos uma coluna antecedente.")
            else:
                with st.spinner("Minerando regras…"):
                    try:
                        result = run_apriori(
                            df,
                            antecedent_cols=selected,
                            min_support=min_sup,
                            min_confidence=min_conf,
                        )
                        st.session_state.mining_result = result
                    except Exception as e:
                        st.error(f"Erro: {e}")

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # ── Results panel ────────────────────────────────────────────────────
        st.markdown(
            '<div class="panel-title">🏅 Relevância (Definição 18 — Likert)</div>',
            unsafe_allow_html=True,
        )

        result = st.session_state.mining_result

        if result is None:
            st.markdown(
                '<div class="empty-state"><div class="icon">🎯</div>'
                "Execute a mineração para ver os resultados.</div>",
                unsafe_allow_html=True,
            )
        else:
            # Stats
            st.markdown(
                f"""
<div class="metric-row">
  <div class="metric-chip">Itemsets: <span>{result['itemsets_count']}</span></div>
  <div class="metric-chip">Regras brutas: <span>{result['rules_count']}</span></div>
  <div class="metric-chip">Regras filtradas: <span>{len(result['scored_df'])}</span></div>
</div>
""",
                unsafe_allow_html=True,
            )

            scored: pd.DataFrame = result["scored_df"]

            if scored.empty:
                st.info("Nenhuma regra encontrada. Reduza os thresholds.")
            else:
                for _, row in scored.iterrows():
                    badge = _severity_badge(row["Categoria da Anomalia"])
                    st.markdown(
                        f"""
<div class="rule-row">
  <span class="rel-score">rel={row['Relevância (rel)']}</span>
  <div class="rule-ant">{row['Antecedentes']}</div>
  <div class="rule-cons">→ {badge}</div>
  <div class="rule-metrics">
    <div class="rule-metric">Suporte: <b>{row['Suporte']:.4f}</b></div>
    <div class="rule-metric">Confiança: <b>{row['Confiança']:.4f}</b></div>
  </div>
</div>
""",
                        unsafe_allow_html=True,
                    )

            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

            # ── Export ───────────────────────────────────────────────────────
            st.markdown('<div class="panel-title">📥 Exportar Relatório</div>', unsafe_allow_html=True)

            report = {
                "metadata": {
                    "dataset": st.session_state.active_name,
                    "dataset_id": st.session_state.active_id,
                    "generated_at": datetime.now().isoformat(),
                },
                "config": {
                    "antecedent_columns": selected,
                    "min_support": min_sup,
                    "min_confidence": min_conf,
                },
                "stats": {
                    "itemsets_count": result["itemsets_count"],
                    "rules_total": result["rules_count"],
                    "rules_filtered": len(result["scored_df"]),
                },
                "rules": scored.to_dict(orient="records") if not scored.empty else [],
            }
            report_json = json.dumps(report, ensure_ascii=False, indent=2)
            report_csv = scored.to_csv(index=False) if not scored.empty else ""

            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "⬇️ JSON",
                    data=report_json,
                    file_name=f"mining_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True,
                )
            with c2:
                st.download_button(
                    "⬇️ CSV",
                    data=report_csv,
                    file_name=f"mining_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    disabled=scored.empty,
                )
