from __future__ import annotations

import pandas as pd

from scripts.analysis_support import get_context_frames, to_numeric_series
from scripts.text_utils import contains_any, format_pct, format_vnd, safe_rate


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
    "X-ray",
    "Ultrasound",
    "Siêu âm",
    "Endoscopy",
    "Nội soi",
]


def _severity(row):
    if (row["high_cost"] or row["flag_sensitive_procedure"]) and row["numerator_orders"] >= 5:
        return "RED"
    if (row["high_cost"] or row["flag_sensitive_procedure"]) and row["numerator_orders"] >= 3:
        return "ORANGE"
    if row["numerator_orders"] >= 3:
        return "YELLOW"
    return "NORMAL"


def _severity_concentration(row):
    if row["concentration_ratio"] >= 3 and row["numerator_orders"] >= 5:
        return "RED"
    if row["concentration_ratio"] >= 2 and row["numerator_orders"] >= 3:
        return "ORANGE"
    if row["concentration_ratio"] >= 1.5 and row["numerator_orders"] >= 3:
        return "YELLOW"
    return "NORMAL"


def _first_keyword(value: str) -> str:
    hits = [keyword for keyword in SENSITIVE_KEYWORDS if contains_any(value, [keyword])]
    return hits[0] if hits else ""


def _base_group_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["doctor", "department", "procedure"])
    return frame


