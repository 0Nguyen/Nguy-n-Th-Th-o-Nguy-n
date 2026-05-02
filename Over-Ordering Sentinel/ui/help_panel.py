from __future__ import annotations

import streamlit as st

from scripts.i18n import get_language, t


def _u(vi: str, en: str) -> str:
    return en if get_language() == "en" else vi


HELP_CONTENT = {
    "vi": {
        "workflow_title": "Lu?ng s? d?ng ?ng d?ng",
        "workflow_lines": [
            "1. Tải file Excel lên.",
            "2. Nếu workbook có nhiều sheet, chọn đúng sheet dữ liệu thật, không chọn sheet README hoặc sheet hướng dẫn.",
            "3. Xem phần Ánh xạ Excel thông minh để biết app đã nhận đúng cột hay chưa.",
            "4. Nếu ánh xạ tự động đúng, giữ nguyên và bấm xác nhận.",
            "5. Nếu ánh xạ sai hoặc thiếu, sửa tay các cột quan trọng trước khi chạy phân tích.",
            "6. Đọc phần tóm tắt ngắn, các bảng cảnh báo, rồi tải Excel kết quả để lưu hồ sơ review.",
        ],
        "prepare_title": "Chuẩn bị file Excel",
        "prepare_lines": [
            "Mỗi dòng nên đại diện cho một chỉ định, dịch vụ, thuốc hoặc thủ thuật.",
            "Nên để một hàng tiêu đề rõ ràng, không chồng nhiều hàng tiêu đề.",
            "Hạn chế gộp ô trong vùng dữ liệu chính nếu có thể.",
            "Nếu workbook có nhiều sheet, nên giữ một sheet dữ liệu sạch nhất để app dễ nhận diện.",
            "Hai cột logic quan trọng nhất là `HasInsurance` và `CoveredByInsurance`.",
        ],
        "auto_title": "?nh x? v? chu?n h?a t? ??ng ho?t ??ng th? n?o",
        "auto_lines": [
            "App tự đoán sheet dữ liệu, dòng tiêu đề và các cột nguồn phù hợp nhất.",
            "App cũng chuẩn hoá các giá trị gần nghĩa thành cùng một logic chung khi bối cảnh bảo hiểm đủ rõ.",
            "Nếu preview sau chuẩn hoá nhìn hợp lý, nên giữ mapping tự động để tiết kiệm thời gian.",
            "N?u m?t c?t tr?ng th?i b? to?n `unknown`, h?y ki?m tra l?i ?nh x? ho?c c?ch ghi d? li?u g?c.",
        ],
        "manual_title": "Khi n?o c?n n?i c?t v? chu?n h?a th? c?ng",
        "manual_lines": [
            "Dùng manual mapping khi app chọn nhầm cột, thiếu cột, hoặc file dùng header riêng của bệnh viện.",
            "Ưu tiên sửa đúng hai cột logic quan trọng nhất: `HasInsurance` và `CoveredByInsurance`.",
            "`HasInsurance` là bệnh nhân có bảo hiểm hay không. `CoveredByInsurance` là chỉ định cụ thể đó có được bảo hiểm chi trả hay không.",
            "Một bệnh nhân có bảo hiểm vẫn có thể có chỉ định ngoài bảo hiểm. Nếu nhầm hai cột này, toàn bộ phân tích sẽ lệch.",
            "Ghi ch? chu?n h?a d? li?u Excel th? c?ng: h?y s?a header, ??ng nh?t m? gi? tr?, b? merged cells ? v?ng d? li?u, r?i ki?m tra `Normalized data preview` tr??c khi ch?y ph?n t?ch.",
        ],
        "read_title": "Cách đọc báo cáo phân tích",
        "read_lines": [
            "`Tổng quan` và các thẻ KPI cho biết quy mô dữ liệu, số chỉ định, tỷ lệ ngoài bảo hiểm và tổng chi phí ngoài bảo hiểm.",
            "`Theo bác sĩ` dùng để so sánh bác sĩ trong cùng một tập dữ liệu, không nên tách rời khỏi quy mô bệnh nhân và số ca.",
            "`Theo khoa` giúp xem khoa nào có mật độ ngoài bảo hiểm hoặc chi phí nổi bật.",
            "`Bảng ưu tiên bác sĩ` là bảng xem xét trước, không phải kết luận sai phạm.",
            "`Bảng rà dịch vụ` tập trung vào dịch vụ hoặc thủ thuật chi phí cao cần soi kỹ hơn.",
            "`Bảng rà ICD / bối cảnh` giúp tìm các chỉ định cần ngữ cảnh ICD hoặc chẩn đoán đi kèm.",
            "`Bảng gỡ cờ đỏ theo bối cảnh` giúp loại bớt các trường hợp nhìn đỏ nhưng có thể hợp lý khi xét ngữ cảnh.",
            "`Bằng chứng theo ca` là nơi xem ví dụ ca cụ thể để đọc sâu hơn thay vì chỉ nhìn thống kê tổng.",
            "`Trạng thái công cụ` cho biết công cụ nào đã chạy, có ghi chú gì, và phần nào chưa đủ dữ liệu để kết luận.",
        ],
        "caution_title": "Lưu ý quan trọng",
        "caution_lines": [
            "Chế độ mặc định phân tích bệnh nhân có bảo hiểm và chỉ định ngoài bảo hiểm.",
            "Bộ lọc thủ công cho phép xem nhóm khác, nhưng kết quả phải đọc đúng theo scope đã chọn.",
            "App chỉ hỗ trợ review thống kê và ưu tiên ca cần xem tiếp, không tự kết luận gian lận hay lạm dụng.",
            "Nếu file gốc quá rối, nên dọn sheet dữ liệu trước khi upload thay vì cố sửa tất cả ngay trong app.",
            "Khi kết quả nhìn bất thường quá mức, hãy kiểm tra lại mapping, preview chuẩn hoá và cách bệnh viện mã hoá trạng thái bảo hiểm.",
        ],
        "tip": "M?o: v?i file ??n gi?n, ch? c?n k?o th? Excel l? app th??ng t? nh?n sheet, header v? ?nh x? kh? t?t ?? ch?y ngay.",
    },
    "en": {
        "workflow_title": "Lu?ng s? d?ng ?ng d?ng",
        "workflow_lines": [
            "1. Upload the Excel file.",
            "2. If the workbook has multiple sheets, choose the real data sheet, not the README or guide sheet.",
            "3. Review Smart Excel Mapper to confirm the detected columns.",
            "4. If the automatic mapping looks correct, keep it and confirm.",
            "5. If the automatic mapping is wrong or incomplete, fix the required columns before running analysis.",
            "6. Read the short summary, the warning tables, then download the Excel result for review records.",
        ],
        "prepare_title": "Prepare the Excel file",
        "prepare_lines": [
            "Each row should represent one order, service, medicine, or procedure.",
            "Keep one clear header row and avoid stacked title rows when possible.",
            "Avoid merged cells in the main data region if possible.",
            "If the workbook has many sheets, keep one clean data sheet so detection works better.",
            "The two most important logic columns are `HasInsurance` and `CoveredByInsurance`.",
        ],
        "auto_title": "?nh x? v? chu?n h?a t? ??ng ho?t ??ng th? n?o",
        "auto_lines": [
            "The app guesses the best data sheet, header row, and matching source columns.",
            "It also normalizes near-equivalent values into a standard meaning when the insurance context is clear.",
            "If the normalized preview looks reasonable, keep the automatic mapping to save time.",
            "N?u m?t c?t tr?ng th?i b? to?n `unknown`, h?y ki?m tra l?i ?nh x? ho?c c?ch ghi d? li?u g?c.",
        ],
        "manual_title": "Khi n?o c?n n?i c?t v? chu?n h?a th? c?ng",
        "manual_lines": [
            "Use manual mapping when the app picked the wrong column, missed a required column, or the hospital uses unusual headers.",
            "Fix the two most important logic columns first: `HasInsurance` and `CoveredByInsurance`.",
            "`HasInsurance` means whether the patient has insurance. `CoveredByInsurance` means whether that specific order is covered.",
            "An insured patient can still have out-of-insurance orders. If these two columns are mixed up, the whole analysis becomes misleading.",
            "Ghi ch? chu?n h?a d? li?u Excel th? c?ng: h?y s?a header, ??ng nh?t m? gi? tr?, b? merged cells ? v?ng d? li?u, r?i ki?m tra `Normalized data preview` tr??c khi ch?y ph?n t?ch.",
        ],
        "read_title": "How to read the analysis",
        "read_lines": [
            "`Overview` and the KPI cards show the cohort size, order volume, out-of-insurance rate, and out-of-insurance amount.",
            "`By doctor` is for comparing doctors inside the same dataset and should be read together with patient volume and case count.",
            "`By department` helps identify departments with notable out-of-insurance density or cost patterns.",
            "`Doctor review priority` is a prioritization list for review, not a wrongdoing verdict.",
            "`Procedure review` focuses on expensive services or procedures that need closer review.",
            "`ICD / Context audit` highlights orders that may need matching ICD or diagnosis context.",
            "`Context resolver` helps reduce cases that look suspicious statistically but may be explainable in context.",
            "`Case evidence` is where reviewers can inspect concrete case-level examples instead of relying only on aggregate numbers.",
            "`Tool status` shows which tools ran, what notes they produced, and whether any part lacked enough data.",
        ],
        "caution_title": "Important cautions",
        "caution_lines": [
            "The app supports statistical review and prioritization. It does not automatically conclude fraud or abuse.",
            "If the raw workbook is extremely messy, clean the main data sheet before upload instead of forcing everything inside the app.",
            "If the results look implausibly extreme, re-check the mapping, the normalized preview, and the hospital's insurance coding.",
        ],
        "tip": "M?o: v?i file ??n gi?n, ch? c?n k?o th? Excel l? app th??ng t? nh?n sheet, header v? ?nh x? kh? t?t ?? ch?y ngay.",
    },
}


def render_help_panel():
    lang = get_language()
    content = HELP_CONTENT.get(lang, HELP_CONTENT["en"])

    with st.expander(t("help_panel_title"), expanded=False):
        st.markdown(_u("**4 bước nhanh**", "**Quick steps**"))
        st.write(f"1. {t('quick_guide_step_1')}")
        st.write(f"2. {t('quick_guide_step_2')}")
        st.write(f"3. {t('quick_guide_step_3')}")
        st.write(f"4. {t('quick_guide_step_4')}")
        st.divider()

        for section_key in [
            "workflow_title",
            "prepare_title",
            "auto_title",
            "manual_title",
            "read_title",
            "caution_title",
        ]:
            st.markdown(f"**{content[section_key]}**")
            lines_key = section_key.replace("_title", "_lines")
            for line in content[lines_key]:
                st.write(f"- {line}")
            st.write("")

        st.info(content["tip"])
