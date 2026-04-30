from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_sample_frame():
    rows = [
        ["CLM001", "Nguyen Van A", "Yes", "BS. Hoang", "Noi tong quat", "Yes", 350000, "Xet nghiem mau", "R73", "Duong huyet cao"],
        ["CLM001", "Nguyen Van A", "Yes", "BS. Hoang", "Noi tong quat", "No", 2800000, "MRI nao", "", "Dau dau"],
        ["CLM001", "Nguyen Van A", "Yes", "BS. Hoang", "Noi tong quat", "No", 3200000, "CT bung", "", "Dau bung"],
        ["CLM002", "Tran Thi B", "Yes", "BS. Linh", "Ngoai tong quat", "Yes", 450000, "Xet nghiem Glucose", "E11", "Tieu duong type 2"],
        ["CLM002", "Tran Thi B", "Yes", "BS. Linh", "Ngoai tong quat", "No", 1800000, "CT nguc", "R07", "Dau nguc"],
        ["CLM003", "Le Van C", "Yes", "BS. Minh", "Tim mach", "No", 2200000, "Troponin", "", "Kham suc khoe"],
        ["CLM003", "Le Van C", "Yes", "BS. Minh", "Tim mach", "Yes", 650000, "Dien tam do", "I20", "Dau that nguc"],
        ["CLM004", "Pham Thi D", "Yes", "BS. Hoang", "Noi tong quat", "No", 1500000, "MRI cot song", "M54", "Dau lung"],
        ["CLM004", "Pham Thi D", "Yes", "BS. Hoang", "Noi tong quat", "No", 1600000, "MRI cot song", "M54", "Dau lung"],
        ["CLM004", "Pham Thi D", "Yes", "BS. Hoang", "Noi tong quat", "No", 1700000, "MRI cot song", "M54", "Dau lung"],
        ["CLM004", "Pham Thi D", "Yes", "BS. Hoang", "Noi tong quat", "No", 1800000, "MRI cot song", "M54", "Dau lung"],
        ["CLM004", "Pham Thi D", "Yes", "BS. Hoang", "Noi tong quat", "No", 1900000, "MRI cot song", "M54", "Dau lung"],
        ["CLM005", "Ngo Van E", "Yes", "BS. Linh", "Ngoai tong quat", "Yes", 300000, "Sieu am bung", "K29", "Viem da day"],
        ["CLM005", "Ngo Van E", "Yes", "BS. Linh", "Ngoai tong quat", "No", 950000, "Xet nghiem HIV", "", "Tam soat HIV"],
        ["CLM006", "Vu Thi F", "Yes", "BS. Minh", "Tim mach", "No", 1200000, "Troponin", "R07", "Dau nguc cap cuu"],
        ["CLM006", "Vu Thi F", "Yes", "BS. Minh", "Tim mach", "Yes", 500000, "Dien tam do", "I21", "Nhoi mau co tim"],
        ["CLM007", "Dang Van G", "Yes", "BS. Hoang", "Noi tong quat", "No", 2400000, "CT bung", "", "Tien phau mo bung"],
        ["CLM008", "Bui Thi H", "No", "BS. Linh", "Ngoai tong quat", "No", 3000000, "MRI nao", "G44", "Kham suc khoe"],
        ["CLM009", "Hoang Van I", "No", "BS. Minh", "Tim mach", "Yes", 450000, "Glucose", "E10", "Tieu duong type 1"],
        ["CLM010", "Trinh Thi K", "Yes", "BS. Minh", "Tim mach", "Yes", 550000, "Dien tam do", "I21", "Nhoi mau co tim"],
        ["CLM011", "Ly Van M", "Yes", "BS. Hoang", "Noi tong quat", "Yes", 260000, "Xet nghiem mau", "R10", "Dau bung"],
        ["CLM011", "Ly Van M", "Yes", "BS. Hoang", "Noi tong quat", "No", 2900000, "PET-CT", "", "Ung thu"],
        ["CLM012", "Do Thi N", "Yes", "BS. Linh", "Ngoai tong quat", "Yes", 410000, "HbA1c", "E11", "Doi soat tieu duong"],
        ["CLM013", "Phan Van P", "Yes", "BS. Hoang", "Noi tong quat", "No", 2800000, "MRI cot song", "M54", "Noi tru dau lung"],
        ["CLM013", "Phan Van P", "Yes", "BS. Hoang", "Noi tong quat", "No", 1500000, "CT bung", "R10", "Phau thuat"],
        ["CLM014", "Vo Thi Q", "Yes", "BS. Minh", "Tim mach", "No", 3200000, "CT nguc", "", "Emergency chest pain"],
        ["CLM015", "Dinh Van R", "Yes", "BS. Hoang", "Noi tong quat", "Yes", 380000, "Noi soi dai trang", "K63", "Viem dai trang"],
        ["CLM016", "Nguyen Thi S", "Yes", "BS. Linh", "Ngoai tong quat", "Yes", 360000, "Xet nghiem Glucose", "R73", "Kiem tra suc khoe"],
        ["CLM017", "Tran Van T", "No", "BS. Hoang", "Noi tong quat", "No", 2200000, "CT nguc", "R07", "Dau nguc"],
        ["CLM018", "Le Thi U", "Yes", "BS. Minh", "Tim mach", "No", 1400000, "Troponin", "", "Tien phau mo tim"],
        ["CLM019", "Pham Van V", "Yes", "BS. Hoang", "Noi tong quat", "No", 2600000, "MRI nao", "", "Phau thuat nao"],
        ["CLM020", "Duong Thi W", "Yes", "BS. Linh", "Ngoai tong quat", "Yes", 210000, "Xet nghiem mau", "B20", "Tam soat HIV"],
        ["CLM021", "Nguyen Van X", "Yes", "BS. An", "Noi tong quat", "Yes", 280000, "Sieu am bung", "R10", "Kham dinh ky"],
        ["CLM021", "Nguyen Van X", "Yes", "BS. An", "Noi tong quat", "Yes", 260000, "Xet nghiem mau", "R10", "Kham dinh ky"],
        ["CLM021", "Nguyen Van X", "Yes", "BS. An", "Noi tong quat", "No", 420000, "Xet nghiem Glucose", "E11", "Tieu duong"],
        ["CLM022", "Tran Van Y", "Yes", "BS. Binh", "Noi tong quat", "Yes", 300000, "Xet nghiem mau", "R10", "Kham suc khoe"],
        ["CLM022", "Tran Van Y", "Yes", "BS. Binh", "Noi tong quat", "Yes", 320000, "Sieu am bung", "R10", "Kham suc khoe"],
        ["CLM025", "Dao Van AB", "Yes", "BS. Cuong", "Noi tong quat", "Yes", 240000, "Xet nghiem mau", "R10", "Kham dinh ky"],
        ["CLM025", "Dao Van AB", "Yes", "BS. Cuong", "Noi tong quat", "Yes", 220000, "Sieu am bung", "R10", "Kham dinh ky"],
        ["CLM023", "Le Thi Z", "Yes", "BS. Chau", "Tim mach", "Yes", 500000, "Dien tam do", "I20", "Dau nguc"],
        ["CLM023", "Le Thi Z", "Yes", "BS. Chau", "Tim mach", "Yes", 520000, "Xet nghiem mau", "I20", "Dau nguc"],
        ["CLM024", "Hoang Van AA", "Yes", "BS. Hang", "Ngoai tong quat", "Yes", 340000, "Xet nghiem mau", "K29", "Viem da day"],
        ["CLM024", "Hoang Van AA", "Yes", "BS. Hang", "Ngoai tong quat", "Yes", 360000, "Sieu am bung", "K29", "Viem da day"],
    ]
    columns = [
        "Mã hồ sơ / ClaimID",
        "Tên bệnh nhân / PatientName",
        "Có bảo hiểm / HasInsurance",
        "Tên bác sĩ / DoctorName",
        "Khoa / Department",
        "Trong bảo hiểm / CoveredByInsurance",
        "Số tiền yêu cầu thanh toán VND / ClaimAmountVND",
        "Tên dịch vụ / ProcedureName",
        "Mã ICD10 / DiagnosisCode",
        "Chẩn đoán / DiagnosisName",
    ]
    return pd.DataFrame(rows, columns=columns)


