from __future__ import annotations

import streamlit as st

from scripts.i18n import SUPPORTED_LANGUAGES, get_language, set_language, t


def setup_page():
    st.set_page_config(page_title=t("app_title"), page_icon="⚕️", layout="wide")
    st.markdown(
        """
        <style>
        .main .block-container { padding-top: 1.25rem; padding-bottom: 2rem; }
        div[data-testid="stFileUploader"] {
            border: 2px dashed #5b7c99;
            border-radius: 16px;
            padding: 12px;
            background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
        }
        .sentinel-card {
            border: 1px solid #d8e2ea;
            border-radius: 16px;
            padding: 16px;
            background: #ffffff;
            box-shadow: 0 1px 6px rgba(20, 40, 60, 0.06);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    st.title(t("app_title"))
    st.caption(t("app_caption"))


def render_sidebar_tools():
    st.sidebar.header(t("sidebar_title"))
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

    st.sidebar.subheader(t("tool_selection_title"))
    selected = []
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
    if "show_about_panel" not in st.session_state:
        st.session_state["show_about_panel"] = False
    if st.sidebar.button(t("about_button_label"), use_container_width=True):
        st.session_state["show_about_panel"] = not bool(st.session_state.get("show_about_panel"))
    if st.session_state.get("show_about_panel"):
        st.sidebar.caption(t("about_panel_title"))
    st.sidebar.divider()
    st.sidebar.caption(t("app_caption"))
    return selected
