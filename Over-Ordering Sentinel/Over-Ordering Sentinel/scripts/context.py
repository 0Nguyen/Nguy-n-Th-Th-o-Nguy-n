from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd

from scripts.analysis_scope import (
    AnalysisScope,
    build_denominator_df,
    build_numerator_df,
    build_reference_df,
    build_scope_from_dict,
    build_scope_summary,
    get_default_scope,
)


@dataclass
class AnalysisContext:
    app_name: str = "Over-Ordering Sentinel"
    language_mode: str = "vi_en"
    raw_df: Optional[pd.DataFrame] = None
    df: Optional[pd.DataFrame] = None
    analysis_scope: Optional[AnalysisScope] = None
    denominator_df: Optional[pd.DataFrame] = None
    numerator_df: Optional[pd.DataFrame] = None
    reference_df: Optional[pd.DataFrame] = None
    scope_summary: dict = field(default_factory=dict)
    selected_tools: list[str] = field(default_factory=list)
    settings: dict = field(default_factory=dict)
    tool_results: list = field(default_factory=list)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key, None)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


def create_context(
    df: Optional[pd.DataFrame] = None,
    selected_tools: Optional[list[str]] = None,
    analysis_scope: Optional[AnalysisScope | dict] = None,
):
    if analysis_scope is None:
        scope = get_default_scope()
    elif isinstance(analysis_scope, AnalysisScope):
        scope = analysis_scope
    else:
        scope = build_scope_from_dict(analysis_scope)

    denominator_df = build_denominator_df(df, scope) if df is not None else pd.DataFrame()
    numerator_df = build_numerator_df(df, scope) if df is not None else pd.DataFrame()
    reference_df = build_reference_df(df, scope) if df is not None else pd.DataFrame()
    scope_summary = build_scope_summary(df if df is not None else pd.DataFrame(), denominator_df, numerator_df, scope)

    return AnalysisContext(
        raw_df=df,
        df=df,
        analysis_scope=scope,
        denominator_df=denominator_df,
        numerator_df=numerator_df,
        reference_df=reference_df,
        scope_summary=scope_summary,
        selected_tools=list(selected_tools or []),
    )
