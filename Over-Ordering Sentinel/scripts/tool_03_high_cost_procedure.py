from __future__ import annotations

import pandas as pd

from scripts.text_utils import contains_any, format_pct, format_vnd


SENSITIVE_KEYWORDS = [
    "MRI",
    "CT",
    "HIV",
    "HbA1c",
    "Glucose",
    "Đường huyết",
    "Troponin",
    "Men tim",
    "CRP",
    "Đông máu",
    "Coagulation",
]


def _severity(row):
    if (row["high_cost"] or row["flag_sensitive_procedure"]) and row["out_of_insurance_orders"] >= 5:
        return "RED"
    if (row["high_cost"] or row["flag_sensitive_procedure"]) and row["out_of_insurance_orders"] >= 3:
        return "ORANGE"
    if row["out_of_insurance_orders"] >= 3:
        return "YELLOW"
    return "NORMAL"


def run(df, context):
    insured_df = df[df["has_insurance_status"] == "yes"].copy()
    if insured_df.empty:
        return {
            "tool_name": "03 - Dịch vụ chi phí cao / High-cost procedure review",
            "status": "completed",
            "summary": {},
            "tables": {"high_cost_procedure_table": pd.DataFrame()},
            "notes": ["Không có bệnh nhân có bảo hiểm để phân tích / No insured patients to analyze."],
        }

    median_amount = float(insured_df["amount"].median()) if not insured_df["amount"].empty else 0.0
    high_cost_threshold = max(median_amount * 3, 500000)

    grouped = (
        insured_df.groupby(["doctor", "department", "procedure"], dropna=False)
        .agg(
            total_orders=("claim_id", "count"),
            out_of_insurance_orders=("covered_status", lambda s: int((s == "out_of_insurance").sum())),
            avg_amount_vnd=("amount", "mean"),
            total_amount_vnd=("amount", "sum"),
        )
        .reset_index()
    )
    out_amount_df = (
        insured_df.loc[insured_df["covered_status"] == "out_of_insurance"]
        .groupby(["doctor", "department", "procedure"], dropna=False)["amount"]
        .sum()
        .reset_index(name="out_of_insurance_amount_vnd")
    )
    grouped = grouped.merge(out_amount_df, on=["doctor", "department", "procedure"], how="left")
    grouped["out_of_insurance_amount_vnd"] = grouped["out_of_insurance_amount_vnd"].fillna(0)
    grouped["out_of_insurance_rate"] = grouped.apply(
        lambda row: 0 if row["total_orders"] == 0 else row["out_of_insurance_orders"] / row["total_orders"],
        axis=1,
    )
    grouped["high_cost"] = grouped["avg_amount_vnd"] >= high_cost_threshold
    grouped["flag_sensitive_procedure"] = grouped["procedure"].apply(lambda value: contains_any(value, SENSITIVE_KEYWORDS))
    grouped["severity"] = grouped.apply(_severity, axis=1)

    high_cost_procedure_table = grouped.rename(
        columns={
            "doctor": "ten_bac_si__doctor",
            "department": "khoa__department",
            "procedure": "ten_dich_vu__procedure",
        }
    )
    high_cost_procedure_table["out_of_insurance_rate"] = high_cost_procedure_table["out_of_insurance_rate"].map(format_pct)
    high_cost_procedure_table["avg_amount_vnd"] = high_cost_procedure_table["avg_amount_vnd"].map(format_vnd)
    high_cost_procedure_table["total_amount_vnd"] = high_cost_procedure_table["total_amount_vnd"].map(format_vnd)
    high_cost_procedure_table["out_of_insurance_amount_vnd"] = high_cost_procedure_table["out_of_insurance_amount_vnd"].map(format_vnd)
    severity_order = {"RED": 0, "ORANGE": 1, "YELLOW": 2, "NORMAL": 3}
    high_cost_procedure_table["_severity_order"] = high_cost_procedure_table["severity"].map(severity_order)
    high_cost_procedure_table = high_cost_procedure_table.sort_values(
        ["_severity_order", "out_of_insurance_orders", "avg_amount_vnd"],
        ascending=[True, False, False],
    ).drop(columns=["_severity_order"])

    return {
        "tool_name": "03 - Dịch vụ chi phí cao / High-cost procedure review",
        "status": "completed",
        "summary": {"high_cost_threshold_vnd": format_vnd(high_cost_threshold)},
        "tables": {"high_cost_procedure_table": high_cost_procedure_table},
        "notes": [
            f"Ngưỡng chi phí cao / High-cost threshold: {format_vnd(high_cost_threshold):,.0f} VND",
            "Tool 03 phát hiện dịch vụ chi phí cao hoặc nhạy cảm có chỉ định ngoài bảo hiểm bất thường / Tool 03 detects high-cost or sensitive procedures with abnormal out-of-insurance ordering.",
        ],
    }