def build_multisheet_workbook(data_df: pd.DataFrame, output_path: Path) -> None:
    readme_sheet = pd.DataFrame(
        {
            "Note": [
                "README sheet only. Not for analysis.",
                "Use the DATA sheet for analysis.",
                "This workbook includes many extra columns to test robust mapping.",
            ]
        }
    )
    data_sheet = data_df.copy()
    for idx in range(1, 21):
        data_sheet[f"Random{idx}"] = [f"X{idx}_{row}" for row in range(len(data_sheet))]
    data_sheet["Note"] = "extra"
    data_sheet["Extra"] = "extra"
    data_sheet["Unnamed: 0"] = list(range(1, len(data_sheet) + 1))

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        readme_sheet.to_excel(writer, index=False, sheet_name="README")
        data_sheet.to_excel(writer, index=False, sheet_name="DATA")


def main():
    output_dir = Path("sample-data")
    output_dir.mkdir(parents=True, exist_ok=True)

    df = build_sample_frame()
    single_path = output_dir / "sample_input.xlsx"
    with pd.ExcelWriter(single_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="InputClaims")
    print(f"Created {single_path} with {len(df)} rows")

    multi_path = output_dir / "sample_input_multisheet.xlsx"
    build_multisheet_workbook(df, multi_path)
    print(f"Created {multi_path} with README and DATA sheets")


if __name__ == "__main__":
    main()
