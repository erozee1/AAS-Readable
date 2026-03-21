from __future__ import annotations

import json


def stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, dict):
        return json.dumps(value, indent=2, sort_keys=True, default=str)
    if isinstance(value, (list, tuple, set, frozenset)):
        # Flat scalar lists are much easier to diff and read inline than JSON arrays.
        if all(isinstance(item, (str, int, float, bool)) for item in value):
            return ", ".join(str(item) for item in value)
        return json.dumps([str(item) for item in value], indent=2)
    return str(value)
