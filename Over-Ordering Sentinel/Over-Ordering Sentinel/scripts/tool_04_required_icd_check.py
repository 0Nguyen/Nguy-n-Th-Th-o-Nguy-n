from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

import pandas as pd

from scripts.analysis_support import get_context_frames, to_numeric_series


DATE_CANDIDATES = [
    "claim_date",
    "order_date",
    "service_date",
    "visit_date",
    "date",
    "ngay_chi_dinh",
    "ngay_kham",
    "ngay_dich_vu",
    "ClaimDate",
    "OrderDate",
    "ServiceDate",
    "VisitDate",
    "Ngày chỉ định / OrderDate",
    "Ngày khám / VisitDate",
]

GENERIC_ICD_PREFIXES = ["Z00", "Z01", "Z13", "R69", "R79"]

GENERIC_TEXT_KEYWORDS = [
    "unknown",
    "general",
    "check up",
    "check-up",
    "screening unspecified",
    "khong ro",
    "không rõ",
    "kham tong quat",
    "khám tổng quát",
    "theo doi",
    "theo dõi",
]


@dataclass(frozen=True)
class ICDRule:
    name: str
    procedure_keywords: list[str]
    expected_icd_prefixes: list[str]
    expected_context_keywords: list[str]
    weak_icd_prefixes: list[str]
    severity_if_missing: str
    severity_if_mismatch: str


RULES = [
    ICDRule(
        name="HIV test ICD/context alignment",
        procedure_keywords=["hiv", "test hiv", "xet nghiem hiv", "xét nghiệm hiv"],
        expected_icd_prefixes=["Z11", "B20", "B21", "B22", "B23", "B24"],
        expected_context_keywords=[
            "screening",
            "sang loc",
            "sàng lọc",
            "pre op",
            "pre-op",
            "tien phau",
            "tiền phẫu",
            "surgery",
            "phau thuat",
            "phẫu thuật",
            "risk",
            "nguy co",
            "nguy cơ",
        ],
        weak_icd_prefixes=["Z00", "Z01", "Z13", "R69"],
        severity_if_missing="RED",
        severity_if_mismatch="RED",
    ),
    ICDRule(
        name="Glucose/HbA1c ICD/context alignment",
        procedure_keywords=["glucose", "duong huyet", "đường huyết", "hba1c", "a1c", "xet nghiem duong", "xét nghiệm đường"],
        expected_icd_prefixes=["E10", "E11", "E12", "E13", "E14", "R73"],
        expected_context_keywords=["diabetes", "dai thao duong", "đái tháo đường", "tieu duong", "tiểu đường", "hyperglycemia", "tang duong huyet", "tăng đường huyết", "pre op", "pre-op", "tien phau", "tiền phẫu"],
        weak_icd_prefixes=["Z00", "Z01", "Z13", "R69"],
        severity_if_missing="ORANGE",
        severity_if_mismatch="ORANGE",
    ),
    ICDRule(
        name="Troponin/Cardiac marker ICD/context alignment",
        procedure_keywords=["troponin", "men tim", "cardiac marker", "xet nghiem tim", "xét nghiệm tim"],
        expected_icd_prefixes=["R07", "I20", "I21", "I22", "I24", "I25", "I50"],
        expected_context_keywords=["chest pain", "dau nguc", "đau ngực", "cardiac", "tim", "myocardial", "coronary", "ischemia", "thiếu máu cơ tim", "hoi chung vanh", "hội chứng vành"],
        weak_icd_prefixes=["Z00", "Z01", "Z13", "R69"],
        severity_if_missing="RED",
        severity_if_mismatch="RED",
    ),
    ICDRule(
        name="CT/MRI ICD/context alignment",
        procedure_keywords=["ct", "mri", "chup ct", "chụp ct", "chup mri", "chụp mri", "computed tomography", "magnetic resonance"],
        expected_icd_prefixes=["S", "T", "I60", "I61", "I62", "I63", "I64", "G", "C", "D", "R51", "R52", "M", "N", "K"],
        expected_context_keywords=[
            "trauma",
            "chan thuong",
            "chấn thương",
            "headache",
            "dau dau",
            "đau đầu",
            "neuro",
            "than kinh",
            "thần kinh",
            "cancer",
            "tumor",
            "u ",
            "stroke",
            "dot quy",
            "đột quỵ",
            "emergency",
            "cap cuu",
            "cấp cứu",
            "surgery",
            "phau thuat",
            "phẫu thuật",
            "inpatient",
            "noi tru",
            "nội trú",
            "pain",
            "dau",
            "đau",
        ],
        weak_icd_prefixes=["Z00", "Z01", "Z13", "R69", "R79"],
        severity_if_missing="RED",
        severity_if_mismatch="YELLOW",
    ),
    ICDRule(
        name="Coagulation/CRP inflammation-context alignment",
        procedure_keywords=["crp", "dong mau", "đông máu", "coagulation", "pt", "aptt", "inr"],
        expected_icd_prefixes=["A", "B", "D", "I", "K", "R", "S", "T", "Z01"],
        expected_context_keywords=["infection", "nhiem trung", "nhiễm trùng", "inflammation", "viem", "viêm", "bleeding", "chay mau", "chảy máu", "surgery", "phau thuat", "phẫu thuật", "pre op", "pre-op", "tien phau", "tiền phẫu", "emergency", "cap cuu", "cấp cứu"],
        weak_icd_prefixes=["Z00", "Z13", "R69"],
        severity_if_missing="YELLOW",
        severity_if_mismatch="YELLOW",
    ),
]


