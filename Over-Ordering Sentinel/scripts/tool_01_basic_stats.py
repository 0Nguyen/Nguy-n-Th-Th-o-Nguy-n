from __future__ import annotations

import pandas as pd

from scripts.text_utils import format_pct, format_vnd, safe_rate


def _coverage_counts(frame: pd.DataFrame):
    covered_orders = int((frame["covered_status"] == "covered").sum())
    out_orders = int((frame["covered_status"] == "out_of_insurance").sum())
    unknown_orders = int((frame["covered_status"] == "unknown").sum())
    return covered_orders, out_orders, unknown_orders


def _group_amount(frame: pd.DataFrame, group_cols):
    return (
        frame.loc[frame["covered_status"] == "out_of_insurance"]
        .groupby(group_cols, dropna=False)["amount"]
        .sum()
        .reset_index(name="chi_phi_ngoai_bao_hiem__out_of_insurance_amount_vnd")
    )


def run(df, context):
    total_patients_in_file = int(df["patient"].nunique())
    insured_df = df[df["has_insurance_status"] == "yes"].copy()

    if insured_df.empty:
        summary = {
            "tong_benh_nhan_trong_file__total_patients_in_file": total_patients_in_file,
            "so_benh_nhan_co_bao_hiem__insured_patient_count": 0,
            "so_bac_si_co_chi_dinh_cho_benh_nhan_co_bao_hiem__doctor_count_for_insured_patients": 0,
            "tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients": 0,
            "chi_dinh_duoc_bao_hiem_chi_tra__covered_by_insurance_orders": 0,
            "chi_dinh_ngoai_bao_hiem__out_of_insurance_orders": 0,
            "chi_dinh_chua_ro_trang_thai_bao_hiem__unknown_coverage_orders": 0,
            "ngoai_bao_hiem_tren_benh_nhan_co_bao_hiem__out_of_insurance_per_insured_patient": 0,
            "ty_le_ngoai_bao_hiem__out_of_insurance_rate": "0.00%",
            "tong_chi_phi_cua_benh_nhan_co_bao_hiem__total_amount_for_insured_patients_vnd": 0,
            "chi_phi_ngoai_bao_hiem_cua_benh_nhan_co_bao_hiem__out_of_insurance_amount_vnd": 0,
        }
        overview_table = pd.DataFrame(
            [
                {"Chi so / Metric": "Tổng bệnh nhân trong file / Total patients in file", "Gia tri / Value": total_patients_in_file},
                {"Chi so / Metric": "Bệnh nhân có bảo hiểm / Insured patients", "Gia tri / Value": 0},
                {"Chi so / Metric": "Bác sĩ có chỉ định cho BN có BH / Doctors ordering for insured patients", "Gia tri / Value": 0},
                {"Chi so / Metric": "Tổng chỉ định của BN có BH / Total orders for insured patients", "Gia tri / Value": 0},
                {"Chi so / Metric": "Được bảo hiểm chi trả / Covered by insurance", "Gia tri / Value": 0},
                {"Chi so / Metric": "Ngoài bảo hiểm / Out of insurance", "Gia tri / Value": 0},
                {"Chi so / Metric": "Chưa rõ trạng thái BH / Unknown coverage", "Gia tri / Value": 0},
                {"Chi so / Metric": "Ngoài BH trên BN có BH / Out-of-insurance per insured patient", "Gia tri / Value": 0},
                {"Chi so / Metric": "Tỷ lệ ngoài BH / Out-of-insurance rate", "Gia tri / Value": "0.00%"},
                {"Chi so / Metric": "Tổng chi phí BN có BH / Total amount for insured patients", "Gia tri / Value": 0},
                {"Chi so / Metric": "Chi phí ngoài BH / Out-of-insurance amount", "Gia tri / Value": 0},
            ]
        )
        return {
            "tool_name": "01 - Thống kê bệnh nhân có bảo hiểm / Insured patient statistics",
            "status": "completed",
            "summary": summary,
            "tables": {"overview": overview_table, "by_doctor": pd.DataFrame(), "by_department": pd.DataFrame()},
            "notes": [
                "Tool 01 chỉ phân tích bệnh nhân có bảo hiểm / Tool 01 only analyzes insured patients.",
                "Chỉ định ngoài bảo hiểm là tín hiệu thống kê cần xem xét, không phải kết luận sai phạm / Out-of-insurance orders are statistical review signals, not wrongdoing conclusions.",
            ],
        }

    insured_patient_count = int(insured_df["patient"].nunique())
    doctor_count_for_insured = int(insured_df["doctor"].nunique())
    total_orders_for_insured = int(len(insured_df))
    covered_orders, out_orders, unknown_orders = _coverage_counts(insured_df)
    out_rate = safe_rate(out_orders, total_orders_for_insured)
    out_per_insured_patient = round(safe_rate(out_orders, insured_patient_count), 3)
    total_amount_for_insured = format_vnd(insured_df["amount"].sum())
    out_amount_for_insured = format_vnd(insured_df.loc[insured_df["covered_status"] == "out_of_insurance", "amount"].sum())

    summary = {
        "tong_benh_nhan_trong_file__total_patients_in_file": total_patients_in_file,
        "so_benh_nhan_co_bao_hiem__insured_patient_count": insured_patient_count,
        "so_bac_si_co_chi_dinh_cho_benh_nhan_co_bao_hiem__doctor_count_for_insured_patients": doctor_count_for_insured,
        "tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients": total_orders_for_insured,
        "chi_dinh_duoc_bao_hiem_chi_tra__covered_by_insurance_orders": covered_orders,
        "chi_dinh_ngoai_bao_hiem__out_of_insurance_orders": out_orders,
        "chi_dinh_chua_ro_trang_thai_bao_hiem__unknown_coverage_orders": unknown_orders,
        "ngoai_bao_hiem_tren_benh_nhan_co_bao_hiem__out_of_insurance_per_insured_patient": out_per_insured_patient,
        "ty_le_ngoai_bao_hiem__out_of_insurance_rate": format_pct(out_rate),
        "tong_chi_phi_cua_benh_nhan_co_bao_hiem__total_amount_for_insured_patients_vnd": total_amount_for_insured,
        "chi_phi_ngoai_bao_hiem_cua_benh_nhan_co_bao_hiem__out_of_insurance_amount_vnd": out_amount_for_insured,
    }

    by_doctor = (
        insured_df.groupby("doctor", dropna=False)
        .agg(
            so_benh_nhan_co_bao_hiem__insured_patient_count=("patient", "nunique"),
            tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients=("claim_id", "count"),
            chi_dinh_duoc_bao_hiem_chi_tra__covered_by_insurance_orders=("covered_status", lambda s: int((s == "covered").sum())),
            chi_dinh_ngoai_bao_hiem__out_of_insurance_orders=("covered_status", lambda s: int((s == "out_of_insurance").sum())),
            chi_dinh_chua_ro_trang_thai_bao_hiem__unknown_coverage_orders=("covered_status", lambda s: int((s == "unknown").sum())),
            tong_chi_phi__total_amount_vnd=("amount", "sum"),
        )
        .reset_index()
    )
    by_doctor = by_doctor.merge(_group_amount(insured_df, ["doctor"]), on="doctor", how="left")
    by_doctor["chi_phi_ngoai_bao_hiem__out_of_insurance_amount_vnd"] = by_doctor["chi_phi_ngoai_bao_hiem__out_of_insurance_amount_vnd"].fillna(0)
    by_doctor["ty_le_ngoai_bao_hiem__out_of_insurance_rate"] = by_doctor.apply(
        lambda row: format_pct(
            safe_rate(
                row["chi_dinh_ngoai_bao_hiem__out_of_insurance_orders"],
                row["tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients"],
            )
        ),
        axis=1,
    )
    by_doctor["ngoai_bao_hiem_tren_benh_nhan_co_bao_hiem__out_of_insurance_per_insured_patient"] = by_doctor.apply(
        lambda row: round(
            safe_rate(
                row["chi_dinh_ngoai_bao_hiem__out_of_insurance_orders"],
                row["so_benh_nhan_co_bao_hiem__insured_patient_count"],
            ),
            3,
        ),
        axis=1,
    )
    by_doctor = by_doctor.sort_values(
        [
            "chi_dinh_ngoai_bao_hiem__out_of_insurance_orders",
            "tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients",
        ],
        ascending=[False, False],
    )
    by_doctor = by_doctor.rename(columns={"doctor": "ten_bac_si__doctor"})

    by_department = (
        insured_df.groupby("department", dropna=False)
        .agg(
            so_bac_si__doctor_count=("doctor", "nunique"),
            so_benh_nhan_co_bao_hiem__insured_patient_count=("patient", "nunique"),
            tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients=("claim_id", "count"),
            chi_dinh_duoc_bao_hiem_chi_tra__covered_by_insurance_orders=("covered_status", lambda s: int((s == "covered").sum())),
            chi_dinh_ngoai_bao_hiem__out_of_insurance_orders=("covered_status", lambda s: int((s == "out_of_insurance").sum())),
            chi_dinh_chua_ro_trang_thai_bao_hiem__unknown_coverage_orders=("covered_status", lambda s: int((s == "unknown").sum())),
            tong_chi_phi__total_amount_vnd=("amount", "sum"),
        )
        .reset_index()
    )
    by_department = by_department.merge(_group_amount(insured_df, ["department"]), on="department", how="left")
    by_department["chi_phi_ngoai_bao_hiem__out_of_insurance_amount_vnd"] = by_department["chi_phi_ngoai_bao_hiem__out_of_insurance_amount_vnd"].fillna(0)
    by_department["ty_le_ngoai_bao_hiem__out_of_insurance_rate"] = by_department.apply(
        lambda row: format_pct(
            safe_rate(
                row["chi_dinh_ngoai_bao_hiem__out_of_insurance_orders"],
                row["tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients"],
            )
        ),
        axis=1,
    )
    by_department["ngoai_bao_hiem_tren_benh_nhan_co_bao_hiem__out_of_insurance_per_insured_patient"] = by_department.apply(
        lambda row: round(
            safe_rate(
                row["chi_dinh_ngoai_bao_hiem__out_of_insurance_orders"],
                row["so_benh_nhan_co_bao_hiem__insured_patient_count"],
            ),
            3,
        ),
        axis=1,
    )
    by_department = by_department.sort_values(
        [
            "chi_dinh_ngoai_bao_hiem__out_of_insurance_orders",
            "tong_chi_dinh_cua_benh_nhan_co_bao_hiem__total_orders_for_insured_patients",
        ],
        ascending=[False, False],
    )
    by_department = by_department.rename(columns={"department": "khoa__department"})

    overview_table = pd.DataFrame(
        [
            {"Chi so / Metric": "Tổng bệnh nhân trong file / Total patients in file", "Gia tri / Value": total_patients_in_file},
            {"Chi so / Metric": "Bệnh nhân có bảo hiểm / Insured patients", "Gia tri / Value": insured_patient_count},
            {"Chi so / Metric": "Bác sĩ có chỉ định cho BN có BH / Doctors ordering for insured patients", "Gia tri / Value": doctor_count_for_insured},
            {"Chi so / Metric": "Tổng chỉ định của BN có BH / Total orders for insured patients", "Gia tri / Value": total_orders_for_insured},
            {"Chi so / Metric": "Được bảo hiểm chi trả / Covered by insurance", "Gia tri / Value": covered_orders},
            {"Chi so / Metric": "Ngoài bảo hiểm / Out of insurance", "Gia tri / Value": out_orders},
            {"Chi so / Metric": "Chưa rõ trạng thái BH / Unknown coverage", "Gia tri / Value": unknown_orders},
            {"Chi so / Metric": "Ngoài BH trên BN có BH / Out-of-insurance per insured patient", "Gia tri / Value": out_per_insured_patient},
            {"Chi so / Metric": "Tỷ lệ ngoài BH / Out-of-insurance rate", "Gia tri / Value": format_pct(out_rate)},
            {"Chi so / Metric": "Tổng chi phí BN có BH / Total amount for insured patients", "Gia tri / Value": total_amount_for_insured},
            {"Chi so / Metric": "Chi phí ngoài BH / Out-of-insurance amount", "Gia tri / Value": out_amount_for_insured},
        ]
    )

    return {
        "tool_name": "01 - Thống kê bệnh nhân có bảo hiểm / Insured patient statistics",
        "status": "completed",
        "summary": summary,
        "tables": {"overview": overview_table, "by_doctor": by_doctor, "by_department": by_department},
        "notes": [
            "Tool 01 chỉ phân tích bệnh nhân có bảo hiểm / Tool 01 only analyzes insured patients.",
            "Chỉ định ngoài bảo hiểm là tín hiệu thống kê cần xem xét, không phải kết luận sai phạm / Out-of-insurance orders are statistical review signals, not wrongdoing conclusions.",
        ],
    }
