from __future__ import annotations

import streamlit as st

from scripts.i18n import get_language
from scripts.analysis_scope import (
    DEFAULT_EXCLUSION_KEYWORDS,
    PRESET_DEFAULTS,
    PRESET_LABELS,
    normalize_list_filter,
)


def _u(vi: str, en: str) -> str:
    return en if get_language() == "en" else vi


PRESET_SEQUENCE = [
    ("🇻🇳 Kiểm tra mặc định: BN có BH + chỉ định ngoài BH", "insured_out_of_insurance_review"),
    ("🇻🇳 BN có BH + tất cả chỉ định", "insured_all_orders_review"),
    ("🇻🇳 BN có BH + chỉ định trong BH", "insured_covered_orders_review"),
    ("🇻🇳 BN không có BH + tất cả chỉ định (tham chiếu)", "uninsured_all_orders_reference"),
    ("🇻🇳 Tất cả bệnh nhân + tất cả chỉ định", "all_patients_all_orders"),
    ("🛠️ Tùy chỉnh thủ công", "custom_manual_filter"),
]

PATIENT_OPTIONS = [
    ("🇻🇳 Bệnh nhân có bảo hiểm", "insured_only"),
    ("🇻🇳 Bệnh nhân không có bảo hiểm", "uninsured_only"),
    ("🇻🇳 Tất cả bệnh nhân", "all_patients"),
]

COVERAGE_OPTIONS = [
    ("🇻🇳 Chỉ định ngoài bảo hiểm", "out_of_insurance_only"),
    ("🇻🇳 Chỉ định trong bảo hiểm", "covered_only"),
    ("🇻🇳 Chỉ định chưa rõ", "unknown_only"),
    ("🇻🇳 Tất cả chỉ định", "all_orders"),
]


def _preset_sequence():
    return [
        (_u("🇻🇳 Kiểm tra mặc định: BN có BH + chỉ định ngoài BH", "🇺🇸 Default audit: insured patients + out-of-insurance orders"), "insured_out_of_insurance_review"),
        (_u("🇻🇳 BN có BH + tất cả chỉ định", "🇺🇸 Insured patients + all orders"), "insured_all_orders_review"),
        (_u("🇻🇳 BN có BH + chỉ định trong BH", "🇺🇸 Insured patients + covered orders"), "insured_covered_orders_review"),
        (_u("🇻🇳 BN không có BH + tất cả chỉ định (tham chiếu)", "🇺🇸 Uninsured patients + all orders reference"), "uninsured_all_orders_reference"),
        (_u("🇻🇳 Tất cả bệnh nhân + tất cả chỉ định", "🇺🇸 All patients + all orders"), "all_patients_all_orders"),
        (_u("🛠️ Tùy chỉnh thủ công", "🛠️ Custom manual filter"), "custom_manual_filter"),
    ]


def _patient_options():
    return [
        (_u("🇻🇳 Bệnh nhân có bảo hiểm", "🇺🇸 Insured patients"), "insured_only"),
        (_u("🇻🇳 Bệnh nhân không có bảo hiểm", "🇺🇸 Uninsured patients"), "uninsured_only"),
        (_u("🇻🇳 Tất cả bệnh nhân", "🇺🇸 All patients"), "all_patients"),
    ]


def _coverage_options():
    return [
        (_u("🇻🇳 Chỉ định ngoài bảo hiểm", "🇺🇸 Out-of-insurance orders"), "out_of_insurance_only"),
        (_u("🇻🇳 Chỉ định trong bảo hiểm", "🇺🇸 Covered orders"), "covered_only"),
        (_u("🇻🇳 Chỉ định chưa rõ", "🇺🇸 Unknown coverage"), "unknown_only"),
        (_u("🇻🇳 Tất cả chỉ định", "🇺🇸 All orders"), "all_orders"),
    ]


def _scope_key(name: str) -> str:
    signature = st.session_state.get("analysis_scope_data_signature", "global")
    return f"analysis_scope_{signature}_{name}"


