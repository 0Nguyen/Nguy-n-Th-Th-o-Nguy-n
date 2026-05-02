from __future__ import annotations

import pandas as pd
import streamlit as st

from scripts.i18n import get_language


def _lang() -> str:
    return get_language()


def _u(vi: str, en: str) -> str:
    return en if _lang() == "en" else vi


def _display_column_map() -> dict[str, str]:
    if _lang() == "en":
        return {
            "priority_rank": "Priority",
            "metric": "Metric",
            "label": "Label",
            "value": "Value",
            "review_target": "Review target",
            "target_type": "Target type",
            "department": "Department",
            "main_signal": "Main signal",
            "review_date": "Review date",
            "claim_id": "Claim ID",
            "patient": "Patient",
            "procedure": "Procedure",
            "diagnosis_code": "ICD code",
            "diagnosis_name": "Diagnosis",
            "amount_vnd": "Amount (VND)",
            "why_flagged": "Why flagged",
            "supporting_evidence": "Supporting evidence",
            "context_status": "Context status",
            "recommended_action": "Recommended action",
            "priority_score": "Priority score",
            "doctor": "Doctor",
            "ten_bac_si__doctor": "Doctor",
            "khoa__department": "Department",
            "numerator_orders": "Signal rows",
            "denominator_orders": "Baseline rows",
            "numerator_rate": "Signal rate",
            "numerator_amount_vnd": "Signal amount (VND)",
            "total_amount_vnd": "Total amount (VND)",
            "patient_count": "Patient count",
            "doctor_count": "Doctor count",
            "procedure_count": "Procedure count",
            "unique_procedure_count": "Unique procedures",
            "pair_count": "Pair count",
            "severity": "Severity",
            "review_priority": "Review priority",
            "mismatch_type": "Mismatch type",
            "rule_name": "Rule name",
            "note": "Note",
            "flag_source": "Flag source",
            "resolution_status": "Resolution status",
            "resolved_count": "Resolved rows",
            "partially_resolved_count": "Partially resolved",
            "unresolved_count": "Unresolved rows",
            "unresolved_rate": "Unresolved rate",
            "covered_status": "Coverage status",
            "order_count": "Order count",
            "share": "Share",
            "cumulative_amount_vnd": "Cumulative amount (VND)",
            "cumulative_percent": "Cumulative share",
            "pareto_rank": "Pareto rank",
            "alignment_status": "Alignment status",
            "explanation_summary": "Explanation summary",
            "risk_score": "Risk score",
            "z_score": "Z score",
            "concentration_ratio": "Concentration ratio",
            "signal_name": "Signal name",
            "signal_value": "Signal value",
            "final_review_action": "Final review action",
            "review_committee_summary_table": "Review committee summary",
        }
    return {
        "priority_rank": "Thứ tự ưu tiên",
        "metric": "Chi số",
        "label": "Nhãn",
        "value": "Giá trị",
        "review_target": "Mục tiêu rà soát",
        "target_type": "Loại mục tiêu",
        "department": "Khoa",
        "main_signal": "Tín hiệu chính",
        "review_date": "Ngày xem",
        "claim_id": "Mã hồ sơ",
        "patient": "Bệnh nhân",
        "procedure": "Dịch vụ",
        "diagnosis_code": "Mã ICD",
        "diagnosis_name": "Tên chẩn đoán",
        "amount_vnd": "Số tiền (VND)",
        "why_flagged": "Vì sao bị gắn cờ",
        "supporting_evidence": "Bằng chứng hỗ trợ",
        "context_status": "Trạng thái bối cảnh",
        "recommended_action": "Việc nên làm tiếp",
        "priority_score": "Điểm ưu tiên",
        "doctor": "Bác sĩ",
        "ten_bac_si__doctor": "Bác sĩ",
        "khoa__department": "Khoa",
        "numerator_orders": "Số dòng tín hiệu",
        "denominator_orders": "Số dòng nền",
        "numerator_rate": "Tỷ lệ tín hiệu",
        "numerator_amount_vnd": "Tiền tín hiệu (VND)",
        "total_amount_vnd": "Tổng tiền (VND)",
        "patient_count": "Số bệnh nhân",
        "doctor_count": "Số bác sĩ",
        "procedure_count": "Số dịch vụ",
        "unique_procedure_count": "Số dịch vụ khác nhau",
        "pair_count": "Số cặp",
        "severity": "Mức độ",
        "review_priority": "Ưu tiên rà soát",
        "mismatch_type": "Loại lệch",
        "rule_name": "Tên quy tắc",
        "note": "Ghi chú",
        "flag_source": "Nguồn cờ",
        "resolution_status": "Trạng thái gỡ cờ",
        "resolved_count": "Số ca gỡ được",
        "partially_resolved_count": "Số ca gỡ một phần",
        "unresolved_count": "Số ca chưa rõ",
        "unresolved_rate": "Tỷ lệ chưa rõ",
        "covered_status": "Trạng thái chỉ định",
        "order_count": "Số chỉ định",
        "share": "Tỷ trọng",
        "cumulative_amount_vnd": "Tiền lũy kế (VND)",
        "cumulative_percent": "Tỷ trọng lũy kế",
        "pareto_rank": "Hạng Pareto",
        "alignment_status": "Trạng thái khớp",
        "explanation_summary": "Tóm tắt giải thích",
        "risk_score": "Điểm rủi ro",
        "z_score": "Z score",
        "concentration_ratio": "Tỷ lệ tập trung",
        "signal_name": "Tên tín hiệu",
        "signal_value": "Giá trị tín hiệu",
        "final_review_action": "Việc rà soát cuối",
        "review_committee_summary_table": "Tóm tắt cho hội đồng",
    }


