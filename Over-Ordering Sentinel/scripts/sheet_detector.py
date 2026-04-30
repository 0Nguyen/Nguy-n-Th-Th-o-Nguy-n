from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from scripts.column_mapper import COLUMN_ALIASES, REQUIRED
from scripts.excel_loader import get_excel_sheet_names, get_sheet_columns


DESCRIPTION_SHEET_NAMES = {
    "readme",
    "guide",
    "huong dan",
    "instruction",
    "instructions",
    "mo ta",
    "mota",
    "description",
    "about",
    "info",
    "note",
    "notes",
}


def normalize_text(value: str) -> str:
    if value is None:
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


def is_description_sheet(sheet_name: str) -> bool:
    normalized = normalize_text(sheet_name)
    if not normalized:
        return False
    return any(token in normalized for token in DESCRIPTION_SHEET_NAMES)


def _column_matches(alias: str, column_name: str) -> bool:
    alias_norm = normalize_text(alias)
    column_norm = normalize_text(column_name)
    if not alias_norm or not column_norm:
        return False
    return alias_norm == column_norm or alias_norm in column_norm or column_norm in alias_norm


def score_sheet_columns(columns: list[str]) -> dict:
    matched = {key: False for key in COLUMN_ALIASES.keys()}
    for canonical, aliases in COLUMN_ALIASES.items():
        for col in columns:
            if str(col).strip().lower().startswith("unnamed"):
                continue
            if any(_column_matches(alias, col) for alias in aliases):
                matched[canonical] = True
                break

    score_weights = {
        "doctor": 3,
        "patient": 3,
        "has_insurance": 4,
        "covered": 4,
        "department": 1,
        "amount": 1,
        "procedure": 1,
        "claim_id": 1,
        "diagnosis_code": 1,
        "diagnosis_name": 1,
    }
    score = sum(weight for key, weight in score_weights.items() if matched.get(key))
    missing_required = [col for col in REQUIRED if not matched.get(col)]
    return {"score": score, "matched": matched, "missing_required": missing_required}


def detect_excel_sheets(file_bytes: bytes) -> list[dict]:
    sheets = []
    for sheet_name in get_excel_sheet_names(file_bytes):
        columns = get_sheet_columns(file_bytes, sheet_name)
        sheet_score = score_sheet_columns(columns)
        is_description = is_description_sheet(sheet_name)
        is_valid_data_sheet = (
            not is_description
            and all(sheet_score["matched"].get(req, False) for req in REQUIRED)
        )
        sheets.append(
            {
                "sheet_name": sheet_name,
                "is_description": is_description,
                "score": sheet_score["score"],
                "is_valid_data_sheet": is_valid_data_sheet,
                "matched": sheet_score["matched"],
                "missing_required": sheet_score["missing_required"],
                "columns": columns,
            }
        )
    return sheets


def find_best_data_sheet(file_bytes: bytes) -> str | None:
    sheet_infos = detect_excel_sheets(file_bytes)
    valid_sheets = [(idx, info) for idx, info in enumerate(sheet_infos) if info["is_valid_data_sheet"]]
    if not valid_sheets:
        return None
    valid_sheets.sort(key=lambda item: (item[1]["score"], -item[0]), reverse=True)
    return valid_sheets[0][1]["sheet_name"]
