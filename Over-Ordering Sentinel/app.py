from __future__ import annotations

import streamlit as st

from scripts.dispatcher import run_pipeline
from scripts.excel_exporter import export_report_to_excel
from scripts.i18n import t
from scripts.report_composer import compose_report
from ui.about_panel import render_about_panel
from ui.auth_gate import require_optional_password
from ui.help_panel import render_help_panel
from ui.layout import render_header, render_sidebar_tools, setup_page
from ui.report_view import render_report_view
from ui.smart_excel_mapper import render_smart_excel_mapper
from ui.upload_panel import render_upload_panel


def main():
    setup_page()
    render_header()
    require_optional_password()
    selected_tools = render_sidebar_tools()
    render_help_panel()
    render_about_panel()
    uploaded = render_upload_panel()

    if uploaded is None:
        st.stop()

    df, mapper_meta = render_smart_excel_mapper(uploaded)
    if df is None:
        st.stop()

    tools_signature = "-".join(selected_tools) if selected_tools else "all"
    mapping_signature = mapper_meta.get("mapping_signature", "mapping")
    analysis_key = f"analysis_result_{mapper_meta.get('file_hash', 'unknown')}_{mapper_meta.get('selected_sheet', 'sheet')}_{mapping_signature}_{tools_signature}"
    if analysis_key not in st.session_state:
        with st.spinner(t("analyzing_data")):
            tool_results = run_pipeline(df, selected_tools)
            final_report = compose_report(tool_results)
            excel_bytes = export_report_to_excel(final_report)
            st.session_state[analysis_key] = {
                "final_report": final_report,
                "tool_results": tool_results,
                "excel_bytes": excel_bytes,
            }
            st.success(t("analysis_completed"))

    cached = st.session_state.get(analysis_key)
    if cached:
        render_report_view(cached["final_report"], cached["tool_results"], cached["excel_bytes"])


if __name__ == "__main__":
    main()
