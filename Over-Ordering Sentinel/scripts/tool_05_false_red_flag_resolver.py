from __future__ import annotations

import pandas as pd

from scripts.text_utils import contains_any


CONTEXT_KEYWORDS = [
    "mo",
    "phau thuat",
    "tien phau",
    "pre op",
    "surgery",
    "operation",
    "noi tru",
    "cap cuu",
    "emergency",
    "inpatient",
]


def _collect_flagged_groups(tool_results):
    groups = []
    for result in tool_results or []:
        tables = result.get("tables", {}) or {}
        doctor_table = tables.get("doctor_outlier_table")
        if doctor_table is not None and not doctor_table.empty:
            for _, row in doctor_table.iterrows():
                if row.get("severity") in {"RED", "ORANGE", "YELLOW"}:
                    groups.append(
                        {
                            "flag_type": "doctor_outlier",
                            "doctor": row.get("ten_bac_si__doctor", ""),
                            "department": row.get("khoa__department", ""),
                            "procedure": "",
                        }
                    )
        proc_table = tables.get("high_cost_procedure_table")
        if proc_table is not None and not proc_table.empty:
            for _, row in proc_table.iterrows():
                if row.get("severity") in {"RED", "ORANGE", "YELLOW"} or row.get("high_cost") or row.get("flag_sensitive_procedure"):
                    groups.append(
                        {
                            "flag_type": "high_cost_procedure",
                            "doctor": row.get("ten_bac_si__doctor", ""),
                            "department": row.get("khoa__department", ""),
                            "procedure": row.get("ten_dich_vu__procedure", ""),
                        }
                    )
    return groups


def run(df, context):
    insured_df = df[df["has_insurance_status"] == "yes"].copy()
    if insured_df.empty:
        return {
            "tool_name": "05 - Gỡ cờ đỏ sai / False red-flag resolver",
            "status": "completed",
            "summary": {},
            "tables": {"false_red_flag_context_table": pd.DataFrame()},
            "notes": ["Không có bệnh nhân có bảo hiểm để phân tích / No insured patients to analyze."],
        }

    flagged_groups = _collect_flagged_groups(getattr(context, "tool_results", []))
    rows = []
    seen = set()

    for group in flagged_groups:
        doctor = group["doctor"]
        department = group["department"]
        procedure = group["procedure"]

        query = insured_df.copy()
        if doctor:
            query = query[query["doctor"] == doctor]
        if department:
            query = query[query["department"] == department]
        if procedure:
            query = query[query["procedure"] == procedure]

        if query.empty:
            context_status = "NO_CONTEXT_FOUND"
            matched_keyword = ""
            evidence_count = 0
        else:
            evidence_count = int(len(query))
            matched_keyword = ""
            context_status = "NO_CONTEXT_FOUND"
            for _, row in query.iterrows():
                combined = " ".join(
                    [
                        str(row.get("procedure", "")),
                        str(row.get("diagnosis_name", "")),
                        str(row.get("diagnosis_code", "")),
                    ]
                )
                for keyword in CONTEXT_KEYWORDS:
                    if contains_any(combined, [keyword]):
                        context_status = "RESOLVED_CONTEXT_PRESENT"
                        matched_keyword = keyword
                        break
                if context_status == "RESOLVED_CONTEXT_PRESENT":
                    break

        key = (group["flag_type"], doctor, department, procedure, context_status)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "flag_type": group["flag_type"],
                "doctor": doctor,
                "department": department,
                "procedure": procedure,
                "context_status": context_status,
                "matched_keyword": matched_keyword,
                "evidence_rows": evidence_count,
            }
        )

    false_red_flag_context_table = pd.DataFrame(rows)
    if false_red_flag_context_table.empty:
        return {
            "tool_name": "05 - Gỡ cờ đỏ sai / False red-flag resolver",
            "status": "completed",
            "summary": {},
            "tables": {"false_red_flag_context_table": pd.DataFrame()},
            "notes": [
                "Chưa có cờ đỏ từ tool trước để đối chiếu context / No red flags from previous tools to resolve.",
                "Tool 05 chỉ đánh dấu RESOLVED_CONTEXT_PRESENT khi tìm thấy context hợp lý trong chỉ định hoặc chẩn đoán / Tool 05 marks RESOLVED_CONTEXT_PRESENT only when it finds a plausible clinical context in the order or diagnosis.",
            ],
        }

    return {
        "tool_name": "05 - Gỡ cờ đỏ sai / False red-flag resolver",
        "status": "completed",
        "summary": {"resolved_rows": int((false_red_flag_context_table["context_status"] == "RESOLVED_CONTEXT_PRESENT").sum())},
        "tables": {"false_red_flag_context_table": false_red_flag_context_table},
        "notes": [
            f"Đã đối chiếu {len(false_red_flag_context_table)} nhóm cờ đỏ với context lâm sàng / Matched {len(false_red_flag_context_table)} flagged groups against clinical context.",
            "RESOLVED_CONTEXT_PRESENT = có context hợp lý; NO_CONTEXT_FOUND = cần hội đồng chuyên môn đánh giá thêm / RESOLVED_CONTEXT_PRESENT means plausible context exists; NO_CONTEXT_FOUND means further expert review is needed.",
        ],
    }
