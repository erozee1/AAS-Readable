"""YAML renderers for structured AAS export artifacts."""

from __future__ import annotations

from typing import Any

import yaml

from .document import ExportDocument, SubmodelDocument
from .payloads import build_index_payload, build_llm_context_payload, build_submodel_payload


def render_index_yaml(
    document: ExportDocument,
    submodels: list[SubmodelDocument],
    markdown_files: list[str],
    yaml_files: list[str],
    json_files: list[str] | None = None,
    profile: str = "agent-structured",
) -> str:
    payload = build_index_payload(
        document=document,
        submodels=submodels,
        markdown_files=markdown_files,
        yaml_files=yaml_files,
        json_files=json_files or [],
        profile=profile,
    )
    return _dump_yaml(payload)


def render_llm_context_yaml(
    document: ExportDocument,
    submodels: list[SubmodelDocument],
    profile: str = "agent-structured",
) -> str:
    return _dump_yaml(build_llm_context_payload(document=document, submodels=submodels, profile=profile))


def render_submodel_yaml(submodel: SubmodelDocument, profile: str = "agent-structured") -> str:
    return _dump_yaml(build_submodel_payload(submodel=submodel, profile=profile))


def _dump_yaml(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(
        payload,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
