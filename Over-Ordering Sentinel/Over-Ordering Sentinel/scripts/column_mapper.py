from __future__ import annotations

import re
import unicodedata

import pandas as pd


COLUMN_ALIASES = {
    "doctor": [
        "Tên bác sĩ / DoctorName",
        "DoctorName",
        "ProviderID",
        "Tên bác sĩ",
        "Bác sĩ",
        "Doctor",
        "Provider",
    ],
    "patient": [
        "Tên bệnh nhân / PatientName",
        "PatientName",
        "PatientID",
        "Tên bệnh nhân",
        "Bệnh nhân",
        "Patient",
    ],
    "has_insurance": [
        "Có bảo hiểm / HasInsurance",
        "Có bảo hiểm",
        "HasInsurance",
        "PatientHasInsurance",
        "InsurancePatient",
        "InsuredPatient",
        "Bệnh nhân có bảo hiểm",
    ],
    "covered": [
        "Trong bảo hiểm / CoveredByInsurance",
        "Trong bảo hiểm",
        "CoveredByInsurance",
        "InsuranceCovered",
        "Covered",
        "PolicyCovered",
        "CoveredByPolicy",
        "Trong gói chi trả / CoveredByPolicy",
        "Trong gói chi trả",
    ],
    "department": ["Khoa / Department", "Department", "Khoa"],
    "amount": ["Số tiền yêu cầu thanh toán VND / ClaimAmountVND", "ClaimAmountVND", "ClaimAmount", "Thành tiền", "Số tiền", "Amount"],
    "procedure": ["Tên dịch vụ / ProcedureName", "ProcedureName", "Tên dịch vụ", "Mã dịch vụ / ProcedureCode", "ProcedureCode"],
    "claim_id": ["Mã hồ sơ / ClaimID", "ClaimID", "Mã hồ sơ", "Mã lượt khám", "VisitID"],
    "diagnosis_code": ["Mã ICD10 / DiagnosisCode", "DiagnosisCode", "ICD10", "Mã ICD10", "ICD"],
    "diagnosis_name": ["Chẩn đoán / DiagnosisName", "DiagnosisName", "Chẩn đoán", "Diagnosis"],
}

REQUIRED = ["doctor", "patient", "covered"]
OPTIONAL_DEFAULTS = {
    "has_insurance": "no",
}

CANONICAL_LABELS = {
    "doctor": "Tên bác sĩ / DoctorName",
    "patient": "Tên bệnh nhân / PatientName",
    "has_insurance": "Có bảo hiểm / HasInsurance",
    "covered": "Trong bảo hiểm / CoveredByInsurance",
}


class ColumnMappingError(Exception):
    def __init__(self, missing_required, found_columns, required_columns, message, mapping_report=None, status_debug=None):
        super().__init__(message)
        self.missing_required = list(missing_required)
        self.found_columns = list(found_columns)
        self.required_columns = list(required_columns)
        self.message = message
        self.mapping_report = mapping_report or {}
        self.status_debug = status_debug or {}


def normalize_header_name(value) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value)
    if not text.strip():
        return ""
    text = text.replace("\u00a0", " ")
    text = text.replace("\n", " ").replace("\r", " ")
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[\/\-\_\.\:]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _is_unnamed_column(column_name: str) -> bool:
    normalized = normalize_header_name(column_name)
    raw = str(column_name).strip().lower()
    return raw.startswith("unnamed") or normalized.startswith("unnamed")


def _build_normalized_alias_map() -> dict[str, str]:
    normalized_alias_to_canonical = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            normalized_alias_to_canonical[normalize_header_name(alias)] = canonical
        normalized_alias_to_canonical[normalize_header_name(canonical)] = canonical
    return normalized_alias_to_canonical


NORMALIZED_ALIAS_TO_CANONICAL = _build_normalized_alias_map()