def _unique_values(df, column: str) -> list[str]:
    if df is None or column not in getattr(df, "columns", []):
        return []
    values = df[column].dropna().astype(str).map(str.strip)
    values = [value for value in values if value and value.lower() != "nan"]
    return sorted(set(values))[:200]


def _preset_defaults(preset_id: str) -> tuple[str, str]:
    defaults = PRESET_DEFAULTS.get(preset_id, PRESET_DEFAULTS["insured_out_of_insurance_review"])
    return defaults["patient_scope"], defaults["coverage_scope"]


def _preset_from_scopes(patient_scope: str, coverage_scope: str) -> str:
    for preset_id, defaults in PRESET_DEFAULTS.items():
        if defaults["patient_scope"] == patient_scope and defaults["coverage_scope"] == coverage_scope:
            return preset_id
    return "custom_manual_filter"


def _ensure_state():
    if _scope_key("preset_id") not in st.session_state:
        st.session_state[_scope_key("preset_id")] = "insured_out_of_insurance_review"
    patient_scope, coverage_scope = _preset_defaults(st.session_state[_scope_key("preset_id")])
    if _scope_key("patient_scope") not in st.session_state:
        st.session_state[_scope_key("patient_scope")] = patient_scope
    if _scope_key("coverage_scope") not in st.session_state:
        st.session_state[_scope_key("coverage_scope")] = coverage_scope
    if _scope_key("benchmark_scope") not in st.session_state:
        st.session_state[_scope_key("benchmark_scope")] = "department"
    for key in ["selected_departments", "selected_doctors", "selected_procedures", "selected_icd_codes"]:
        if _scope_key(key) not in st.session_state:
            st.session_state[_scope_key(key)] = []
    if _scope_key("min_amount") not in st.session_state:
        st.session_state[_scope_key("min_amount")] = 0.0
    if _scope_key("include_unknown_coverage") not in st.session_state:
        st.session_state[_scope_key("include_unknown_coverage")] = True
    if _scope_key("exclusion_keywords") not in st.session_state:
        st.session_state[_scope_key("exclusion_keywords")] = list(DEFAULT_EXCLUSION_KEYWORDS)


def _set_preset(preset_id: str):
    patient_scope, coverage_scope = _preset_defaults(preset_id)
    st.session_state[_scope_key("preset_id")] = preset_id
    st.session_state[_scope_key("patient_scope")] = patient_scope
    st.session_state[_scope_key("coverage_scope")] = coverage_scope


