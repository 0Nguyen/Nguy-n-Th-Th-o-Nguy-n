from __future__ import annotations

from io import BytesIO

import pandas as pd


def _safe_sheet_name(name):
    for ch in ["\\", "/", "*", "[", "]", ":", "?"]:
        name = name.replace(ch, "_")
    return name[:31]


def export_report_to_excel(final_report):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        overview = final_report.get("overview", {}) or {}
        pd.DataFrame([{"Chi so / Metric": k, "Gia tri / Value": v} for k, v in overview.items()]).to_excel(
            writer,
            sheet_name=_safe_sheet_name("TongQuan_Overview"),
            index=False,
        )

        tables = final_report.get("tables", {}) or {}
        sheet_name_overrides = {
            "overview": "overview",
            "by_doctor": "by_doctor",
            "by_department": "by_department",
            "judge_action_table": "Judge_Action",
            "doctor_outlier_table": "doctor_outlier_table",
            "doctor_review_priority_table": "doctor_review_priority",
            "doctor_risk_fingerprint_table": "doctor_risk_fingerprint",
            "doctor_statistical_outlier_table": "doctor_statistical",
            "high_cost_procedure_table": "high_cost_procedure",
            "doctor_procedure_concentration_table": "procedure_concentration",
            "procedure_pareto_table": "procedure_pareto",
            "sensitive_service_by_doctor_table": "sensitive_service",
            "required_icd_flags": "required_icd_flags",
            "icd_mismatch_case_evidence": "icd_mismatch_cases",
            "doctor_icd_mismatch_summary": "doctor_icd_summary",
            "procedure_icd_pair_table": "procedure_icd_pairs",
            "doctor_icd_usage_table": "doctor_icd_usage",
            "false_red_flag_context_table": "false_red_flag_context",
            "case_context_resolution_table": "case_context_resolution",
            "case_evidence_table": "case_evidence_table",
            "review_committee_summary_table": "review_committee_summary",
            "patient_burden_table": "patient_burden",
            "coverage_status_table": "coverage_status",
            "executive_summary_table": "executive_summary",
            "chart_coverage_pie": "chart_coverage_pie",
            "chart_top_doctor_amount": "chart_top_doctor_amount",
            "chart_doctor_scatter": "chart_doctor_scatter",
            "chart_procedure_pareto": "chart_procedure_pareto",
            "chart_top_procedure_amount": "chart_top_procedure_amount",
            "chart_doctor_procedure_heatmap": "chart_doctor_proc_heat",
        }
        preferred_order = [
            "overview",
            "by_doctor",
            "by_department",
            "judge_action_table",
            "doctor_outlier_table",
            "doctor_review_priority_table",
            "doctor_risk_fingerprint_table",
            "doctor_statistical_outlier_table",
            "high_cost_procedure_table",
            "doctor_procedure_concentration_table",
            "procedure_pareto_table",
            "sensitive_service_by_doctor_table",
            "required_icd_flags",
            "icd_mismatch_case_evidence",
            "doctor_icd_mismatch_summary",
            "procedure_icd_pair_table",
            "doctor_icd_usage_table",
            "false_red_flag_context_table",
            "case_context_resolution_table",
            "case_evidence_table",
            "patient_burden_table",
        ]

        used_sheet_names: set[str] = set()

        def _write_table(table_key: str, table):
            if table is None or not hasattr(table, "to_excel"):
                return
            sheet_name = _safe_sheet_name(sheet_name_overrides.get(table_key, table_key))
            original_sheet_name = sheet_name
            suffix = 1
            while sheet_name in used_sheet_names:
                base = original_sheet_name[: max(1, 31 - len(str(suffix)) - 1)]
                sheet_name = _safe_sheet_name(f"{base}_{suffix}")
                suffix += 1
            used_sheet_names.add(sheet_name)
            table.to_excel(writer, sheet_name=sheet_name, index=False)

        for key in preferred_order:
            _write_table(key, tables.get(key))

        for key, table in tables.items():
            if key in preferred_order:
                continue
            _write_table(key, table)

        status_rows = []
        for result in final_report.get("tool_results", []) or []:
            status_rows.append(
                {
                    "Tool": result.get("tool_name"),
                    "Status": result.get("status"),
                    "Notes": " | ".join(str(x) for x in result.get("notes", [])),
                }
            )
        pd.DataFrame(status_rows).to_excel(writer, sheet_name=_safe_sheet_name("ToolStatus"), index=False)

    output.seek(0)
    return output.getvalue()