def _make_default_series(series_length: int, canonical: str) -> pd.Series:
    if canonical == "department":
        return pd.Series(["Không rõ khoa / Unknown department"] * series_length)
    if canonical == "amount":
        return pd.Series([0] * series_length)
    if canonical == "procedure":
        return pd.Series(["Không rõ dịch vụ / Unknown procedure"] * series_length)
    if canonical == "claim_id":
        return pd.Series([f"ROW{i+1:06d}" for i in range(series_length)])
    if canonical in {"diagnosis_code", "diagnosis_name"}:
        return pd.Series([""] * series_length)
    return pd.Series([""] * series_length)


def normalize_yes_no_value(value):
    """Normalize yes/no values to: yes, no, unknown."""
    if pd.isna(value):
        return "unknown"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)) and not pd.isna(value):
        if value == 1:
            return "yes"
        if value == 0:
            return "no"
    text = normalize_header_name(value)
    if not text:
        return "unknown"
    yes_tokens = {"yes", "y", "co", "c", "insured", "patienthasinsurance", "insurancepatient", "co bao hiem", "1", "true", "duoc bao hiem"}
    no_tokens = {"no", "n", "khong", "khong co", "uninsured", "not insured", "false", "0"}
    if text in no_tokens or text.startswith("khong ") or text.endswith(" khong"):
        return "no"
    if text in yes_tokens or text.startswith("co ") or text.endswith(" co"):
        return "yes"
    return "unknown"


def normalize_covered_value(value):
    """Normalize covered status to: covered, out_of_insurance, unknown."""
    if pd.isna(value):
        return "unknown"
    if isinstance(value, bool):
        return "covered" if value else "out_of_insurance"
    if isinstance(value, (int, float)) and not pd.isna(value):
        if value == 1:
            return "covered"
        if value == 0:
            return "out_of_insurance"
    text = normalize_header_name(value)
    if not text:
        return "unknown"
    covered_tokens = {
        "covered",
        "trong",
        "trong bao hiem",
        "duoc chi tra",
        "duoc bao hiem chi tra",
        "in policy",
        "in insurance",
        "policy covered",
        "insurance covered",
        "1",
        "yes",
        "true",
        "co",
        "trong goi chi tra",
    }
    out_tokens = {
        "out of insurance",
        "ngoai",
        "ngoai bao hiem",
        "khong chi tra",
        "not covered",
        "no",
        "false",
        "0",
        "uncovered",
    }
    if text in out_tokens or text.startswith("ngoai ") or "ngoai bao hiem" in text:
        return "out_of_insurance"
    if text in covered_tokens or text.startswith("trong ") or "duoc chi tra" in text:
        return "covered"
    return "unknown"


def _alias_quality(alias: str, column_name: str) -> int:
    alias_norm = normalize_header_name(alias)
    col_norm = normalize_header_name(column_name)
    if not alias_norm or not col_norm:
        return -1
    if alias_norm == col_norm:
        return 4
    if col_norm.startswith(alias_norm):
        return 3
    if alias_norm in col_norm or col_norm in alias_norm:
        return 2
    return 0


def _column_non_null_count(df: pd.DataFrame, column_name: str) -> int:
    try:
        idx = df.columns.get_loc(column_name)
        if isinstance(idx, slice):
            return int(df.iloc[:, idx.start].notna().sum())
        if isinstance(idx, (list, tuple)):
            return int(df.iloc[:, idx[0]].notna().sum())
        return int(df.iloc[:, idx].notna().sum())
    except Exception:
        return 0


def _candidate_is_better(new_candidate, old_candidate) -> bool:
    if old_candidate is None:
        return True
    new_score, new_non_null, new_exact, new_order = new_candidate
    old_score, old_non_null, old_exact, old_order = old_candidate
    return (new_score, new_non_null, new_exact, -new_order) > (old_score, old_non_null, old_exact, -old_order)


