from __future__ import annotations

from typing import Any

import pandas as pd

from scripts.i18n import get_language




def _lang() -> str:
    return get_language()


def _u(vi: str, en: str) -> str:
    return en if _lang() == "en" else vi

def _as_int(value, default=0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _as_float(value, default=0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _first_table(tables: dict[str, Any], *keys):
    for key in keys:
        table = tables.get(key)
        if table is not None and hasattr(table, "empty") and not table.empty:
            return table
    return None


def _top_row(table: pd.DataFrame | None):
    if table is None or table.empty:
        return None
    return table.iloc[0]


def _traffic_light(level: str, short_label: str, explanation: str) -> dict:
    return {"level": level, "short_label": short_label, "explanation": explanation}


def _pretty_number(value):
    if value is None or value == "":
        return ""
    if isinstance(value, str):
        return value
    try:
        numeric = float(value)
    except Exception:
        return str(value)
    if 0 <= numeric <= 1:
        return f"{numeric:.1%}"
    if numeric.is_integer():
        return f"{int(numeric):,}"
    return f"{numeric:,.0f}"


def _get_top_doctor(tables):
    doctor_table = _first_table(tables, "doctor_review_priority_table", "doctor_outlier_table")
    row = _top_row(doctor_table)
    if row is None:
        return None
    return {
        "review_target": str(row.get("ten_bac_si__doctor", row.get("doctor", ""))),
        "department": str(row.get("department", row.get("khoa__department", ""))),
        "main_signal": _u(
            f"Điểm rủi ro {row.get('risk_score', row.get('severity', ''))}",
            f"Risk score {row.get('risk_score', row.get('severity', ''))}",
        ),
        "why_flagged": (
            _u(
                f"Bác sĩ có {row.get('numerator_orders', '')} chỉ định tín hiệu; "
                f"tỷ lệ tín hiệu {row.get('numerator_rate', row.get('out_of_insurance_rate', ''))}; "
                f"tiền tín hiệu {row.get('numerator_amount_vnd', '')}.",
                f"The doctor has {row.get('numerator_orders', '')} signal orders; "
                f"signal rate {row.get('numerator_rate', row.get('out_of_insurance_rate', ''))}; "
                f"signal amount {row.get('numerator_amount_vnd', '')}.",
            )
        ),
        "supporting_evidence": (
            _u(
                f"Số dòng nền: {row.get('denominator_orders', '')}; "
                f"số dòng tín hiệu: {row.get('numerator_orders', '')}; "
                f"số tiền tín hiệu: {row.get('numerator_amount_vnd', '')}.",
                f"Baseline rows: {row.get('denominator_orders', '')}; "
                f"signal rows: {row.get('numerator_orders', '')}; "
                f"signal amount: {row.get('numerator_amount_vnd', '')}.",
            )
        ),
        "context_status": str(row.get("review_priority", row.get("severity", ""))),
        "recommended_action": _u("Hội đồng nên xem bác sĩ này trước.", "Review this doctor first."),
        "rank_value": _as_float(row.get("risk_score", 0)),
    }


def _get_top_procedure(tables):
    proc_table = _first_table(tables, "procedure_pareto_table", "high_cost_procedure_table")
    if proc_table is None:
        return None
    row = _top_row(proc_table)
    if row is None:
        return None
    amount = _as_float(row.get("numerator_amount_vnd", row.get("total_amount_vnd", 0)))
    total_amount = _as_float(
        proc_table["numerator_amount_vnd"].sum()
        if "numerator_amount_vnd" in proc_table.columns
        else proc_table["total_amount_vnd"].sum()
    )
    share = amount / total_amount if total_amount else 0.0
    return {
        "review_target": str(row.get("procedure", row.get("ten_dich_vu__procedure", ""))),
        "department": str(row.get("department", row.get("khoa__department", ""))),
        "main_signal": _u(f"Tỷ trọng tiền tín hiệu {share:.1%}", f"Signal amount share {share:.1%}"),
        "why_flagged": (
            _u(
                f"Dịch vụ này có số tiền tín hiệu {amount:,.0f} VND và "
                f"{row.get('numerator_orders', row.get('pair_count', ''))} dòng tín hiệu.",
                f"This procedure has signal amount {amount:,.0f} VND and "
                f"{row.get('numerator_orders', row.get('pair_count', ''))} signal rows.",
            )
        ),
        "supporting_evidence": _u(
            f"Chi phí cao: {row.get('high_cost', '')}; dịch vụ nhạy cảm: {row.get('flag_sensitive_procedure', '')}",
            f"High cost: {row.get('high_cost', '')}; sensitive procedure: {row.get('flag_sensitive_procedure', '')}",
        ),
        "context_status": str(row.get("severity", row.get("alignment_status", ""))),
        "recommended_action": _u("Hội đồng nên xem dịch vụ này trước.", "Review this procedure first."),
        "rank_value": share,
    }


def _get_icd_signal(tables):
    icd_table = _first_table(tables, "doctor_icd_mismatch_summary", "required_icd_flags", "icd_mismatch_case_evidence")
    if icd_table is None:
        return None
    if "mismatch_count" in icd_table.columns:
        row = _top_row(icd_table)
        return {
            "review_target": str(row.get("doctor", "")),
            "department": str(row.get("department", "")),
            "main_signal": _u(
                f"Số tín hiệu ICD không khớp {row.get('mismatch_count', 0)}",
                f"ICD mismatch signals {row.get('mismatch_count', 0)}",
            ),
            "why_flagged": _u(
                f"Có {row.get('mismatch_count', 0)} dòng cần rà ICD / bối cảnh.",
                f"There are {row.get('mismatch_count', 0)} rows needing ICD/context review.",
            ),
            "supporting_evidence": _u(
                f"Thiếu ICD: {row.get('missing_icd_count', 0)}; ICD yếu: {row.get('weak_icd_count', 0)}",
                f"Missing ICD: {row.get('missing_icd_count', 0)}; weak ICD: {row.get('weak_icd_count', 0)}",
            ),
            "context_status": str(row.get("severity", "")),
            "recommended_action": _u("Kiểm tra ICD và chỉ định cho bác sĩ này.", "Check ICD and orders for this doctor."),
            "rank_value": _as_float(row.get("mismatch_count", 0)),
        }
    row = _top_row(icd_table)
    if row is None:
        return None
    return {
        "review_target": str(row.get("procedure", "")),
        "department": str(row.get("department", "")),
        "main_signal": _u(
            f"Rà soát ICD / {str(row.get('mismatch_type', row.get('rule_name', 'ICD review')))}",
            f"ICD review / {str(row.get('mismatch_type', row.get('rule_name', 'ICD review')))}",
        ),
        "why_flagged": _u(str(row.get("note", "")), str(row.get("note", ""))),
        "supporting_evidence": _u(
            f"Hồ sơ {row.get('claim_id', '')}; mức độ {row.get('severity', '')}",
            f"Claim {row.get('claim_id', '')}; severity {row.get('severity', '')}",
        ),
        "context_status": str(row.get("severity", "")),
        "recommended_action": _u("Kiểm tra ICD và bối cảnh của ca này.", "Check the ICD and context for this case."),
        "rank_value": 1.0,
    }


def _get_context_resolution(tables):
    ctx_table = _first_table(tables, "case_context_resolution_table", "false_red_flag_context_table")
    if ctx_table is None:
        return None
    total = len(ctx_table)
    if total == 0:
        return None
    if "resolution_status" in ctx_table.columns:
        resolved = int((ctx_table["resolution_status"] == "RESOLVED_CONTEXT_PRESENT").sum())
        partial = int((ctx_table["resolution_status"] == "PARTIALLY_RESOLVED_WEAK_CONTEXT").sum())
        unresolved = int((ctx_table["resolution_status"] == "NO_CONTEXT_FOUND").sum())
    else:
        resolved = int(ctx_table.get("resolved_count", pd.Series(dtype=float)).sum()) if "resolved_count" in ctx_table.columns else 0
        partial = int(ctx_table.get("partially_resolved_count", pd.Series(dtype=float)).sum()) if "partially_resolved_count" in ctx_table.columns else 0
        unresolved = int(ctx_table.get("unresolved_count", pd.Series(dtype=float)).sum()) if "unresolved_count" in ctx_table.columns else 0
    ratio = resolved / total if total else 0
    return {"total": total, "resolved": resolved, "partial": partial, "unresolved": unresolved, "ratio": ratio}


def _build_committee_table(items: list[dict]) -> pd.DataFrame:
    rows = []
    for rank, item in enumerate(items[:10], start=1):
        rows.append(
            {
                "priority_rank": rank,
                "review_target": item["review_target"],
                "target_type": item["target_type"],
                "department": item.get("department", ""),
                "main_signal": item["main_signal"],
                "why_flagged": item["why_flagged"],
                "supporting_evidence": item["supporting_evidence"],
                "context_status": item["context_status"],
                "recommended_action": item["recommended_action"],
            }
        )
    return pd.DataFrame(rows)


def build_human_summary(final_report: dict) -> dict:
    overview = final_report.get("overview", {}) or {}
    tables = final_report.get("tables", {}) or {}
    human_prev = final_report.get("human_summary", {}) or {}

    current_measure = {
        "preset_name": overview.get("scope_preset_name", human_prev.get("current_measure", {}).get("preset_name", "")),
        "patient_scope": overview.get("patient_scope", human_prev.get("current_measure", {}).get("patient_scope", "")),
        "coverage_scope": overview.get("coverage_scope", human_prev.get("current_measure", {}).get("coverage_scope", "")),
        "denominator_rows": _as_int(overview.get("denominator_rows", overview.get("tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients", 0))),
        "numerator_rows": _as_int(overview.get("numerator_rows", overview.get("chi_dinh_ngoai_bao_hiem__out_of_insurance_orders", 0))),
    }

    doctor_table = _first_table(tables, "doctor_review_priority_table", "doctor_outlier_table")
    proc_table = _first_table(tables, "procedure_pareto_table", "high_cost_procedure_table")
    icd_summary = _first_table(tables, "doctor_icd_mismatch_summary", "required_icd_flags")
    ctx_summary = _get_context_resolution(tables)

    key_numbers = {
        "denominator_rows": current_measure["denominator_rows"],
        "numerator_rows": current_measure["numerator_rows"],
        "numerator_rate": _pretty_number(overview.get("numerator_rate", overview.get("ty_le_ngoai_bao_hiem__out_of_insurance_rate", 0))),
        "numerator_amount": _pretty_number(overview.get("numerator_amount_vnd", overview.get("chi_phi_ngoai_bao_hiem_cua_benh_nhan_co_bao_hiem__out_of_insurance_amount_vnd", 0))),
        "top_doctor": "",
        "top_procedure": "",
        "icd_flags": 0,
    }

    top_doctor = _get_top_doctor(tables)
    top_procedure = _get_top_procedure(tables)
    icd_signal = _get_icd_signal(tables)

    if top_doctor:
        key_numbers["top_doctor"] = top_doctor["review_target"]
    if top_procedure:
        key_numbers["top_procedure"] = top_procedure["review_target"]
    if icd_summary is not None:
        if "mismatch_count" in icd_summary.columns:
            key_numbers["icd_flags"] = int(icd_summary["mismatch_count"].sum())
        elif "mismatch_type" in icd_summary.columns:
            key_numbers["icd_flags"] = int(len(icd_summary))

    doctor_signal = _traffic_light("LOW", "Chưa thấy tín hiệu mạnh", "Chưa có bác sĩ nào nổi bật.")
    if doctor_table is not None and not doctor_table.empty and "review_priority" in doctor_table.columns:
        priorities = doctor_table["review_priority"].astype(str).str.upper().tolist()
        if any("HIGH REVIEW PRIORITY" in value for value in priorities):
            doctor_signal = _traffic_light("HIGH", "Ưu tiên cao", "Có ít nhất một bác sĩ cần hội đồng xem trước.")
        elif any("MODERATE REVIEW PRIORITY" in value for value in priorities):
            doctor_signal = _traffic_light("MODERATE", "Ưu tiên vừa", "Có bác sĩ cần hội đồng xem lại.")
        else:
            doctor_signal = _traffic_light("LOW", "Ưu tiên thấp", "Mẫu chỉ định chưa nổi bật ở mức cao.")
    elif top_doctor:
        doctor_signal = _traffic_light(
            "MODERATE" if _as_float(top_doctor.get("rank_value")) >= 45 else "LOW",
            "Cần xem trước" if _as_float(top_doctor.get("rank_value")) >= 45 else "Ưu tiên thấp",
            "Có bác sĩ cần hội đồng xem lại." if _as_float(top_doctor.get("rank_value")) >= 45 else "Mẫu chỉ định chưa nổi bật ở mức cao.",
        )

    procedure_signal = _traffic_light("LOW", "Chưa thấy tập trung mạnh", "Chưa có dịch vụ nào nổi bật.")
    if top_procedure:
        share = _as_float(top_procedure.get("rank_value"))
        if share >= 0.25:
            procedure_signal = _traffic_light("HIGH", "Tập trung mạnh", "Một dịch vụ chiếm ít nhất 25% tiền tín hiệu.")
        elif share >= 0.10:
            procedure_signal = _traffic_light("MODERATE", "Tập trung vừa", "Một dịch vụ chiếm ít nhất 10% tiền tín hiệu.")

    icd_count = key_numbers["icd_flags"]
    if icd_count >= 20:
        icd_context_signal = _traffic_light("HIGH", "Nhiều cờ ICD / bối cảnh", f"Có {icd_count} dòng cần hội đồng xem ICD / bối cảnh.")
    elif icd_count >= 5:
        icd_context_signal = _traffic_light("MODERATE", "Có cờ ICD / bối cảnh", f"Có {icd_count} dòng cần kiểm tra.")
    else:
        icd_context_signal = _traffic_light("LOW", "Ít cờ ICD / bối cảnh", f"Chỉ có {icd_count} dòng cần kiểm tra.")

    if ctx_summary is None:
        context_resolution_signal = _traffic_light("UNKNOWN", "Chưa có bảng gỡ cờ", "Chưa có dữ liệu gỡ cờ theo bối cảnh.")
    else:
        ratio = ctx_summary["ratio"]
        if ratio >= 0.7:
            context_resolution_signal = _traffic_light("GOOD", "Bối cảnh khá rõ", f"{ctx_summary['resolved']}/{ctx_summary['total']} dòng có bối cảnh mạnh.")
        elif ratio >= 0.3:
            context_resolution_signal = _traffic_light("PARTIAL", "Bối cảnh một phần", f"{ctx_summary['resolved']}/{ctx_summary['total']} dòng có bối cảnh mạnh.")
        else:
            context_resolution_signal = _traffic_light("POOR", "Bối cảnh yếu", f"{ctx_summary['resolved']}/{ctx_summary['total']} dòng có bối cảnh mạnh.")

    plain_language_summary = []
    preset_name = current_measure.get("preset_name") or overview.get("scope_preset_name") or "bộ lọc hiện tại"
    plain_language_summary.append(_u(
        f"App đang xem theo bộ lọc: {preset_name}.",
        f"The app is reviewing this scope: {preset_name}.",
    ))
    plain_language_summary.append(_u(
        f"Tổng số dòng nền là {current_measure['denominator_rows']}; trong đó {current_measure['numerator_rows']} dòng là tín hiệu cần xem trước.",
        f"There are {current_measure['denominator_rows']} baseline rows; {current_measure['numerator_rows']} rows are review signals.",
    ))
    if top_doctor:
        plain_language_summary.append(_u(
            f"Bác sĩ nên xem trước: {top_doctor['review_target']}, vì {top_doctor['why_flagged']}.",
            f"Doctor to review first: {top_doctor['review_target']}, because {top_doctor['why_flagged']}.",
        ))
    if top_procedure:
        plain_language_summary.append(_u(
            f"Dịch vụ nên xem trước: {top_procedure['review_target']}, vì {top_procedure['why_flagged']}.",
            f"Procedure to review first: {top_procedure['review_target']}, because {top_procedure['why_flagged']}.",
        ))
    if icd_count:
        plain_language_summary.append(_u(
            f"Có {icd_count} dòng cần kiểm tra ICD / bối cảnh.",
            f"There are {icd_count} rows needing ICD/context review.",
        ))
    if ctx_summary:
        plain_language_summary.append(_u(
            f"Có {ctx_summary['resolved']}/{ctx_summary['total']} dòng cờ đỏ đã có bối cảnh hợp lý.",
            f"{ctx_summary['resolved']}/{ctx_summary['total']} red flags have a reasonable context explanation.",
        ))
    if not plain_language_summary:
        plain_language_summary.append(_u("Chưa đủ dữ liệu để tạo nhận định tự động.", "Not enough data to generate an automatic interpretation."))
    plain_language_summary.append(_u(
        "Kết quả chỉ là tín hiệu rà soát, không phải kết luận sai phạm.",
        "This result is a review signal, not a finding of wrongdoing.",
    ))

    how_to_read = [
        _u("Công cụ 01 = xem quy mô mẫu và số dòng tín hiệu.", "Tool 01 = review the cohort size and signal rows."),
        _u("Công cụ 02 = biết bác sĩ nào nên xem trước.", "Tool 02 = see which doctor should be reviewed first."),
        _u("Công cụ 03 = biết dịch vụ nào đang nổi bật hoặc tốn tiền.", "Tool 03 = see which procedure is prominent or costly."),
        _u("Công cụ 04 = biết dòng nào cần kiểm tra ICD / bối cảnh.", "Tool 04 = see which rows need ICD/context review."),
        _u("Công cụ 05 = biết dòng nào có bối cảnh hợp lý để bớt báo động giả.", "Tool 05 = see which rows have a reasonable context explanation."),
        _u("Mức ưu tiên rà soát không phải bằng chứng sai phạm.", "Review priority is not evidence of wrongdoing."),
    ]

    recommended_next_actions = []
    if top_doctor:
        recommended_next_actions.append(_u(f"Ưu tiên xem bác sĩ {top_doctor['review_target']} trước.", f"Review doctor {top_doctor['review_target']} first."))
    if top_procedure:
        recommended_next_actions.append(_u(
            f"Đối chiếu dịch vụ {top_procedure['review_target']} với ICD và bối cảnh lâm sàng.",
            f"Cross-check procedure {top_procedure['review_target']} with ICD and clinical context.",
        ))
    if icd_count:
        recommended_next_actions.append(_u("Rà các ca thiếu ICD hoặc ICD yếu trước khi tổng hợp báo cáo.", "Review rows with missing or weak ICD before final reporting."))
    if ctx_summary and ctx_summary["unresolved"] > 0:
        recommended_next_actions.append(_u("Tập trung các ca chưa có bối cảnh rõ để hội đồng xem thêm.", "Focus on unresolved rows for committee follow-up."))
    if not recommended_next_actions:
        recommended_next_actions.append(_u("Duyệt lại bộ lọc và chạy thêm lọc thủ công nếu cần.", "Review the filters and run a manual filter if needed."))

    committee_items: list[dict] = []
    if top_doctor:
        committee_items.append({**top_doctor, "target_type": "doctor"})
    if top_procedure:
        committee_items.append({**top_procedure, "target_type": "procedure"})
    if icd_signal:
        committee_items.append({**icd_signal, "target_type": "ICD/context"})
    if ctx_summary:
        committee_items.append(
            {
                "review_target": _u("Case context resolution", "Case context resolution"),
                "department": "",
                "target_type": _u("case context", "case context"),
                "main_signal": _u(
                    f"{ctx_summary['resolved']} đã gỡ / {ctx_summary['total']} đã xem",
                    f"{ctx_summary['resolved']} resolved / {ctx_summary['total']} reviewed",
                ),
                "why_flagged": _u(
                    f"Còn {ctx_summary['unresolved']} ca chưa có bối cảnh rõ.",
                    f"{ctx_summary['unresolved']} rows still have no clear context.",
                ),
                "supporting_evidence": _u(
                    f"Gỡ một phần: {ctx_summary['partial']}; chưa rõ: {ctx_summary['unresolved']}",
                    f"Partially resolved: {ctx_summary['partial']}; unresolved: {ctx_summary['unresolved']}",
                ),
                "context_status": context_resolution_signal["level"],
                "recommended_action": _u("Xem các ca chưa rõ bối cảnh trước.", "Review unresolved rows first."),
                "rank_value": 0.0,
            }
        )

    committee_table = _build_committee_table(committee_items)
    return {
        "current_measure": current_measure,
        "key_numbers": key_numbers,
        "traffic_lights": {
            "doctor_signal": doctor_signal,
            "procedure_signal": procedure_signal,
            "icd_context_signal": icd_context_signal,
            "context_resolution_signal": context_resolution_signal,
        },
        "top_review_priorities": committee_items[:10],
        "plain_language_summary": plain_language_summary,
        "how_to_read": how_to_read,
        "recommended_next_actions": recommended_next_actions,
        "review_committee_summary_table": committee_table,
    }
