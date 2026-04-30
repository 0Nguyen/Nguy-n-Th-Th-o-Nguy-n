from __future__ import annotations

import pandas as pd

from scripts.text_utils import contains_any, format_vnd


RULES = [
    {
        "name": "HIV test requires ICD/context",
        "keywords": ["HIV", "xet nghiem hiv", "test hiv"],
        "required_icd": ["Z11", "B20", "B21", "B22", "B23", "B24"],
        "context_keywords": ["tien phau", "phau thuat", "surgery", "pre op"],
    },
    {
        "name": "Glucose/HbA1c requires ICD/context",
        "keywords": ["Glucose", "Duong huyet", "HbA1c", "duong huyet", "xet nghiem duong huyet"],
        "required_icd": ["E10", "E11", "E12", "E13", "E14", "R73"],
        "context_keywords": ["tien phau", "pre op"],
    },
    {
        "name": "Troponin/Men tim requires ICD/context",
        "keywords": ["Troponin", "Men tim", "xet nghiem tim", "cardiac marker"],
        "required_icd": ["R07", "I20", "I21", "I22", "I24"],
        "context_keywords": [],
    },
]

MRI_CT_KEYWORDS = ["MRI", "CT", "chup mri", "chup ct"]
GLOBAL_CONTEXT_KEYWORDS = ["tien phau", "phau thuat", "pre op", "surgery", "operation", "noi tru", "cap cuu", "emergency", "inpatient"]


def _has_required_icd(code: object, required_icd: list[str]) -> bool:
    code_text = str(code or "").upper()
    return any(icd.upper() in code_text for icd in required_icd)


def _has_context(row) -> bool:
    combined = " ".join(
        [
            str(row.get("procedure", "")),
            str(row.get("diagnosis_name", "")),
            str(row.get("diagnosis_code", "")),
        ]
    )
    return contains_any(combined, GLOBAL_CONTEXT_KEYWORDS)


def run(df, context):
    insured_df = df[df["has_insurance_status"] == "yes"].copy()
    if insured_df.empty:
        return {
            "tool_name": "04 - Chỉ định cần ICD đi kèm / Required ICD-context check",
            "status": "completed",
            "summary": {},
            "tables": {"required_icd_flags": pd.DataFrame(), "case_evidence_table": pd.DataFrame()},
            "notes": ["Không có bệnh nhân có bảo hiểm để phân tích / No insured patients to analyze."],
        }

    diagnosis_code_present = bool(insured_df["diagnosis_code"].astype(str).str.strip().replace("nan", "").ne("").any())
    diagnosis_name_present = bool(insured_df["diagnosis_name"].astype(str).str.strip().replace("nan", "").ne("").any())
    flags = []

    median_amount = float(insured_df["amount"].median()) if not insured_df["amount"].empty else 0.0
    high_cost_threshold = max(median_amount * 3, 500000)

    for _, row in insured_df.iterrows():
        procedure = str(row.get("procedure", ""))
        diagnosis_code = str(row.get("diagnosis_code", ""))
        diagnosis_name = str(row.get("diagnosis_name", ""))
        covered_status = row.get("covered_status", "unknown")
        amount_vnd = format_vnd(row.get("amount", 0))

        for rule in RULES:
            if not contains_any(procedure, rule["keywords"]):
                continue
            has_icd = _has_required_icd(diagnosis_code, rule["required_icd"])
            has_context = contains_any(f"{diagnosis_code} {diagnosis_name} {procedure}", rule["context_keywords"] + GLOBAL_CONTEXT_KEYWORDS)
            if not has_icd and not has_context:
                flags.append(
                    {
                        "claim_id": row.get("claim_id", ""),
                        "patient": row.get("patient", ""),
                        "doctor": row.get("doctor", ""),
                        "department": row.get("department", ""),
                        "procedure": procedure,
                        "diagnosis_code": diagnosis_code,
                        "diagnosis_name": diagnosis_name,
                        "covered_status": covered_status,
                        "amount_vnd": amount_vnd,
                        "rule_name": rule["name"],
                        "severity": "RED",
                        "note": "Thiếu ICD/context phù hợp / Missing required ICD-context",
                    }
                )
            break

        if covered_status == "out_of_insurance" and contains_any(procedure, MRI_CT_KEYWORDS):
            has_icd = bool(str(diagnosis_code).strip())
            has_context = _has_context(row)
            severity = "RED" if amount_vnd >= high_cost_threshold else "YELLOW"
            if not has_icd and not has_context:
                flags.append(
                    {
                        "claim_id": row.get("claim_id", ""),
                        "patient": row.get("patient", ""),
                        "doctor": row.get("doctor", ""),
                        "department": row.get("department", ""),
                        "procedure": procedure,
                        "diagnosis_code": diagnosis_code,
                        "diagnosis_name": diagnosis_name,
                        "covered_status": covered_status,
                        "amount_vnd": amount_vnd,
                        "rule_name": "MRI/CT out-of-insurance without clear ICD/context",
                        "severity": severity,
                        "note": "MRI/CT ngoài bảo hiểm nhưng thiếu ICD/context rõ ràng / MRI/CT out-of-insurance lacks clear ICD/context",
                    }
                )

    required_icd_flags = pd.DataFrame(flags)
    if required_icd_flags.empty:
        return {
            "tool_name": "04 - Chỉ định cần ICD đi kèm / Required ICD-context check",
            "status": "completed",
            "summary": {
                "diagnosis_code_present": diagnosis_code_present,
                "diagnosis_name_present": diagnosis_name_present,
                "high_cost_threshold_vnd": high_cost_threshold,
            },
            "tables": {"required_icd_flags": pd.DataFrame(), "case_evidence_table": pd.DataFrame()},
            "notes": [
                "Không phát hiện trường hợp thiếu ICD/context bắt buộc / No missing required ICD-context cases found.",
                "Nếu cột ICD không có dữ liệu, app vẫn chạy và chỉ ghi chú thay vì crash / If ICD columns are empty, the app still runs and notes it instead of crashing.",
            ],
        }

    case_evidence_table = required_icd_flags[
        ["claim_id", "patient", "doctor", "department", "procedure", "diagnosis_code", "diagnosis_name", "rule_name", "severity", "note"]
    ].copy()

    return {
        "tool_name": "04 - Chỉ định cần ICD đi kèm / Required ICD-context check",
        "status": "completed",
        "summary": {
            "flag_count": int(len(required_icd_flags)),
            "diagnosis_code_present": diagnosis_code_present,
            "diagnosis_name_present": diagnosis_name_present,
            "high_cost_threshold_vnd": high_cost_threshold,
        },
        "tables": {"required_icd_flags": required_icd_flags, "case_evidence_table": case_evidence_table},
        "notes": [
            f"Phát hiện {len(required_icd_flags)} trường hợp cần xem xét ICD/context / Found {len(required_icd_flags)} cases needing ICD/context review.",
            f"Cột ICD có dữ liệu: {diagnosis_code_present}; cột chẩn đoán có dữ liệu: {diagnosis_name_present} / ICD column present: {diagnosis_code_present}; diagnosis name present: {diagnosis_name_present}.",
            "Severity RED = thiếu ICD/context phù hợp cần xem xét / RED = missing required ICD-context for review.",
        ],
    }