def _friendly_required_message(canonical: str) -> str:
    label = CANONICAL_LABELS.get(canonical, canonical)
    if canonical == "has_insurance":
        return f"Thiếu cột bắt buộc: {label}. App cần biết bệnh nhân có bảo hiểm hay không."
    if canonical == "covered":
        return f"Thiếu cột bắt buộc: {label}. App cần biết từng chỉ định có được bảo hiểm chi trả hay không."
    if canonical == "doctor":
        return f"Thiếu cột bắt buộc: {label}."
    if canonical == "patient":
        return f"Thiếu cột bắt buộc: {label}."
    return f"Thiếu cột bắt buộc: {label}."


def _build_mapping_report(raw_df: pd.DataFrame, resolved_columns: dict[str, dict], missing_required: list[str]) -> list[dict]:
    report = []
    for canonical, info in resolved_columns.items():
        report.append(
            {
                "canonical": canonical,
                "source_column": info.get("source_column"),
                "normalized_source_column": info.get("normalized_source_column"),
                "matched_alias": info.get("matched_alias"),
                "match_quality": info.get("match_quality"),
                "non_null_count": info.get("non_null_count"),
                "source_order": info.get("source_order"),
                "is_default": info.get("is_default", False),
            }
        )
    for canonical in missing_required:
        report.append(
            {
                "canonical": canonical,
                "source_column": None,
                "normalized_source_column": None,
                "matched_alias": None,
                "match_quality": 0,
                "non_null_count": 0,
                "source_order": None,
                "is_default": True,
            }
        )
    return report


