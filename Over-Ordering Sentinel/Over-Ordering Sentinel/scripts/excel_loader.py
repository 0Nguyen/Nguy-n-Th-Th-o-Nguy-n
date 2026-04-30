from __future__ import annotations

from io import BytesIO

import pandas as pd


def read_uploaded_file_bytes(uploaded_file) -> bytes:
    if uploaded_file is None:
        return b""
    if hasattr(uploaded_file, "seek"):
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
    if hasattr(uploaded_file, "getvalue"):
        return uploaded_file.getvalue()
    if hasattr(uploaded_file, "read"):
        return uploaded_file.read()
    raise TypeError("Unsupported uploaded file object.")


def get_excel_sheet_names(file_bytes: bytes) -> list[str]:
    with pd.ExcelFile(BytesIO(file_bytes)) as excel:
        return list(excel.sheet_names)


def read_excel_sheet(file_bytes: bytes, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name, dtype=object)


def get_sheet_columns(file_bytes: bytes, sheet_name: str) -> list[str]:
    try:
        preview_df = pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name, nrows=0)
        return list(preview_df.columns)
    except Exception:
        try:
            return list(read_excel_sheet(file_bytes, sheet_name).columns)
        except Exception:
            return []


def preview_excel_sheet(file_bytes: bytes, sheet_name: str, max_rows: int = 5) -> pd.DataFrame:
    try:
        return pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name, nrows=max_rows, dtype=object)
    except Exception:
        try:
            return read_excel_sheet(file_bytes, sheet_name).head(max_rows)
        except Exception:
            return pd.DataFrame()
