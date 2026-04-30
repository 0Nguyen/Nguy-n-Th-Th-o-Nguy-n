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

        sheet_mapping = [
            ("overview", "overview"),
            ("by_doctor", "by_doctor"),
            ("by_department", "by_department"),
            ("doctor_outlier_table", "doctor_outlier_table"),
            ("high_cost_procedure_table", "high_cost_procedure_table"),
            ("required_icd_flags", "required_icd_flags"),
            ("false_red_flag_context_table", "false_red_flag_context_table"),
            ("case_evidence_table", "case_evidence_table"),
        ]

        tables = final_report.get("tables", {}) or {}
        for table_key, sheet_name in sheet_mapping:
            table = tables.get(table_key)
            if table is None or not hasattr(table, "to_excel"):
                continue
            table.to_excel(writer, sheet_name=_safe_sheet_name(sheet_name), index=False)

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
