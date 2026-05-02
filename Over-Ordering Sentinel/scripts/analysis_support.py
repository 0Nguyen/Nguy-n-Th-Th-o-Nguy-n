from __future__ import annotations

from dataclasses import is_dataclass
from typing import Any

import pandas as pd

from scripts.analysis_scope import AnalysisScope, build_denominator_df, build_numerator_df, build_reference_df, get_default_scope


def _fallback_denominator(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    if "has_insurance_status" in df.columns:
        return df[df["has_insurance_status"] == "yes"].copy()
    return df.copy()


def _fallback_numerator(df: pd.DataFrame) -> pd.DataFrame:
    denominator = _fallback_denominator(df)
    if "covered_status" in denominator.columns:
        return denominator[denominator["covered_status"] == "out_of_insurance"].copy()
    return denominator.copy()


def get_scope_from_context(context: Any) -> AnalysisScope:
    scope = getattr(context, "analysis_scope", None)
    if isinstance(scope, AnalysisScope):
        return scope
    if isinstance(scope, dict):
        from scripts.analysis_scope import build_scope_from_dict

        return build_scope_from_dict(scope)
    return get_default_scope()


def get_context_frames(df: pd.DataFrame, context: Any):
    scope = get_scope_from_context(context)
    denominator_df = getattr(context, "denominator_df", None)
    numerator_df = getattr(context, "numerator_df", None)
    reference_df = getattr(context, "reference_df", None)

    if denominator_df is None or not isinstance(denominator_df, pd.DataFrame):
        try:
            denominator_df = build_denominator_df(df, scope)
        except Exception:
            denominator_df = _fallback_denominator(df)

    if numerator_df is None or not isinstance(numerator_df, pd.DataFrame):
        try:
            numerator_df = build_numerator_df(df, scope)
        except Exception:
            numerator_df = _fallback_numerator(df)

    if reference_df is None or not isinstance(reference_df, pd.DataFrame):
        try:
            reference_df = build_reference_df(df, scope)
        except Exception:
            reference_df = denominator_df.copy()

    if denominator_df is None or denominator_df.empty:
        denominator_df = _fallback_denominator(df)
    if numerator_df is None or numerator_df.empty:
        numerator_df = _fallback_numerator(df)
    if reference_df is None or reference_df.empty:
        reference_df = denominator_df.copy()

    return scope, denominator_df.copy(), numerator_df.copy(), reference_df.copy()


def to_numeric_series(series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def format_amount(value) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").fillna(0).iloc[0]
    return float(round(float(numeric), 0))


def safe_dataframe(df: pd.DataFrame | None) -> pd.DataFrame:
    if isinstance(df, pd.DataFrame):
        return df.copy()
    return pd.DataFrame()


def first_nonempty(values, default=""):
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() != "nan":
            return text
    return default
