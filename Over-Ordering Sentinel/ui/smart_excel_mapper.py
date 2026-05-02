from __future__ import annotations

import hashlib
import json
from io import BytesIO

import pandas as pd
import streamlit as st

from scripts.column_inference import infer_best_sheet_and_header, infer_header_row_for_sheet
from scripts import column_mapper as cm
from scripts.excel_intake import load_uploaded_excel
from scripts.manual_mapping import (
    apply_column_mapping,
    build_default_column_mapping,
    get_missing_required_columns,
    load_mapping_preset,
    serialize_mapping_preset,
)
from scripts.sheet_detector import detect_excel_sheets, find_best_data_sheet, is_description_sheet
from scripts.value_mapper import apply_value_mapping, build_unique_value_options, coerce_status_choice, suggest_covered_value, suggest_has_insurance_value
from scripts.i18n import get_language, t

CANONICAL_LABELS = getattr(cm, "CANONICAL_LABELS", {})
COLUMN_ALIASES = getattr(cm, "COLUMN_ALIASES", {})
ColumnMappingError = getattr(cm, "ColumnMappingError")
normalize_columns = getattr(cm, "normalize_columns")


def _lang() -> str:
    return get_language()


def _u(vi: str, en: str) -> str:
    return en if _lang() == "en" else vi


def _canonical_label(canonical: str) -> str:
    if _lang() == "en":
        return {
            "doctor": "Doctor",
            "patient": "Patient",
            "has_insurance": "Has insurance",
            "covered": "Covered by insurance",
            "department": "Department",
            "amount": "Amount",
            "procedure": "Procedure",
            "claim_id": "Claim ID",
            "diagnosis_code": "ICD code",
            "diagnosis_name": "Diagnosis",
        }.get(canonical, canonical)
    return CANONICAL_LABELS.get(canonical, canonical)


def _file_hash(file_bytes: bytes) -> str:
    return hashlib.md5(file_bytes).hexdigest()


def _state_key(file_hash: str, suffix: str) -> str:
    return f"smart_mapper_{file_hash}_{suffix}"


def _sheet_label(sheet_info: dict) -> str:
    sheet_name = sheet_info["sheet_name"]
    if sheet_info.get("is_valid_data_sheet"):
        return f"{t('data_sheet')} ✅ - {sheet_name}"
    if sheet_info.get("is_description"):
        return f"{t('description_sheet')} ℹ️ - {sheet_name}"
    return f"{t('sheet_status_invalid')} ⚠️ - {sheet_name}"


def _ensure_state(file_hash: str, best_sheet: str | None):
    key = _state_key(file_hash, "state")
    if key not in st.session_state:
        st.session_state[key] = {
            "selected_sheet": best_sheet,
            "manual_mode": False,
            "confirmed": False,
            "last_signature": "",
            "preset_loaded": False,
        }
        st.session_state["analysis_tools_visible"] = False
    state = st.session_state[key]
    if best_sheet and not state.get("selected_sheet"):
        state["selected_sheet"] = best_sheet
    return state


def _current_column_mapping(file_hash: str, selected_sheet: str, raw_columns: list[str], auto_mapping: dict[str, str | None]) -> dict[str, str | None]:
    mapping = {}
    for canonical in COLUMN_ALIASES.keys():
        widget_key = _state_key(file_hash, f"{selected_sheet}_column_{canonical}")
        default_value = auto_mapping.get(canonical) or "<Missing>"
        if widget_key not in st.session_state:
            st.session_state[widget_key] = default_value
        value = st.session_state.get(widget_key, default_value)
        mapping[canonical] = None if value in (None, "<Missing>") else value
    return mapping


def _set_auto_column_mapping(file_hash: str, selected_sheet: str, auto_mapping: dict[str, str | None]) -> None:
    for canonical in COLUMN_ALIASES.keys():
        widget_key = _state_key(file_hash, f"{selected_sheet}_column_{canonical}")
        st.session_state[widget_key] = auto_mapping.get(canonical) or "<Missing>"


