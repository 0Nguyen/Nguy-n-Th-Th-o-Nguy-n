from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from scripts.text_utils import contains_any, normalize_text


DEFAULT_EXCLUSION_KEYWORDS = [
    "emergency",
    "cap cuu",
    "cấp cứu",
    "inpatient",
    "noi tru",
    "nội trú",
    "pre op",
    "pre-op",
    "tien phau",
    "tiền phẫu",
    "surgery",
    "phau thuat",
    "phẫu thuật",
    "operation",
]

PRESET_LABELS = {
    "insured_out_of_insurance_review": "Insured patients + out-of-insurance orders",
    "insured_all_orders_review": "Insured patients + all orders",
    "insured_covered_orders_review": "Insured patients + covered orders",
    "all_patients_all_orders": "All patients + all orders",
    "uninsured_all_orders_reference": "Uninsured patients + all orders reference",
}

PRESET_DEFAULTS: dict[str, dict[str, Any]] = {
    "insured_out_of_insurance_review": {
        "patient_scope": "insured_only",
        "coverage_scope": "out_of_insurance_only",
        "benchmark_scope": "department",
    },
    "insured_all_orders_review": {
        "patient_scope": "insured_only",
        "coverage_scope": "all_orders",
        "benchmark_scope": "department_and_global",
    },
    "insured_covered_orders_review": {
        "patient_scope": "insured_only",
        "coverage_scope": "covered_only",
        "benchmark_scope": "department_and_global",
    },
    "all_patients_all_orders": {
        "patient_scope": "all_patients",
        "coverage_scope": "all_orders",
        "benchmark_scope": "global",
    },
    "uninsured_all_orders_reference": {
        "patient_scope": "uninsured_only",
        "coverage_scope": "all_orders",
        "benchmark_scope": "global",
    },
    "custom_manual_filter": {
        "patient_scope": "insured_only",
        "coverage_scope": "out_of_insurance_only",
        "benchmark_scope": "department",
    },
}


@dataclass
class AnalysisScope:
    preset_id: str = "insured_out_of_insurance_review"
    preset_name: str = PRESET_LABELS["insured_out_of_insurance_review"]
    patient_scope: str = "insured_only"
    coverage_scope: str = "out_of_insurance_only"
    selected_departments: list[str] = field(default_factory=list)
    selected_doctors: list[str] = field(default_factory=list)
    selected_procedures: list[str] = field(default_factory=list)
    selected_icd_codes: list[str] = field(default_factory=list)
    min_amount: float | None = None
    include_unknown_coverage: bool = True
    exclusion_keywords: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUSION_KEYWORDS))
    benchmark_scope: str = "department"


def safe_get_column(df: pd.DataFrame | None, column: str, default=None):
    if df is None or not isinstance(df, pd.DataFrame) or column not in df.columns:
        return default
    return df[column]


def normalize_list_filter(values) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        values = [values]
    items: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in {"<Missing>", "None", "nan"}:
            continue
        key = normalize_text(text)
        if not key or key in seen:
            continue
        seen.add(key)
        items.append(text)
    return items


def _coerce_float(value):
    if value in (None, "", "None"):
        return None
    try:
        numeric = float(value)
    except Exception:
        return None
    if pd.isna(numeric):
        return None
    return numeric


def get_default_scope() -> AnalysisScope:
    return AnalysisScope()


def build_scope_from_dict(data: dict | None) -> AnalysisScope:
    if not data:
        return get_default_scope()

    preset_id = str(data.get("preset_id") or data.get("preset") or "insured_out_of_insurance_review")
    preset_defaults = PRESET_DEFAULTS.get(preset_id, PRESET_DEFAULTS["insured_out_of_insurance_review"])
    preset_name = str(data.get("preset_name") or PRESET_LABELS.get(preset_id, "Custom manual filter"))

    patient_scope = str(data.get("patient_scope") or preset_defaults["patient_scope"])
    coverage_scope = str(data.get("coverage_scope") or preset_defaults["coverage_scope"])
    benchmark_scope = str(data.get("benchmark_scope") or preset_defaults["benchmark_scope"])

    include_unknown_coverage = bool(data.get("include_unknown_coverage", True))
    exclusion_keywords = normalize_list_filter(data.get("exclusion_keywords", list(DEFAULT_EXCLUSION_KEYWORDS)))

    return AnalysisScope(
        preset_id=preset_id,
        preset_name=preset_name,
        patient_scope=patient_scope,
        coverage_scope=coverage_scope,
        selected_departments=normalize_list_filter(data.get("selected_departments")),
        selected_doctors=normalize_list_filter(data.get("selected_doctors")),
        selected_procedures=normalize_list_filter(data.get("selected_procedures")),
        selected_icd_codes=normalize_list_filter(data.get("selected_icd_codes")),
        min_amount=_coerce_float(data.get("min_amount")),
        include_unknown_coverage=include_unknown_coverage,
        exclusion_keywords=exclusion_keywords,
        benchmark_scope=benchmark_scope,
    )


def apply_patient_scope(df: pd.DataFrame, scope: AnalysisScope) -> pd.DataFrame:
    if df is None or df.empty:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    working = df.copy()
    if "has_insurance_status" not in working.columns:
        return working

    if scope.patient_scope == "insured_only":
        return working[working["has_insurance_status"] == "yes"].copy()
    if scope.patient_scope == "uninsured_only":
        return working[working["has_insurance_status"] == "no"].copy()
    return working


