from __future__ import annotations

from pathlib import Path

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

    sample_path = Path("sample-data/sample_input_multisheet.xlsx")
    if sample_path.exists():
        with open(sample_path, "rb") as f:
            st.download_button(
                t("download_multi_sheet_sample"),
                data=f.read(),
                file_name=sample_path.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    sample_path_single = Path("sample-data/sample_input.xlsx")
    if sample_path_single.exists():
        with open(sample_path_single, "rb") as f:
            st.download_button(
                t("download_sample_excel"),
                data=f.read(),
                file_name=sample_path_single.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    if uploaded is None:
        st.info(t("no_file_uploaded"))
    return uploaded