def _apply_preset(file_hash: str, selected_sheet: str, preset: dict, raw_columns: list[str]) -> None:
    column_mapping = preset.get("column_mapping", {}) or {}
    value_mapping = preset.get("value_mapping", {}) or {}
    for canonical in COLUMN_ALIASES.keys():
        widget_key = _state_key(file_hash, f"{selected_sheet}_column_{canonical}")
        value = column_mapping.get(canonical)
        st.session_state[widget_key] = value if value in raw_columns else "<Missing>"
    for kind in ("has_insurance", "covered"):
        for raw_value, normalized_value in (value_mapping.get(kind, {}) or {}).items():
            widget_key = _state_key(file_hash, f"{selected_sheet}_{kind}_{hashlib.md5(str(raw_value).encode('utf-8')).hexdigest()[:8]}")
            st.session_state[widget_key] = coerce_status_choice(normalized_value, kind)


def _apply_value_mapping_to_working_df(raw_df: pd.DataFrame, column_mapping: dict[str, str | None], value_mapping: dict[str, dict[str, str]]) -> pd.DataFrame:
    working_df = apply_column_mapping(raw_df, column_mapping)
    for kind in ("has_insurance", "covered"):
        source_column = column_mapping.get(kind)
        if not source_column or source_column not in raw_df.columns:
            continue
        mapped_series = apply_value_mapping(raw_df[source_column], value_mapping.get(kind, {}), kind)
        working_df[kind] = mapped_series
    return working_df


def _preview_summary(df: pd.DataFrame) -> dict[str, object]:
    insured_df = df[df["has_insurance_status"] == "yes"].copy()
    return {
        "total_rows": int(len(df)),
        "insured_patients": int(insured_df["patient"].nunique()) if "patient" in insured_df.columns else 0,
        "insured_orders": int(len(insured_df)),
        "out_of_insurance_orders": int((insured_df["covered_status"] == "out_of_insurance").sum()) if "covered_status" in insured_df.columns else 0,
        "has_insurance_counts": df["has_insurance_status"].value_counts(dropna=False).to_dict() if "has_insurance_status" in df.columns else {},
        "covered_counts": df["covered_status"].value_counts(dropna=False).to_dict() if "covered_status" in df.columns else {},
    }


def _render_required_missing_warning(missing_required: list[str]) -> None:
    if missing_required:
        labels = [_canonical_label(col) for col in missing_required]
        st.warning(f"{t('smart_mapper_required_missing')} {', '.join(labels)}")


def _render_mapping_summary(column_mapping: dict[str, str | None], header_row: int, sheet_name: str) -> None:
    summary_rows = []
    for canonical, source in column_mapping.items():
        summary_rows.append(
            {
                "canonical": canonical,
                "label": CANONICAL_LABELS.get(canonical, canonical),
                "source_column": source or "<Missing>",
                "status": "OK" if source else "MISSING",
            }
        )
    st.subheader(t("smart_mapper_mapping_summary"))
    st.write(f"**{t('smart_mapper_sheet')}:** {sheet_name}")
    st.write(f"**{t('smart_mapper_header_row')}:** {header_row + 1}")
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)


