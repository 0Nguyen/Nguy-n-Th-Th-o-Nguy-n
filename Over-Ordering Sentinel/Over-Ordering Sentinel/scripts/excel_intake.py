from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from scripts.column_inference import infer_best_sheet_and_header, infer_sheet_with_header
from scripts.excel_loader import get_excel_sheet_names, read_uploaded_file_bytes
from scripts.sheet_detector import detect_excel_sheets, find_best_data_sheet, is_description_sheet


@dataclass
class ExcelIntakeResult:
    file_bytes: bytes
    file_hash: str
    sheet_infos: list[dict] = field(default_factory=list)
    best_sheet: str | None = None
    best_header_row: int = 0
    selected_sheet: str | None = None


def load_uploaded_excel(uploaded_file) -> ExcelIntakeResult:
    file_bytes = read_uploaded_file_bytes(uploaded_file)
    file_hash = hashlib.md5(file_bytes).hexdigest() if file_bytes else ""
    sheet_infos = detect_excel_sheets(file_bytes) if file_bytes else []
    best_sheet = find_best_data_sheet(file_bytes) if file_bytes else None
    best_sheet_info = infer_best_sheet_and_header(file_bytes, sheet_infos) if file_bytes else None
    return ExcelIntakeResult(
        file_bytes=file_bytes,
        file_hash=file_hash,
        sheet_infos=sheet_infos,
        best_sheet=best_sheet,
        best_header_row=best_sheet_info["header_row"] if best_sheet_info else 0,
        selected_sheet=best_sheet,
    )


def get_sheet_names(file_bytes: bytes) -> list[str]:
    return get_excel_sheet_names(file_bytes)


def infer_selected_sheet_details(file_bytes: bytes, sheet_name: str) -> dict:
    return infer_sheet_with_header(file_bytes, sheet_name)


def is_data_sheet_valid(sheet_info: dict) -> bool:
    return bool(sheet_info and sheet_info.get("is_valid_data_sheet") and not is_description_sheet(sheet_info.get("sheet_name", "")))
