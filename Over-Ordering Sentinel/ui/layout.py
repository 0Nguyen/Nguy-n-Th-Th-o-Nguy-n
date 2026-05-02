from __future__ import annotations

import streamlit as st

from scripts.i18n import SUPPORTED_LANGUAGES, get_language, set_language, t


def _u(vi: str, en: str) -> str:
    return en if get_language() == "en" else vi


def setup_page():
    st.set_page_config(
        page_title=t("app_title"),
        page_icon="🇺🇸" if get_language() == "en" else "🇻🇳",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        :root {
            --sentinel-bg: linear-gradient(180deg, #f4f8ff 0%, #ffffff 28%, #f9fbff 100%);
            --sentinel-card: rgba(255, 255, 255, 0.78);
            --sentinel-border: rgba(86, 118, 160, 0.18);
            --sentinel-shadow: 0 14px 38px rgba(32, 54, 88, 0.08);
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: var(--sentinel-bg);
        }

        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            animation: sentinelFadeIn 0.4s ease-out;
        }

        @keyframes sentinelFadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f7f9fd 0%, #eef3fb 100%);
            border-right: 1px solid rgba(80, 102, 130, 0.12);
            overflow-y: scroll;
            scrollbar-gutter: stable;
        }

        [data-testid="stSidebar"]::-webkit-scrollbar {
            width: 10px;
        }

        [data-testid="stSidebar"]::-webkit-scrollbar-track {
            background: rgba(180, 193, 214, 0.20);
        }

        [data-testid="stSidebar"]::-webkit-scrollbar-thumb {
            background: rgba(86, 118, 160, 0.45);
            border-radius: 999px;
            border: 2px solid rgba(247, 249, 253, 0.85);
        }

        [data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover {
            background: rgba(67, 97, 138, 0.62);
        }

        .sentinel-sidebar-hint {
            margin: 0.25rem 0 0.6rem 0;
            padding: 0.55rem 0.7rem;
            border-radius: 12px;
            border: 1px solid rgba(76, 102, 140, 0.14);
            background: linear-gradient(90deg, rgba(76, 102, 140, 0.08), rgba(76, 102, 140, 0.03));
            color: #426086;
            font-size: 0.84rem;
            line-height: 1.35;
        }

        .sentinel-sidebar-title {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            font-weight: 800;
            font-size: 1.15rem;
            letter-spacing: -0.01em;
        }

        .sentinel-sidebar-chevron {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.5rem;
            height: 1.5rem;
            border-radius: 999px;
            background: rgba(73, 108, 170, 0.12);
            color: #315181;
            font-size: 0.95rem;
            box-shadow: inset 0 0 0 1px rgba(73, 108, 170, 0.10);
        }

        [data-testid="stExpander"] {
            border-radius: 18px;
            border: 1px solid rgba(85, 118, 160, 0.18);
            background: linear-gradient(180deg, rgba(255,255,255,0.88), rgba(244,248,255,0.88));
            box-shadow: 0 8px 24px rgba(20, 40, 60, 0.05);
            overflow: hidden;
        }

        [data-testid="stExpander"] details summary {
            background: linear-gradient(90deg, rgba(73,108,170,0.10), rgba(73,108,170,0.03));
            border-bottom: 1px solid rgba(85, 118, 160, 0.12);
            font-weight: 700;
        }

        div[data-testid="stFileUploader"] {
            border: 1.5px dashed rgba(78, 114, 160, 0.42);
            border-radius: 18px;
            padding: 12px;
            background: linear-gradient(180deg, #ffffff 0%, #f6f9ff 100%);
            box-shadow: var(--sentinel-shadow);
        }

        .sentinel-card {
            border: 1px solid var(--sentinel-border);
            border-radius: 18px;
            padding: 16px 18px;
            background: var(--sentinel-card);
            box-shadow: var(--sentinel-shadow);
            backdrop-filter: blur(8px);
        }

        .sentinel-hero {
            padding: 18px 20px;
            border-radius: 22px;
            border: 1px solid rgba(76, 102, 140, 0.14);
            background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(239,246,255,0.92));
            box-shadow: var(--sentinel-shadow);
        }

        .sentinel-hero h1 {
            margin-bottom: 0.1rem;
            letter-spacing: -0.03em;
        }

        .sentinel-pill {
            display: inline-block;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            background: rgba(77, 110, 168, 0.10);
            color: #315181;
            font-size: 0.84rem;
            margin-right: 0.35rem;
        }

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.74);
            border: 1px solid rgba(91, 124, 153, 0.14);
            border-radius: 16px;
            padding: 0.4rem 0.8rem;
            box-shadow: 0 6px 18px rgba(20, 40, 60, 0.05);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: rgba(67, 97, 138, 0.28);
            box-shadow: 0 12px 24px rgba(20, 40, 60, 0.08);
        }

        div[data-testid="stTabs"] [role="tab"] {
            border-radius: 999px;
            padding: 0.45rem 0.9rem;
            margin-right: 0.25rem;
            transition: background-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
        }

        div[data-testid="stTabs"] [role="tab"]:hover {
            background: rgba(80, 116, 170, 0.08);
            transform: translateY(-1px);
        }

        div[data-testid="stTabs"] [aria-selected="true"] {
            background: rgba(73, 108, 170, 0.12);
            color: #274571;
            font-weight: 700;
            border-bottom: 2px solid #4b74b5;
        }

        button[kind="secondary"], button[kind="primary"] {
            border-radius: 14px;
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }

        button[kind="secondary"]:hover, button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 20px rgba(20, 40, 60, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    pill_1 = _u("Analysis filters", "Analysis filters")
    pill_2 = _u("Easy-read report", "Easy-read report")
    st.markdown(
        f"""
        <div class="sentinel-hero">
            <div class="sentinel-pill">{pill_1}</div>
            <div class="sentinel-pill">{pill_2}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title(t("app_title"))
    st.caption(t("app_caption"))


def render_sidebar_tools():
    lang_code = get_language()
    language_labels = list(SUPPORTED_LANGUAGES.values())
    language_codes = list(SUPPORTED_LANGUAGES.keys())
    current_label = SUPPORTED_LANGUAGES.get(lang_code, SUPPORTED_LANGUAGES["vi"])
    selected_label = st.sidebar.selectbox(
        t("language_label"),
        options=language_labels,
        index=language_labels.index(current_label),
        key="language_selector",
    )
    selected_lang = language_codes[language_labels.index(selected_label)]
    st.session_state["language"] = selected_lang
    set_language(selected_lang)

    if "show_about_panel" not in st.session_state:
        st.session_state["show_about_panel"] = False
    if st.sidebar.button(t("about_button_label"), use_container_width=True):
        st.session_state["show_about_panel"] = not bool(st.session_state.get("show_about_panel"))
    if st.session_state.get("show_about_panel"):
        st.sidebar.caption(t("about_panel_title"))

    selected = []
    if not st.session_state.get("analysis_tools_visible", False):
        st.sidebar.caption(
        _u(
            "The tools section appears after you confirm mapping and start analysis.",
            "The tools section appears after you confirm mapping and start analysis.",
        )
        )
        return selected

    st.sidebar.markdown(
        f"""
        <div class="sentinel-sidebar-title">
            <span class="sentinel-sidebar-chevron">▸</span>
            <span>🛠️ {t('sidebar_title')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        f"""
        <div class="sentinel-sidebar-hint">{_u("▾ Kéo xuống để xem thêm bộ lọc và phần mở rộng", "▾ Scroll down for more filters and expanded sections")}</div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.subheader("🔍 " + t("tool_selection_title"))
    options = [
        (t("tool_01_label"), "tool_01_basic_stats"),
        (t("tool_02_label"), "tool_02_doctor_outlier"),
        (t("tool_03_label"), "tool_03_high_cost_procedure"),
        (t("tool_04_label"), "tool_04_required_icd_check"),
        (t("tool_05_label"), "tool_05_false_red_flag_resolver"),
    ]
    for label, key in options:
        if st.sidebar.checkbox(label, value=True, key=f"sidebar_{key}"):
            selected.append(key)

    st.sidebar.divider()
    st.sidebar.caption(
        _u(
            "Default mode: insured patients + out-of-insurance orders. Manual filters let you explore other cohorts, but results must be read according to the selected scope.",
            "Default mode: insured patients + out-of-insurance orders. Manual filters let you explore other cohorts, but results must be read according to the selected scope.",
        )
    )
    st.sidebar.markdown(
        f"""
        <div class="sentinel-sidebar-hint">{_u("▾ Phía dưới còn phần mở rộng và bộ lọc phân tích.", "▾ More analysis filters and expanded sections are below.")}</div>
        """,
        unsafe_allow_html=True,
    )
    return selected
