from __future__ import annotations

from scripts.context import create_context
from scripts import tool_01_basic_stats
from scripts import tool_02_doctor_outlier
from scripts import tool_03_high_cost_procedure
from scripts import tool_04_required_icd_check
from scripts import tool_05_false_red_flag_resolver

TOOL_REGISTRY = {
    "tool_01_basic_stats": tool_01_basic_stats.run,
    "tool_02_doctor_outlier": tool_02_doctor_outlier.run,
    "tool_03_high_cost_procedure": tool_03_high_cost_procedure.run,
    "tool_04_required_icd_check": tool_04_required_icd_check.run,
    "tool_05_false_red_flag_resolver": tool_05_false_red_flag_resolver.run,
}

TOOL_ORDER = [
    "tool_01_basic_stats",
    "tool_02_doctor_outlier",
    "tool_03_high_cost_procedure",
    "tool_04_required_icd_check",
    "tool_05_false_red_flag_resolver",
]


def run_pipeline(df, selected_tools):
    selected = list(selected_tools or TOOL_ORDER)
    selected_set = set(selected)
    context = create_context(df=df, selected_tools=selected)
    results = []
    for tool_name in TOOL_ORDER:
        if tool_name not in selected_set:
            continue
        try:
            result = TOOL_REGISTRY[tool_name](df, context)
            results.append(result)
            context.tool_results = results
        except Exception as ex:
            results.append(
                {
                    "tool_name": tool_name,
                    "status": "error",
                    "summary": {},
                    "tables": {},
                    "notes": [f"Lỗi tool / Tool error: {ex}"],
                }
            )
            context.tool_results = results
    return results
