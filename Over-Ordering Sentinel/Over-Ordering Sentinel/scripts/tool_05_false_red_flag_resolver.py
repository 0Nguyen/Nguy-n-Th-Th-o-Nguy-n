from __future__ import annotations

import pandas as pd

from scripts.analysis_support import get_context_frames
from scripts.text_utils import contains_any, format_vnd


STRONG_CONTEXT_KEYWORDS = [
    "emergency",
    "cấp cứu",
    "cap cuu",
    "inpatient",
    "nội trú",
    "noi tru",
    "trauma",
    "chấn thương",
    "chan thuong",
    "cancer",
    "tumor",
    "u",
    "stroke",
    "đột quỵ",
    "dot quy",
    "pregnancy",
    "thai",
    "icu",
]

WEAK_CONTEXT_KEYWORDS = [
    "pre-op",
    "pre op",
    "tiền phẫu",
    "tien phau",
    "surgery",
    "operation",
    "phẫu thuật",
    "phau thuat",
]


def _context_status(text: str) -> tuple[str, str]:
    if contains_any(text, STRONG_CONTEXT_KEYWORDS):
        for keyword in STRONG_CONTEXT_KEYWORDS:
            if contains_any(text, [keyword]):
                return "STRONG_CONTEXT", keyword
    if contains_any(text, WEAK_CONTEXT_KEYWORDS):
        for keyword in WEAK_CONTEXT_KEYWORDS:
            if contains_any(text, [keyword]):
                return "WEAK_CONTEXT", keyword
    return "NO_CONTEXT", ""


def _resolution_status(context_status: str) -> str:
    if context_status == "STRONG_CONTEXT":
        return "RESOLVED_CONTEXT_PRESENT"
    if context_status == "WEAK_CONTEXT":
        return "PARTIALLY_RESOLVED_WEAK_CONTEXT"
    return "NO_CONTEXT_FOUND"


def _final_action(resolution_status: str) -> str:
    if resolution_status == "RESOLVED_CONTEXT_PRESENT":
        return "Giữ ca này trong diện xem xét vì có bối cảnh rõ."
    if resolution_status == "PARTIALLY_RESOLVED_WEAK_CONTEXT":
        return "Xem thận trọng; bối cảnh chỉ mới một phần."
    return "Cần xem thủ công; chưa thấy bối cảnh rõ."


def _case_from_row(row, flag_source: str, flag_reason: str, flag_severity: str, source_claim_id: str = "") -> dict:
    combined = " ".join(
        [
            str(row.get("procedure", "")),
            str(row.get("diagnosis_name", "")),
            str(row.get("diagnosis_code", "")),
        ]
    )
    context_status, matched_keyword = _context_status(combined)
    resolution_status = _resolution_status(context_status)
    return {
        "claim_id": row.get("claim_id", source_claim_id),
        "patient": row.get("patient", ""),
        "doctor": row.get("doctor", ""),
        "department": row.get("department", ""),
        "procedure": row.get("procedure", ""),
        "diagnosis_code": row.get("diagnosis_code", ""),
        "diagnosis_name": row.get("diagnosis_name", ""),
        "amount_vnd": format_vnd(row.get("amount", row.get("amount_vnd", 0))),
        "original_flag_source": flag_source,
        "original_flag_reason": flag_reason,
        "original_severity": flag_severity,
        "matched_context_keyword": matched_keyword,
        "context_status": context_status,
        "resolution_status": resolution_status,
        "final_review_action": _final_action(resolution_status),
    }