def _fold_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"\s+", " ", text)
    return text


def _contains_any(text: Any, keywords: list[str]) -> bool:
    folded = _fold_text(text)
    return any(_fold_text(keyword) in folded for keyword in keywords)


def _icd_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.strip().upper()
    text = text.replace(".", "")
    return text


def _icd_has_prefix(icd: Any, prefixes: list[str]) -> bool:
    code = _icd_text(icd)
    if not code:
        return False
    normalized_prefixes = [prefix.upper().replace(".", "") for prefix in prefixes]
    return any(code.startswith(prefix) for prefix in normalized_prefixes)


def _is_generic_icd(icd: Any, diagnosis_name: Any = "") -> bool:
    code = _icd_text(icd)
    if code and _icd_has_prefix(code, GENERIC_ICD_PREFIXES):
        return True
    combined = f"{diagnosis_name or ''} {icd or ''}"
    return _contains_any(combined, GENERIC_TEXT_KEYWORDS)


def _find_first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for name in candidates:
        if name in df.columns:
            return name
    return None


def _amount_number(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("VND", "").replace("₫", "")
    match = re.findall(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0
    try:
        return float(match[0])
    except ValueError:
        return 0.0


def _format_vnd(value: Any) -> str:
    return f"{_amount_number(value):,.0f} VND"


def _review_df_for_context(df: pd.DataFrame, context: Any) -> pd.DataFrame:
    scope, denominator_df, numerator_df, _ = get_context_frames(df, context)
    coverage_scope = getattr(scope, "coverage_scope", "out_of_insurance_only")
    if coverage_scope == "all_orders":
        return denominator_df.copy()
    if numerator_df is not None and not numerator_df.empty:
        return numerator_df.copy()
    if denominator_df is not None and not denominator_df.empty:
        return denominator_df.copy()
    return df.copy()


def _matched_rule(procedure: Any) -> ICDRule | None:
    for rule in RULES:
        if _contains_any(procedure, rule.procedure_keywords):
            return rule
    return None


def _context_status(row: pd.Series, rule: ICDRule) -> tuple[str, str]:
    combined = " ".join([str(row.get("procedure", "")), str(row.get("diagnosis_code", "")), str(row.get("diagnosis_name", ""))])
    if _contains_any(combined, rule.expected_context_keywords):
        return "CONTEXT_PRESENT_RESOLVED", "resolved context keyword"
    if _contains_any(combined, ["pre op", "pre-op", "tiền phẫu", "tien phau", "surgery", "operation", "phẫu thuật", "phau thuat"]):
        return "PARTIALLY_RESOLVED_WEAK_CONTEXT", "weak context keyword"
    return "NO_CONTEXT_FOUND", ""


def _build_flag(row: pd.Series, rule: ICDRule, mismatch_type: str, severity: str, note: str, context_keyword: str = "") -> dict[str, Any]:
    return {
        "claim_id": row.get("claim_id", ""),
        "patient": row.get("patient", ""),
        "doctor": row.get("doctor", ""),
        "department": row.get("department", ""),
        "review_date": row.get("_review_date", "N/A"),
        "procedure": row.get("procedure", ""),
        "diagnosis_code": row.get("diagnosis_code", ""),
        "diagnosis_name": row.get("diagnosis_name", ""),
        "covered_status": row.get("covered_status", ""),
        "amount_vnd": _format_vnd(row.get("amount", 0)),
        "rule_name": rule.name,
        "mismatch_type": mismatch_type,
        "expected_icd_or_context": "ICD prefixes: " + ", ".join(rule.expected_icd_prefixes) + " | Context: " + ", ".join(rule.expected_context_keywords[:8]),
        "actual_icd": row.get("diagnosis_code", ""),
        "actual_diagnosis": row.get("diagnosis_name", ""),
        "severity": severity,
        "note": note,
        "context_keyword": context_keyword,
        "recommended_review_action": "Kiểm tra lại ICD, chỉ định, và bối cảnh lâm sàng trước khi ra quyết định.",
    }


def _generic_repeated_icd_flags(review_df: pd.DataFrame) -> pd.DataFrame:
    if review_df.empty or "diagnosis_code" not in review_df.columns or "doctor" not in review_df.columns or "procedure" not in review_df.columns:
        return pd.DataFrame()
    working = review_df.copy()
    working["diagnosis_code"] = working["diagnosis_code"].astype(str).str.strip()
    generic_mask = working.apply(lambda row: _is_generic_icd(row.get("diagnosis_code", ""), row.get("diagnosis_name", "")), axis=1)
    generic_df = working.loc[generic_mask].copy()
    if generic_df.empty:
        return pd.DataFrame()
    grouped = (
        generic_df.groupby(["doctor", "department", "diagnosis_code", "diagnosis_name"], dropna=False)
        .agg(unique_procedure_count=("procedure", "nunique"), procedure_count=("claim_id", "count"), amount_vnd=("amount", "sum"))
        .reset_index()
    )
    grouped = grouped[grouped["unique_procedure_count"] >= 3].copy()
    if grouped.empty:
        return pd.DataFrame()
    grouped["rule_name"] = "Generic repeated ICD"
    grouped["mismatch_type"] = "GENERIC_REPEATED_ICD"
    grouped["expected_icd_or_context"] = "Generic ICD should not be reused across multiple procedures"
    grouped["context_keyword"] = "generic repeated ICD"
    grouped["note"] = "Generic ICD is reused across three or more distinct procedures."
    grouped["severity"] = grouped["unique_procedure_count"].apply(lambda n: "ORANGE" if n >= 5 else "YELLOW")
    grouped["amount_vnd"] = grouped["amount_vnd"].map(_format_vnd)
    return grouped


def _alignment_status(row: pd.Series) -> str:
    diagnosis_code = str(row.get("diagnosis_code", "")).strip()
    diagnosis_name = str(row.get("diagnosis_name", "")).strip()
    if _is_generic_icd(diagnosis_code, diagnosis_name):
        return "REVIEW"
    if not diagnosis_code:
        return "MISSING_ICD"
    return "ALIGNED"


def run(df, context):
    review_df = _review_df_for_context(df, context)
    if review_df.empty:
        empty = pd.DataFrame()
        return {
            "tool_name": "04 - Rà ICD và chỉ định",
            "status": "completed",
            "summary": {
                "flag_count": 0,
                "mismatch_case_count": 0,
                "diagnosis_code_present": False,
                "diagnosis_name_present": False,
                "high_cost_threshold_vnd": _format_vnd(0),
            },
            "tables": {
                "required_icd_flags": empty,
                "case_evidence_table": empty,
                "icd_mismatch_case_evidence": empty,
                "doctor_icd_mismatch_summary": empty,
                "procedure_icd_pair_table": empty,
                "doctor_icd_usage_table": empty,
            },
            "notes": ["Không có dòng nào trong scope hiện tại để rà ICD / chỉ định."],
        }

    review_df = review_df.copy()
    date_col = _find_first_col(review_df, DATE_CANDIDATES)
    if date_col:
        review_df["_review_date"] = review_df[date_col].astype(str)
    else:
        review_df["_review_date"] = "N/A"

    for col in ["claim_id", "patient", "doctor", "department", "procedure", "diagnosis_code", "diagnosis_name", "covered_status", "amount"]:
        if col not in review_df.columns:
            review_df[col] = ""

    diagnosis_code_present = bool(review_df["diagnosis_code"].astype(str).str.strip().replace("nan", "").ne("").any()) if "diagnosis_code" in review_df.columns else False
    diagnosis_name_present = bool(review_df["diagnosis_name"].astype(str).str.strip().replace("nan", "").ne("").any()) if "diagnosis_name" in review_df.columns else False
    base_median_amount = float(to_numeric_series(review_df["amount"]).median()) if "amount" in review_df.columns and not review_df.empty else 0.0
    high_cost_threshold = max(base_median_amount * 3, 500000)

    flags: list[dict[str, Any]] = []
    reviewed_rows = 0

    for _, row in review_df.iterrows():
        procedure = row.get("procedure", "")
        rule = _matched_rule(procedure)
        if rule is None:
            continue

        reviewed_rows += 1
        diagnosis_code = row.get("diagnosis_code", "")
        diagnosis_name = row.get("diagnosis_name", "")
        has_icd = bool(str(diagnosis_code or "").strip())
        has_expected_icd = _icd_has_prefix(diagnosis_code, rule.expected_icd_prefixes)
        context_status, matched_context = _context_status(row, rule)
        is_generic = _is_generic_icd(diagnosis_code, diagnosis_name)
        amount_value = float(row.get("amount", 0) or 0)
        covered_status = str(row.get("covered_status", "unknown"))

        if not has_icd and context_status == "NO_CONTEXT_FOUND":
            flags.append(
                _build_flag(
                    row,
                    rule,
                    "MISSING_ICD",
                    rule.severity_if_missing,
                    "Thiếu ICD và chưa thấy bối cảnh lâm sàng phù hợp.",
                    matched_context,
                )
            )
            continue

        if is_generic and context_status == "NO_CONTEXT_FOUND":
            flags.append(
                _build_flag(
                    row,
                    rule,
                    "WEAK_ICD",
                    "YELLOW",
                    "ICD/chẩn đoán quá chung hoặc yếu, chưa đủ giải thích rõ chỉ định.",
                    matched_context,
                )
            )
            continue

        if has_icd and not has_expected_icd and context_status == "NO_CONTEXT_FOUND":
            flags.append(
                _build_flag(
                    row,
                    rule,
                    "PROCEDURE_ICD_MISMATCH",
                    rule.severity_if_mismatch,
                    "ICD hiện tại chưa khớp với nhóm chỉ định theo rule audit.",
                    matched_context,
                )
            )
            continue

        if context_status == "PARTIALLY_RESOLVED_WEAK_CONTEXT" and not has_expected_icd:
            flags.append(
                _build_flag(
                    row,
                    rule,
                    "WEAK_ICD",
                    "YELLOW",
                    "Có bối cảnh yếu nhưng ICD vẫn chưa đủ mạnh để giải thích chỉ định.",
                    matched_context,
                )
            )
            continue

        if has_expected_icd and context_status == "NO_CONTEXT_FOUND" and covered_status == "out_of_insurance" and amount_value >= high_cost_threshold:
            flags.append(
                _build_flag(
                    row,
                    rule,
                    "PROCEDURE_ICD_MISMATCH",
                    "RED" if rule.severity_if_mismatch == "RED" else rule.severity_if_mismatch,
                    "Dòng này có ICD/ctx chưa đủ rõ trong nhóm phí cao ngoài bảo hiểm.",
                    matched_context,
                )
            )

    required_icd_flags = pd.DataFrame(flags)

    generic_repeated_df = _generic_repeated_icd_flags(review_df)
    if not generic_repeated_df.empty:
        generic_rows = []
        for _, row in generic_repeated_df.iterrows():
            generic_rows.append(
                {
                    "claim_id": row.get("claim_id", ""),
                    "patient": row.get("patient", ""),
                    "doctor": row.get("doctor", ""),
                    "department": row.get("department", ""),
                    "review_date": row.get("_review_date", "N/A"),
                    "procedure": row.get("procedure", ""),
                    "diagnosis_code": row.get("diagnosis_code", ""),
                    "diagnosis_name": row.get("diagnosis_name", ""),
                    "covered_status": row.get("covered_status", "unknown"),
                    "amount_vnd": row.get("amount_vnd", _format_vnd(row.get("amount", 0))),
                    "rule_name": row.get("rule_name", "Generic repeated ICD"),
                    "mismatch_type": row.get("mismatch_type", "GENERIC_REPEATED_ICD"),
                    "expected_icd_or_context": row.get("expected_icd_or_context", ""),
                    "actual_icd": row.get("diagnosis_code", ""),
                    "actual_diagnosis": row.get("diagnosis_name", ""),
                    "severity": row.get("severity", "YELLOW"),
                    "note": row.get("note", ""),
                    "context_keyword": row.get("context_keyword", ""),
                    "recommended_review_action": "Xem lại pattern dùng ICD chung lặp lại cho nhiều dịch vụ.",
                }
            )
        generic_flag_df = pd.DataFrame(generic_rows)
        required_icd_flags = pd.concat([required_icd_flags, generic_flag_df], ignore_index=True, sort=False) if not required_icd_flags.empty else generic_flag_df

    required_icd_flags = required_icd_flags.drop_duplicates(subset=["claim_id", "rule_name", "mismatch_type", "procedure", "diagnosis_code"], keep="first")

    if required_icd_flags.empty:
        empty = pd.DataFrame()
        return {
            "tool_name": "04 - Rà ICD và chỉ định",
            "status": "completed",
            "summary": {
                "flag_count": 0,
                "mismatch_case_count": 0,
                "diagnosis_code_present": diagnosis_code_present,
                "diagnosis_name_present": diagnosis_name_present,
                "high_cost_threshold_vnd": _format_vnd(high_cost_threshold),
            },
            "tables": {
                "required_icd_flags": empty,
                "case_evidence_table": empty,
                "icd_mismatch_case_evidence": empty,
                "doctor_icd_mismatch_summary": empty,
                "procedure_icd_pair_table": empty,
                "doctor_icd_usage_table": empty,
            },
            "notes": [
                "Không tìm thấy ca ICD / chỉ định lệch trong scope đã chọn.",
                "Nếu cột ICD thưa dữ liệu, app vẫn chạy tiếp và chỉ ghi chú thay vì bị dừng.",
            ],
        }

    case_evidence_table = required_icd_flags[
        [
            "claim_id",
            "patient",
            "doctor",
            "department",
            "review_date",
            "procedure",
            "diagnosis_code",
            "diagnosis_name",
            "covered_status",
            "amount_vnd",
            "rule_name",
            "mismatch_type",
            "expected_icd_or_context",
            "actual_icd",
            "actual_diagnosis",
            "severity",
            "note",
            "context_keyword",
            "recommended_review_action",
        ]
    ].copy()
    case_evidence_table["flag_source"] = "Tool 04"

    icd_mismatch_case_evidence = case_evidence_table.copy()
    mismatch_rows = required_icd_flags.loc[required_icd_flags["mismatch_type"].isin(["MISSING_ICD", "WEAK_ICD", "PROCEDURE_ICD_MISMATCH", "GENERIC_REPEATED_ICD"])].copy()

    if mismatch_rows.empty:
        doctor_icd_mismatch_summary = pd.DataFrame(
            columns=[
                "doctor",
                "department",
                "total_reviewed_orders",
                "missing_icd_count",
                "weak_icd_count",
                "mismatch_count",
                "generic_repeated_icd_count",
                "out_of_insurance_mismatch_count",
                "mismatch_rate",
                "mismatch_amount_vnd",
                "top_problem_icd",
                "top_problem_procedure",
                "severity",
                "explanation_summary",
            ]
        )
    else:
        doctor_icd_mismatch_summary = (
            mismatch_rows.groupby(["doctor", "department"], dropna=False)
            .agg(
                total_reviewed_orders=("claim_id", "count"),
                missing_icd_count=("mismatch_type", lambda s: int((s == "MISSING_ICD").sum())),
                weak_icd_count=("mismatch_type", lambda s: int((s == "WEAK_ICD").sum())),
                mismatch_count=("mismatch_type", lambda s: int(s.isin(["MISSING_ICD", "WEAK_ICD", "PROCEDURE_ICD_MISMATCH", "GENERIC_REPEATED_ICD"]).sum())),
                generic_repeated_icd_count=("mismatch_type", lambda s: int((s == "GENERIC_REPEATED_ICD").sum())),
                out_of_insurance_mismatch_count=("covered_status", lambda s: int((s == "out_of_insurance").sum())),
                mismatch_amount_raw=("amount_vnd", lambda s: sum(_amount_number(v) for v in s)),
            )
            .reset_index()
        )
        doctor_icd_mismatch_summary["mismatch_rate"] = doctor_icd_mismatch_summary.apply(
            lambda row: row["mismatch_count"] / row["total_reviewed_orders"] if row["total_reviewed_orders"] else 0.0,
            axis=1,
        )
        top_problem_icd = (
            mismatch_rows.groupby(["doctor", "department", "diagnosis_code"], dropna=False)["claim_id"].count().reset_index(name="cnt").sort_values(["doctor", "department", "cnt"], ascending=[True, True, False])
            .drop_duplicates(["doctor", "department"], keep="first").rename(columns={"diagnosis_code": "top_problem_icd"})
        )
        top_problem_proc = (
            mismatch_rows.groupby(["doctor", "department", "procedure"], dropna=False)["claim_id"].count().reset_index(name="cnt").sort_values(["doctor", "department", "cnt"], ascending=[True, True, False])
            .drop_duplicates(["doctor", "department"], keep="first").rename(columns={"procedure": "top_problem_procedure"})
        )
        doctor_icd_mismatch_summary = doctor_icd_mismatch_summary.merge(top_problem_icd[["doctor", "department", "top_problem_icd"]], on=["doctor", "department"], how="left")
        doctor_icd_mismatch_summary = doctor_icd_mismatch_summary.merge(top_problem_proc[["doctor", "department", "top_problem_procedure"]], on=["doctor", "department"], how="left")
        doctor_icd_mismatch_summary["severity"] = doctor_icd_mismatch_summary["mismatch_rate"].apply(
            lambda value: "HIGH" if value >= 0.5 else "MODERATE" if value >= 0.2 else "LOW"
        )
        doctor_icd_mismatch_summary["mismatch_amount_vnd"] = doctor_icd_mismatch_summary["mismatch_amount_raw"].map(_format_vnd)
        doctor_icd_mismatch_summary["explanation_summary"] = doctor_icd_mismatch_summary.apply(
            lambda row: (
                f"{row['doctor']} có {int(row['mismatch_count'])} tín hiệu ICD/context cần rà soát; "
                f"thiếu ICD={int(row['missing_icd_count'])}, ICD yếu={int(row['weak_icd_count'])}, "
                f"không khớp={int(row['mismatch_count'])}."
            ),
            axis=1,
        )
        doctor_icd_mismatch_summary = doctor_icd_mismatch_summary.drop(columns=["mismatch_amount_raw"])

    procedure_icd_pair_table = (
        review_df.groupby(["procedure", "diagnosis_code", "diagnosis_name"], dropna=False)
        .agg(pair_count=("claim_id", "count"), amount_vnd=("amount", "sum"), doctor_count=("doctor", "nunique"))
        .reset_index()
        .sort_values(["pair_count", "amount_vnd"], ascending=[False, False])
        .reset_index(drop=True)
    )
    if not procedure_icd_pair_table.empty:
        procedure_icd_pair_table["numerator_count"] = procedure_icd_pair_table["pair_count"]
        procedure_icd_pair_table["alignment_status"] = procedure_icd_pair_table.apply(_alignment_status, axis=1)
        procedure_icd_pair_table["amount_vnd"] = procedure_icd_pair_table["amount_vnd"].map(_format_vnd)
        procedure_icd_pair_table["review_note"] = procedure_icd_pair_table["alignment_status"].apply(
            lambda value: "Procedure and ICD pair should be reviewed together." if value != "ALIGNED" else "Pair looks aligned in the current scope."
        )

    doctor_icd_usage_table = (
        review_df.groupby(["doctor", "department", "diagnosis_code", "diagnosis_name"], dropna=False)
        .agg(procedure_count=("claim_id", "count"), unique_procedure_count=("procedure", "nunique"), numerator_count=("claim_id", "count"), amount_vnd=("amount", "sum"))
        .reset_index()
        .sort_values(["procedure_count", "amount_vnd"], ascending=[False, False])
        .reset_index(drop=True)
    )
    if not doctor_icd_usage_table.empty:
        doctor_icd_usage_table["amount_vnd"] = doctor_icd_usage_table["amount_vnd"].map(_format_vnd)
        doctor_icd_usage_table["icd_reuse_pattern"] = doctor_icd_usage_table.apply(
            lambda row: "GENERIC_REUSE"
            if _is_generic_icd(str(row["diagnosis_code"]), str(row["diagnosis_name"])) and row["unique_procedure_count"] >= 3
            else "NORMAL",
            axis=1,
        )

    summary = {
        "flag_count": int(len(required_icd_flags)),
        "diagnosis_code_present": diagnosis_code_present,
        "diagnosis_name_present": diagnosis_name_present,
        "high_cost_threshold_vnd": _format_vnd(high_cost_threshold),
        "mismatch_case_count": int(len(mismatch_rows)),
        "reviewed_rows": int(reviewed_rows),
    }

    return {
        "tool_name": "04 - Rà ICD và chỉ định",
        "status": "completed",
        "summary": summary,
        "tables": {
            "required_icd_flags": required_icd_flags,
            "case_evidence_table": case_evidence_table,
            "icd_mismatch_case_evidence": icd_mismatch_case_evidence,
            "doctor_icd_mismatch_summary": doctor_icd_mismatch_summary,
            "procedure_icd_pair_table": procedure_icd_pair_table,
            "doctor_icd_usage_table": doctor_icd_usage_table,
        },
        "notes": [
            "Khớp ICD / chỉ định chỉ được xem là bằng chứng rà soát, không phải kết luận sai phạm.",
            "Việc dùng ICD chung lặp lại và các ca chỉ khớp theo bối cảnh được tách riêng để hội đồng xem trong ngữ cảnh.",
        ],
    }
