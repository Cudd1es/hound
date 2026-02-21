"""Suggestion generator for unmatched requirements."""

from typing import Any

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _priority_for_row(row: dict[str, Any]) -> str:
    verdict = row.get("verdict")
    category = row.get("category")

    if verdict == "not_met" and category == "must":
        return "high"
    if verdict == "not_met":
        return "medium"
    if verdict == "partial" and category == "must":
        return "medium"
    return "low"


def generate_suggestions(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    suggestions: list[dict[str, str]] = []

    for row in rows:
        if row.get("verdict") not in {"not_met", "partial"}:
            continue

        requirement_id = str(row.get("requirement_id", "unknown"))
        requirement_text = str(row.get("requirement_text", "this requirement"))
        priority = _priority_for_row(row)

        suggestions.append(
            {
                "priority": priority,
                "message": f"For {requirement_id}: add measurable evidence for '{requirement_text}' in resume bullets.",
            }
        )

    suggestions.sort(key=lambda item: _PRIORITY_ORDER[item["priority"]])
    return suggestions
