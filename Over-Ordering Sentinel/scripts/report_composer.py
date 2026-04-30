from __future__ import annotations


def compose_report(tool_results):
    final_report = {"overview": {}, "tables": {}, "tool_results": tool_results, "notes": []}

    for result in tool_results:
        final_report["notes"].extend(result.get("notes", []))
        tables = result.get("tables", {}) or {}

        if "overview" in tables:
            final_report["tables"]["overview"] = tables.get("overview")
        if "by_doctor" in tables:
            final_report["tables"]["by_doctor"] = tables.get("by_doctor")
        if "by_department" in tables:
            final_report["tables"]["by_department"] = tables.get("by_department")
        if "doctor_outlier_table" in tables:
            final_report["tables"]["doctor_outlier_table"] = tables.get("doctor_outlier_table")
        if "high_cost_procedure_table" in tables:
            final_report["tables"]["high_cost_procedure_table"] = tables.get("high_cost_procedure_table")
        if "required_icd_flags" in tables:
            final_report["tables"]["required_icd_flags"] = tables.get("required_icd_flags")
        if "false_red_flag_context_table" in tables:
            final_report["tables"]["false_red_flag_context_table"] = tables.get("false_red_flag_context_table")
        if "case_evidence_table" in tables:
            final_report["tables"]["case_evidence_table"] = tables.get("case_evidence_table")

        summary = result.get("summary") or {}
        if summary and not final_report["overview"]:
            final_report["overview"] = summary

    return final_report
