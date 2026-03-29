"""YAML helpers for deterministic AAS document views."""

from __future__ import annotations

from typing import Any

import yaml


def dump_yaml(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(
        payload,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
