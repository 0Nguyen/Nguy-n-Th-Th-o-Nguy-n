from __future__ import annotations

import streamlit as st

from scripts.i18n import t


def _show_table(title, table):
    st.subheader(title)
    if table is not None and len(table) > 0:
        st.dataframe(table, use_container_width=True, height=360)
    else:
        st.info(t("no_data"))


def render_report_view(final_report, tool_results, excel_bytes):
    overview = final_report.get("overview", {}) or {}
    tables = final_report.get("tables", {}) or {}

    st.subheader(t("report_title"))
    metrics = [
        (t("kpi_insured_patients"), overview.get("so_benh_nhan_co_bao_hiem__insured_patient_count", 0)),
        (t("kpi_doctors"), overview.get("so_bac_si_co_chi_dinh_cho_benh_nhan_co_bao_hiem__doctor_count_for_insured_patients", 0)),
        (t("kpi_orders_for_insured"), overview.get("tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients", 0)),
        (t("kpi_out_per_insured"), overview.get("ngoai_bao_hiem_tren_benh_nhan_co_bao_hiem__out_of_insurance_per_insured_patient", 0)),
        (t("kpi_covered"), overview.get("chi_dinh_duoc_bao_hiem_chi_tra__covered_by_insurance_orders", 0)),
        (t("kpi_out_of_insurance"), overview.get("chi_dinh_ngoai_bao_hiem__out_of_insurance_orders", 0)),
        (t("kpi_out_rate"), overview.get("ty_le_ngoai_bao_hiem__out_of_insurance_rate", "0.00%")),
        (t("kpi_out_amount"), overview.get("chi_phi_ngoai_bao_hiem_cua_benh_nhan_co_bao_hiem__out_of_insurance_amount_vnd", 0)),
    ]

    for row_start in range(0, len(metrics), 4):
        row_metrics = metrics[row_start:row_start + 4]
        cols = st.columns(4)
        for col, (label, value) in zip(cols, row_metrics):
            col.metric(label, value)

    _show_table(t("table_overview"), tables.get("overview"))
    _show_table(t("table_by_doctor"), tables.get("by_doctor"))
    _show_table(t("table_by_department"), tables.get("by_department"))
    _show_table(t("table_doctor_outlier"), tables.get("doctor_outlier_table"))
    _show_table(t("table_high_cost"), tables.get("high_cost_procedure_table"))
    _show_table(t("table_icd_flags"), tables.get("required_icd_flags"))
    _show_table(t("table_false_red_flag"), tables.get("false_red_flag_context_table"))
    if tables.get("case_evidence_table") is not None and len(tables.get("case_evidence_table")) > 0:
        _show_table(t("case_evidence_title"), tables.get("case_evidence_table"))

    with st.expander(t("tool_status"), expanded=False):
        for result in tool_results:
            st.write(f"**{result.get('tool_name')}** - {result.get('status')}")
            for note in result.get("notes", []):
                st.write(f"- {note}")

    st.download_button(
        label=t("download_excel"),
        data=excel_bytes,
        file_name="over_ordering_sentinel_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
