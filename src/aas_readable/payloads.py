"""Machine-facing payload builders used by JSON, YAML, and LLM-context renderers."""

from __future__ import annotations

from collections import defaultdict
import re
from typing import Any, Callable, Iterable

from .document import AssetShellDocument, ElementDocument, ExportDocument, ReferenceDocument, SubmodelDocument
from .util import stringify

PayloadHook = Callable[[str, dict[str, Any], ExportDocument], dict[str, Any] | None]

_EQUIPMENT_FIELDS = {"supportedrobots", "supportedendeffectors"}
_MATERIAL_FIELDS = {"supportedmaterials"}
_SENSOR_FIELDS = {"supportedsensors"}
_CAPABILITY_FIELDS = {"capabilities", "supportedprocesses", "functions", "appcapabilities"}
_LIFECYCLE_TERMS = ("lifecycle", "maintenance", "uptime", "service", "error", "health")
_KPI_TERMS = ("cycle", "cpu", "memory", "throughput", "availability", "oee", "scrap", "load", "latency")


def build_index_payload(
    document: ExportDocument,
    submodels: list[SubmodelDocument],
    markdown_files: list[str],
    yaml_files: list[str],
    json_files: list[str],
    profile: str = "agent-structured",
    hooks: list[PayloadHook] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": document.schema_version,
        "profile": profile,
        "source": {
            "file": document.source_path.name,
            "format": document.source_kind,
            "asset_shell_count": len(document.asset_shells),
            "exported_submodel_count": len(submodels),
        },
        "assets": [_asset_shell_payload(asset_shell, compact=True) for asset_shell in document.asset_shells],
        "submodels": [],
        "artifacts": {
            "llm_context": _artifact_names("llm-context", markdown_files=["llm-context.md"] if markdown_files else [], yaml_files=["llm-context.yaml"] if yaml_files else [], json_files=["llm-context.json"] if json_files else []),
        },
        "validation": build_validation_payload(document, submodels),
    }
    if yaml_files:
        payload["llm_context_file"] = "llm-context.yaml"
    if json_files:
        payload["llm_context_json_file"] = "llm-context.json"

    for index, submodel in enumerate(submodels):
        entry = {
            "id": submodel.id,
            "id_short": submodel.id_short,
            "synopsis": build_submodel_synopsis(submodel),
            "asset_shell_ids": list(submodel.asset_shell_ids),
            "artifacts": _artifact_names(
                _artifact_slug(
                    markdown_files[index:index + 1],
                    yaml_files[index:index + 1],
                    json_files[index:index + 1],
                    fallback=_slug_for_submodel(submodel),
                ),
                markdown_files=markdown_files[index:index + 1],
                yaml_files=yaml_files[index:index + 1],
                json_files=json_files[index:index + 1],
            ),
        }
        if index < len(markdown_files):
            entry["markdown_file"] = markdown_files[index]
        if index < len(yaml_files):
            entry["yaml_file"] = yaml_files[index]
        if index < len(json_files):
            entry["json_file"] = json_files[index]
        payload["submodels"].append(entry)
    return _apply_hooks("index", payload, document, hooks)


def build_llm_context_payload(
    document: ExportDocument,
    submodels: list[SubmodelDocument],
    profile: str = "agent-structured",
    hooks: list[PayloadHook] | None = None,
) -> dict[str, Any]:
    validation = build_validation_payload(document, submodels)
    engineering_views = build_engineering_views(submodels)
    prompt_text = build_prompt_text(document, submodels, validation, engineering_views)
    payload: dict[str, Any] = {
        "schema_version": document.schema_version,
        "profile": profile,
        "source": {
            "file": document.source_path.name,
            "format": document.source_kind,
        },
        "prompt_text": prompt_text,
        "asset_shells": [_asset_shell_payload(asset_shell, compact=profile == "prompt-compact") for asset_shell in document.asset_shells],
        "submodels": [_submodel_summary_payload(submodel, compact=profile == "prompt-compact") for submodel in submodels],
        "engineering_views": engineering_views,
        "validation": validation,
        "known_gaps": validation.get("known_gaps", []),
    }
    if document.canonical_text:
        payload["canonical_text"] = document.canonical_text.strip()
    return _apply_hooks("llm-context", payload, document, hooks)