def _render_column_mapping_controls(file_hash: str, selected_sheet: str, raw_columns: list[str], auto_mapping: dict[str, str | None], manual_mode: bool) -> dict[str, str | None]:
    left, right = st.columns(2)
    if left.button(t("smart_mapper_auto_mapping"), use_container_width=True, key=_state_key(file_hash, f"{selected_sheet}_use_auto")):
        _set_auto_column_mapping(file_hash, selected_sheet, auto_mapping)
        st.session_state[_state_key(file_hash, "state")]["manual_mode"] = False
        st.session_state[_state_key(file_hash, "state")]["confirmed"] = False
        st.rerun()
    if right.button(t("smart_mapper_manual_mapping"), use_container_width=True, key=_state_key(file_hash, f"{selected_sheet}_use_manual")):
        st.session_state[_state_key(file_hash, "state")]["manual_mode"] = True
        st.session_state[_state_key(file_hash, "state")]["confirmed"] = False
        st.rerun()

    column_mapping = _current_column_mapping(file_hash, selected_sheet, raw_columns, auto_mapping)

    if manual_mode or any(value is None for value in column_mapping.values()):
        st.markdown("### " + t("smart_mapper_manual_mapping"))
        options = ["<Missing>"] + raw_columns
        for canonical in COLUMN_ALIASES.keys():
            widget_key = _state_key(file_hash, f"{selected_sheet}_column_{canonical}")
            current_value = st.session_state.get(widget_key, auto_mapping.get(canonical) or "<Missing>")
            if current_value not in options:
                current_value = auto_mapping.get(canonical) or "<Missing>"
            index = options.index(current_value) if current_value in options else 0
            st.selectbox(
                _canonical_label(canonical),
                options=options,
                index=index,
                key=widget_key,
                help=_u("Chọn cột nguồn tương ứng", "Select the matching source column.") if not manual_mode else None,
            )
        column_mapping = _current_column_mapping(file_hash, selected_sheet, raw_columns, auto_mapping)
    return column_mapping


def _render_value_mapping_controls(file_hash: str, selected_sheet: str, raw_df: pd.DataFrame, column_mapping: dict[str, str | None], preset_loaded: bool) -> dict[str, dict[str, str]]:
    st.subheader(t("smart_mapper_value_mapping"))
    value_mapping = {"has_insurance": {}, "covered": {}}
    for kind in ("has_insurance", "covered"):
        source_column = column_mapping.get(kind)
        st.write(f"**{_canonical_label(kind)}**")
        if not source_column or source_column not in raw_df.columns:
            st.caption("No source column selected.")
            continue
        raw_values = build_unique_value_options(raw_df[source_column], limit=30)
        if not raw_values:
            st.caption("No values detected.")
            continue
        cols = st.columns(2)
        st.caption(f"Unique values: {len(raw_values)}")
        for idx, raw_value in enumerate(raw_values):
            with cols[idx % 2]:
                widget_key = _state_key(file_hash, f"{selected_sheet}_{kind}_{hashlib.md5(raw_value.encode('utf-8')).hexdigest()[:8]}")
                default_choice = st.session_state.get(widget_key)
                if default_choice not in (None, "yes", "no", "unknown", "covered", "out_of_insurance"):
                    default_choice = suggest_has_insurance_value(raw_value) if kind == "has_insurance" else suggest_covered_value(raw_value)
                if default_choice is None:
                    default_choice = suggest_has_insurance_value(raw_value) if kind == "has_insurance" else suggest_covered_value(raw_value)
                st.selectbox(
                    raw_value,
                    options=["yes", "no", "unknown"] if kind == "has_insurance" else ["covered", "out_of_insurance", "unknown"],
                    index=(["yes", "no", "unknown"] if kind == "has_insurance" else ["covered", "out_of_insurance", "unknown"]).index(default_choice) if default_choice in (["yes", "no", "unknown"] if kind == "has_insurance" else ["covered", "out_of_insurance", "unknown"]) else 2,
                    key=widget_key,
                )
            value_mapping[kind][raw_value] = st.session_state.get(widget_key)
    if preset_loaded:
        st.caption(_u("Preset ánh xạ đã được nạp.", "Mapping preset loaded."))
    return value_mapping


def _maybe_warn_unknown_statuses(df: pd.DataFrame) -> None:
    warn_unknown = False
    if "has_insurance_status" in df.columns and df["has_insurance_status"].nunique(dropna=False) == 1 and df["has_insurance_status"].iloc[0] == "unknown":
        warn_unknown = True
    if "covered_status" in df.columns and df["covered_status"].nunique(dropna=False) == 1 and df["covered_status"].iloc[0] == "unknown":
        warn_unknown = True
    if warn_unknown:
        st.warning(t("smart_mapper_warning_unknown"))


