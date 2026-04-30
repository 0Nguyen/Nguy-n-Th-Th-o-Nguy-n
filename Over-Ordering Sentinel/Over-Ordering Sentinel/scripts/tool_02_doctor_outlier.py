from __future__ import annotations

import math

import numpy as np
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


def _review_priority(score: float) -> str:
    if score >= 70:
        return "HIGH REVIEW PRIORITY"
    if score >= 45:
        return "MODERATE REVIEW PRIORITY"
    if score >= 20:
        return "LOW REVIEW PRIORITY"
    return "MONITOR"


def _low_volume_warning(orders: int) -> str:
    if orders < 10:
        return "LOW_VOLUME"
    if orders < 30:
        return "MODERATE_VOLUME"
    return "STABLE_SIGNAL"


def _top_values(frame: pd.DataFrame, group_cols: list[str], target_col: str, n: int = 3) -> dict[tuple, str]:
    if frame is None or frame.empty or target_col not in frame.columns:
        return {}
    agg = frame.groupby(group_cols + [target_col], dropna=False)["claim_id"].count().reset_index(name="cnt")
    agg = agg.sort_values(group_cols + ["cnt", target_col], ascending=[True] * len(group_cols) + [False, True])
    result = {}
    for keys, group in agg.groupby(group_cols, dropna=False):
        values = group[target_col].dropna().astype(str).tolist()[:n]
        key = keys if isinstance(keys, tuple) else (keys,)
        result[key] = ", ".join(v for v in values if v and v.lower() != "nan")
    return result


def _safe_std(series: pd.Series) -> float:
    if series is None or len(series) < 2:
        return 0.0
    value = float(series.std(ddof=0))
    return 0.0 if math.isnan(value) else value


