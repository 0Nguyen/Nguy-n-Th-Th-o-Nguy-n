from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.text_utils import format_pct, safe_rate


def _severity(row):
    if row["out_of_insurance_orders"] >= 5:
        if row["ratio_vs_department_median"] >= 3:
            return "RED"
        if row["ratio_vs_department_median"] >= 2:
            return "ORANGE"
        if row["ratio_vs_department_median"] >= 1.5:
            return "YELLOW"
    return "NORMAL"


def _format_ratio(value):
    if np.isinf(value):
        return "inf"
    return f"{value:.2f}"


def run(df, context):
    insured_df = df[df["has_insurance_status"] == "yes"].copy()
    if insured_df.empty:
        return {
            "tool_name": "02 - Bác sĩ có tỷ lệ bất thường / Doctor outlier detection",
            "status": "completed",
            "summary": {},
            "tables": {"doctor_outlier_table": pd.DataFrame()},
            "notes": ["Không có bệnh nhân có bảo hiểm để phân tích / No insured patients to analyze."],
        }

    grouped = (
        insured_df.groupby(["department", "doctor"], dropna=False)
        .agg(
            insured_patient_count=("patient", "nunique"),
            total_orders_for_insured_patients=("claim_id", "count"),
            out_of_insurance_orders=("covered_status", lambda s: int((s == "out_of_insurance").sum())),
            total_amount_vnd=("amount", "sum"),
        )
        .reset_index()
    )

    out_amount_df = (
        insured_df.loc[insured_df["covered_status"] == "out_of_insurance"]
        .groupby(["department", "doctor"], dropna=False)["amount"]
        .sum()
        .reset_index(name="out_of_insurance_amount_vnd")
    )
    grouped = grouped.merge(out_amount_df, on=["department", "doctor"], how="left")
    grouped["out_of_insurance_amount_vnd"] = grouped["out_of_insurance_amount_vnd"].fillna(0)
    grouped["out_of_insurance_rate"] = grouped.apply(
        lambda row: safe_rate(row["out_of_insurance_orders"], row["total_orders_for_insured_patients"]),
        axis=1,
    )

    dept_medians = grouped.groupby("department", dropna=False)["out_of_insurance_rate"].median().reset_index(name="department_median_rate")
    grouped = grouped.merge(dept_medians, on="department", how="left")
    grouped["department_median_rate"] = grouped["department_median_rate"].fillna(0)

    def _ratio(row):
        median_rate = row["department_median_rate"]
        doctor_rate = row["out_of_insurance_rate"]
        if median_rate > 0:
            return doctor_rate / median_rate
        if doctor_rate > 0:
            return np.inf
        return 1.0

    grouped["ratio_vs_department_median"] = grouped.apply(_ratio, axis=1)
    grouped["severity"] = grouped.apply(_severity, axis=1)
    grouped["top_reason"] = grouped.apply(
        lambda row: (
            f"Tỷ lệ chỉ định ngoài bảo hiểm cao hơn median khoa {_format_ratio(row['ratio_vs_department_median'])} lần / "
            f"Out-of-insurance rate is {_format_ratio(row['ratio_vs_department_median'])} times department median"
        ),
        axis=1,
    )
    grouped["_ratio_sort"] = grouped["ratio_vs_department_median"]

    doctor_outlier_table = grouped.rename(
        columns={
            "department": "khoa__department",
            "doctor": "ten_bac_si__doctor",
        }
    )
    doctor_outlier_table["out_of_insurance_rate"] = doctor_outlier_table["out_of_insurance_rate"].map(format_pct)
    doctor_outlier_table["department_median_rate"] = doctor_outlier_table["department_median_rate"].map(format_pct)
    doctor_outlier_table["ratio_vs_department_median"] = doctor_outlier_table["ratio_vs_department_median"].map(_format_ratio)
    severity_order = {"RED": 0, "ORANGE": 1, "YELLOW": 2, "NORMAL": 3}
    doctor_outlier_table["_severity_order"] = doctor_outlier_table["severity"].map(severity_order)
    doctor_outlier_table = doctor_outlier_table.sort_values(
        ["_severity_order", "out_of_insurance_orders", "_ratio_sort"],
        ascending=[True, False, False],
    ).drop(columns=["_severity_order", "_ratio_sort"])

    return {
        "tool_name": "02 - Bác sĩ có tỷ lệ bất thường / Doctor outlier detection",
        "status": "completed",
        "summary": {"doctor_outlier_table_rows": int(len(doctor_outlier_table))},
        "tables": {"doctor_outlier_table": doctor_outlier_table},
        "notes": [
            "Tool 02 phát hiện bác sĩ có tỷ lệ chỉ định ngoài bảo hiểm bất thường theo khoa / Tool 02 detects doctors with abnormal out-of-insurance rates relative to department median.",
            "Đây là bất thường thống kê, cần hội đồng chuyên môn đánh giá / This is a statistical abnormality that needs expert review.",
        ],
    }
