from __future__ import annotations

import math
import re
from typing import Any

import pandas as pd


DATE_CANDIDATES = [
    "claim_date",
    "order_date",
    "service_date",
    "visit_date",
    "date",
    "ngay_chi_dinh",
    "ngay_kham",
    "ngay_dich_vu",
    "ngay_yeu_cau",
    "Ngày chỉ định / OrderDate",
    "Ngày khám / VisitDate",
    "ClaimDate",
    "OrderDate",
    "ServiceDate",
    "VisitDate",
]

DOCTOR_CANDIDATES = [
    "doctor",
    "ten_bac_si__doctor",
    "Tên bác sĩ / DoctorName",
    "DoctorName",
]

DEPARTMENT_CANDIDATES = [
    "department",
    "khoa__department",
    "Khoa / Department",
    "Department",
]

PROCEDURE_CANDIDATES = [
    "procedure",
    "ten_dich_vu__procedure",
    "Tên dịch vụ / ProcedureName",
    "ProcedureName",
]

PATIENT_CANDIDATES = [
    "patient",
    "Tên bệnh nhân / PatientName",
    "PatientName",
]

CLAIM_ID_CANDIDATES = [
    "claim_id",
    "Mã hồ sơ / ClaimID",
    "ClaimID",
    "VisitID",
]

ICD_CODE_CANDIDATES = [
    "diagnosis_code",
    "Mã ICD10 / DiagnosisCode",
    "DiagnosisCode",
    "ICD10",
    "ICD",
]

DIAGNOSIS_NAME_CANDIDATES = [
    "diagnosis_name",
    "Chẩn đoán / DiagnosisName",
    "DiagnosisName",
    "Diagnosis",
]

AMOUNT_CANDIDATES = [
    "amount_vnd",
    "amount",
    "numerator_amount_vnd",
    "out_of_insurance_amount_vnd",
    "chi_phi_ngoai_bao_hiem__out_of_insurance_amount_vnd",
    "Số tiền yêu cầu thanh toán VND / ClaimAmountVND",
    "ClaimAmountVND",
    "Amount",
]

SEVERITY_ORDER = {
    "HIGH REVIEW PRIORITY": 0,
    "RED": 0,
    "MODERATE REVIEW PRIORITY": 1,
    "ORANGE": 1,
    "LOW REVIEW PRIORITY": 2,
    "YELLOW": 2,
    "MONITOR": 3,
    "NORMAL": 3,
    "": 4,
}


def _table(tables: dict[str, Any], name: str) -> pd.DataFrame:
    obj = tables.get(name)
    if isinstance(obj, pd.DataFrame):
        return obj.copy()
    return pd.DataFrame()


def _first_value(row: pd.Series, candidates: list[str], default: str = "") -> Any:
    for name in candidates:
        if name in row.index:
            value = row.get(name)
            if pd.notna(value) and str(value).strip() != "":
                return value
    return default


