from __future__ import annotations

import re
import unicodedata
from typing import Iterable

import pandas as pd


def strip_accents(text: object) -> str:
    if text is None or pd.isna(text):
        return ""
    normalized = unicodedata.normalize("NFKD", str(text))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_text(text: object) -> str:
    if text is None or pd.isna(text):
        return ""
    text = strip_accents(text).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def contains_any(text: object, keywords: Iterable[str]) -> bool:
    haystack = normalize_text(text)
    return any(normalize_text(keyword) in haystack for keyword in keywords)


def safe_rate(numerator: float, denominator: float) -> float:
    return 0.0 if denominator in (0, None) else float(numerator) / float(denominator)


def format_pct(value: float) -> str:
    return f"{value:.2%}"


def format_vnd(value: float) -> float:
    if pd.isna(value):
        return 0.0
    return float(round(value, 0))
