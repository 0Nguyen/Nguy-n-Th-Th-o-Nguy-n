from __future__ import annotations

from io import BytesIO
import re
import unicodedata

import pandas as pd

from scripts.column_mapper import COLUMN_ALIASES, REQUIRED
from scripts.sheet_detector import is_description_sheet


HEADER_SCAN_ROWS = 20

HEADER_WEIGHTS = {
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


def _row_cells(row: pd.Series) -> list[str]:
    cells = []
    for value in row.tolist():
        text = normalize_header_name(value)
        if text:
            cells.append(text)
    return cells


def _cell_matches_alias(cell: str, alias: str) -> bool:
    if not cell:
        return False
    alias_norm = normalize_header_name(alias)
    if not alias_norm:
        return False
    return alias_norm == cell or alias_norm in cell or cell in alias_norm


def score_header_row(row_values: list[str]) -> dict:
    matched = {key: False for key in COLUMN_ALIASES.keys()}
    score = 0
    for canonical, aliases in COLUMN_ALIASES.items():
        for cell in row_values:
            if any(_cell_matches_alias(cell, alias) for alias in aliases):
                matched[canonical] = True
                score += HEADER_WEIGHTS.get(canonical, 1)
                break
    return {
        "score": score,
        "matched": matched,
        "missing_required": [col for col in REQUIRED if not matched.get(col)],
    }


def infer_header_row_for_sheet(file_bytes: bytes, sheet_name: str, max_scan_rows: int = HEADER_SCAN_ROWS) -> dict:
    preview = pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name, header=None, nrows=max_scan_rows, dtype=object)
    best = {
        "header_row": 0,
        "score": -1,
        "matched": {key: False for key in COLUMN_ALIASES.keys()},
        "missing_required": list(REQUIRED),
    }
    for row_index in range(len(preview.index)):
        row_cells = _row_cells(preview.iloc[row_index])
        row_score = score_header_row(row_cells)
        if row_score["score"] > best["score"]:
            best = {
                "header_row": row_index,
                **row_score,
            }
    if best["score"] < 0:
        best["score"] = 0
    return best


def infer_sheet_with_header(file_bytes: bytes, sheet_name: str, max_scan_rows: int = HEADER_SCAN_ROWS) -> dict:
    header_info = infer_header_row_for_sheet(file_bytes, sheet_name, max_scan_rows=max_scan_rows)
    raw_df = pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name, header=header_info["header_row"], dtype=object)
    raw_df = raw_df.loc[:, ~raw_df.columns.astype(str).str.startswith("Unnamed")]
    return {
        "sheet_name": sheet_name,
        "header_row": header_info["header_row"],
        "score": header_info["score"],
        "matched": header_info["matched"],
        "missing_required": header_info["missing_required"],
        "raw_df": raw_df,
    }


def infer_best_sheet_and_header(file_bytes: bytes, sheet_infos: list[dict] | None = None) -> dict | None:
    if sheet_infos is None:
        from scripts.sheet_detector import detect_excel_sheets

        sheet_infos = detect_excel_sheets(file_bytes)

    best = None
    for info in sheet_infos:
        if is_description_sheet(info["sheet_name"]):
            continue
        sheet_result = infer_header_row_for_sheet(file_bytes, info["sheet_name"])
        score = sheet_result["score"] + int(info.get("score", 0))
        candidate = {
            "sheet_name": info["sheet_name"],
            "header_row": sheet_result["header_row"],
            "score": score,
            "matched": sheet_result["matched"],
            "missing_required": sheet_result["missing_required"],
        }
        if best is None or candidate["score"] > best["score"]:
            best = candidate
    return best