def normalize_columns(raw_df: pd.DataFrame):
    df = raw_df.copy()
    raw_columns = list(raw_df.columns)
    found_columns = [str(col) for col in raw_columns if not _is_unnamed_column(col)]
    normalized_alias_to_canonical = NORMALIZED_ALIAS_TO_CANONICAL

    candidates: dict[str, dict] = {}
    for order, raw_column in enumerate(raw_columns):
        if _is_unnamed_column(raw_column):
            continue
        normalized_column = normalize_header_name(raw_column)
        if not normalized_column:
            continue
        canonical = normalized_alias_to_canonical.get(normalized_column)
        if canonical is None:
            continue

        matched_alias = next((alias for alias in COLUMN_ALIASES[canonical] if normalize_header_name(alias) == normalized_column), canonical)
        candidate = {
            "raw_column": raw_column,
            "normalized_source_column": normalized_column,
            "matched_alias": matched_alias,
            "match_quality": _alias_quality(matched_alias, raw_column),
            "non_null_count": int(df[raw_column].notna().sum()),
            "source_order": order,
        }
        current = candidates.get(canonical)
        if current is None:
            candidates[canonical] = candidate
            continue

        if candidate["non_null_count"] == 0 and current["non_null_count"] > 0:
            continue
        if current["non_null_count"] == 0 and candidate["non_null_count"] > 0:
            candidates[canonical] = candidate
            continue

        new_exact = int(normalize_header_name(candidate["matched_alias"]) == candidate["normalized_source_column"])
        old_exact = int(normalize_header_name(current["matched_alias"]) == current["normalized_source_column"])
        new_tuple = (candidate["match_quality"], candidate["non_null_count"], new_exact, candidate["source_order"])
        old_tuple = (current["match_quality"], current["non_null_count"], old_exact, current["source_order"])
        if _candidate_is_better(new_tuple, old_tuple):
            candidates[canonical] = candidate

    resolved_columns: dict[str, dict] = {}
    for canonical in COLUMN_ALIASES.keys():
        candidate = candidates.get(canonical)
        if candidate is not None:
            df[canonical] = df[candidate["raw_column"]]
            resolved_columns[canonical] = {
                "source_column": str(candidate["raw_column"]),
                "normalized_source_column": candidate["normalized_source_column"],
                "matched_alias": candidate["matched_alias"],
                "match_quality": candidate["match_quality"],
                "non_null_count": candidate["non_null_count"],
                "source_order": candidate["source_order"],
                "is_default": False,
            }
        else:
            resolved_columns[canonical] = {
                "source_column": None,
                "normalized_source_column": None,
                "matched_alias": None,
                "match_quality": 0,
                "non_null_count": 0,
                "source_order": None,
                "is_default": True,
            }

    missing_required = [canonical for canonical in REQUIRED if canonical not in df.columns or resolved_columns.get(canonical, {}).get("source_column") is None]
    if missing_required:
        message = " ".join(_friendly_required_message(canonical) for canonical in missing_required)
        mapping_report = _build_mapping_report(raw_df, resolved_columns, missing_required)
        status_debug = {}
        for canonical in REQUIRED:
            if canonical in df.columns:
                status_debug[f"{canonical}_raw_unique"] = df[canonical].dropna().astype(str).unique().tolist()[:20]
        raise ColumnMappingError(
            missing_required=missing_required,
            found_columns=found_columns,
            required_columns=REQUIRED,
            message=message,
            mapping_report=mapping_report,
            status_debug=status_debug,
        )

    if "department" not in df.columns:
        df["department"] = "Không rõ khoa / Unknown department"
    if "amount" not in df.columns:
        df["amount"] = 0
    if "procedure" not in df.columns:
        df["procedure"] = "Không rõ dịch vụ / Unknown procedure"
    if "has_insurance" not in df.columns:
        df["has_insurance"] = OPTIONAL_DEFAULTS["has_insurance"]
    if "claim_id" not in df.columns:
        df["claim_id"] = [f"ROW{i+1:06d}" for i in range(len(df))]
    if "diagnosis_code" not in df.columns:
        df["diagnosis_code"] = ""
    if "diagnosis_name" not in df.columns:
        df["diagnosis_name"] = ""

    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["has_insurance_status"] = df["has_insurance"].apply(normalize_yes_no_value)
    df["covered_status"] = df["covered"].apply(normalize_covered_value)

    df.attrs["column_mapping_report"] = {
        "raw_columns": [str(col) for col in raw_df.columns],
        "mapped_columns": _build_mapping_report(raw_df, resolved_columns, []),
        "missing_required": [],
    }
    df.attrs["status_debug"] = {
        "has_insurance_source_missing": resolved_columns.get("has_insurance", {}).get("source_column") is None,
        "has_insurance_raw_unique": df["has_insurance"].dropna().astype(str).unique().tolist()[:20],
        "has_insurance_status_counts": df["has_insurance_status"].value_counts(dropna=False).to_dict(),
        "covered_raw_unique": df["covered"].dropna().astype(str).unique().tolist()[:20],
        "covered_status_counts": df["covered_status"].value_counts(dropna=False).to_dict(),
    }
    df.attrs["analysis_assumptions"] = {
        "has_insurance_defaulted_to_no": resolved_columns.get("has_insurance", {}).get("source_column") is None,
        "has_insurance_assumed_value": "no" if resolved_columns.get("has_insurance", {}).get("source_column") is None else None,
        "analysis_fallback_label": "uninsured_reference" if resolved_columns.get("has_insurance", {}).get("source_column") is None else None,
    }
    return df


def get_column_report(raw_df: pd.DataFrame):
    rows = []
    normalized_alias_to_canonical = NORMALIZED_ALIAS_TO_CANONICAL
    for raw_column in raw_df.columns:
        if _is_unnamed_column(raw_column):
            continue
        normalized_column = normalize_header_name(raw_column)
        canonical = normalized_alias_to_canonical.get(normalized_column)
        if canonical is None:
            rows.append(
                {
                    "Raw column": str(raw_column),
                    "Normalized": normalized_column,
                    "Canonical": "",
                    "Alias matched": "",
                    "Status": "Unmapped",
                }
            )
            continue
        matched_alias = next((alias for alias in COLUMN_ALIASES[canonical] if normalize_header_name(alias) == normalized_column), canonical)
        rows.append(
            {
                "Raw column": str(raw_column),
                "Normalized": normalized_column,
                "Canonical": canonical,
                "Alias matched": matched_alias,
                "Status": "Mapped",
            }
        )
    return pd.DataFrame(rows)