def _collect_case_rows(context, denominator_df: pd.DataFrame, numerator_df: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    tool_results = getattr(context, "tool_results", []) or []
    for result in tool_results:
        tables = result.get("tables", {}) or {}

        icd_tables = [
            ("required_icd_flags", "Tool 04"),
            ("icd_mismatch_case_evidence", "Tool 04"),
            ("case_evidence_table", "Tool 04"),
        ]
        for table_key, source_label in icd_tables:
            table = tables.get(table_key)
            if table is None or table.empty:
                continue
            for _, row in table.iterrows():
                source_row = {
                    "claim_id": row.get("claim_id", ""),
                    "patient": row.get("patient", ""),
                    "doctor": row.get("doctor", ""),
                    "department": row.get("department", ""),
                    "procedure": row.get("procedure", ""),
                    "diagnosis_code": row.get("diagnosis_code", ""),
                    "diagnosis_name": row.get("diagnosis_name", ""),
                    "amount": row.get("amount_vnd", 0),
                }
                rows.append(_case_from_row(source_row, source_label, row.get("rule_name", row.get("mismatch_type", "ICD review")), row.get("severity", "")))

        doctor_table = tables.get("doctor_outlier_table")
        if doctor_table is not None and not doctor_table.empty and not numerator_df.empty:
            for _, row in doctor_table.iterrows():
                doctor = str(row.get("ten_bac_si__doctor", row.get("doctor", "")))
                department = str(row.get("department", row.get("khoa__department", "")))
                subset = numerator_df.copy()
                if doctor:
                    subset = subset[subset["doctor"].astype(str) == doctor]
                if department:
                    subset = subset[subset["department"].astype(str) == department]
                if subset.empty:
                    subset = denominator_df.copy()
                    if doctor:
                        subset = subset[subset["doctor"].astype(str) == doctor]
                    if department:
                        subset = subset[subset["department"].astype(str) == department]
                if subset.empty:
                    continue
                reason = row.get("review_priority", row.get("severity", "Doctor review"))
                for _, source_row in subset.iterrows():
                    rows.append(
                        _case_from_row(
                            source_row,
                            "Tool 02",
                            f"Doctor review priority: {reason}",
                            row.get("severity", ""),
                        )
                    )

        proc_table = tables.get("high_cost_procedure_table")
        if proc_table is not None and not proc_table.empty and not numerator_df.empty:
            for _, row in proc_table.iterrows():
                doctor = str(row.get("doctor", ""))
                department = str(row.get("department", ""))
                procedure = str(row.get("procedure", ""))
                subset = numerator_df.copy()
                if doctor:
                    subset = subset[subset["doctor"].astype(str) == doctor]
                if department:
                    subset = subset[subset["department"].astype(str) == department]
                if procedure:
                    subset = subset[subset["procedure"].astype(str) == procedure]
                if subset.empty:
                    continue
                reason = row.get("review_reason", "Procedure review")
                for _, source_row in subset.iterrows():
                    rows.append(
                        _case_from_row(
                            source_row,
                            "Tool 03",
                            reason,
                            row.get("severity", ""),
                        )
                    )

    return rows


def run(df, context):
    scope, denominator_df, numerator_df, reference_df = get_context_frames(df, context)
    denominator_df = denominator_df if denominator_df is not None else pd.DataFrame()
    numerator_df = numerator_df if numerator_df is not None else pd.DataFrame()

    if denominator_df.empty and numerator_df.empty:
        empty = pd.DataFrame()
        return {
            "tool_name": "05 - Gỡ cờ đỏ theo bối cảnh",
            "status": "completed",
            "summary": {"total_flags_reviewed": 0, "resolved_count": 0, "partially_resolved_count": 0, "unresolved_count": 0, "unresolved_rate": 0},
            "tables": {
                "false_red_flag_context_table": empty,
                "case_context_resolution_table": empty,
            },
            "notes": ["No rows were available for context resolution."],
        }

    case_rows = _collect_case_rows(context, denominator_df, numerator_df)
    case_context_resolution_table = pd.DataFrame(case_rows)
    if case_context_resolution_table.empty:
        empty = pd.DataFrame()
        return {
            "tool_name": "05 - Gỡ cờ đỏ theo bối cảnh",
            "status": "completed",
            "summary": {"total_flags_reviewed": 0, "resolved_count": 0, "partially_resolved_count": 0, "unresolved_count": 0, "unresolved_rate": 0},
            "tables": {
                "false_red_flag_context_table": empty,
                "case_context_resolution_table": empty,
            },
            "notes": [
                "No flagged cases were available from previous tools.",
                "Tool 05 only classifies context; it does not remove or overwrite any flags.",
            ],
        }

    false_red_flag_context_table = (
        case_context_resolution_table.groupby(["original_flag_source", "doctor", "department", "procedure"], dropna=False)
        .agg(
            total_flags=("claim_id", "count"),
            resolved_count=("resolution_status", lambda s: int((s == "RESOLVED_CONTEXT_PRESENT").sum())),
            partially_resolved_count=("resolution_status", lambda s: int((s == "PARTIALLY_RESOLVED_WEAK_CONTEXT").sum())),
            unresolved_count=("resolution_status", lambda s: int((s == "NO_CONTEXT_FOUND").sum())),
        )
        .reset_index()
    )
    false_red_flag_context_table["unresolved_rate"] = false_red_flag_context_table.apply(
        lambda row: row["unresolved_count"] / row["total_flags"] if row["total_flags"] else 0,
        axis=1,
    )

    summary = {
        "total_flags_reviewed": int(len(case_context_resolution_table)),
        "resolved_count": int((case_context_resolution_table["resolution_status"] == "RESOLVED_CONTEXT_PRESENT").sum()),
        "partially_resolved_count": int((case_context_resolution_table["resolution_status"] == "PARTIALLY_RESOLVED_WEAK_CONTEXT").sum()),
        "unresolved_count": int((case_context_resolution_table["resolution_status"] == "NO_CONTEXT_FOUND").sum()),
        "unresolved_rate": float((case_context_resolution_table["resolution_status"] == "NO_CONTEXT_FOUND").mean()),
    }

    return {
        "tool_name": "05 - Gỡ cờ đỏ theo bối cảnh",
        "status": "completed",
        "summary": summary,
        "tables": {
            "false_red_flag_context_table": false_red_flag_context_table,
            "case_context_resolution_table": case_context_resolution_table,
        },
        "notes": [
            "Tool 05 reclassifies flagged cases by context only; it does not delete or confirm any flag.",
            "Bối cảnh mạnh sẽ đưa ca về diện hỗ trợ rà soát, bối cảnh yếu chỉ mở một phần, và không có bối cảnh thì vẫn để mở.",
        ],
    }
