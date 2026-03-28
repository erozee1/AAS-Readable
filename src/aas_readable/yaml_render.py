from __future__ import annotations

from typing import Any

import yaml

from .document import AssetShellDocument, ElementDocument, ExportDocument, SubmodelDocument
from .util import stringify


def render_index_yaml(
    document: ExportDocument,
    submodels: list[SubmodelDocument],
    markdown_files: list[str],
    yaml_files: list[str],
) -> str:
    submodel_entries = []
    for index, submodel in enumerate(submodels):
        entry = {
            "id": submodel.id,
            "id_short": submodel.id_short,
            "yaml_file": yaml_files[index],
        }
        if index < len(markdown_files):
            entry["markdown_file"] = markdown_files[index]
        submodel_entries.append(entry)

    payload = {
        "source": {
            "file": document.source_path.name,
            "format": document.source_kind,
            "asset_shell_count": len(document.asset_shells),
            "exported_submodel_count": len(submodels),
        },
        "assets": [_asset_shell_payload(asset_shell) for asset_shell in document.asset_shells],
        "submodels": submodel_entries,
        "llm_context_file": "llm-context.yaml",
    }
    return _dump_yaml(payload)


def render_llm_context_yaml(document: ExportDocument, submodels: list[SubmodelDocument]) -> str:
    payload: dict[str, Any] = {
        "source": {
            "file": document.source_path.name,
            "format": document.source_kind,
        },
        "asset_shells": [_asset_shell_payload(asset_shell) for asset_shell in document.asset_shells],
        "submodels": [_submodel_summary_payload(submodel) for submodel in submodels],
    }
    if document.canonical_text:
        payload["canonical_text"] = document.canonical_text.strip()
    return _dump_yaml(payload)


def render_submodel_yaml(submodel: SubmodelDocument) -> str:
    payload: dict[str, Any] = {
        "id": submodel.id,
        "id_short": submodel.id_short,
        "elements": [_element_payload(element) for element in submodel.elements],
    }
    _set_if_present(payload, "kind", submodel.kind)
    _set_if_present(payload, "semantic_id", submodel.semantic_id)
    _set_if_present(payload, "description", submodel.description)
    return _dump_yaml(payload)


def _asset_shell_payload(asset_shell: AssetShellDocument) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": asset_shell.id,
        "id_short": asset_shell.id_short,
    }
    _set_if_present(payload, "description", asset_shell.description)
    _set_if_present(payload, "asset_kind", asset_shell.asset_kind)
    _set_if_present(payload, "asset_type", asset_shell.asset_type)
    _set_if_present(payload, "global_asset_id", asset_shell.global_asset_id)
    if asset_shell.submodel_ids:
        payload["submodel_ids"] = list(asset_shell.submodel_ids)
    return payload


def _submodel_summary_payload(submodel: SubmodelDocument) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": submodel.id,
        "id_short": submodel.id_short,
        "key_elements": [_brief_element_payload(element) for element in submodel.elements],
    }
    _set_if_present(payload, "description", submodel.description)
    _set_if_present(payload, "semantic_id", submodel.semantic_id)
    return payload


def _element_payload(element: ElementDocument) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id_short": element.id_short,
        "model_type": element.model_type,
    }
    if element.children:
        payload["children"] = [_element_payload(child) for child in element.children]
    else:
        _set_if_present(payload, "value", stringify(element.value))
    _set_if_present(payload, "value_type", element.value_type)
    _set_if_present(payload, "semantic_id", element.semantic_id)
    _set_if_present(payload, "category", element.category)
    _set_if_present(payload, "description", element.description)
    _set_if_present(payload, "unit", element.unit)
    return payload


def _brief_element_payload(element: ElementDocument) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id_short": element.id_short,
        "model_type": element.model_type,
    }
    value = stringify(element.value).replace("\n", " ").strip()
    if value:
        payload["value"] = value
    _set_if_present(payload, "unit", element.unit)
    if element.children:
        payload["children"] = [_brief_element_payload(child) for child in element.children]
    return payload


def _set_if_present(payload: dict[str, Any], key: str, value: Any) -> None:
    if value in ("", None, (), [], {}):
        return
    payload[key] = value


def _dump_yaml(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(
        payload,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