def build_submodel_payload(
    submodel: SubmodelDocument,
    profile: str = "agent-structured",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": submodel.id,
        "id_short": submodel.id_short,
        "elements": [
            _brief_element_payload(element) if profile == "prompt-compact" else _element_payload(element)
            for element in submodel.elements
        ],
    }
    payload["synopsis"] = build_submodel_synopsis(submodel)
    payload["asset_shell_ids"] = list(submodel.asset_shell_ids)
    payload["source"] = {
        "file": submodel.source_file,
        "format": submodel.source_kind,
    }
    _set_if_present(payload, "kind", submodel.kind)
    _set_if_present(payload, "semantic_id", submodel.semantic_id)
    if submodel.semantic_ids:
        payload["semantic_ids"] = list(submodel.semantic_ids)
    _set_if_present(payload, "description", submodel.description)
    return payload


def build_validation_payload(document: ExportDocument, submodels: list[SubmodelDocument]) -> dict[str, Any]:
    flat_elements = [element for submodel in submodels for element in iter_elements(submodel.elements)]
    missing_submodel_semantic_ids = [submodel.id_short for submodel in submodels if not submodel.semantic_ids]
    missing_element_semantic_ids = [element.path for element in flat_elements if not element.semantic_ids]
    empty_values = [element.path for element in flat_elements if not element.children and not element.value_text]
    numeric_without_unit = [element.path for element in flat_elements if element.number_value is not None and not element.normalized_unit]

    units_by_field: dict[str, set[str]] = defaultdict(set)
    for element in flat_elements:
        if element.normalized_unit:
            units_by_field[_normalize_name(element.id_short)].add(element.normalized_unit)
    unit_inconsistencies = [
        {"field": field, "units": sorted(units)}
        for field, units in sorted(units_by_field.items())
        if len(units) > 1
    ]

    known_submodels = {submodel.id for submodel in submodels}
    known_ids = {
        asset_shell.id
        for asset_shell in document.asset_shells
        if asset_shell.id
    } | known_submodels | {
        asset_shell.global_asset_id
        for asset_shell in document.asset_shells
        if asset_shell.global_asset_id
    } | {
        element.stable_key
        for element in flat_elements
        if element.stable_key
    }

    missing_submodel_references = []
    for asset_shell in document.asset_shells:
        for submodel_id in asset_shell.submodel_ids:
            if submodel_id not in known_submodels:
                missing_submodel_references.append(
                    {
                        "asset_shell_id": asset_shell.id,
                        "missing_submodel_id": submodel_id,
                    }
                )

    unresolved_references = []
    for element in flat_elements:
        for reference in element.references:
            if reference.type not in {"Submodel", "AssetAdministrationShell", "Asset", "GlobalReference"}:
                continue
            if reference.value not in known_ids:
                unresolved_references.append(
                    {
                        "path": element.path,
                        "type": reference.type,
                        "value": reference.value,
                    }
                )

    known_gaps = []
    if not document.canonical_text:
        known_gaps.append("Canonical description is missing.")
    if missing_submodel_semantic_ids:
        known_gaps.append(f"{len(missing_submodel_semantic_ids)} submodel(s) are missing semantic IDs.")
    if missing_element_semantic_ids:
        known_gaps.append(f"{len(missing_element_semantic_ids)} element(s) are missing semantic IDs.")
    if unit_inconsistencies:
        known_gaps.append(f"{len(unit_inconsistencies)} field(s) use inconsistent units.")
    if missing_submodel_references or unresolved_references:
        known_gaps.append("Some references could not be resolved within the export.")

    return {
        "missing_canonical_text": not bool(document.canonical_text.strip()),
        "missing_semantic_ids": {
            "submodels": missing_submodel_semantic_ids,
            "elements": missing_element_semantic_ids[:25],
            "submodel_count": len(missing_submodel_semantic_ids),
            "element_count": len(missing_element_semantic_ids),
        },
        "unit_inconsistencies": unit_inconsistencies,
        "empty_values": empty_values[:25],
        "numeric_without_unit": numeric_without_unit[:25],
        "reference_integrity": {
            "missing_submodel_references": missing_submodel_references,
            "unresolved_references": unresolved_references[:25],
        },
        "known_gaps": known_gaps,
    }


def build_engineering_views(submodels: list[SubmodelDocument]) -> dict[str, Any]:
    flat_elements = [(submodel, element) for submodel in submodels for element in iter_elements(submodel.elements)]
    capability_sheet = _collect_token_sheet(flat_elements, _CAPABILITY_FIELDS)
    equipment_sheet = _collect_token_sheet(flat_elements, _EQUIPMENT_FIELDS)
    material_sheet = _collect_token_sheet(flat_elements, _MATERIAL_FIELDS)
    sensor_sheet = _collect_token_sheet(flat_elements, _SENSOR_FIELDS)
    lifecycle_digest = _collect_digest(flat_elements, _LIFECYCLE_TERMS, max_items=8)
    operational_kpis = _collect_digest(flat_elements, _KPI_TERMS, max_items=10)
    numeric_facts = _collect_numeric_facts(flat_elements)
    return {
        "capability_sheet": capability_sheet,
        "equipment_compatibility_sheet": equipment_sheet,
        "material_compatibility_sheet": material_sheet,
        "sensor_compatibility_sheet": sensor_sheet,
        "lifecycle_digest": lifecycle_digest,
        "operational_kpi_digest": operational_kpis,
        "numeric_facts": numeric_facts,
    }


