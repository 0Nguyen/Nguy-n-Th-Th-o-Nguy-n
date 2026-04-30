from __future__ import annotations

from pathlib import Path

import streamlit as st

from scripts.i18n import t


ABOUT_FILE = Path(__file__).resolve().parents[1] / "About this APP .txt"


def _read_about_text() -> str:
    encodings = ("utf-8-sig", "utf-8", "cp1252")
    for encoding in encodings:
        try:
            return ABOUT_FILE.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            return ""
    try:
        return ABOUT_FILE.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def render_about_panel() -> None:
    if not st.session_state.get("show_about_panel", False):
        return

    about_text = _read_about_text()
    if not about_text.strip():
        st.warning("About file not found or could not be read.")
        return

    st.markdown(f"## {t('about_panel_title')}")
    st.caption(t("about_panel_hint"))
    with st.container(border=True):
        st.markdown(about_text)
