from __future__ import annotations

import pandas as pd

from scripts.analysis_scope import build_scope_summary
from scripts.analysis_support import get_context_frames, to_numeric_series
from scripts.text_utils import format_pct, format_vnd, safe_rate


def _safe_mode(series: pd.Series) -> str:
    if series is None or series.empty:
        return ""
    values = series.dropna().astype(str)
    if values.empty:
        return ""
    return values.value_counts().index[0]


def _top_value(frame: pd.DataFrame, group_cols: list[str], target_col: str, value_col: str, fallback: str = "") -> str:
    if frame is None or frame.empty or target_col not in frame.columns:
        return fallback
    agg = frame.groupby(target_col, dropna=False)[value_col].sum().reset_index()
    if agg.empty:
        return fallback
    agg = agg.sort_values(value_col, ascending=False)
    top = agg.iloc[0][target_col]
    top_text = str(top).strip()
    return top_text if top_text and top_text.lower() != "nan" else fallback


def _build_coverage_table(denominator_df: pd.DataFrame) -> pd.DataFrame:
    if denominator_df is None or denominator_df.empty or "covered_status" not in denominator_df.columns:
        return pd.DataFrame(columns=["covered_status", "order_count", "amount_vnd", "share"])
    table = (
        denominator_df.groupby("covered_status", dropna=False)
        .agg(
            order_count=("claim_id", "count"),
            amount_vnd=("amount", "sum"),
        )
        .reset_index()
    )
    total_orders = max(int(table["order_count"].sum()), 1)
    table["share"] = table["order_count"].apply(lambda value: safe_rate(value, total_orders))
    table["amount_vnd"] = table["amount_vnd"].apply(format_vnd)
    return table.sort_values("order_count", ascending=False).reset_index(drop=True)


def _group_by_doctor(denominator_df: pd.DataFrame, numerator_df: pd.DataFrame) -> pd.DataFrame:
    if denominator_df is None or denominator_df.empty:
        return pd.DataFrame(
            columns=[
                "ten_bac_si__doctor",
                "department",
                "denominator_orders",
                "numerator_orders",
                "numerator_rate",
                "numerator_amount_vnd",
                "total_amount_vnd",
                "patient_count",
                "top_numerator_procedure",
                "top_diagnosis_code",
                "review_note",
            ]
        )

    numerator_group = (
        numerator_df.groupby(["doctor", "department"], dropna=False)
        .agg(
            numerator_orders=("claim_id", "count"),
            numerator_amount_vnd=("amount", "sum"),
        )
        .reset_index()
    ) if numerator_df is not None and not numerator_df.empty else pd.DataFrame(columns=["doctor", "department", "numerator_orders", "numerator_amount_vnd"])

    denominator_group = (
        denominator_df.groupby(["doctor", "department"], dropna=False)
        .agg(
            denominator_orders=("claim_id", "count"),
            total_amount_vnd=("amount", "sum"),
            patient_count=("patient", "nunique"),
        )
        .reset_index()
    )

    table = denominator_group.merge(numerator_group, on=["doctor", "department"], how="left")
    table["numerator_orders"] = table["numerator_orders"].fillna(0).astype(int)
    table["numerator_amount_vnd"] = table["numerator_amount_vnd"].fillna(0).apply(format_vnd)
    table["numerator_rate"] = table.apply(lambda row: safe_rate(row["numerator_orders"], row["denominator_orders"]), axis=1)

    if numerator_df is not None and not numerator_df.empty:
        top_proc = (
            numerator_df.groupby(["doctor", "department", "procedure"], dropna=False)["claim_id"]
            .count()
            .reset_index(name="cnt")
            .sort_values(["doctor", "department", "cnt", "procedure"], ascending=[True, True, False, True])
        )
        top_diag = (
            numerator_df.groupby(["doctor", "department", "diagnosis_code"], dropna=False)["claim_id"]
            .count()
            .reset_index(name="cnt")
            .sort_values(["doctor", "department", "cnt", "diagnosis_code"], ascending=[True, True, False, True])
        )
        top_proc = top_proc.drop_duplicates(["doctor", "department"], keep="first").rename(columns={"procedure": "top_numerator_procedure"})
        top_diag = top_diag.drop_duplicates(["doctor", "department"], keep="first").rename(columns={"diagnosis_code": "top_diagnosis_code"})
        table = table.merge(top_proc[["doctor", "department", "top_numerator_procedure"]], on=["doctor", "department"], how="left")
        table = table.merge(top_diag[["doctor", "department", "top_diagnosis_code"]], on=["doctor", "department"], how="left")
    else:
        table["top_numerator_procedure"] = ""
        table["top_diagnosis_code"] = ""

    table["top_numerator_procedure"] = table["top_numerator_procedure"].fillna("")
    table["top_diagnosis_code"] = table["top_diagnosis_code"].fillna("")
    table["review_note"] = table.apply(
        lambda row: "Has review signals in the current scope." if row["numerator_orders"] > 0 else "No review signals in the current scope.",
        axis=1,
    )
    table = table.rename(columns={"doctor": "ten_bac_si__doctor"})
    table = table.sort_values(["numerator_orders", "numerator_amount_vnd", "denominator_orders"], ascending=[False, False, False]).reset_index(drop=True)
    return table


