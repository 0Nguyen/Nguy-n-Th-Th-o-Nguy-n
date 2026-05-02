from __future__ import annotations

import streamlit as st

from scripts.i18n import get_language, t


def _u(vi: str, en: str) -> str:
    return en if get_language() == "en" else vi


def render_upload_panel():
    st.subheader(t("upload_title"))
    headline = _u("Tải file Excel lên để bắt đầu.", "Upload an Excel file to get started.")
    subhead = _u("Chế độ mặc định: bệnh nhân có bảo hiểm + chỉ định ngoài bảo hiểm.", "Default mode: insured patients + out-of-insurance orders.")
    st.markdown(
        f"""
        <div class="sentinel-card">
            <b>{headline}</b><br>
            {subhead}
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        t("upload_file_label"),
        type=["xlsx", "xls"],
        accept_multiple_files=False,
        help=t("upload_help"),
    )

    if uploaded is None:
        st.info(t("no_file_uploaded"))
    return uploaded