def _tab_badges() -> dict[str, tuple[str, str]]:
    if _lang() == "en":
        return {
            "Overview": ("#e8f1ff", "#2f5d9b"),
            "Doctor review": ("#ffe9e9", "#a22b2b"),
            "Procedure review": ("#fff4dd", "#8b6400"),
            "ICD / context audit": ("#eef0ff", "#42539a"),
            "Context resolver": ("#e8f7ec", "#1d7a3a"),
            "Patient burden": ("#fff1df", "#995a00"),
            "Case evidence": ("#edf1f7", "#38506b"),
        }
    return {
        "Tổng quan": ("#e8f1ff", "#2f5d9b"),
        "Bác sĩ": ("#ffe9e9", "#a22b2b"),
        "Dịch vụ": ("#fff4dd", "#8b6400"),
        "ICD / bối cảnh": ("#eef0ff", "#42539a"),
        "Gỡ cờ đỏ": ("#e8f7ec", "#1d7a3a"),
        "Gánh nặng bệnh nhân": ("#fff1df", "#995a00"),
        "Bằng chứng theo ca": ("#edf1f7", "#38506b"),
    }


def _to_text(value, default: str = "") -> str:
    if value is None:
        return default
    try:
        text = str(value).strip()
    except Exception:
        return default
    return text if text else default


def _first_df(tables: dict, *keys):
    for key in keys:
        table = tables.get(key)
        if table is not None and hasattr(table, "empty") and not table.empty:
            return table
    return None


def _first_table(*tables):
    for table in tables:
        if table is not None and hasattr(table, "empty") and not table.empty:
            return table
    return None


def _pretty_table(table: pd.DataFrame | None) -> pd.DataFrame | None:
    if table is None or table.empty:
        return table
    mapping = _display_column_map()
    renamed = table.copy()
    rename_map = {key: value for key, value in mapping.items() if key in renamed.columns}
    if rename_map:
        renamed = renamed.rename(columns=rename_map)
    return renamed


def _resolve_cell(row: pd.Series, column: str):
    if column in row.index:
        return row.get(column, "")
    mapping = _display_column_map()
    translated = mapping.get(column)
    if translated and translated in row.index:
        return row.get(translated, "")
    reverse = {value: key for key, value in mapping.items()}
    original = reverse.get(column)
    if original and original in row.index:
        return row.get(original, "")
    return ""


def _value_chip(label: str, value) -> str:
    value_text = _to_text(value, "—")
    return (
        "<span style='display:inline-block;margin:0.12rem 0.28rem 0.12rem 0;"
        "padding:0.2rem 0.58rem;border-radius:999px;background:rgba(73,108,170,0.10);"
        "color:#25436a;font-size:0.82rem;line-height:1.4;'>"
        f"<strong>{label}:</strong> {value_text}</span>"
    )