def _group_by_department(denominator_df: pd.DataFrame, numerator_df: pd.DataFrame) -> pd.DataFrame:
    if denominator_df is None or denominator_df.empty:
        return pd.DataFrame(columns=["khoa__department", "doctor_count", "patient_count", "denominator_orders", "numerator_orders", "numerator_rate", "numerator_amount_vnd", "total_amount_vnd"])

    numerator_group = (
        numerator_df.groupby("department", dropna=False)
        .agg(
            numerator_orders=("claim_id", "count"),
            numerator_amount_vnd=("amount", "sum"),
        )
        .reset_index()
    ) if numerator_df is not None and not numerator_df.empty else pd.DataFrame(columns=["department", "numerator_orders", "numerator_amount_vnd"])

    denominator_group = (
        denominator_df.groupby("department", dropna=False)
        .agg(
            doctor_count=("doctor", "nunique"),
            patient_count=("patient", "nunique"),
            denominator_orders=("claim_id", "count"),
            total_amount_vnd=("amount", "sum"),
        )
        .reset_index()
    )

    table = denominator_group.merge(numerator_group, on="department", how="left")
    table["numerator_orders"] = table["numerator_orders"].fillna(0).astype(int)
    table["numerator_amount_vnd"] = table["numerator_amount_vnd"].fillna(0).apply(format_vnd)
    table["numerator_rate"] = table.apply(lambda row: safe_rate(row["numerator_orders"], row["denominator_orders"]), axis=1)
    table = table.rename(columns={"department": "khoa__department"})
    table = table.sort_values(["numerator_orders", "numerator_amount_vnd", "denominator_orders"], ascending=[False, False, False]).reset_index(drop=True)
    return table


