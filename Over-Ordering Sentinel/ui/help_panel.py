from __future__ import annotations

import streamlit as st

from scripts.i18n import get_language, t


HELP_CONTENT = {
    "vi": {
        "workflow_title": "Luong dung app",
        "workflow_lines": [
            "1. Chay app roi keo tha file Excel hoac dung file mau.",
            "2. Neu workbook co nhieu sheet, chon dung sheet du lieu that, khong chon sheet README hay huong dan.",
            "3. Xem Smart Excel Mapper tu nhan dien header row, cot nguon va gia tri chuan hoa.",
            "4. Neu mapping tu dong dung thi giu nguyen va bam xac nhan.",
            "5. Neu mapping tu dong sai hoac con thieu thi sua tay tung cot bat buoc truoc khi chay phan tich.",
            "6. Doc KPI, cac bang co do, bang go co do, roi tai Excel ket qua de luu ho so review.",
        ],
        "prepare_title": "Chuan bi file Excel",
        "prepare_lines": [
            "Moi dong nen dai dien cho mot chi dinh, dich vu, thuoc hoac thu thuat.",
            "Co gang de mot dong header ro rang, khong tron nhieu dong tieu de.",
            "Khong gop o o vung du lieu chinh neu co the.",
            "Neu workbook co nhieu sheet, nen giu mot sheet du lieu sach nhat de app de nhan dien.",
            "Bon cot toi thieu phai map duoc la `DoctorName`, `PatientName`, `HasInsurance`, `CoveredByInsurance`.",
        ],
        "auto_title": "Chuan hoa tu dong hoat dong the nao",
        "auto_lines": [
            "App tu doan sheet du lieu, header row va cot phu hop nhat.",
            "App cung tu gom cac gia tri gan nghia ve cung chuan, vi du `Co`, `Khong`, `BHYT`, `Yes`, `No` khi ngu canh du ro.",
            "Neu preview sau chuan hoa nhin hop ly, ban nen giu auto mapping de tiet kiem thoi gian.",
            "Neu thay mot cot trang thai bi toan `unknown`, do la dau hieu can kiem tra lai mapping hoac cach ghi du lieu goc.",
        ],
        "manual_title": "Khi nao can noi cot va chuan hoa thu cong",
        "manual_lines": [
            "Dung manual mapping khi app chon nham cot, thieu cot hoac file dung ten cot la cua tung benh vien.",
            "Uu tien sua dung hai cot logic quan trong nhat la `HasInsurance` va `CoveredByInsurance` truoc.",
            "`HasInsurance` la benh nhan co BHYT hay khong. `CoveredByInsurance` la chi dinh cu the do co duoc BHYT chi tra hay khong.",
            "Mot benh nhan co BHYT van co the phat sinh chi dinh ngoai BHYT. Neu nhap nham hai cot nay, toan bo phan tich se lech.",
            "Sau khi chinh tay, hay nhin `Normalized data preview` de xem du lieu da ve dung logic chua roi moi chay phan tich.",
        ],
        "read_title": "Cach doc bao cao phan tich",
        "read_lines": [
            "`Overview` va cac KPI cho biet quy mo du lieu insured, so chi dinh, ty le ngoai bao hiem va tong chi phi ngoai bao hiem.",
            "`By doctor` dung de so sanh bac si voi nhau trong cung tap du lieu, khong nen doc tach roi khoi quy mo benh nhan va so ca.",
            "`By department` giup xem khoa nao co mat do ngoai bao hiem hoac chi phi noi bat.",
            "`Doctor Red Flag Ranking` la bang uu tien xem xet truoc, khong phai ket luan sai pham.",
            "`Suspicious High-Cost Procedure` tap trung vao dich vu hoac thu thuat chi phi cao can soi ky hon.",
            "`Required ICD Flags` giup tim cac chi dinh can ngu canh ICD hoac chan doan di kem.",
            "`False Red Flag Context` giup loai bot cac truong hop nhin do nhung co the hop ly khi xet context.",
            "`Case evidence` la noi xem vi du ca cu the de hoi dong doc sau hon thay vi chi nhin thong ke tong.",
            "`Tool status` cho biet cong cu nao da chay, co ghi chu gi, va co phan nao khong du du lieu de ket luan.",
        ],
        "caution_title": "Luu y quan trong",
        "caution_lines": [
            "App chi ho tro review thong ke va uu tien ca can xem tiep, khong tu ket luan gian lan hay lam dung.",
            "Neu file goc qua lon xon, nen don sheet du lieu truoc khi upload thay vi co sua moi thu trong app.",
            "Khi ket qua trong bat thuong qua muc, hay kiem tra lai mapping, preview chuan hoa va cach benh vien ma hoa trang thai bao hiem.",
        ],
        "tip": "Meo: voi file don gian, chi can keo tha Excel la app thuong tu nhan sheet, header va mapping du tot de chay ngay.",
    },
    "en": {
        "workflow_title": "App workflow",
        "workflow_lines": [
            "1. Start the app, then drop the Excel file or use a sample file.",
            "2. If the workbook has multiple sheets, choose the real data sheet, not the README or guide sheet.",
            "3. Let Smart Excel Mapper detect the header row, source columns, and normalized values.",
            "4. If the automatic mapping looks correct, keep it and confirm.",
            "5. If the automatic mapping is wrong or incomplete, manually fix the required columns before running analysis.",
            "6. Read the KPIs, red-flag tables, false-red-flag table, then export the Excel report for review.",
        ],
        "prepare_title": "Prepare the Excel file",
        "prepare_lines": [
            "Each row should ideally represent one order, service, medicine, or procedure.",
            "Keep one clear header row and avoid stacked title rows when possible.",
            "Avoid merged cells in the main data region if possible.",
            "If the workbook has many sheets, keep one clean data sheet so detection works better.",
            "The four minimum columns are `DoctorName`, `PatientName`, `HasInsurance`, and `CoveredByInsurance`.",
        ],
        "auto_title": "How automatic normalization works",
        "auto_lines": [
            "The app guesses the best data sheet, header row, and matching source columns.",
            "It also normalizes near-equivalent values into a standard meaning when the insurance context is clear.",
            "If the normalized preview looks reasonable, keep the automatic mapping to save time.",
            "If one status column becomes entirely `unknown`, review the source mapping or the raw value patterns.",
        ],
        "manual_title": "When to use manual mapping and manual normalization",
        "manual_lines": [
            "Use manual mapping when the app picked the wrong column, missed a required column, or the hospital uses unusual headers.",
            "Fix the two most important logic columns first: `HasInsurance` and `CoveredByInsurance`.",
            "`HasInsurance` means whether the patient has insurance. `CoveredByInsurance` means whether that specific order is covered.",
            "An insured patient can still have out-of-insurance orders. If these two columns are mixed up, the whole analysis becomes misleading.",
            "After manual changes, always review the `Normalized data preview` before you run the analysis.",
        ],
        "read_title": "How to read the analysis",
        "read_lines": [
            "`Overview` and the KPI cards show the insured-data size, order volume, out-of-insurance rate, and out-of-insurance amount.",
            "`By doctor` is for comparing doctors inside the same dataset and should be read together with patient volume and case count.",
            "`By department` helps identify departments with notable out-of-insurance density or cost patterns.",
            "`Doctor Red Flag Ranking` is a prioritization list for review, not a wrongdoing verdict.",
            "`Suspicious High-Cost Procedure` focuses on expensive services or procedures that need closer review.",
            "`Required ICD Flags` highlights orders that may need matching ICD or diagnosis context.",
            "`False Red Flag Context` helps remove cases that look suspicious statistically but may be explainable in context.",
            "`Case evidence` is where reviewers can inspect concrete case-level examples instead of relying only on aggregate numbers.",
            "`Tool status` shows which tools ran, what notes they produced, and whether any part lacked enough data.",
        ],
        "caution_title": "Important cautions",
        "caution_lines": [
            "The app supports statistical review and prioritization. It does not automatically conclude fraud or abuse.",
            "If the raw workbook is extremely messy, clean the main data sheet before upload instead of forcing everything inside the app.",
            "If the results look implausibly extreme, re-check the mapping, the normalized preview, and the hospital's insurance coding.",
        ],
        "tip": "Tip: with a simple workbook, drag-and-drop is often enough for the app to detect the sheet, header, and mapping automatically.",
    },
}


def render_help_panel():
    lang = get_language()
    content = HELP_CONTENT.get(lang, HELP_CONTENT["en"])

    with st.expander(t("help_panel_title"), expanded=False):
        st.markdown(f"**{t('quick_guide_title')}**")
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