def _render_card_rows(title: str, table: pd.DataFrame | None, field_map: list[tuple[str, str]], max_rows: int = 4):
    st.subheader(title)
    pretty = _pretty_table(table)
    if pretty is None or pretty.empty:
        st.info(_u("Không có dữ liệu", "No data"))
        return

    rows = pretty.head(max_rows)
    first_col = rows.columns[0]
    for _, row in rows.iterrows():
        chips = "".join(_value_chip(label, _resolve_cell(row, column)) for column, label in field_map)
        st.markdown(
            f"""
            <div style="padding:14px 16px;border-radius:16px;background:rgba(255,255,255,0.90);border:1px solid rgba(91,124,153,0.16);box-shadow:0 8px 20px rgba(20,40,60,0.05);margin:0.42rem 0;">
                <div style="font-weight:700;margin-bottom:0.35rem;">{_to_text(row.get(first_col, ''))}</div>
                <div style="line-height:1.7;">{chips}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if len(pretty) > max_rows:
        with st.expander(_u("Xem bảng đầy đủ", "Show full table"), expanded=False):
            st.dataframe(pretty, use_container_width=True, height=280)


def _show_traffic_light(label: str, item: dict | None):
    if item is None:
        return
    level = str(item.get("level", "UNKNOWN")).upper()
    short_label = _to_text(item.get("short_label"), label)
    explanation = _to_text(item.get("explanation"), "")
    message = f"{label}: {short_label}"
    if explanation:
        message = f"{message} - {explanation}"

    if level in {"HIGH", "RED", "POOR"}:
        st.error(message)
    elif level in {"MODERATE", "PARTIAL"}:
        st.warning(message)
    elif level in {"GOOD", "LOW"}:
        st.success(message)
    else:
        st.info(message)


def _status_box(title: str, text: str, tone: str = "blue"):
    colors = {
        "blue": ("#eaf3ff", "#2b5aa7"),
        "green": ("#e7f7ec", "#1d7a3a"),
        "yellow": ("#fff6da", "#8a6700"),
        "red": ("#ffe8e8", "#a32626"),
    }
    bg, fg = colors.get(tone, colors["blue"])
    st.markdown(
        f"""
        <div style="padding:14px 16px;border-radius:16px;background:{bg};color:{fg};border:1px solid rgba(0,0,0,0.06);box-shadow:0 6px 18px rgba(20,40,60,0.05);margin:0.35rem 0;">
            <div style="font-weight:700;margin-bottom:0.15rem;">{title}</div>
            <div style="line-height:1.45;">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _tab_badge(label: str):
    bg, fg = _tab_badges().get(label, ("#edf1f7", "#38506b"))
    st.markdown(
        f"""
        <div style="display:inline-block;padding:0.2rem 0.7rem;border-radius:999px;background:{bg};color:{fg};font-size:0.82rem;font-weight:700;margin-bottom:0.4rem;">
            {label}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_bar_chart(table: pd.DataFrame | None, x_col: str, y_col: str, title: str):
    st.subheader(title)
    if table is None or table.empty or x_col not in table.columns or y_col not in table.columns:
        st.info(_u("Không có dữ liệu", "No data"))
        return
    chart_df = table[[x_col, y_col]].copy().dropna(subset=[x_col])
    if chart_df.empty:
        st.info(_u("Không có dữ liệu", "No data"))
        return
    try:
        st.bar_chart(chart_df.set_index(x_col)[y_col])
    except Exception:
        st.dataframe(chart_df, use_container_width=True)


def _summary_value(summary: dict, *keys, default=""):
    for key in keys:
        value = summary.get(key)
        if value not in [None, "", []]:
            return value
    return default


def _render_quick_read(final_report: dict, tables: dict):
    human_summary = final_report.get("human_summary", {}) or {}
    judge_summary = final_report.get("judge_summary", {}) or {}

    current_measure = human_summary.get("current_measure", {}) or {}
    key_numbers = human_summary.get("key_numbers", {}) or {}
    traffic_lights = human_summary.get("traffic_lights", {}) or {}

    preset_name = _to_text(
        _summary_value(
            current_measure,
            "preset_name",
            default=_summary_value(final_report.get("overview", {}) or {}, "scope_preset_name", "preset_name", default=_u("Chưa rõ", "Unknown")),
        ),
        _u("Chưa rõ", "Unknown"),
    )
    denominator_rows = _summary_value(key_numbers, "denominator_rows", default=_summary_value(final_report.get("overview", {}) or {}, "denominator_rows", default=0))
    numerator_rows = _summary_value(key_numbers, "numerator_rows", default=_summary_value(final_report.get("overview", {}) or {}, "numerator_rows", default=0))
    numerator_rate = _summary_value(key_numbers, "numerator_rate", default=_summary_value(final_report.get("overview", {}) or {}, "numerator_rate", default="0%"))
    numerator_amount = _summary_value(key_numbers, "numerator_amount_vnd", default=_summary_value(final_report.get("overview", {}) or {}, "numerator_amount_vnd", default=0))
    top_doctor_name = _to_text(_summary_value(key_numbers, "top_doctor", default=""), "")
    top_procedure_name = _to_text(_summary_value(key_numbers, "top_procedure", default=""), "")

    review_table = _first_table(
        human_summary.get("review_committee_summary_table"),
        tables.get("review_committee_summary_table"),
        judge_summary.get("judge_action_table"),
    )

    st.markdown(f"## {_u('Bản đọc nhanh', 'Quick read')}")
    st.caption(_u("Đọc phần này trước. Nếu chỉ cần hiểu nhanh, chưa cần mở bảng kỹ thuật.", "Read this first. If you only need the quick view, you do not need the technical tables yet."))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(_u("Đang xem gì", "What is being reviewed"), preset_name)
    c2.metric(_u("Số dòng nền", "Baseline rows"), denominator_rows)
    c3.metric(_u("Số dòng tín hiệu", "Signal rows"), numerator_rows)
    c4.metric(_u("Tỷ lệ tín hiệu", "Signal rate"), numerator_rate)

    st.markdown(f"### {_u('Tóm tắt 1 phút', '1-minute summary')}")
    summary_lines = list(human_summary.get("plain_language_summary", []) or [])
    if not summary_lines and judge_summary.get("judge_plain_language_summary"):
        summary_lines = list(judge_summary.get("judge_plain_language_summary", []))
    if not summary_lines:
        summary_lines = [
            _u("Chưa có phần tóm tắt tự động.", "No automatic summary is available yet."),
            _u("Kết quả hiện tại vẫn là tín hiệu rà soát, không phải kết luận sai phạm.", "The current result is only a review signal, not a finding of wrongdoing."),
        ]

    with st.container(border=True):
        for line in summary_lines[:6]:
            st.markdown(f"- {line}")

    left, right = st.columns(2)
    with left:
        st.markdown(f"### {_u('Nên xem trước gì?', 'What should I review first?')}")
        top_doctor = _first_df(tables, "doctor_review_priority_table", "doctor_outlier_table", "by_doctor")
        if top_doctor is not None and not top_doctor.empty:
            first = top_doctor.iloc[0]
            doctor_name = _resolve_cell(first, "doctor") or _resolve_cell(first, "ten_bac_si__doctor")
            department_name = _resolve_cell(first, "department") or _resolve_cell(first, "khoa__department")
            reason = _resolve_cell(first, "explanation_summary") or _resolve_cell(first, "why_flagged") or _resolve_cell(first, "review_priority")
            st.success(_u(f"Bác sĩ cần xem trước: {doctor_name}", f"Doctor to review first: {doctor_name}"))
            if department_name:
                st.caption(_u(f"Khoa: {department_name}", f"Department: {department_name}"))
            if reason:
                st.write(_u(f"Lý do: {reason}", f"Reason: {reason}"))
        else:
            st.info(_u("Chưa có bác sĩ nào nổi bật.", "No doctor stands out yet."))

        top_procedure = _first_df(tables, "procedure_pareto_table", "high_cost_procedure_table")
        if top_procedure is not None and not top_procedure.empty:
            first = top_procedure.iloc[0]
            procedure_name = _resolve_cell(first, "procedure")
            reason = _resolve_cell(first, "review_reason") or _resolve_cell(first, "severity") or _resolve_cell(first, "why_flagged")
            st.info(_u(f"Dịch vụ cần xem trước: {procedure_name}", f"Procedure to review first: {procedure_name}"))
            if reason:
                st.write(_u(f"Lý do: {reason}", f"Reason: {reason}"))
        else:
            st.info(_u("Chưa có dịch vụ nào nổi bật.", "No procedure stands out yet."))

    with right:
        st.markdown(f"### {_u('Cờ màu đang bật', 'Active signal lights')}")
        _show_traffic_light(_u("Bác sĩ", "Doctor"), traffic_lights.get("doctor_signal"))
        _show_traffic_light(_u("Dịch vụ", "Procedure"), traffic_lights.get("procedure_signal"))
        _show_traffic_light(_u("ICD / bối cảnh", "ICD / context"), traffic_lights.get("icd_context_signal"))
        _show_traffic_light(_u("Gỡ cờ đỏ theo bối cảnh", "Context resolution"), traffic_lights.get("context_resolution_signal"))

        if top_doctor_name or top_procedure_name:
            with st.container(border=True):
                st.markdown(f"**{_u('Kết luận ngắn', 'Short conclusion')}**")
                if top_doctor_name:
                    st.markdown(_u(f"Bác sĩ ưu tiên xem trước: {top_doctor_name}", f"Doctor to review first: {top_doctor_name}"))
                if top_procedure_name:
                    st.markdown(_u(f"Dịch vụ ưu tiên xem trước: {top_procedure_name}", f"Procedure to review first: {top_procedure_name}"))
                st.markdown(_u("Đây là tín hiệu rà soát, không phải kết luận sai phạm.", "This is a review signal, not a finding of wrongdoing."))

    if review_table is not None and hasattr(review_table, "empty") and not review_table.empty:
        st.markdown(f"### {_u('Danh sách ưu tiên cho hội đồng', 'Review committee priority list')}")
        _render_card_rows(
            _u("Mục tiêu nên xem trước", "Items to review first"),
            review_table,
            [
                ("priority_rank", _u("Hạng", "Rank")),
                ("review_target", _u("Mục tiêu", "Target")),
                ("target_type", _u("Loại", "Type")),
                ("department", _u("Khoa", "Department")),
                ("main_signal", _u("Tín hiệu", "Signal")),
                ("context_status", _u("Bối cảnh", "Context")),
                ("recommended_action", _u("Nên làm gì", "Recommended action")),
            ],
            max_rows=5,
        )

    if top_doctor_name or top_procedure_name or denominator_rows or numerator_rows:
        st.markdown(f"### {_u('Giải thích dễ hiểu', 'Plain-language explanation')}")
        st.markdown(
            _u(
                f"- App đang xem theo bộ lọc: {preset_name}\n"
                f"- Số dòng nền: {denominator_rows}\n"
                f"- Số dòng tín hiệu: {numerator_rows}\n"
                f"- Tỷ lệ tín hiệu: {numerator_rate}\n"
                f"- Tổng giá trị tín hiệu: {numerator_amount}",
                f"- Current review measure: {preset_name}\n"
                f"- Baseline rows: {denominator_rows}\n"
                f"- Signal rows: {numerator_rows}\n"
                f"- Signal rate: {numerator_rate}\n"
                f"- Signal amount: {numerator_amount}",
            )
        )


def _render_simple_summary(final_report: dict, tables: dict):
    human_summary = final_report.get("human_summary", {}) or {}
    judge_summary = final_report.get("judge_summary", {}) or {}

    current_measure = human_summary.get("current_measure", {}) or {}
    key_numbers = human_summary.get("key_numbers", {}) or {}
    traffic_lights = human_summary.get("traffic_lights", {}) or {}

    st.subheader(_u("Tóm tắt nhanh", "Quick summary"))
    st.markdown(f"### {_u('Bộ lọc đang xem', 'Current scope')}")
    _render_card_rows(
        _u("Bộ lọc hiện tại", "Current scope"),
        pd.DataFrame([
            {
                "metric": _u("Chế độ", "Mode"),
                "value": _to_text(current_measure.get("preset_name") or _summary_value(final_report.get("overview", {}) or {}, "scope_preset_name", default="")),
            },
            {
                "metric": _u("Mẫu nền", "Baseline rows"),
                "value": _summary_value(key_numbers, "denominator_rows", default=_summary_value(final_report.get("overview", {}) or {}, "denominator_rows", default="")),
            },
            {
                "metric": _u("Dòng tín hiệu", "Signal rows"),
                "value": _summary_value(key_numbers, "numerator_rows", default=_summary_value(final_report.get("overview", {}) or {}, "numerator_rows", default="")),
            },
            {
                "metric": _u("Tỷ lệ tín hiệu", "Signal rate"),
                "value": _summary_value(key_numbers, "numerator_rate", default=_summary_value(final_report.get("overview", {}) or {}, "numerator_rate", default="")),
            },
        ]),
        [("metric", _u("Nhãn", "Label")), ("value", _u("Giá trị", "Value"))],
        max_rows=4,
    )

    st.markdown(f"### {_u('Con số chính', 'Key numbers')}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(_u("Tỷ lệ tín hiệu", "Signal rate"), _summary_value(key_numbers, "numerator_rate", default=_summary_value(final_report.get("overview", {}) or {}, "numerator_rate", default=0)))
    c2.metric(_u("Tổng giá trị tín hiệu", "Signal amount"), _summary_value(key_numbers, "numerator_amount_vnd", default=_summary_value(final_report.get("overview", {}) or {}, "numerator_amount_vnd", default=0)))
    c3.metric(_u("Bác sĩ cần xem trước", "Doctor to review first"), _to_text(_summary_value(key_numbers, "top_doctor", default=""), "—"))
    c4.metric(_u("Dịch vụ cần xem trước", "Procedure to review first"), _to_text(_summary_value(key_numbers, "top_procedure", default=""), "—"))

    st.markdown(f"### {_u('Đèn tín hiệu', 'Traffic lights')}")
    _show_traffic_light(_u("Bác sĩ", "Doctor"), traffic_lights.get("doctor_signal"))
    _show_traffic_light(_u("Dịch vụ", "Procedure"), traffic_lights.get("procedure_signal"))
    _show_traffic_light(_u("ICD / bối cảnh", "ICD / context"), traffic_lights.get("icd_context_signal"))
    _show_traffic_light(_u("Gỡ cờ đỏ", "Context resolution"), traffic_lights.get("context_resolution_signal"))

    st.markdown(f"### {_u('Bảng ưu tiên rà soát', 'Review priority list')}")
    committee_table = _first_table(
        human_summary.get("review_committee_summary_table"),
        tables.get("review_committee_summary_table"),
        judge_summary.get("judge_action_table"),
    )
    if committee_table is not None and not committee_table.empty:
        _render_card_rows(
            _u("Danh sách ưu tiên cho hội đồng", "Review committee priority list"),
            committee_table,
            [
                ("priority_rank", _u("Hạng", "Rank")),
                ("review_target", _u("Mục tiêu", "Target")),
                ("target_type", _u("Loại", "Type")),
                ("department", _u("Khoa", "Department")),
                ("main_signal", _u("Tín hiệu", "Signal")),
                ("context_status", _u("Bối cảnh", "Context")),
                ("recommended_action", _u("Nên làm gì", "Recommended action")),
            ],
            max_rows=5,
        )
    else:
        st.info(_u("Không có dữ liệu", "No data"))

    st.markdown(f"### {_u('Giải thích dễ hiểu', 'Plain-language explanation')}")
    explanation_lines = list(human_summary.get("plain_language_summary", []) or [])
    if not explanation_lines and judge_summary.get("judge_plain_language_summary"):
        explanation_lines = list(judge_summary.get("judge_plain_language_summary", []))
    if not explanation_lines:
        explanation_lines = [_u("Chưa có phần tóm tắt tự động.", "No automatic summary is available yet.")]
    for line in explanation_lines:
        st.write(f"- {line}")

    _status_box(_u("Màu xanh", "Green"), _u("Phần này cho biết tín hiệu đang ở mức dễ theo dõi hơn.", "This section indicates a lower-priority signal."), "green")
    _status_box(_u("Màu vàng", "Yellow"), _u("Phần này cần xem thêm, nhưng chưa đủ mạnh để kết luận bất thường lớn.", "This section needs more review, but is not strong enough for a major conclusion."), "yellow")
    _status_box(_u("Màu đỏ", "Red"), _u("Phần này có tín hiệu mạnh hơn và nên được đọc trước.", "This section is stronger and should be read first."), "red")

    st.markdown(f"### {_u('Cách đọc dashboard', 'How to read the dashboard')}")
    how_to_read = list(human_summary.get("how_to_read", []) or [])
    if not how_to_read and judge_summary.get("judge_how_to_read"):
        how_to_read = list(judge_summary.get("judge_how_to_read", []))
    for line in how_to_read:
        st.write(f"- {line}")

    st.markdown(f"### {_u('Việc nên làm tiếp', 'Recommended next steps')}")
    next_steps = list(human_summary.get("recommended_next_actions", []) or [])
    if not next_steps:
        next_steps = [_u("Mở bảng kỹ thuật nếu muốn xem chi tiết từng tín hiệu.", "Open the technical tables if you want more detail on each signal.")]
    for line in next_steps:
        st.write(f"- {line}")


def _render_technical_dashboard(tables: dict):
    tabs = st.tabs(
        [
            f"\U0001F4CA {_u('Tổng quan', 'Overview')}",
            f"\U0001F468\u200D\u2695\ufe0f {_u('Bác sĩ', 'Doctor review')}",
            f"\U0001F9EA {_u('Dịch vụ', 'Procedure review')}",
            f"\U0001F4DC {_u('ICD / bối cảnh', 'ICD / context audit')}",
            f"\U0001F7E2 {_u('Gỡ cờ đỏ', 'Context resolver')}",
            f"\U0001F4B8 {_u('Gánh nặng bệnh nhân', 'Patient burden')}",
            f"\U0001F9F1 {_u('Bằng chứng theo ca', 'Case evidence')}",
        ]
    )

    with tabs[0]:
        _tab_badge(_u("Tổng quan", "Overview"))
        _render_card_rows(
            _u("Trạng thái chỉ định", "Coverage status"),
            tables.get("coverage_status_table"),
            [("covered_status", _u("Trạng thái", "Status")), ("order_count", _u("Số chỉ định", "Order count")), ("amount_vnd", _u("Tiền", "Amount")), ("share", _u("Tỷ trọng", "Share"))],
            max_rows=4,
        )
        _render_card_rows(
            _u("Tóm tắt điều hành", "Executive summary"),
            tables.get("executive_summary_table"),
            [("metric", _u("Chỉ số", "Metric")), ("value", _u("Giá trị", "Value"))],
            max_rows=6,
        )
        _render_bar_chart(tables.get("chart_coverage_pie"), "covered_status", "order_count", _u("Phân bố trạng thái chỉ định", "Coverage status distribution"))

    with tabs[1]:
        _tab_badge(_u("Bác sĩ", "Doctor review"))
        _render_card_rows(
            _u("Ưu tiên rà soát bác sĩ", "Doctor review priority"),
            tables.get("doctor_review_priority_table"),
            [("doctor", _u("Bác sĩ", "Doctor")), ("department", _u("Khoa", "Department")), ("review_priority", _u("Ưu tiên", "Priority")), ("numerator_amount_vnd", _u("Tiền tín hiệu", "Signal amount")), ("numerator_rate", _u("Tỷ lệ", "Rate"))],
            max_rows=5,
        )
        _render_card_rows(
            _u("Bảng bác sĩ bất thường", "Doctor outlier table"),
            tables.get("doctor_outlier_table"),
            [("doctor", _u("Bác sĩ", "Doctor")), ("department", _u("Khoa", "Department")), ("risk_score", _u("Điểm", "Score")), ("review_priority", _u("Ưu tiên", "Priority")), ("explanation_summary", _u("Giải thích", "Explanation"))],
            max_rows=4,
        )
        _render_card_rows(
            _u("Dấu vân tay rủi ro", "Risk fingerprint"),
            tables.get("doctor_risk_fingerprint_table"),
            [("doctor", _u("Bác sĩ", "Doctor")), ("department", _u("Khoa", "Department")), ("signal_name", _u("Tín hiệu", "Signal")), ("signal_value", _u("Giá trị", "Value"))],
            max_rows=4,
        )
        _render_card_rows(
            _u("Bác sĩ bất thường thống kê", "Statistical outlier doctors"),
            tables.get("doctor_statistical_outlier_table"),
            [("doctor", _u("Bác sĩ", "Doctor")), ("department", _u("Khoa", "Department")), ("z_score", _u("Z-score", "Z score")), ("numerator_rate", _u("Tỷ lệ", "Rate")), ("risk_score", _u("Điểm", "Score"))],
            max_rows=4,
        )

    with tabs[2]:
        _tab_badge(_u("Dịch vụ", "Procedure review"))
        _render_card_rows(
            _u("Dịch vụ chi phí cao", "High-cost procedures"),
            tables.get("high_cost_procedure_table"),
            [("procedure", _u("Dịch vụ", "Procedure")), ("department", _u("Khoa", "Department")), ("severity", _u("Mức độ", "Severity")), ("numerator_orders", _u("Dòng tín hiệu", "Signal rows")), ("numerator_amount_vnd", _u("Tiền tín hiệu", "Signal amount"))],
            max_rows=5,
        )
        _render_card_rows(
            _u("Tập trung dịch vụ theo bác sĩ", "Doctor procedure concentration"),
            tables.get("doctor_procedure_concentration_table"),
            [("doctor", _u("Bác sĩ", "Doctor")), ("department", _u("Khoa", "Department")), ("procedure", _u("Dịch vụ", "Procedure")), ("concentration_ratio", _u("Tỷ lệ tập trung", "Concentration ratio")), ("severity", _u("Mức độ", "Severity"))],
            max_rows=5,
        )
        _render_card_rows(
            _u("Biểu đồ Pareto dịch vụ", "Procedure Pareto"),
            tables.get("procedure_pareto_table"),
            [("procedure", _u("Dịch vụ", "Procedure")), ("numerator_amount_vnd", _u("Tiền tín hiệu", "Signal amount")), ("cumulative_percent", _u("Lũy kế", "Cumulative share")), ("pareto_rank", _u("Hạng", "Rank"))],
            max_rows=5,
        )
        _render_card_rows(
            _u("Dịch vụ nhạy cảm theo bác sĩ", "Sensitive services by doctor"),
            tables.get("sensitive_service_by_doctor_table"),
            [("doctor", _u("Bác sĩ", "Doctor")), ("department", _u("Khoa", "Department")), ("procedure", _u("Dịch vụ", "Procedure")), ("numerator_orders", _u("Dòng tín hiệu", "Signal rows"))],
            max_rows=5,
        )

    with tabs[3]:
        _tab_badge(_u("ICD / bối cảnh", "ICD / context audit"))
        _render_card_rows(
            _u("Cờ ICD bắt buộc", "Required ICD flags"),
            tables.get("required_icd_flags"),
            [("claim_id", _u("Claim", "Claim")), ("doctor", _u("Bác sĩ", "Doctor")), ("procedure", _u("Dịch vụ", "Procedure")), ("diagnosis_code", _u("ICD", "ICD")), ("mismatch_type", _u("Loại lệch", "Mismatch type")), ("severity", _u("Mức độ", "Severity"))],
            max_rows=5,
        )
        _render_card_rows(
            _u("Bằng chứng ICD không khớp", "ICD mismatch evidence"),
            tables.get("icd_mismatch_case_evidence"),
            [("claim_id", _u("Claim", "Claim")), ("doctor", _u("Bác sĩ", "Doctor")), ("procedure", _u("Dịch vụ", "Procedure")), ("diagnosis_code", _u("ICD", "ICD")), ("mismatch_type", _u("Loại lệch", "Mismatch type"))],
            max_rows=5,
        )
        _render_card_rows(
            _u("Tổng hợp ICD theo bác sĩ", "Doctor ICD summary"),
            tables.get("doctor_icd_mismatch_summary"),
            [("doctor", _u("Bác sĩ", "Doctor")), ("department", _u("Khoa", "Department")), ("mismatch_count", _u("Không khớp", "Mismatch")), ("missing_icd_count", _u("Thiếu ICD", "Missing ICD")), ("weak_icd_count", _u("ICD yếu", "Weak ICD")), ("severity", _u("Mức độ", "Severity"))],
            max_rows=5,
        )
        _render_card_rows(
            _u("Cặp dịch vụ - ICD", "Procedure-ICD pairs"),
            tables.get("procedure_icd_pair_table"),
            [("procedure", _u("Dịch vụ", "Procedure")), ("diagnosis_code", _u("ICD", "ICD")), ("pair_count", _u("Số cặp", "Pair count")), ("alignment_status", _u("Trạng thái", "Status"))],
            max_rows=5,
        )
        _render_card_rows(
            _u("Bác sĩ dùng ICD chung", "Doctor ICD usage"),
            tables.get("doctor_icd_usage_table"),
            [("doctor", _u("Bác sĩ", "Doctor")), ("diagnosis_code", _u("ICD", "ICD")), ("procedure_count", _u("Số dịch vụ", "Procedure count")), ("icd_reuse_pattern", _u("Kiểu dùng", "Usage pattern"))],
            max_rows=5,
        )

    with tabs[4]:
        _tab_badge(_u("Gỡ cờ đỏ", "Context resolver"))
        _render_card_rows(
            _u("Bối cảnh gỡ cờ đỏ", "False red-flag context"),
            tables.get("false_red_flag_context_table"),
            [("flag_source", _u("Nguồn cờ", "Flag source")), ("doctor", _u("Bác sĩ", "Doctor")), ("procedure", _u("Dịch vụ", "Procedure")), ("resolved_count", _u("Đã gỡ", "Resolved")), ("unresolved_count", _u("Chưa rõ", "Unresolved")), ("unresolved_rate", _u("Tỷ lệ chưa rõ", "Unresolved rate"))],
            max_rows=5,
        )
        _render_card_rows(
            _u("Bảng gỡ cờ đỏ theo ca", "Case context resolution"),
            tables.get("case_context_resolution_table"),
            [("claim_id", _u("Claim", "Claim")), ("doctor", _u("Bác sĩ", "Doctor")), ("procedure", _u("Dịch vụ", "Procedure")), ("resolution_status", _u("Trạng thái", "Status")), ("final_review_action", _u("Việc cần làm", "Action"))],
            max_rows=5,
        )

    with tabs[5]:
        _tab_badge(_u("Gánh nặng bệnh nhân", "Patient burden"))
        _render_card_rows(
            _u("Gánh nặng bệnh nhân", "Patient burden"),
            tables.get("patient_burden_table"),
            [("patient", _u("Bệnh nhân", "Patient")), ("has_insurance_status", _u("Bảo hiểm", "Insurance")), ("total_orders", _u("Tổng chỉ định", "Total orders")), ("numerator_orders", _u("Dòng tín hiệu", "Signal rows")), ("numerator_amount_vnd", _u("Tiền tín hiệu", "Signal amount")), ("review_priority", _u("Ưu tiên", "Priority"))],
            max_rows=5,
        )

    with tabs[6]:
        _tab_badge(_u("Bằng chứng theo ca", "Case evidence"))
        case_table = tables.get("case_evidence_table")
        if case_table is None or case_table.empty:
            st.info(_u("Không có dữ liệu", "No data"))
        else:
            severity_options = [_u("Tất cả", "All")] + sorted({str(value) for value in case_table.get("severity", pd.Series(dtype=object)).dropna().astype(str).tolist()})
            doctor_options = [_u("Tất cả", "All")] + sorted({str(value) for value in case_table.get("doctor", pd.Series(dtype=object)).dropna().astype(str).tolist()})
            department_options = [_u("Tất cả", "All")] + sorted({str(value) for value in case_table.get("department", pd.Series(dtype=object)).dropna().astype(str).tolist()})
            c1, c2, c3 = st.columns(3)
            selected_severity = c1.selectbox(_u("Mức độ", "Severity"), severity_options, index=0)
            selected_doctor = c2.selectbox(_u("Bác sĩ", "Doctor"), doctor_options, index=0)
            selected_department = c3.selectbox(_u("Khoa", "Department"), department_options, index=0)
            filtered = case_table.copy()
            if selected_severity != _u("Tất cả", "All") and "severity" in filtered.columns:
                filtered = filtered[filtered["severity"].astype(str) == selected_severity]
            if selected_doctor != _u("Tất cả", "All") and "doctor" in filtered.columns:
                filtered = filtered[filtered["doctor"].astype(str) == selected_doctor]
            if selected_department != _u("Tất cả", "All") and "department" in filtered.columns:
                filtered = filtered[filtered["department"].astype(str) == selected_department]
            _render_card_rows(
                _u("Bằng chứng theo ca", "Case evidence"),
                filtered,
                [("claim_id", _u("Claim", "Claim")), ("patient", _u("Bệnh nhân", "Patient")), ("doctor", _u("Bác sĩ", "Doctor")), ("department", _u("Khoa", "Department")), ("procedure", _u("Dịch vụ", "Procedure")), ("diagnosis_code", _u("ICD", "ICD")), ("severity", _u("Mức độ", "Severity")), ("recommended_review_action", _u("Nên làm gì", "Recommended action"))],
                max_rows=5,
            )


def render_report_view(final_report, tool_results, excel_bytes):
    tables = final_report.get("tables", {}) or {}
    human_summary = final_report.get("human_summary", {}) or {}
    judge_summary = final_report.get("judge_summary", {}) or {}

    easy_read = st.checkbox(_u("Giao diện dễ đọc", "Easy-read view"), value=True)

    _render_quick_read(final_report, tables)

    if easy_read:
        with st.expander(_u("Xem thêm bảng kỹ thuật", "Show technical details"), expanded=False):
            _render_technical_dashboard(tables)
    else:
        _render_simple_summary(final_report, tables)
        _render_technical_dashboard(tables)

    st.markdown(f"### {_u('Tải xuống', 'Download')}")
    st.download_button(
        label=_u("Tải file Excel", "Download Excel file"),
        data=excel_bytes,
        file_name="over_ordering_sentinel_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    with st.expander(_u("Trạng thái công cụ", "Tool status"), expanded=False):
        for result in tool_results:
            st.write(f"**{result.get('tool_name')}** - {result.get('status')}")
            for note in result.get("notes", []):
                st.write(f"- {note}")