def run(df, context):
    scope, denominator_df, numerator_df, reference_df = get_context_frames(df, context)
    raw_df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()

    total_patients_in_file = int(raw_df["patient"].nunique()) if not raw_df.empty and "patient" in raw_df.columns else int(len(raw_df))
    denominator_rows = int(len(denominator_df))
    numerator_rows = int(len(numerator_df))
    denominator_patient_count = int(denominator_df["patient"].nunique()) if not denominator_df.empty and "patient" in denominator_df.columns else 0
    numerator_patient_count = int(numerator_df["patient"].nunique()) if not numerator_df.empty and "patient" in numerator_df.columns else 0

    numerator_rate = safe_rate(numerator_rows, denominator_rows)
    denominator_amount_vnd = format_vnd(to_numeric_series(denominator_df["amount"]).sum()) if not denominator_df.empty and "amount" in denominator_df.columns else 0
    numerator_amount_vnd = format_vnd(to_numeric_series(numerator_df["amount"]).sum()) if not numerator_df.empty and "amount" in numerator_df.columns else 0

    coverage_status_table = _build_coverage_table(denominator_df)
    by_doctor = _group_by_doctor(denominator_df, numerator_df)
    by_department = _group_by_department(denominator_df, numerator_df)

    top_risk_doctor = ""
    top_risk_department = ""
    top_risk_procedure = ""
    if not by_doctor.empty:
        top_risk_doctor = str(by_doctor.iloc[0]["ten_bac_si__doctor"])
        top_risk_department = str(by_doctor.iloc[0]["department"])
        top_risk_procedure = str(by_doctor.iloc[0]["top_numerator_procedure"])

    summary = {
        "tong_benh_nhan_trong_file__total_patients_in_file": total_patients_in_file,
        "so_benh_nhan_co_bao_hiem__insured_patient_count": denominator_patient_count if scope.patient_scope == "insured_only" else denominator_patient_count,
        "so_bac_si_co_chi_dinh_cho_benh_nhan_co_bao_hiem__doctor_count_for_insured_patients": int(denominator_df["doctor"].nunique()) if not denominator_df.empty and "doctor" in denominator_df.columns else 0,
        "tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients": denominator_rows,
        "chi_dinh_duoc_bao_hiem_chi_tra__covered_by_insurance_orders": int((denominator_df["covered_status"] == "covered").sum()) if not denominator_df.empty and "covered_status" in denominator_df.columns else 0,
        "chi_dinh_ngoai_bao_hiem__out_of_insurance_orders": numerator_rows,
        "chi_dinh_chua_ro_trang_thai_bao_hiem__unknown_coverage_orders": int((denominator_df["covered_status"] == "unknown").sum()) if not denominator_df.empty and "covered_status" in denominator_df.columns else 0,
        "ngoai_bao_hiem_tren_benh_nhan_co_bao_hiem__out_of_insurance_per_insured_patient": round(safe_rate(numerator_rows, denominator_patient_count), 3) if denominator_patient_count else 0,
        "ty_le_ngoai_bao_hiem__out_of_insurance_rate": format_pct(numerator_rate),
        "tong_chi_phi_cua_benh_nhan_co_bao_hiem__total_amount_for_insured_patients_vnd": denominator_amount_vnd,
        "chi_phi_ngoai_bao_hiem_cua_benh_nhan_co_bao_hiem__out_of_insurance_amount_vnd": numerator_amount_vnd,
        "scope_preset_name": scope.preset_name,
        "denominator_rows": denominator_rows,
        "numerator_rows": numerator_rows,
        "numerator_rate": numerator_rate,
        "numerator_amount_vnd": numerator_amount_vnd,
        "patient_scope": scope.patient_scope,
        "coverage_scope": scope.coverage_scope,
        "top_risk_doctor": top_risk_doctor,
        "top_risk_department": top_risk_department,
        "top_risk_procedure": top_risk_procedure,
    }

    overview_table = pd.DataFrame(
        [
            {"Chi so / Metric": "Total patients in file", "Gia tri / Value": total_patients_in_file},
            {"Chi so / Metric": "Current preset", "Gia tri / Value": scope.preset_name},
            {"Chi so / Metric": "Patient scope", "Gia tri / Value": scope.patient_scope},
            {"Chi so / Metric": "Coverage scope", "Gia tri / Value": scope.coverage_scope},
            {"Chi so / Metric": "Baseline rows", "Gia tri / Value": denominator_rows},
            {"Chi so / Metric": "Signal rows", "Gia tri / Value": numerator_rows},
            {"Chi so / Metric": "Signal rate", "Gia tri / Value": format_pct(numerator_rate)},
            {"Chi so / Metric": "Denominator patients", "Gia tri / Value": denominator_patient_count},
            {"Chi so / Metric": "Numerator patients", "Gia tri / Value": numerator_patient_count},
            {"Chi so / Metric": "Denominator amount", "Gia tri / Value": denominator_amount_vnd},
            {"Chi so / Metric": "Numerator amount", "Gia tri / Value": numerator_amount_vnd},
        ]
    )

    executive_summary_table = pd.DataFrame(
        [
            {"Metric": "Total rows", "Value": total_patients_in_file if raw_df.empty else int(len(raw_df))},
            {"Metric": "Denominator rows", "Value": denominator_rows},
            {"Metric": "Numerator rows", "Value": numerator_rows},
            {"Metric": "Numerator rate", "Value": format_pct(numerator_rate)},
            {"Metric": "Numerator amount", "Value": numerator_amount_vnd},
            {"Metric": "Top doctor by numerator amount", "Value": top_risk_doctor},
            {"Metric": "Top department by numerator amount", "Value": top_risk_department},
            {"Metric": "Top procedure by numerator amount", "Value": top_risk_procedure},
            {"Metric": "Current preset", "Value": scope.preset_name},
        ]
    )

    result_tables = {
        "overview": overview_table,
        "by_doctor": by_doctor,
        "by_department": by_department,
        "executive_summary_table": executive_summary_table,
        "coverage_status_table": coverage_status_table,
        "chart_coverage_pie": coverage_status_table.copy(),
    }

    return {
        "tool_name": "01 - Analysis overview",
        "status": "completed",
        "summary": summary,
        "tables": result_tables,
        "notes": [
            f"Scope preset: {scope.preset_name}. Denominator rows: {denominator_rows}. Numerator rows: {numerator_rows}.",
            "This result is only a review aid for the selected cohort, not a finding of wrongdoing.",
        ],
    }