def _build_doctor_frame(denominator_df: pd.DataFrame, numerator_df: pd.DataFrame) -> pd.DataFrame:
    if denominator_df is None or denominator_df.empty:
        return pd.DataFrame(
            columns=[
                "ten_bac_si__doctor",
                "department",
                "patient_count",
                "denominator_orders",
                "numerator_orders",
                "numerator_rate",
                "denominator_amount_vnd",
                "numerator_amount_vnd",
                "department_baseline_rate",
                "global_baseline_rate",
                "ratio_vs_department",
                "risk_difference_vs_department",
                "expected_numerator_orders",
                "excess_numerator_orders",
                "excess_amount_vnd",
                "z_score",
                "low_volume_warning",
                "top_numerator_procedures",
                "top_icd_codes",
                "missing_icd_count",
                "sensitive_service_count",
                "high_cost_service_count",
                "risk_score",
                "review_priority",
                "severity",
                "explanation_summary",
            ]
        )

    numerator_df = numerator_df if numerator_df is not None else pd.DataFrame()

    doctor_base = (
        denominator_df.groupby(["department", "doctor"], dropna=False)
        .agg(
            patient_count=("patient", "nunique"),
            denominator_orders=("claim_id", "count"),
            denominator_amount_vnd=("amount", "sum"),
        )
        .reset_index()
    )
    doctor_signal = (
        numerator_df.groupby(["department", "doctor"], dropna=False)
        .agg(
            numerator_orders=("claim_id", "count"),
            numerator_amount_vnd=("amount", "sum"),
        )
        .reset_index()
    ) if not numerator_df.empty else pd.DataFrame(columns=["department", "doctor", "numerator_orders", "numerator_amount_vnd"])

    table = doctor_base.merge(doctor_signal, on=["department", "doctor"], how="left")
    table["numerator_orders"] = table["numerator_orders"].fillna(0).astype(int)
    table["numerator_amount_vnd"] = table["numerator_amount_vnd"].fillna(0).apply(format_vnd)
    table["denominator_amount_vnd"] = table["denominator_amount_vnd"].fillna(0).apply(format_vnd)
    table["numerator_rate"] = table.apply(lambda row: safe_rate(row["numerator_orders"], row["denominator_orders"]), axis=1)

    dept_stats = (
        table.groupby("department", dropna=False)
        .agg(
            department_rate_mean=("numerator_rate", "mean"),
            department_rate_std=("numerator_rate", lambda s: _safe_std(s)),
            department_total_orders=("denominator_orders", "sum"),
            department_total_signal=("numerator_orders", "sum"),
            department_total_amount=("numerator_amount_vnd", "sum"),
            department_mean_signal_amount=("numerator_amount_vnd", "mean"),
        )
        .reset_index()
    )
    dept_stats["department_baseline_rate"] = dept_stats.apply(
        lambda row: safe_rate(row["department_total_signal"], row["department_total_orders"]),
        axis=1,
    )
    global_baseline_rate = safe_rate(int(numerator_df.shape[0]), int(denominator_df.shape[0])) if len(denominator_df) else 0
    table = table.merge(dept_stats, on="department", how="left")
    table["department_baseline_rate"] = table["department_baseline_rate"].fillna(0)
    table["department_rate_std"] = table["department_rate_std"].fillna(0)
    table["global_baseline_rate"] = global_baseline_rate

    table["ratio_vs_department"] = table.apply(
        lambda row: row["numerator_rate"] / row["department_baseline_rate"] if row["department_baseline_rate"] > 0 else (np.inf if row["numerator_rate"] > 0 else 1.0),
        axis=1,
    )
    table["risk_difference_vs_department"] = table["numerator_rate"] - table["department_baseline_rate"]
    table["expected_numerator_orders"] = table["denominator_orders"] * table["department_baseline_rate"]
    table["excess_numerator_orders"] = table["numerator_orders"] - table["expected_numerator_orders"]
    table["excess_amount_vnd"] = (
        table["numerator_amount_vnd"] - (table["expected_numerator_orders"] * table["department_mean_signal_amount"].fillna(0))
    ).round(0)

    if numerator_df is not None and not numerator_df.empty:
        top_procedures = (
            numerator_df.groupby(["department", "doctor", "procedure"], dropna=False)["claim_id"]
            .count()
            .reset_index(name="cnt")
            .sort_values(["department", "doctor", "cnt", "procedure"], ascending=[True, True, False, True])
            .drop_duplicates(["department", "doctor"], keep="first")
            .rename(columns={"procedure": "top_numerator_procedures"})
        )
        top_icd = (
            numerator_df.groupby(["department", "doctor", "diagnosis_code"], dropna=False)["claim_id"]
            .count()
            .reset_index(name="cnt")
            .sort_values(["department", "doctor", "cnt", "diagnosis_code"], ascending=[True, True, False, True])
            .drop_duplicates(["department", "doctor"], keep="first")
            .rename(columns={"diagnosis_code": "top_icd_codes"})
        )
        table = table.merge(top_procedures[["department", "doctor", "top_numerator_procedures"]], on=["department", "doctor"], how="left")
        table = table.merge(top_icd[["department", "doctor", "top_icd_codes"]], on=["department", "doctor"], how="left")
    else:
        table["top_numerator_procedures"] = ""
        table["top_icd_codes"] = ""

    table["top_numerator_procedures"] = table["top_numerator_procedures"].fillna("")
    table["top_icd_codes"] = table["top_icd_codes"].fillna("")

    if numerator_df is not None and not numerator_df.empty:
        top_q75 = float(numerator_df.groupby(["department", "doctor"], dropna=False)["amount"].sum().quantile(0.75))
    else:
        top_q75 = 0.0

    def _doctor_rows(row):
        mask = pd.Series(True, index=numerator_df.index if not numerator_df.empty else pd.Index([]))
        if numerator_df.empty:
            return pd.DataFrame()
        mask = numerator_df["doctor"].astype(str) == str(row["doctor"])
        if "department" in numerator_df.columns:
            mask &= numerator_df["department"].astype(str) == str(row["department"])
        return numerator_df.loc[mask].copy()

    risk_scores = []
    explanations = []
    review_priorities = []
    severities = []
    z_scores = []
    missing_icd_counts = []
    sensitive_counts = []
    high_cost_counts = []

    base_median_amount = float(denominator_df["amount"].median()) if "amount" in denominator_df.columns and not denominator_df.empty else 0.0
    high_cost_threshold = max(base_median_amount * 3, 500000)
    q75_amount = float(table["numerator_amount_vnd"].quantile(0.75)) if not table.empty else 0.0

    for _, row in table.iterrows():
        doctor_rows = _doctor_rows(row)
        missing_icd_count = int(doctor_rows["diagnosis_code"].astype(str).str.strip().replace("nan", "").eq("").sum()) if not doctor_rows.empty and "diagnosis_code" in doctor_rows.columns else 0
        sensitive_service_count = int(doctor_rows["procedure"].apply(lambda value: contains_any(value, SENSITIVE_KEYWORDS)).sum()) if not doctor_rows.empty and "procedure" in doctor_rows.columns else 0
        high_cost_service_count = int((to_numeric_series(doctor_rows["amount"]) >= high_cost_threshold).sum()) if not doctor_rows.empty else 0

        score = 0
        ratio_vs_department = row["ratio_vs_department"]
        if row["numerator_orders"] >= 5 and ratio_vs_department >= 3:
            score += 25
        if row["numerator_orders"] >= 5 and ratio_vs_department >= 2:
            score += 18
        if row["numerator_orders"] >= 5 and ratio_vs_department >= 1.5:
            score += 10
        if row["numerator_amount_vnd"] >= q75_amount and q75_amount > 0:
            score += 15
        if missing_icd_count >= 5:
            score += 15
        if sensitive_service_count >= 5:
            score += 10
        if high_cost_service_count >= 5:
            score += 10
        if _low_volume_warning(int(row["denominator_orders"])) == "STABLE_SIGNAL":
            score += 7
        score = min(int(score), 100)

        review_priority = _review_priority(score)
        if score >= 70:
            severity = "HIGH REVIEW PRIORITY"
        elif score >= 45:
            severity = "MODERATE REVIEW PRIORITY"
        elif score >= 20:
            severity = "LOW REVIEW PRIORITY"
        else:
            severity = "NORMAL / MONITOR"

        if row["department_rate_std"] > 0:
            z_score = (row["numerator_rate"] - row["department_baseline_rate"]) / row["department_rate_std"]
        else:
            z_score = 0.0

        explanation = (
            f"Doctor has {int(row['numerator_orders'])} numerator orders, {format_pct(row['numerator_rate'])} numerator rate, "
            f"{row['ratio_vs_department']:.2f}x department baseline, {int(round(row['excess_numerator_orders']))} excess orders, "
            f"amount {format_vnd(row['numerator_amount_vnd']):,.0f} VND."
        )

        risk_scores.append(score)
        explanations.append(explanation)
        review_priorities.append(review_priority)
        severities.append(severity)
        z_scores.append(float(z_score))
        missing_icd_counts.append(missing_icd_count)
        sensitive_counts.append(sensitive_service_count)
        high_cost_counts.append(high_cost_service_count)

    table["missing_icd_count"] = missing_icd_counts
    table["sensitive_service_count"] = sensitive_counts
    table["high_cost_service_count"] = high_cost_counts
    table["low_volume_warning"] = table["denominator_orders"].astype(int).apply(_low_volume_warning)
    table["z_score"] = z_scores
    table["risk_score"] = risk_scores
    table["review_priority"] = review_priorities
    table["severity"] = severities
    table["explanation_summary"] = explanations
    display_table = table.rename(columns={"doctor": "ten_bac_si__doctor"}).copy()

    doctor_review_priority_table = display_table[
        [
            "ten_bac_si__doctor",
            "department",
            "denominator_orders",
            "numerator_orders",
            "numerator_rate",
            "numerator_amount_vnd",
            "risk_score",
            "review_priority",
            "severity",
            "explanation_summary",
        ]
    ].sort_values(["risk_score", "numerator_amount_vnd", "numerator_orders"], ascending=[False, False, False]).reset_index(drop=True)

    doctor_statistical_outlier_table = display_table.sort_values(["risk_score", "numerator_amount_vnd", "numerator_orders"], ascending=[False, False, False])[
        [
            "ten_bac_si__doctor",
            "department",
            "patient_count",
            "denominator_orders",
            "numerator_orders",
            "numerator_rate",
            "department_baseline_rate",
            "global_baseline_rate",
            "ratio_vs_department",
            "risk_difference_vs_department",
            "expected_numerator_orders",
            "excess_numerator_orders",
            "excess_amount_vnd",
            "z_score",
            "low_volume_warning",
            "top_numerator_procedures",
            "top_icd_codes",
            "missing_icd_count",
            "sensitive_service_count",
            "high_cost_service_count",
            "risk_score",
            "review_priority",
            "severity",
            "explanation_summary",
        ]
    ].reset_index(drop=True)

    doctor_risk_fingerprint_table = display_table.sort_values(["risk_score", "numerator_amount_vnd"], ascending=[False, False])[
        [
            "ten_bac_si__doctor",
            "department",
            "denominator_orders",
            "numerator_orders",
            "numerator_rate",
            "ratio_vs_department",
            "low_volume_warning",
            "missing_icd_count",
            "sensitive_service_count",
            "high_cost_service_count",
            "risk_score",
            "review_priority",
            "severity",
        ]
    ].reset_index(drop=True)

    doctor_outlier_table = doctor_review_priority_table.copy()
    doctor_outlier_table["numerator_rate"] = doctor_outlier_table["numerator_rate"].map(format_pct)

    chart_top_doctor_amount = display_table.sort_values("numerator_amount_vnd", ascending=False)[
        ["ten_bac_si__doctor", "department", "numerator_amount_vnd", "numerator_orders", "risk_score"]
    ].head(20).reset_index(drop=True)
    chart_doctor_scatter = display_table[
        [
            "ten_bac_si__doctor",
            "department",
            "denominator_orders",
            "numerator_rate",
            "numerator_amount_vnd",
            "risk_score",
        ]
    ].copy()

    summary = {
        "doctor_outlier_table_rows": int(len(doctor_outlier_table)),
        "top_review_priority_doctor": str(doctor_review_priority_table.iloc[0]["ten_bac_si__doctor"]) if not doctor_review_priority_table.empty else "",
        "top_review_priority_department": str(doctor_review_priority_table.iloc[0]["department"]) if not doctor_review_priority_table.empty else "",
        "top_review_priority_score": int(doctor_review_priority_table.iloc[0]["risk_score"]) if not doctor_review_priority_table.empty else 0,
    }

    return {
        "tool_name": "02 - Xếp hạng bác sĩ cần xem",
        "status": "completed",
        "summary": summary,
        "tables": {
            "doctor_outlier_table": doctor_outlier_table,
            "doctor_review_priority_table": doctor_review_priority_table,
            "doctor_statistical_outlier_table": doctor_statistical_outlier_table,
            "doctor_risk_fingerprint_table": doctor_risk_fingerprint_table,
            "chart_top_doctor_amount": chart_top_doctor_amount,
            "chart_doctor_scatter": chart_doctor_scatter,
        },
        "notes": [
            "This ranking compares each doctor against the current denominator scope and department baseline.",
            "Điểm số này chỉ dùng để ưu tiên rà soát, không được hiểu là kết luận sai phạm.",
        ],
    }


def run(df, context):
    scope, denominator_df, numerator_df, reference_df = get_context_frames(df, context)
    denominator_df = denominator_df if denominator_df is not None else pd.DataFrame()
    numerator_df = numerator_df if numerator_df is not None else pd.DataFrame()
    if denominator_df.empty:
        empty = pd.DataFrame()
        return {
        "tool_name": "02 - Xếp hạng bác sĩ cần xem",
            "status": "completed",
            "summary": {},
            "tables": {
                "doctor_outlier_table": empty,
                "doctor_review_priority_table": empty,
                "doctor_statistical_outlier_table": empty,
                "doctor_risk_fingerprint_table": empty,
                "chart_top_doctor_amount": empty,
                "chart_doctor_scatter": empty,
            },
            "notes": ["Không có dòng mẫu nền để xếp hạng bác sĩ trong scope hiện tại."],
        }

    return _build_doctor_frame(denominator_df, numerator_df)