def run(df, context):
    scope, denominator_df, numerator_df, reference_df = get_context_frames(df, context)
    denominator_df = _base_group_frame(denominator_df)
    numerator_df = _base_group_frame(numerator_df)

    if denominator_df.empty:
        empty = pd.DataFrame()
        return {
            "tool_name": "03 - Procedure and cost review",
            "status": "completed",
            "summary": {"high_cost_threshold_vnd": 0},
            "tables": {
                "high_cost_procedure_table": empty,
                "doctor_procedure_concentration_table": empty,
                "procedure_pareto_table": empty,
                "sensitive_service_by_doctor_table": empty,
                "chart_procedure_pareto": empty,
                "chart_top_procedure_amount": empty,
                "chart_doctor_procedure_heatmap": empty,
            },
            "notes": ["No baseline rows were available to review procedures in the current scope."],
        }

    global_median = float(to_numeric_series(denominator_df["amount"]).median()) if "amount" in denominator_df.columns else 0.0
    high_cost_threshold = max(global_median * 3, 500000)

    denominator_group = (
        denominator_df.groupby(["doctor", "department", "procedure"], dropna=False)
        .agg(
            denominator_orders=("claim_id", "count"),
            avg_amount_vnd=("amount", "mean"),
            median_amount_vnd=("amount", "median"),
            total_amount_vnd=("amount", "sum"),
        )
        .reset_index()
    )
    numerator_group = (
        numerator_df.groupby(["doctor", "department", "procedure"], dropna=False)
        .agg(
            numerator_orders=("claim_id", "count"),
            numerator_amount_vnd=("amount", "sum"),
        )
        .reset_index()
    ) if not numerator_df.empty else pd.DataFrame(columns=["doctor", "department", "procedure", "numerator_orders", "numerator_amount_vnd"])

    high_cost_procedure_table = denominator_group.merge(numerator_group, on=["doctor", "department", "procedure"], how="left")
    high_cost_procedure_table["numerator_orders"] = high_cost_procedure_table["numerator_orders"].fillna(0).astype(int)
    high_cost_procedure_table["numerator_amount_vnd"] = high_cost_procedure_table["numerator_amount_vnd"].fillna(0).apply(format_vnd)
    high_cost_procedure_table["avg_amount_vnd"] = to_numeric_series(high_cost_procedure_table["avg_amount_vnd"]).apply(format_vnd)
    high_cost_procedure_table["median_amount_vnd"] = to_numeric_series(high_cost_procedure_table["median_amount_vnd"]).apply(format_vnd)
    high_cost_procedure_table["total_amount_vnd"] = to_numeric_series(high_cost_procedure_table["total_amount_vnd"]).apply(format_vnd)
    high_cost_procedure_table["numerator_rate"] = high_cost_procedure_table.apply(lambda row: safe_rate(row["numerator_orders"], row["denominator_orders"]), axis=1)
    high_cost_procedure_table["high_cost"] = high_cost_procedure_table["avg_amount_vnd"] >= high_cost_threshold
    high_cost_procedure_table["flag_sensitive_procedure"] = high_cost_procedure_table["procedure"].astype(str).apply(lambda value: bool(_first_keyword(value)))
    high_cost_procedure_table["severity"] = high_cost_procedure_table.apply(_severity, axis=1)
    high_cost_procedure_table["review_reason"] = high_cost_procedure_table.apply(
        lambda row: (
            "High-cost procedure in the current scope."
            if row["high_cost"]
            else "Sensitive procedure in the current scope."
            if row["flag_sensitive_procedure"]
            else "Procedure signal is within the current review scope."
        ),
        axis=1,
    )

    doctor_conc = (
        numerator_df.groupby(["doctor", "department", "procedure"], dropna=False)
        .agg(
            numerator_orders=("claim_id", "count"),
            numerator_amount_vnd=("amount", "sum"),
        )
        .reset_index()
    ) if not numerator_df.empty else pd.DataFrame(columns=["doctor", "department", "procedure", "numerator_orders", "numerator_amount_vnd"])

    if not numerator_df.empty:
        doctor_totals = (
            numerator_df.groupby(["doctor", "department"], dropna=False)
            .agg(
                doctor_total_numerator_orders=("claim_id", "count"),
                doctor_total_numerator_amount_vnd=("amount", "sum"),
            )
            .reset_index()
        )
        department_totals = (
            numerator_df.groupby(["department", "procedure"], dropna=False)
            .agg(department_procedure_numerator_orders=("claim_id", "count"))
            .reset_index()
        )
        department_scope_total = (
            numerator_df.groupby(["department"], dropna=False)
            .agg(department_total_numerator_orders=("claim_id", "count"))
            .reset_index()
        )
        doctor_conc = doctor_conc.merge(doctor_totals, on=["doctor", "department"], how="left")
        doctor_conc["procedure_share_of_doctor_numerator_orders"] = doctor_conc.apply(
            lambda row: safe_rate(row["numerator_orders"], row["doctor_total_numerator_orders"]),
            axis=1,
        )
        doctor_conc["procedure_share_of_doctor_numerator_amount"] = doctor_conc.apply(
            lambda row: safe_rate(row["numerator_amount_vnd"], row["doctor_total_numerator_amount_vnd"]),
            axis=1,
        )
        doctor_conc = doctor_conc.merge(department_totals, on=["department", "procedure"], how="left")
        doctor_conc = doctor_conc.merge(department_scope_total, on=["department"], how="left")
        doctor_conc["department_procedure_baseline_share"] = doctor_conc.apply(
            lambda row: safe_rate(row["department_procedure_numerator_orders"], row["department_total_numerator_orders"]),
            axis=1,
        )
        doctor_conc["concentration_ratio"] = doctor_conc.apply(
            lambda row: row["procedure_share_of_doctor_numerator_orders"] / row["department_procedure_baseline_share"]
            if row["department_procedure_baseline_share"] > 0
            else (float("inf") if row["procedure_share_of_doctor_numerator_orders"] > 0 else 1.0),
            axis=1,
        )
        doctor_conc["severity"] = doctor_conc.apply(_severity_concentration, axis=1)
        doctor_conc["explanation_summary"] = doctor_conc.apply(
            lambda row: (
                f"Procedure share is {format_pct(row['procedure_share_of_doctor_numerator_orders'])} of the doctor's numerator volume, "
                f"{row['concentration_ratio']:.2f}x the department baseline."
            ),
            axis=1,
        )
    else:
        doctor_conc = pd.DataFrame(
            columns=[
                "doctor",
                "department",
                "procedure",
                "numerator_orders",
                "doctor_total_numerator_orders",
                "procedure_share_of_doctor_numerator_orders",
                "numerator_amount_vnd",
                "doctor_total_numerator_amount_vnd",
                "procedure_share_of_doctor_numerator_amount",
                "department_procedure_baseline_share",
                "concentration_ratio",
                "severity",
                "explanation_summary",
            ]
        )

    procedure_pareto_table = (
        numerator_df.groupby("procedure", dropna=False)
        .agg(
            numerator_orders=("claim_id", "count"),
            numerator_amount_vnd=("amount", "sum"),
        )
        .reset_index()
        .sort_values("numerator_amount_vnd", ascending=False)
        .reset_index(drop=True)
    ) if not numerator_df.empty else pd.DataFrame(columns=["procedure", "numerator_orders", "numerator_amount_vnd"])
    if not procedure_pareto_table.empty:
        procedure_pareto_table["numerator_amount_vnd"] = to_numeric_series(procedure_pareto_table["numerator_amount_vnd"]).apply(format_vnd)
        procedure_pareto_table["cumulative_amount_vnd"] = procedure_pareto_table["numerator_amount_vnd"].cumsum()
        total_amount = max(float(procedure_pareto_table["numerator_amount_vnd"].sum()), 1.0)
        procedure_pareto_table["cumulative_percent"] = procedure_pareto_table["cumulative_amount_vnd"].apply(lambda value: safe_rate(value, total_amount))
        procedure_pareto_table["pareto_rank"] = range(1, len(procedure_pareto_table) + 1)
    else:
        procedure_pareto_table = pd.DataFrame(columns=["procedure", "numerator_orders", "numerator_amount_vnd", "cumulative_amount_vnd", "cumulative_percent", "pareto_rank"])

    sensitive_rows = []
    if not numerator_df.empty:
        for _, row in numerator_df.iterrows():
            matched_keyword = _first_keyword(str(row.get("procedure", "")))
            if not matched_keyword:
                continue
            sensitive_rows.append(
                {
                    "doctor": row.get("doctor", ""),
                    "department": row.get("department", ""),
                    "procedure": row.get("procedure", ""),
                    "sensitive_keyword_matched": matched_keyword,
                    "amount_vnd": format_vnd(row.get("amount", 0)),
                    "claim_id": row.get("claim_id", ""),
                }
            )

    sensitive_service_by_doctor_table = pd.DataFrame(sensitive_rows)
    if not sensitive_service_by_doctor_table.empty:
        sensitive_service_by_doctor_table = (
            sensitive_service_by_doctor_table.groupby(["doctor", "department", "procedure", "sensitive_keyword_matched"], dropna=False)
            .agg(
                numerator_orders=("claim_id", "count"),
                numerator_amount_vnd=("amount_vnd", "sum"),
            )
            .reset_index()
        )
        doctor_totals = (
            numerator_df.groupby(["doctor", "department"], dropna=False)
            .agg(doctor_total_numerator_orders=("claim_id", "count"), doctor_total_numerator_amount_vnd=("amount", "sum"))
            .reset_index()
        )
        sensitive_service_by_doctor_table = sensitive_service_by_doctor_table.merge(doctor_totals, on=["doctor", "department"], how="left")
        sensitive_service_by_doctor_table["rate"] = sensitive_service_by_doctor_table.apply(
            lambda row: safe_rate(row["numerator_orders"], row["doctor_total_numerator_orders"]),
            axis=1,
        )
    else:
        sensitive_service_by_doctor_table = pd.DataFrame(
            columns=[
                "doctor",
                "department",
                "procedure",
                "sensitive_keyword_matched",
                "numerator_orders",
                "numerator_amount_vnd",
                "rate",
            ]
        )

    chart_top_procedure_amount = procedure_pareto_table.head(20).copy()
    chart_doctor_procedure_heatmap = doctor_conc[
        [
            "doctor",
            "department",
            "procedure",
            "numerator_orders",
            "procedure_share_of_doctor_numerator_orders",
            "concentration_ratio",
            "severity",
        ]
    ].copy() if not doctor_conc.empty else pd.DataFrame()

    summary = {
        "high_cost_threshold_vnd": format_vnd(high_cost_threshold),
        "high_cost_rows": int((high_cost_procedure_table["high_cost"] | high_cost_procedure_table["flag_sensitive_procedure"]).sum()) if not high_cost_procedure_table.empty else 0,
        "sensitive_rows": int(len(sensitive_service_by_doctor_table)),
        "procedure_pareto_rows": int(len(procedure_pareto_table)),
    }

    return {
        "tool_name": "03 - Procedure and cost review",
        "status": "completed",
        "summary": summary,
        "tables": {
            "high_cost_procedure_table": high_cost_procedure_table,
            "doctor_procedure_concentration_table": doctor_conc,
            "procedure_pareto_table": procedure_pareto_table,
            "sensitive_service_by_doctor_table": sensitive_service_by_doctor_table,
            "chart_procedure_pareto": procedure_pareto_table.head(20).copy(),
            "chart_top_procedure_amount": chart_top_procedure_amount,
            "chart_doctor_procedure_heatmap": chart_doctor_procedure_heatmap,
        },
        "notes": [
            f"High-cost threshold is {format_vnd(high_cost_threshold):,.0f} VND in the current scope.",
            "This table only highlights procedure concentration and cost patterns for further review; it is not a finding of wrongdoing.",
        ],
    }
