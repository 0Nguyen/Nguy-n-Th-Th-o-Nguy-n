from __future__ import annotations

import pandas as pd

from scripts.summary_builder import build_human_summary


def compose_report(tool_results):
    final_report = {"overview": {}, "tables": {}, "tool_results": tool_results, "notes": []}

    for result in tool_results:
        final_report["notes"].extend(result.get("notes", []))
        tables = result.get("tables", {}) or {}

        for key, table in tables.items():
            if table is None:
                continue
            if key in {"overview", "by_doctor", "by_department"}:
                if key not in final_report["tables"] or _is_empty_table(final_report["tables"].get(key)):
                    final_report["tables"][key] = table
                continue
            if key == "case_evidence_table" and key in final_report["tables"]:
                existing = final_report["tables"].get(key)
                if _is_empty_table(existing):
                    final_report["tables"][key] = table
                elif not _is_empty_table(table):
                    try:
                        final_report["tables"][key] = pd.concat([existing, table], ignore_index=True, sort=False).drop_duplicates()
                    except Exception:
                        final_report["tables"][key] = existing
                continue
            if key not in final_report["tables"]:
                final_report["tables"][key] = table
            else:
                if _is_empty_table(final_report["tables"].get(key)) and not _is_empty_table(table):
                    final_report["tables"][key] = table

        summary = result.get("summary") or {}
        if summary and not final_report["overview"]:
            final_report["overview"] = summary

    human_summary = build_human_summary(final_report)
    final_report["human_summary"] = human_summary
    committee_table = human_summary.get("review_committee_summary_table")
    if committee_table is not None and hasattr(committee_table, "to_excel"):
        final_report["tables"]["review_committee_summary_table"] = committee_table

    try:
        from scripts.judge_summary_builder import attach_judge_summary

        final_report = attach_judge_summary(final_report)
    except Exception as exc:
        final_report.setdefault("notes", []).append(
            f"Judge summary could not be built: {exc}"
        )

    return final_report


def _is_empty_table(table) -> bool:
    if table is None:
        return True
    try:
        return len(table) == 0
    except Exception:
        return False