def render_smart_excel_mapper(uploaded_file):
    st.subheader(t("smart_mapper_title"))
    intake = load_uploaded_excel(uploaded_file)
    file_bytes = intake.file_bytes
    if not file_bytes:
        st.warning(t("no_file_uploaded"))
        return None, {}

    file_hash = intake.file_hash or _file_hash(file_bytes)
    sheet_infos = intake.sheet_infos or detect_excel_sheets(file_bytes)
    best_sheet_info = infer_best_sheet_and_header(file_bytes, sheet_infos)
    best_sheet = best_sheet_info["sheet_name"] if best_sheet_info else intake.best_sheet or find_best_data_sheet(file_bytes)
    state = _ensure_state(file_hash, best_sheet)

    sheet_names = [info["sheet_name"] for info in sheet_infos]
    if not sheet_names:
        st.error(t("no_valid_data_sheet"))
        return None, {"file_hash": file_hash, "sheet_infos": sheet_infos}

    sheet_info_map = {info["sheet_name"]: info for info in sheet_infos}
    if state["selected_sheet"] not in sheet_names:
        state["selected_sheet"] = best_sheet or sheet_names[0]

    selected_sheet = st.selectbox(
        t("smart_mapper_sheet"),
        options=sheet_names,
        index=sheet_names.index(state["selected_sheet"]) if state["selected_sheet"] in sheet_names else 0,
        key=_state_key(file_hash, "sheet_selector"),
        format_func=lambda sheet: _sheet_label(sheet_info_map.get(sheet, {"sheet_name": sheet, "is_valid_data_sheet": False, "is_description": False})),
    )
    state["selected_sheet"] = selected_sheet

    if is_description_sheet(selected_sheet):
        st.warning(t("sheet_description_warning"))
        st.dataframe(pd.read_excel(BytesIO(file_bytes), sheet_name=selected_sheet, header=None, nrows=5, dtype=object), use_container_width=True)
        return None, {"file_hash": file_hash, "sheet_infos": sheet_infos, "selected_sheet": selected_sheet}

    header_info = infer_header_row_for_sheet(file_bytes, selected_sheet)
    raw_df = pd.read_excel(BytesIO(file_bytes), sheet_name=selected_sheet, header=header_info["header_row"], dtype=object)
    raw_df = raw_df.loc[:, ~raw_df.columns.astype(str).str.startswith("Unnamed")]
    raw_columns = [str(col) for col in raw_df.columns]

    st.write(f"**{t('smart_mapper_header_row')}:** {header_info['header_row'] + 1}")
    st.dataframe(raw_df.head(5), use_container_width=True, hide_index=True)

    auto_mapping = build_default_column_mapping(raw_columns)
    with st.expander(t("smart_mapper_mapping_summary"), expanded=False):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "canonical": canonical,
                        "label": _canonical_label(canonical),
                        "auto_source_column": auto_mapping.get(canonical) or "<Missing>",
                        "required": canonical in {"doctor", "patient", "has_insurance", "covered"},
                    }
                    for canonical in COLUMN_ALIASES.keys()
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    column_mapping = _render_column_mapping_controls(file_hash, selected_sheet, raw_columns, auto_mapping, state.get("manual_mode", False))
    missing_required = get_missing_required_columns(column_mapping)

    if missing_required:
        _render_required_missing_warning(missing_required)

    preset_key = _state_key(file_hash, f"{selected_sheet}_preset_upload")
    preset_upload = st.file_uploader(t("smart_mapper_upload_preset"), type=["json"], key=preset_key)
    if preset_upload is not None:
        try:
            preset = load_mapping_preset(preset_upload.read().decode("utf-8"))
            _apply_preset(file_hash, selected_sheet, preset, raw_columns)
            state["preset_loaded"] = True
            state["confirmed"] = False
            st.session_state[preset_key] = None
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    value_mapping = _render_value_mapping_controls(file_hash, selected_sheet, raw_df, column_mapping, state.get("preset_loaded", False))

    mapped_df = _apply_value_mapping_to_working_df(raw_df, column_mapping, value_mapping)

    preview_df = None
    normalized_df = None
    normalization_error = None
    if not missing_required:
        try:
            normalized_df = normalize_columns(mapped_df)
            preview_df = normalized_df.head(20)
        except ColumnMappingError as exc:
            normalization_error = exc
            missing_required = exc.missing_required
            _render_required_missing_warning(missing_required)
        except Exception as exc:
            normalization_error = exc
            st.error(t("analysis_failed"))

    if normalized_df is not None:
        assumptions = normalized_df.attrs.get("analysis_assumptions", {}) if hasattr(normalized_df, "attrs") else {}
        if assumptions.get("has_insurance_defaulted_to_no"):
            st.error(
                "ASSUMPTION ACTIVE: No HasInsurance column was found. The app is defaulting all rows to uninsured "
                "(HasInsurance = no) so analysis can continue. This is a fallback, not a conclusion about insurance status."
            )
        summary = _preview_summary(normalized_df)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(t("smart_mapper_total_rows"), summary["total_rows"])
        c2.metric(t("smart_mapper_insured_patients"), summary["insured_patients"])
        c3.metric(t("smart_mapper_insured_orders"), summary["insured_orders"])
        c4.metric(t("smart_mapper_out_orders"), summary["out_of_insurance_orders"])
        st.write(summary["has_insurance_counts"])
        st.write(summary["covered_counts"])
        _maybe_warn_unknown_statuses(normalized_df)
        st.subheader(t("smart_mapper_preview_rows"))
        st.dataframe(preview_df, use_container_width=True, height=320)

    st.download_button(
        t("smart_mapper_download_preset"),
        data=serialize_mapping_preset(column_mapping, value_mapping),
        file_name="smart_excel_mapping_preset.json",
        mime="application/json",
        use_container_width=True,
        key=_state_key(file_hash, f"{selected_sheet}_download_preset"),
    )

    mapping_signature = json.dumps(
        {
            "selected_sheet": selected_sheet,
            "column_mapping": column_mapping,
            "value_mapping": value_mapping,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    if state.get("last_signature") != mapping_signature:
        state["confirmed"] = False
        state["last_signature"] = mapping_signature
        st.session_state["analysis_tools_visible"] = False

    if not missing_required and normalized_df is not None:
        if st.button(t("smart_mapper_confirm"), type="primary", use_container_width=True, key=_state_key(file_hash, f"{selected_sheet}_confirm")):
            state["confirmed"] = True
            st.session_state["analysis_tools_visible"] = True

    if not state.get("confirmed"):
        if normalized_df is not None:
            st.info(t("smart_mapper_ready"))
        return None, {
            "file_hash": file_hash,
            "sheet_infos": sheet_infos,
            "selected_sheet": selected_sheet,
            "header_row": header_info["header_row"],
            "column_mapping": column_mapping,
            "value_mapping": value_mapping,
            "missing_required": missing_required,
            "raw_columns": raw_columns,
            "normalized_preview": preview_df,
            "summary": _preview_summary(normalized_df) if normalized_df is not None else {},
            "preview_ready": normalized_df is not None,
        }

    if normalized_df is None:
        st.error(t("smart_mapper_required_missing"))
        return None, {
            "file_hash": file_hash,
            "sheet_infos": sheet_infos,
            "selected_sheet": selected_sheet,
            "header_row": header_info["header_row"],
            "column_mapping": column_mapping,
            "value_mapping": value_mapping,
            "missing_required": missing_required,
            "raw_columns": raw_columns,
            "preview_ready": False,
        }

    mapper_meta = {
        "file_hash": file_hash,
        "sheet_infos": sheet_infos,
        "selected_sheet": selected_sheet,
        "header_row": header_info["header_row"],
        "column_mapping": column_mapping,
        "value_mapping": value_mapping,
        "missing_required": missing_required,
        "raw_columns": raw_columns,
        "preview_ready": True,
        "summary": _preview_summary(normalized_df),
        "mapping_signature": mapping_signature,
    }

    return normalized_df, mapper_meta