def _to_number(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return 0.0
        return float(value)
    text = str(value).strip()
    if not text:
        return 0.0
    text = text.replace("VND", "").replace("₫", "").replace("%", "")
    text = text.replace(",", "").replace(" ", "")
    match = re.findall(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    try:
        return float(match[0])
    except ValueError:
        return 0.0


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    text = str(value).strip()
    return text if text else default


def _format_vnd(value: Any) -> str:
    return f"{_to_number(value):,.0f} VND"


def _severity_rank(value: Any) -> int:
    return SEVERITY_ORDER.get(_safe_str(value).upper(), 4)


def _make_review_question(
    target_type: str,
    doctor: str,
    procedure: str,
    icd: str,
    reason: str,
) -> str:
    if target_type == "doctor":
        return (
            f"Rà soát hồ sơ của {doctor}: xem các chỉ định nào tạo tín hiệu, "
            f"ICD/bối cảnh có hợp lý không, và pattern có khác baseline khoa không."
        )
    if target_type == "procedure":
        return (
            f"Rà soát dịch vụ {procedure}: kiểm tra vì sao dịch vụ này tạo nhiều tín hiệu "
            f"hoặc chi phí cao trong nhóm đang phân tích."
        )
    if target_type == "icd_context":
        return f"Kiểm tra ICD {icd} cho chỉ định {procedure}: ICD/bối cảnh có đủ giải thích cho chỉ định không."
    if target_type == "case":
        return f"Kiểm tra case này: {reason}"
    return "Hội đồng chuyên môn xem lại bằng chứng trước khi kết luận."


def _extract_top_doctors(tables: dict[str, Any], limit: int = 10) -> pd.DataFrame:
    source = _table(tables, "doctor_review_priority_table")
    if source.empty:
        source = _table(tables, "doctor_outlier_table")
    if source.empty:
        source = _table(tables, "by_doctor")
    if source.empty:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for _, row in source.iterrows():
        doctor = _safe_str(_first_value(row, DOCTOR_CANDIDATES, "Unknown doctor"))
        department = _safe_str(_first_value(row, DEPARTMENT_CANDIDATES, "Unknown department"))
        severity = _safe_str(row.get("review_priority", row.get("severity", row.get("final_severity", ""))), "MONITOR")
        risk_score = _to_number(row.get("risk_score", 0))
        numerator_orders = _to_number(
            row.get(
                "numerator_orders",
                row.get("out_of_insurance_orders", row.get("chi_dinh_ngoai_bao_hiem__out_of_insurance_orders", 0)),
            )
        )
        denominator_orders = _to_number(
            row.get(
                "denominator_orders",
                row.get("total_orders_for_insured_patients", row.get("tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients", 0)),
            )
        )
        numerator_rate = _safe_str(
            row.get("numerator_rate", row.get("out_of_insurance_rate", row.get("ty_le_ngoai_bao_hiem__out_of_insurance_rate", ""))),
            "",
        )
        ratio = _safe_str(row.get("ratio_vs_department", row.get("ratio_vs_department_median", "")), "")
        amount = _first_value(row, AMOUNT_CANDIDATES, 0)
        top_procedure = _safe_str(row.get("top_numerator_procedures", row.get("top_out_procedure", "")), "")
        top_icd = _safe_str(row.get("top_icd_codes", row.get("top_icd", "")), "")

        reason_parts = []
        if numerator_orders:
            reason_parts.append(f"{int(numerator_orders)} tín hiệu")
        if numerator_rate:
            reason_parts.append(f"tỷ lệ {numerator_rate}")
        if ratio:
            reason_parts.append(f"cao hơn baseline khoa {ratio} lần")
        if amount:
            reason_parts.append(f"số tiền {_format_vnd(amount)}")
        if top_procedure:
            reason_parts.append(f"dịch vụ chính: {top_procedure}")
        if top_icd:
            reason_parts.append(f"ICD hay gặp: {top_icd}")

        why = "; ".join(reason_parts) if reason_parts else "Có tín hiệu cần hội đồng xem xét."

        rows.append(
            {
                "priority_rank": 0,
                "review_target": doctor,
                "target_type": "doctor",
                "department": department,
                "main_signal": severity,
                "review_date": "N/A",
                "claim_id": "N/A",
                "patient": "N/A",
                "procedure": top_procedure or "N/A",
                "diagnosis_code": top_icd or "N/A",
                "amount_vnd": _format_vnd(amount),
                "why_flagged": why,
                "supporting_evidence": (
                    f"denominator_orders={int(denominator_orders)}, "
                    f"numerator_orders={int(numerator_orders)}, risk_score={risk_score:.0f}"
                ),
                "context_status": "See case evidence",
                "recommended_action": _make_review_question("doctor", doctor, top_procedure, top_icd, why),
                "priority_score": risk_score + 100 - _severity_rank(severity) * 10 + numerator_orders,
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values(["priority_score", "review_target"], ascending=[False, True]).head(limit)
    out["priority_rank"] = range(1, len(out) + 1)
    return out


def _extract_top_procedures(tables: dict[str, Any], limit: int = 10) -> pd.DataFrame:
    source = _table(tables, "procedure_pareto_table")
    if source.empty:
        source = _table(tables, "high_cost_procedure_table")
    if source.empty:
        source = _table(tables, "doctor_procedure_concentration_table")
    if source.empty:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for _, row in source.iterrows():
        procedure = _safe_str(_first_value(row, PROCEDURE_CANDIDATES, "Unknown procedure"))
        doctor = _safe_str(_first_value(row, DOCTOR_CANDIDATES, "Multiple doctors"))
        department = _safe_str(_first_value(row, DEPARTMENT_CANDIDATES, ""))
        amount = _first_value(row, AMOUNT_CANDIDATES, 0)
        numerator_orders = _to_number(row.get("numerator_orders", row.get("out_of_insurance_orders", row.get("total_orders", 0))))
        severity = _safe_str(row.get("severity", row.get("review_priority", "")), "MONITOR")
        high_cost = _safe_str(row.get("high_cost", ""))
        sensitive = _safe_str(row.get("flag_sensitive_procedure", ""))

        why_parts = []
        if numerator_orders:
            why_parts.append(f"{int(numerator_orders)} tín hiệu")
        if amount:
            why_parts.append(f"số tiền {_format_vnd(amount)}")
        if high_cost.lower() in {"true", "1", "yes"}:
            why_parts.append("dịch vụ chi phí cao")
        if sensitive.lower() in {"true", "1", "yes"}:
            why_parts.append("dịch vụ nhạy cảm")

        why = "; ".join(why_parts) if why_parts else "Dịch vụ có tín hiệu cần xem xét."

        rows.append(
            {
                "priority_rank": 0,
                "review_target": procedure,
                "target_type": "procedure",
                "department": department,
                "main_signal": severity,
                "review_date": "N/A",
                "claim_id": "N/A",
                "patient": "N/A",
                "procedure": procedure,
                "diagnosis_code": "N/A",
                "amount_vnd": _format_vnd(amount),
                "why_flagged": why,
                "supporting_evidence": f"doctor={doctor}, numerator_orders={int(numerator_orders)}",
                "context_status": "See ICD/context table",
                "recommended_action": _make_review_question("procedure", doctor, procedure, "", why),
                "priority_score": _to_number(amount) + numerator_orders * 1_000_000 - _severity_rank(severity) * 100_000,
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values(["priority_score", "review_target"], ascending=[False, True]).head(limit)
    out["priority_rank"] = range(1, len(out) + 1)
    return out


def _extract_icd_cases(tables: dict[str, Any], limit: int = 20) -> pd.DataFrame:
    frames = []
    for table_name in ["icd_mismatch_case_evidence", "required_icd_flags", "case_evidence_table"]:
        frame = _table(tables, table_name)
        if not frame.empty:
            frame = frame.copy()
            frame["_source_table"] = table_name
            frames.append(frame)
    if not frames:
        return pd.DataFrame()

    source = pd.concat(frames, ignore_index=True, sort=False)
    rows: list[dict[str, Any]] = []
    for _, row in source.iterrows():
        doctor = _safe_str(_first_value(row, DOCTOR_CANDIDATES, "Unknown doctor"))
        department = _safe_str(_first_value(row, DEPARTMENT_CANDIDATES, "Unknown department"))
        procedure = _safe_str(_first_value(row, PROCEDURE_CANDIDATES, "Unknown procedure"))
        patient = _safe_str(_first_value(row, PATIENT_CANDIDATES, "Unknown patient"))
        claim_id = _safe_str(_first_value(row, CLAIM_ID_CANDIDATES, "N/A"))
        icd = _safe_str(_first_value(row, ICD_CODE_CANDIDATES, "N/A"))
        diagnosis = _safe_str(_first_value(row, DIAGNOSIS_NAME_CANDIDATES, ""))
        date_value = _safe_str(_first_value(row, DATE_CANDIDATES, "N/A"))
        amount = _first_value(row, AMOUNT_CANDIDATES, 0)
        mismatch_type = _safe_str(row.get("mismatch_type", row.get("rule_name", row.get("flag_reason", ""))), "ICD/context review")
        severity = _safe_str(row.get("severity", row.get("original_severity", "")), "MONITOR")
        note = _safe_str(row.get("note", row.get("reason", row.get("recommended_review_action", ""))), "")
        context_status = _safe_str(row.get("context_status", row.get("resolution_status", "")), "Not checked")

        why = f"{mismatch_type}. ICD={icd}; diagnosis={diagnosis or 'N/A'}; note={note or 'cần hội đồng xem lại ICD/bối cảnh'}"

        rows.append(
            {
                "priority_rank": 0,
                "review_target": doctor,
                "target_type": "case",
                "department": department,
                "main_signal": severity,
                "review_date": date_value,
                "claim_id": claim_id,
                "patient": patient,
                "procedure": procedure,
                "diagnosis_code": icd,
                "amount_vnd": _format_vnd(amount),
                "why_flagged": why,
                "supporting_evidence": f"source={row.get('_source_table', '')}",
                "context_status": context_status,
                "recommended_action": _make_review_question("icd_context", doctor, procedure, icd, why),
                "priority_score": 100 - _severity_rank(severity) * 10 + _to_number(amount) / 1_000_000,
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values(["priority_score", "review_target", "procedure"], ascending=[False, True, True]).head(limit)
    out["priority_rank"] = range(1, len(out) + 1)
    return out


def _make_plain_language_summary(final_report: dict[str, Any], action_table: pd.DataFrame) -> list[str]:
    overview = final_report.get("overview", {}) or {}
    human = final_report.get("human_summary", {}) or {}
    current_measure = human.get("current_measure", {}) if isinstance(human, dict) else {}

    preset_name = current_measure.get("preset_name") or overview.get("scope_preset_name") or overview.get("preset_name") or "Default review measure"
    denominator_rows = current_measure.get("denominator_rows") or overview.get("denominator_rows") or overview.get("tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients") or "N/A"
    numerator_rows = current_measure.get("numerator_rows") or overview.get("numerator_rows") or overview.get("chi_dinh_ngoai_bao_hiem__out_of_insurance_orders") or "N/A"
    numerator_amount = current_measure.get("numerator_amount_vnd") or overview.get("numerator_amount_vnd") or overview.get("chi_phi_ngoai_bao_hiem_cua_benh_nhan_co_bao_hiem__out_of_insurance_amount_vnd") or "N/A"

    lines = [
        f"App đang phân tích: {preset_name}.",
        f"Mẫu nền có {denominator_rows} dòng; trong đó {numerator_rows} dòng là tín hiệu cần rà soát.",
        f"Tổng giá trị tín hiệu ước tính: {numerator_amount}.",
    ]

    if not action_table.empty:
        first = action_table.iloc[0]
        target = _safe_str(first.get("review_target", "N/A"))
        target_type = _safe_str(first.get("target_type", "N/A"))
        why = _safe_str(first.get("why_flagged", ""))
        lines.append(f"Ưu tiên rà soát đầu tiên: {target} ({target_type}) vì {why}.")

        case_rows = action_table[action_table["target_type"].isin(["case", "icd_context"])] if "target_type" in action_table.columns else pd.DataFrame()
        if not case_rows.empty:
            case = case_rows.iloc[0]
            lines.append(
                "Case cần xem bằng chứng: "
                f"bác sĩ {case.get('review_target', 'N/A')}, "
                f"chỉ định {case.get('procedure', 'N/A')}, "
                f"ngày {case.get('review_date', 'N/A')}, "
                f"claim {case.get('claim_id', 'N/A')}."
            )
    else:
        lines.append("Chưa có đủ dữ liệu để tạo danh sách ưu tiên rà soát tự động.")

    lines.append("Kết quả là tín hiệu hỗ trợ rà soát, không phải kết luận sai phạm hay gian lận.")
    return lines


def build_judge_summary(final_report: dict[str, Any], max_rows: int = 25) -> dict[str, Any]:
    tables = final_report.get("tables", {}) or {}
    doctor_items = _extract_top_doctors(tables, limit=10)
    procedure_items = _extract_top_procedures(tables, limit=10)
    icd_case_items = _extract_icd_cases(tables, limit=20)

    frames = [df for df in [doctor_items, procedure_items, icd_case_items] if not df.empty]
    if frames:
        action_table = pd.concat(frames, ignore_index=True, sort=False)
        action_table = action_table.sort_values(["priority_score", "target_type", "review_target"], ascending=[False, True, True]).head(max_rows)
        action_table["priority_rank"] = range(1, len(action_table) + 1)
    else:
        action_table = pd.DataFrame(
            columns=[
                "priority_rank",
                "review_target",
                "target_type",
                "department",
                "main_signal",
                "review_date",
                "claim_id",
                "patient",
                "procedure",
                "diagnosis_code",
                "amount_vnd",
                "why_flagged",
                "supporting_evidence",
                "context_status",
                "recommended_action",
                "priority_score",
            ]
        )

    plain_summary = _make_plain_language_summary(final_report, action_table)
    top_cards = []
    if not action_table.empty:
        for _, row in action_table.head(3).iterrows():
            top_cards.append(
                {
                    "title": f"{row.get('priority_rank')}. {row.get('review_target')}",
                    "subtitle": f"{row.get('target_type')} | {row.get('main_signal')}",
                    "body": row.get("why_flagged", ""),
                    "action": row.get("recommended_action", ""),
                }
            )

    how_to_read = [
        "Tool 01 = quy mô mẫu và tín hiệu.",
        "Tool 02 = bác sĩ nào cần xem trước.",
        "Tool 03 = dịch vụ nào đáng chú ý về chi phí hoặc tần suất.",
        "Tool 04 = ICD/bối cảnh nào thiếu, yếu hoặc không khớp.",
        "Tool 05 = ca nào có bối cảnh hợp lý để giảm báo động giả.",
        "Review priority là mức ưu tiên rà soát, không phải bằng chứng kết luận sai phạm.",
    ]

    return {
        "judge_action_table": action_table,
        "judge_plain_language_summary": plain_summary,
        "judge_top_cards": top_cards,
        "judge_how_to_read": how_to_read,
    }


def attach_judge_summary(final_report: dict[str, Any]) -> dict[str, Any]:
    summary = build_judge_summary(final_report)
    final_report["judge_summary"] = summary
    tables = final_report.setdefault("tables", {})
    tables["judge_action_table"] = summary["judge_action_table"]
    return final_report
