from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd


@dataclass
class AnalysisContext:
    app_name: str = "Over-Ordering Sentinel"
    language_mode: str = "vi_en"
    df: Optional[pd.DataFrame] = None
    selected_tools: list[str] = field(default_factory=list)
    settings: dict = field(default_factory=dict)
    tool_results: list = field(default_factory=list)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key, None)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


def create_context(df: Optional[pd.DataFrame] = None, selected_tools: Optional[list[str]] = None):
    return AnalysisContext(df=df, selected_tools=list(selected_tools or []))