def build_prompt_text(
    document: ExportDocument,
    submodels: list[SubmodelDocument],
    validation: dict[str, Any],
    engineering_views: dict[str, Any],
) -> str:
    segments: list[str] = []
    if document.canonical_text:
        segments.append(document.canonical_text.strip())
    else:
        names = ", ".join(submodel.id_short for submodel in submodels[:4] if submodel.id_short)
        if names:
            segments.append(f"AAS export covering submodels: {names}.")

    capability_items = engineering_views.get("capability_sheet", {}).get("items", [])
    equipment_items = engineering_views.get("equipment_compatibility_sheet", {}).get("items", [])
    material_items = engineering_views.get("material_compatibility_sheet", {}).get("items", [])
    numeric_facts = engineering_views.get("numeric_facts", [])

    if capability_items:
        segments.append("Capabilities: " + ", ".join(capability_items[:8]) + ".")
    if equipment_items:
        segments.append("Equipment compatibility: " + ", ".join(equipment_items[:8]) + ".")
    if material_items:
        segments.append("Material compatibility: " + ", ".join(material_items[:8]) + ".")
    if numeric_facts:
        rendered = []
        for fact in numeric_facts[:6]:
            tail = f" {fact['unit']}" if fact.get("unit") else ""
            if fact.get("min_value") is not None and fact.get("max_value") is not None and fact["min_value"] != fact["max_value"]:
                rendered.append(f"{fact['label']} {fact['min_value']}-{fact['max_value']}{tail}")
            elif fact.get("number_value") is not None:
                rendered.append(f"{fact['label']} {fact['number_value']}{tail}")
        if rendered:
            segments.append("Numeric facts: " + ", ".join(rendered) + ".")
    if validation.get("known_gaps"):
        segments.append("Known gaps: " + " ".join(validation["known_gaps"]))
    return " ".join(part for part in segments if part).strip()


def build_submodel_synopsis(submodel: SubmodelDocument, max_items: int = 4) -> str:
    items = []
    for element in iter_elements(submodel.elements):
        if element.children:
            continue
        if not element.value_text:
            continue
        items.append(f"{element.id_short}={element.value_text}")
        if len(items) >= max_items:
            break
    if not items:
        return submodel.description or submodel.id_short
    return "; ".join(items)


def iter_elements(elements: Iterable[ElementDocument]) -> Iterable[ElementDocument]:
    for element in elements:
        yield element
        yield from iter_elements(element.children)


def _asset_shell_payload(asset_shell: AssetShellDocument, compact: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": asset_shell.id,
        "id_short": asset_shell.id_short,
    }
    _set_if_present(payload, "asset_kind", asset_shell.asset_kind)
    _set_if_present(payload, "asset_type", asset_shell.asset_type)
    _set_if_present(payload, "global_asset_id", asset_shell.global_asset_id)
    if not compact:
        _set_if_present(payload, "description", asset_shell.description)
        if asset_shell.submodel_ids:
            payload["submodel_ids"] = list(asset_shell.submodel_ids)
    return payload


def _submodel_summary_payload(submodel: SubmodelDocument, compact: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": submodel.id,
        "id_short": submodel.id_short,
        "synopsis": build_submodel_synopsis(submodel),
        "asset_shell_ids": list(submodel.asset_shell_ids),
        "key_elements": [_brief_element_payload(element) for element in submodel.elements[:8]],
    }
    _set_if_present(payload, "description", submodel.description)
    _set_if_present(payload, "semantic_id", submodel.semantic_id)
    if submodel.semantic_ids:
        payload["semantic_ids"] = list(submodel.semantic_ids)
    if not compact:
        payload["source"] = {
            "file": submodel.source_file,
            "format": submodel.source_kind,
        }
    return payload


