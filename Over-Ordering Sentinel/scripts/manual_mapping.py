from __future__ import annotations

import json
import re
import unicodedata

import pandas as pd

from scripts.column_mapper import COLUMN_ALIASES, REQUIRED
from scripts.value_mapper import coerce_status_choice


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


def build_column_candidates(raw_columns: list[str]) -> dict[str, list[str]]:
    candidates = {}
    normalized_candidates = []
    for column in raw_columns:
        if str(column).strip().lower().startswith("unnamed"):
            continue
        normalized_candidates.append(str(column))
    for canonical in COLUMN_ALIASES.keys():
        candidates[canonical] = ["<Missing>"] + normalized_candidates
    return candidates


def build_default_column_mapping(raw_columns: list[str]) -> dict[str, str | None]:
    mapping = {canonical: None for canonical in COLUMN_ALIASES.keys()}
    normalized_lookup = {normalize_header_name(col): col for col in raw_columns if not str(col).strip().lower().startswith("unnamed")}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases + [canonical]:
            source = normalized_lookup.get(normalize_header_name(alias))
            if source is not None:
                mapping[canonical] = source
                break
    return mapping


def apply_column_mapping(raw_df: pd.DataFrame, column_mapping: dict[str, str | None]) -> pd.DataFrame:
    df = pd.DataFrame(index=raw_df.index)
    for canonical in COLUMN_ALIASES.keys():
        source_column = column_mapping.get(canonical)
        if source_column and source_column in raw_df.columns:
            df[canonical] = raw_df[source_column]
    return df


def get_missing_required_columns(column_mapping: dict[str, str | None]) -> list[str]:
    return [canonical for canonical in REQUIRED if not column_mapping.get(canonical)]


def build_value_mapping_from_df(df: pd.DataFrame, kind: str) -> dict[str, str]:
    if kind not in {"has_insurance", "covered"}:
        return {}
    series = df[kind] if kind in df.columns else pd.Series([], dtype=object)
    unique_values = series.dropna().astype(str).tolist()
    mapping = {}
    for value in unique_values:
        mapping.setdefault(value, coerce_status_choice(value, kind))
    return mapping


def serialize_mapping_preset(column_mapping: dict, value_mapping: dict) -> str:
    payload = {"column_mapping": column_mapping, "value_mapping": value_mapping}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def load_mapping_preset(raw_text: str) -> dict:
    data = json.loads(raw_text)
    if not isinstance(data, dict):
        raise ValueError("Mapping preset must be a JSON object.")
    return {
        "column_mapping": data.get("column_mapping", {}) or {},
        "value_mapping": data.get("value_mapping", {}) or {},
    }