def render_analysis_scope_panel(df=None) -> dict:
    st.sidebar.subheader(f"🔎 {_u('Bộ lọc phân tích', 'Analysis filter')}")
    st.sidebar.caption(
        _u(
            "Chọn nhóm bệnh nhân và loại chỉ định muốn phân tích. Mặc định của app là: bệnh nhân có bảo hiểm + chỉ định ngoài bảo hiểm.",
            "Choose the patient group and order coverage you want to analyze. The default is: insured patients + out-of-insurance orders.",
        )
    )
    _ensure_state()

    has_insurance_defaulted_to_no = bool(getattr(df, "attrs", {}).get("analysis_assumptions", {}).get("has_insurance_defaulted_to_no"))
    if has_insurance_defaulted_to_no and st.session_state[_scope_key("preset_id")] == "insured_out_of_insurance_review" and not st.session_state.get(_scope_key("auto_uninsured_applied")):
        _set_preset("uninsured_all_orders_reference")
        st.session_state[_scope_key("auto_uninsured_applied")] = True
        st.sidebar.error(
            _u(
                "ĐANG DÙNG GIẢ ĐỊNH: Không tìm thấy cột HasInsurance. App đang xem các dòng này như bệnh nhân không có bảo hiểm để tiếp tục phân tích.",
                "ASSUMPTION ACTIVE: No HasInsurance column was found. The app is treating these rows as uninsured so analysis can continue.",
            )
        )

    preset_sequence = _preset_sequence()
    patient_options = _patient_options()
    coverage_options = _coverage_options()
    preset_label_to_id = {label: preset_id for label, preset_id in preset_sequence}
    preset_id_to_label = {preset_id: label for label, preset_id in preset_sequence}

    current_patient_scope = st.session_state[_scope_key("patient_scope")]
    current_coverage_scope = st.session_state[_scope_key("coverage_scope")]
    derived_preset_id = _preset_from_scopes(current_patient_scope, current_coverage_scope)
    if derived_preset_id != st.session_state[_scope_key("preset_id")]:
        st.session_state[_scope_key("preset_id")] = derived_preset_id

    preset_label = st.sidebar.selectbox(
        _u("Chế độ nhanh / Preset", "Quick mode / Preset"),
        options=[label for label, _ in preset_sequence],
        index=[label for label, _ in preset_sequence].index(preset_id_to_label.get(st.session_state[_scope_key("preset_id")], _u("🛠️ Tùy chỉnh thủ công", "🛠️ Custom manual filter")))
        if st.session_state[_scope_key("preset_id")] in preset_id_to_label
        else len(preset_sequence) - 1,
        key=_scope_key("preset_select"),
    )
    selected_preset_id = preset_label_to_id[preset_label]
    if selected_preset_id != st.session_state[_scope_key("preset_id")]:
        _set_preset(selected_preset_id)
        st.rerun()

    patient_label_to_value = {label: value for label, value in patient_options}
    coverage_label_to_value = {label: value for label, value in coverage_options}

    patient_label = next(label for label, value in patient_options if value == st.session_state[_scope_key("patient_scope")])
    coverage_label = next(label for label, value in coverage_options if value == st.session_state[_scope_key("coverage_scope")])

    selected_patient_label = st.sidebar.selectbox(
        _u("Nhóm bệnh nhân", "Patient group"),
        options=[label for label, _ in patient_options],
        index=[label for label, _ in patient_options].index(patient_label),
        key=_scope_key("patient_select"),
    )
    st.session_state[_scope_key("patient_scope")] = patient_label_to_value[selected_patient_label]

    selected_coverage_label = st.sidebar.selectbox(
        _u("Trạng thái chỉ định", "Order coverage"),
        options=[label for label, _ in coverage_options],
        index=[label for label, _ in coverage_options].index(coverage_label),
        key=_scope_key("coverage_select"),
    )
    st.session_state[_scope_key("coverage_scope")] = coverage_label_to_value[selected_coverage_label]

    if _preset_from_scopes(st.session_state[_scope_key("patient_scope")], st.session_state[_scope_key("coverage_scope")]) != st.session_state[_scope_key("preset_id")]:
        st.session_state[_scope_key("preset_id")] = "custom_manual_filter"

    st.sidebar.caption(_u("HasInsurance = bệnh nhân có bảo hiểm hay không.", "HasInsurance = whether the patient has insurance."))
    st.sidebar.caption(_u("CoveredByInsurance = chỉ định/dịch vụ đó có được bảo hiểm chi trả hay không.", "CoveredByInsurance = whether that order/service is covered by insurance."))
    st.sidebar.caption(_u("Nếu bệnh nhân không có bảo hiểm, các chỉ định của họ được xem là ngoài bảo hiểm trong lớp phân tích.", "If the patient has no insurance, their orders are treated as out-of-insurance in the analysis layer."))
    if has_insurance_defaulted_to_no:
        st.sidebar.error(
            _u(
                "ĐANG DÙNG GIẢ ĐỊNH: file này không có HasInsurance, nên app đang xem cohort hiện tại là không có bảo hiểm để phân tích.",
                "ASSUMPTION ACTIVE: this file has no HasInsurance column, so the current cohort is treated as uninsured for analysis.",
            )
        )

    if df is not None:
        if "department" in df.columns:
            st.sidebar.multiselect(_u("Khoa", "Department"), options=_unique_values(df, "department"), key=_scope_key("selected_departments"))
        if "doctor" in df.columns:
            st.sidebar.multiselect(_u("Bác sĩ", "Doctor"), options=_unique_values(df, "doctor"), key=_scope_key("selected_doctors"))
        if "procedure" in df.columns:
            st.sidebar.multiselect(_u("Dịch vụ", "Procedure"), options=_unique_values(df, "procedure"), key=_scope_key("selected_procedures"))
        if "diagnosis_code" in df.columns:
            st.sidebar.multiselect(_u("Mã ICD", "ICD code"), options=_unique_values(df, "diagnosis_code"), key=_scope_key("selected_icd_codes"))

    if df is not None and "amount" in df.columns:
        current_min = float(st.session_state.get(_scope_key("min_amount"), 0.0) or 0.0)
        min_amount = st.sidebar.number_input(_u("Số tiền tối thiểu", "Minimum amount"), min_value=0.0, value=current_min, step=50000.0, key=_scope_key("min_amount_input"))
        st.session_state[_scope_key("min_amount")] = min_amount
    else:
        st.session_state[_scope_key("min_amount")] = None

    st.sidebar.checkbox(
        _u("Tính cả chỉ định chưa rõ trong mẫu nền", "Include unknown coverage in denominator"),
        value=bool(st.session_state.get(_scope_key("include_unknown_coverage"), True)),
        key=_scope_key("include_unknown_coverage"),
    )

    preset_id = st.session_state[_scope_key("preset_id")]
    preset_name = PRESET_LABELS.get(preset_id, "Custom manual filter")

    if st.session_state[_scope_key("patient_scope")] == "uninsured_only":
        st.sidebar.warning(_u("Bệnh nhân không có bảo hiểm là nhóm tham chiếu/thăm dò. Không diễn giải kết quả này như quyền lợi bảo hiểm bị bỏ sót.", "Uninsured patients are a reference/exploratory group. Do not interpret the result as missed insurance benefits."))
        if st.session_state[_scope_key("coverage_scope")] == "covered_only":
            st.sidebar.warning(_u("Với bệnh nhân không có bảo hiểm, lựa chọn chỉ định trong bảo hiểm thường không tạo dữ liệu hợp lệ vì các chỉ định được xem là không được chi trả.", "For uninsured patients, choosing covered orders usually does not produce valid data because the orders are treated as not covered."))
    if st.session_state[_scope_key("coverage_scope")] == "all_orders":
        st.sidebar.info(_u("Đang phân tích tất cả chỉ định. Tỷ lệ tín hiệu có thể không còn nghĩa là tỷ lệ ngoài bảo hiểm.", "Analyzing all orders. Signal rate may no longer mean out-of-insurance rate."))
    if st.session_state[_scope_key("patient_scope")] == "insured_only" and st.session_state[_scope_key("coverage_scope")] == "out_of_insurance_only":
        st.sidebar.success(_u("Đây là chế độ gốc của app: bệnh nhân có bảo hiểm + chỉ định ngoài bảo hiểm.", "This is the app's default mode: insured patients + out-of-insurance orders."))

    return {
        "preset_id": preset_id,
        "preset_name": preset_name,
        "patient_scope": st.session_state[_scope_key("patient_scope")],
        "coverage_scope": st.session_state[_scope_key("coverage_scope")],
        "selected_departments": normalize_list_filter(st.session_state.get(_scope_key("selected_departments"), [])),
        "selected_doctors": normalize_list_filter(st.session_state.get(_scope_key("selected_doctors"), [])),
        "selected_procedures": normalize_list_filter(st.session_state.get(_scope_key("selected_procedures"), [])),
        "selected_icd_codes": normalize_list_filter(st.session_state.get(_scope_key("selected_icd_codes"), [])),
        "min_amount": st.session_state.get(_scope_key("min_amount")),
        "include_unknown_coverage": bool(st.session_state.get(_scope_key("include_unknown_coverage"), True)),
        "benchmark_scope": "department",
    }