def _element_payload(element: ElementDocument) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id_short": element.id_short,
        "model_type": element.model_type,
        "path": element.path,
        "stable_key": element.stable_key,
    }
    if element.children:
        payload["children"] = [_element_payload(child) for child in element.children]
    else:
        _set_if_present(payload, "value", stringify(element.value))
    _set_if_present(payload, "value_text", element.value_text)
    _set_if_present(payload, "value_type", element.value_type)
    _set_if_present(payload, "semantic_id", element.semantic_id)
    if element.semantic_ids:
        payload["semantic_ids"] = list(element.semantic_ids)
    _set_if_present(payload, "category", element.category)
    _set_if_present(payload, "description", element.description)
    _set_if_present(payload, "unit", element.unit)
    _set_if_present(payload, "normalized_unit", element.normalized_unit)
    _set_if_present(payload, "number_value", element.number_value)
    _set_if_present(payload, "min_value", element.min_value)
    _set_if_present(payload, "max_value", element.max_value)
    if element.references:
        payload["references"] = [_reference_payload(reference) for reference in element.references]
    return payload


def _brief_element_payload(element: ElementDocument) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id_short": element.id_short,
        "model_type": element.model_type,
    }
    if element.value_text:
        payload["value"] = element.value_text
    _set_if_present(payload, "unit", element.unit)
    _set_if_present(payload, "path", element.path)
    if element.children:
        payload["children"] = [_brief_element_payload(child) for child in element.children]
    return payload


def _reference_payload(reference: ReferenceDocument) -> dict[str, Any]:
    return {
        "type": reference.type,
        "value": reference.value,
    }


def _collect_token_sheet(
    flat_elements: list[tuple[SubmodelDocument, ElementDocument]],
    normalized_fields: set[str],
) -> dict[str, Any]:
    items: list[str] = []
    evidence: list[dict[str, str]] = []
    for submodel, element in flat_elements:
        if _normalize_name(element.id_short) not in normalized_fields or not element.value_text:
            continue
        for token in _split_value_tokens(element.value_text):
            if token not in items:
                items.append(token)
                evidence.append({"submodel": submodel.id_short, "path": element.path, "value": token})
    return {"items": items, "evidence": evidence[:20]}


def _collect_digest(
    flat_elements: list[tuple[SubmodelDocument, ElementDocument]],
    terms: tuple[str, ...],
    max_items: int,
) -> list[dict[str, Any]]:
    items = []
    for submodel, element in flat_elements:
        haystack = f"{submodel.id_short} {element.id_short} {element.path}".lower()
        if not any(term in haystack for term in terms):
            continue
        if not element.value_text and not element.children:
            continue
        items.append(
            {
                "submodel": submodel.id_short,
                "path": element.path,
                "label": element.id_short,
                "value": element.value_text or build_submodel_synopsis(submodel, max_items=2),
            }
        )
        if len(items) >= max_items:
            break
    return items


def _collect_numeric_facts(flat_elements: list[tuple[SubmodelDocument, ElementDocument]]) -> list[dict[str, Any]]:
    facts = []
    for submodel, element in flat_elements:
        if element.number_value is None and element.min_value is None and element.max_value is None:
            continue
        facts.append(
            {
                "submodel": submodel.id_short,
                "path": element.path,
                "label": element.id_short,
                "number_value": element.number_value,
                "min_value": element.min_value,
                "max_value": element.max_value,
                "unit": element.normalized_unit or element.unit,
            }
        )
    return facts[:20]


def _split_value_tokens(value_text: str) -> list[str]:
    tokens = []
    for token in re.split(r"[,\n;|]+", value_text):
        clean = token.strip()
        if clean and clean not in tokens:
            tokens.append(clean)
    return tokens


def _artifact_names(
    slug: str,
    markdown_files: list[str],
    yaml_files: list[str],
    json_files: list[str],
) -> dict[str, list[str]]:
    payload = {
        "slug": slug,
        "markdown": markdown_files,
        "yaml": yaml_files,
        "json": json_files,
    }
    return {key: value for key, value in payload.items() if value not in ("", [], None)}


def _artifact_slug(
    markdown_files: list[str],
    yaml_files: list[str],
    json_files: list[str],
    fallback: str,
) -> str:
    for files in (markdown_files, yaml_files, json_files):
        if files:
            return str(files[0]).split(".", 1)[0]
    return fallback


def _slug_for_submodel(submodel: SubmodelDocument) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (submodel.id_short or submodel.id).lower()).strip("-")
    return slug or "submodel"


def _apply_hooks(
    kind: str,
    payload: dict[str, Any],
    document: ExportDocument,
    hooks: list[PayloadHook] | None,
) -> dict[str, Any]:
    if not hooks:
        return payload
    current = payload
    for hook in hooks:
        updated = hook(kind, current, document)
        if updated is not None:
            current = updated
    return current


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _set_if_present(payload: dict[str, Any], key: str, value: Any) -> None:
    if value in ("", None, (), [], {}):
        return
    payload[key] = value
