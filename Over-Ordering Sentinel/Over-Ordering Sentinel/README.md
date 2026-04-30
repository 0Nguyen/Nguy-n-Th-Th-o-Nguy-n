# Over-Ordering Sentinel

Over-Ordering Sentinel is a Streamlit app for reviewing hospital Excel data with a Review Measure Builder, evidence tables, and statistical review-support for selected cohorts.

## What the app does

- Detects data sheets, header rows, and columns with Smart Excel Mapper.
- Lets users build a review scope before analysis.
- Defaults to insured patients + out-of-insurance orders.
- Separates `HasInsurance` from `CoveredByInsurance`.
- Produces denominator/numerator evidence tables, benchmarks, and case-level audit support.
- Exports an Excel report for committee or reviewer follow-up.

## Default language

- The app opens in English by default.
- A language selector is still available in the sidebar.
- Both Vietnamese and English UI text are supported.

## Requirements

Before running the app, make sure this machine has:

- Python 3.10 or newer
- Internet access if you want temporary public sharing in online mode

## Install

1. Install Python 3.10+.
2. Make sure `python` is available in PATH.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Launchers

There are only two launchers for users.

### Offline local mode

Double-click:

```text
START_OFFLINE.bat
```

Use this when the app runs on one computer only and no public link is needed.

### Online admin mode

Double-click:

```text
START_ONLINE.bat
```

This opens a local admin console on `http://127.0.0.1:8502`.
From there, you can start the backend app on `http://127.0.0.1:8501` and create a temporary public share link to the backend only.

## Cloudflared

The online launcher uses Cloudflare Quick Tunnel through `cloudflared`.

- If `cloudflared.exe` already exists in `tools/`, the app uses it.
- If `cloudflared` is already in PATH, the app uses it.
- If neither is available, the app tries to install it automatically with `winget`.
- If `winget` is unavailable or fails, the app downloads the official Windows AMD64 release into `tools/cloudflared.exe`.

If the machine has no internet access, offline mode still works, but online sharing does not.

## Quick workflow

1. Open the app.
2. Upload an Excel file or use a sample file.
3. Let Smart Excel Mapper detect the data sheet, header row, and columns.
4. Keep auto mapping if it is correct. Switch to manual mapping only if needed.
5. Confirm the mapping.
6. The Tools panel appears after you confirm mapping and start analysis.
7. Review the report tables and export the Excel result.

## Prepare the Excel file

- Each row should ideally represent one order, service, medicine, or procedure.
- Keep one clear header row when possible.
- Avoid merged cells in the main data area if possible.
- If the workbook has multiple sheets, keep one clean data sheet for analysis and keep README or guide sheets separate.
- The app works best when insurance-related fields use consistent labels inside the same workbook.

## Smart Excel Mapper

The app supports Excel files that do not exactly match one template.

It can:

- detect the data sheet automatically
- detect the header row
- map columns automatically
- let you adjust columns manually
- normalize insurance-related values into app logic

### Minimum required columns

- `DoctorName`
- `PatientName`
- `HasInsurance`
- `CoveredByInsurance`

### Automatic normalization

Auto mapping is usually enough when the workbook is already fairly clean.

- The app guesses the best sheet and header row.
- The app tries to normalize equivalent values into the same meaning.
- If the normalized preview looks reasonable, keep the automatic mapping.
- If a status column becomes entirely `unknown`, review the mapping before running analysis.

### Manual mapping and manual normalization

Use manual mapping when:

- the wrong column was selected automatically
- a required column is missing
- the hospital uses unusual header names
- insurance status values are coded in a non-standard way

The two most important logic columns are:

- `HasInsurance`: whether the patient has insurance
- `CoveredByInsurance`: whether that specific order is covered by insurance

These are not interchangeable. An insured patient can still have out-of-insurance orders. If these two columns are mixed up, the whole analysis becomes misleading.

Manual Excel standardization note:

- update headers so the mapped columns match the real workbook meaning
- normalize coded values before analysis when the hospital uses local labels
- remove merged cells from the data region if possible
- check the `Normalized data preview` before running analysis

## How to read the report

### KPI cards and overview

- `Overview` and the KPI cards show the insured-data size, order count, out-of-insurance rate, and out-of-insurance amount.
- Read these first to understand the size and shape of the dataset before focusing on flagged doctors or cases.

### Main tables

- `By doctor`: compares doctors inside the same dataset
- `By department`: compares departments or specialties
- `Doctor Red Flag Ranking`: prioritization list for manual review
- `Suspicious High-Cost Procedure`: expensive items or services that deserve closer attention
- `Required ICD Flags`: items that may need diagnosis or ICD context
- `False Red Flag Context`: cases that may look suspicious statistically but can become explainable in context
- `Case evidence`: concrete example rows for deeper review

### Tool status

- `Tool status` shows which tools ran successfully.
- Notes there often explain whether a tool had too little data or found no review-worthy pattern.

## Business rules

- `HasInsurance` means whether the patient has insurance.
- `CoveredByInsurance` means whether a specific order or procedure is covered.
- A patient can have insurance while one specific order is still out of insurance.
- The app does not make final fraud or wrongdoing conclusions.
- The report uses review-oriented language and should be treated as review-support only.

## Sample data

- `sample-data/sample_input.xlsx`
- `sample-data/sample_input_multisheet.xlsx`

## Folder guide

- `app.py`: main Streamlit app
- `scripts/launcher_offline.py`: starts the local offline experience
- `scripts/launcher_online.py`: opens the local admin console
- `scripts/online_admin_app.py`: admin console for backend, password, and public sharing
- `scripts/share_tunnel.py`: cloudflared detection, install, download, and tunnel control
- `ui/layout.py`: page layout and sidebar tools
- `ui/upload_panel.py`: Excel upload area
- `ui/help_panel.py`: quick guide and user help panel
- `ui/report_view.py`: report display
- `scripts/dispatcher.py`: tool orchestration
- `scripts/report_composer.py`: report aggregation
- `scripts/excel_exporter.py`: Excel export

## Launch summary

1. `START_OFFLINE.bat`
   - local-only use
   - no admin
   - no public link
2. `START_ONLINE.bat`
   - local admin console on port 8502
   - backend app on port 8501
   - optional password
   - temporary Cloudflare public link to the backend app

## License

Over-Ordering Sentinel is released under the GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later).

This project is shared for everyone who wants to use data and public health knowledge to support fairer healthcare review, protect insured patients, and strengthen transparency in universal health coverage.
