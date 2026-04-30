from __future__ import annotations

import os

import streamlit as st

from scripts.i18n import t


def require_optional_password() -> None:
    expected_password = str(st.session_state.get("APP_ACCESS_PASSWORD_RUNTIME", "")).strip()
    if not expected_password:
        expected_password = os.getenv("APP_ACCESS_PASSWORD", "").strip()

    if not expected_password:
        return

    st.sidebar.markdown(t("access_control_title"))

    entered_password = st.sidebar.text_input(
        t("password_label"),
        type="password",
        placeholder="Enter password",
    )

    if entered_password != expected_password:
        st.warning(t("app_protected_warning"))
        st.stop()

    st.session_state["APP_PASSWORD_AUTHENTICATED"] = True
