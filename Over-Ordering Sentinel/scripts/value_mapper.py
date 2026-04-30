from __future__ import annotations

import re
import unicodedata

import pandas as pd

from scripts.column_mapper import normalize_covered_value, normalize_yes_no_value


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


HAS_INSURANCE_CHOICES = ["yes", "no", "unknown"]
COVERED_CHOICES = ["covered", "out_of_insurance", "unknown"]


def _normalize_choice_group(value: object, allowed_choices: list[str], default_choice: str) -> str:
    if value is None or pd.isna(value):
        return default_choice
    text = normalize_header_name(value)
    allowed_normalized = {normalize_header_name(choice): choice for choice in allowed_choices}
    if text in allowed_normalized:
        return allowed_normalized[text]
    return default_choice


def suggest_has_insurance_value(value: object) -> str:
    if value is None or pd.isna(value):
        return "unknown"
    text = normalize_header_name(value)
    yes_tokens = {
        "co",
        "co bao hiem",
        "bhyt",
        "bao hiem y te",
        "insured",
        "patienthasinsurance",
        "insurancepatient",
        "yes",
        "y",
        "true",
        "1",
    }
    no_tokens = {
        "khong",
        "khong co",
        "dich vu",
        "tu chi tra",
        "uninsured",
        "no",
        "n",
        "false",
        "0",
    }
    if text in yes_tokens or text.startswith("co ") or "bhyt" in text:
        return "yes"
    if text in no_tokens or text.startswith("khong ") or "tu chi tra" in text:
        return "no"
    return normalize_yes_no_value(value)


def suggest_covered_value(value: object) -> str:
    if value is None or pd.isna(value):
        return "unknown"
    text = normalize_header_name(value)
    covered_tokens = {
        "covered",
        "trong",
        "trong bao hiem",
        "trong goi",
        "duoc chi tra",
        "co",
        "yes",
        "y",
        "true",
        "1",
    }
    out_tokens = {
        "out",
        "ngoai",
        "ngoai bao hiem",
        "ngoai goi",
        "tu chi tra",
        "khong",
        "khong chi tra",
        "not covered",
        "uncovered",
        "no",
        "n",
        "false",
        "0",
    }
    if text in covered_tokens or text.startswith("trong ") or "duoc chi tra" in text:
        return "covered"
    if text in out_tokens or text.startswith("ngoai ") or "tu chi tra" in text:
        return "out_of_insurance"
    return normalize_covered_value(value)


def build_unique_value_options(series: pd.Series, limit: int = 30) -> list[str]:
    values = []
    seen = set()
    for value in series.dropna().astype(str).tolist():
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        values.append(normalized)
        if len(values) >= limit:
            break
    return values


def apply_value_mapping(series: pd.Series, mapping: dict[str, str], kind: str) -> pd.Series:
    if kind == "has_insurance":
        return series.apply(lambda v: mapping.get(str(v).strip(), suggest_has_insurance_value(v)))
    if kind == "covered":
        return series.apply(lambda v: mapping.get(str(v).strip(), suggest_covered_value(v)))
    return series


def coerce_status_choice(value: object, kind: str) -> str:
    if kind == "has_insurance":
        return _normalize_choice_group(value, HAS_INSURANCE_CHOICES, "unknown")
    if kind == "covered":
        return _normalize_choice_group(value, COVERED_CHOICES, "unknown")
    return "unknown"