def apply_business_coverage_rules(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    working = df.copy()
    if "has_insurance_status" in working.columns and "covered_status" in working.columns:
        uninsured_mask = working["has_insurance_status"].astype(str) == "no"
        if uninsured_mask.any():
            working.loc[uninsured_mask, "covered_status"] = "out_of_insurance"
    return working


def apply_coverage_scope(df: pd.DataFrame, scope: AnalysisScope) -> pd.DataFrame:
    if df is None or df.empty:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    working = df.copy()
    if "covered_status" not in working.columns:
        return working

    if scope.coverage_scope == "out_of_insurance_only":
        working = working[working["covered_status"] == "out_of_insurance"].copy()
    elif scope.coverage_scope == "covered_only":
        working = working[working["covered_status"] == "covered"].copy()
    elif scope.coverage_scope == "unknown_only":
        working = working[working["covered_status"] == "unknown"].copy()
    elif scope.coverage_scope == "all_orders":
        working = working.copy()

    if not scope.include_unknown_coverage and "covered_status" in working.columns:
        working = working[working["covered_status"] != "unknown"].copy()
    return working


def _filter_exact_normalized(df: pd.DataFrame, column: str, selected_values: list[str]) -> pd.DataFrame:
    if not selected_values or column not in df.columns:
        return df
    selected_norm = {normalize_text(value) for value in selected_values if normalize_text(value)}
    if not selected_norm:
        return df
    series = df[column].astype(str).map(normalize_text)
    return df[series.isin(selected_norm)].copy()


def _apply_exclusion_keywords(df: pd.DataFrame, keywords: list[str]) -> pd.DataFrame:
    if not keywords:
        return df
    text_columns = [column for column in ["procedure", "diagnosis_name", "diagnosis_code", "department"] if column in df.columns]
    if not text_columns:
        return df
    combined = df[text_columns].fillna("").astype(str).apply(lambda row: " ".join(row.tolist()), axis=1)
    mask = combined.apply(lambda value: contains_any(value, keywords))
    return df[~mask].copy()


def apply_dimension_filters(df: pd.DataFrame, scope: AnalysisScope) -> pd.DataFrame:
    if df is None or df.empty:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    working = df.copy()
    working = _filter_exact_normalized(working, "department", scope.selected_departments)
    working = _filter_exact_normalized(working, "doctor", scope.selected_doctors)
    working = _filter_exact_normalized(working, "procedure", scope.selected_procedures)
    working = _filter_exact_normalized(working, "diagnosis_code", scope.selected_icd_codes)
    if scope.min_amount is not None and "amount" in working.columns:
        working = working[pd.to_numeric(working["amount"], errors="coerce").fillna(0) >= float(scope.min_amount)].copy()
    working = _apply_exclusion_keywords(working, scope.exclusion_keywords)
    return working


def build_denominator_df(df: pd.DataFrame, scope: AnalysisScope) -> pd.DataFrame:
    working = apply_business_coverage_rules(df)
    working = apply_patient_scope(working, scope)
    working = apply_dimension_filters(working, scope)
    return working.copy()


def build_numerator_df(df: pd.DataFrame, scope: AnalysisScope) -> pd.DataFrame:
    working = build_denominator_df(df, scope)
    working = apply_coverage_scope(working, scope)
    return working.copy()


def build_reference_df(df: pd.DataFrame, scope: AnalysisScope) -> pd.DataFrame:
    denominator_df = build_denominator_df(df, scope)
    if scope.benchmark_scope == "global":
        return denominator_df.copy()
    if scope.benchmark_scope == "department_and_global":
        return denominator_df.copy()
    return denominator_df.copy()


def build_scope_summary(raw_df: pd.DataFrame, denominator_df: pd.DataFrame, numerator_df: pd.DataFrame, scope: AnalysisScope) -> dict:
    raw_rows = int(len(raw_df)) if isinstance(raw_df, pd.DataFrame) else 0
    denominator_rows = int(len(denominator_df)) if isinstance(denominator_df, pd.DataFrame) else 0
    numerator_rows = int(len(numerator_df)) if isinstance(numerator_df, pd.DataFrame) else 0
    denominator_patient_count = int(denominator_df["patient"].nunique()) if isinstance(denominator_df, pd.DataFrame) and "patient" in denominator_df.columns else 0
    numerator_patient_count = int(numerator_df["patient"].nunique()) if isinstance(numerator_df, pd.DataFrame) and "patient" in numerator_df.columns else 0

    return {
        "preset_id": scope.preset_id,
        "preset_name": scope.preset_name,
        "patient_scope": scope.patient_scope,
        "coverage_scope": scope.coverage_scope,
        "benchmark_scope": scope.benchmark_scope,
        "denominator_rows": denominator_rows,
        "numerator_rows": numerator_rows,
        "total_rows": raw_rows,
        "denominator_patient_count": denominator_patient_count,
        "numerator_patient_count": numerator_patient_count,
        "selected_departments": list(scope.selected_departments),
        "selected_doctors": list(scope.selected_doctors),
        "selected_procedures": list(scope.selected_procedures),
        "selected_icd_codes": list(scope.selected_icd_codes),
        "min_amount": scope.min_amount,
    }
