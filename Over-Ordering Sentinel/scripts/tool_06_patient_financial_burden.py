from __future__ import annotations

import pandas as pd

from scripts.analysis_support import get_context_frames, to_numeric_series
from scripts.text_utils import format_vnd


def run(df, context):
    scope, denominator_df, numerator_df, reference_df = get_context_frames(df, context)
    denominator_df = denominator_df if denominator_df is not None else pd.DataFrame()
    numerator_df = numerator_df if numerator_df is not None else pd.DataFrame()

    if denominator_df.empty:
        empty = pd.DataFrame()
        return {
            "tool_name": "06 - Patient financial burden review",
            "status": "completed",
            "summary": {
                "total_patients_with_burden": 0,
                "total_numerator_amount_vnd": 0,
                "average_burden_vnd": 0,
                "median_burden_vnd": 0,
                "p90_burden_vnd": 0,
                "max_burden_vnd": 0,
            },
            "tables": {
                "patient_burden_table": empty,
                "patient_burden_summary_table": empty,
                "chart_patient_burden_top20": empty,
            },
            "notes": ["No denominator rows were available for patient burden review."],
        }

    burden_table = (
        numerator_df.groupby(["patient"], dropna=False)
        .agg(
            has_insurance_status=("has_insurance_status", "first"),
            total_orders=("claim_id", "count"),
            numerator_orders=("claim_id", "count"),
            numerator_amount_vnd=("amount", "sum"),
            highest_numerator_order_vnd=("amount", "max"),
            doctor_count=("doctor", "nunique"),
            department_count=("department", "nunique"),
        )
        .reset_index()
    ) if not numerator_df.empty else pd.DataFrame(columns=["patient", "has_insurance_status", "total_orders", "numerator_orders", "numerator_amount_vnd", "highest_numerator_order_vnd", "doctor_count", "department_count"])

    if burden_table.empty:
        burden_table = pd.DataFrame(columns=[
            "patient",
            "has_insurance_status",
            "total_orders",
            "numerator_orders",
            "numerator_amount_vnd",
            "highest_numerator_order_vnd",
            "doctor_count",
            "department_count",
            "top_procedure",
            "review_priority",
        ])
    else:
        top_proc = (
            numerator_df.groupby(["patient", "procedure"], dropna=False)["claim_id"]
            .count()
            .reset_index(name="cnt")
            .sort_values(["patient", "cnt", "procedure"], ascending=[True, False, True])
            .drop_duplicates(["patient"], keep="first")
            .rename(columns={"procedure": "top_procedure"})
        )
        burden_table = burden_table.merge(top_proc[["patient", "top_procedure"]], on="patient", how="left")
        burden_table["review_priority"] = burden_table["numerator_amount_vnd"].apply(
            lambda value: "HIGH" if value >= burden_table["numerator_amount_vnd"].quantile(0.9) else "MEDIUM" if value >= burden_table["numerator_amount_vnd"].median() else "LOW"
        )

    burden_table["numerator_amount_vnd"] = to_numeric_series(burden_table["numerator_amount_vnd"]).apply(format_vnd)
    burden_table["highest_numerator_order_vnd"] = to_numeric_series(burden_table["highest_numerator_order_vnd"]).apply(format_vnd)
    burden_table = burden_table.sort_values("numerator_amount_vnd", ascending=False).reset_index(drop=True)

    summary_table = pd.DataFrame(
        [
            {"Metric": "total_patients_with_burden", "Value": int(len(burden_table))},
            {"Metric": "total_numerator_amount_vnd", "Value": format_vnd(burden_table["numerator_amount_vnd"].sum()) if not burden_table.empty else 0},
            {"Metric": "average_burden_vnd", "Value": format_vnd(burden_table["numerator_amount_vnd"].mean()) if not burden_table.empty else 0},
            {"Metric": "median_burden_vnd", "Value": format_vnd(burden_table["numerator_amount_vnd"].median()) if not burden_table.empty else 0},
            {"Metric": "p90_burden_vnd", "Value": format_vnd(burden_table["numerator_amount_vnd"].quantile(0.9)) if not burden_table.empty else 0},
            {"Metric": "max_burden_vnd", "Value": format_vnd(burden_table["numerator_amount_vnd"].max()) if not burden_table.empty else 0},
        ]
    )

    chart_patient_burden_top20 = burden_table.head(20).copy()

    return {
        "tool_name": "06 - Patient financial burden review",
        "status": "completed",
        "summary": {
            "total_patients_with_burden": int(len(burden_table)),
            "total_numerator_amount_vnd": format_vnd(burden_table["numerator_amount_vnd"].sum()) if not burden_table.empty else 0,
            "average_burden_vnd": format_vnd(burden_table["numerator_amount_vnd"].mean()) if not burden_table.empty else 0,
            "median_burden_vnd": format_vnd(burden_table["numerator_amount_vnd"].median()) if not burden_table.empty else 0,
            "p90_burden_vnd": format_vnd(burden_table["numerator_amount_vnd"].quantile(0.9)) if not burden_table.empty else 0,
            "max_burden_vnd": format_vnd(burden_table["numerator_amount_vnd"].max()) if not burden_table.empty else 0,
        },
        "tables": {
            "patient_burden_table": burden_table,
            "patient_burden_summary_table": summary_table,
            "chart_patient_burden_top20": chart_patient_burden_top20,
        },
        "notes": [
            "Tool 06 is available as a dormant module but is not yet wired into the dispatcher.",
            "It is intended for patient burden review within the selected scope.",
        ],
    }
