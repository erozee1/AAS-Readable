"""Deterministic view builders for lossless, agent, brief, and review outputs."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable

from .document import AssetShellIR, DocumentIR, ElementIR, QualifierIR, ReferenceIR, SubmodelIR
from .util import stringify

PayloadHook = Callable[[str, dict[str, Any], DocumentIR], dict[str, Any] | None]

_IDENTIFIER_FIELDS = {
    "appname": "app_name",
    "appid": "app_id",
}
_LIST_CATEGORY_FIELDS = {
    "capabilities": "capabilities",
    "supportedprocesses": "capabilities",
    "functions": "capabilities",
    "appcapabilities": "capabilities",
    "supportedmaterials": "materials",
    "supportedrobots": "robots",
    "supportedsensors": "sensors",
    "supportedendeffectors": "end_effectors",
}
_RANGE_KEYS = frozenset({"min", "minimum", "max", "maximum", "nominal", "value"})


def build_index_payload(
    document: DocumentIR,
    submodels: list[SubmodelIR],
    markdown_files: list[str],
    yaml_files: list[str],
    json_files: list[str],
    view: str = "review",
    hooks: list[PayloadHook] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": document.source.schema_version,
        "view": view,
        "source": {
            "file": document.source.file,
            "input_kind": document.source.input_kind,
            "wrapper_kind": document.source.wrapper_kind,
            "asset_shell_count": len(document.asset_shells),
            "exported_submodel_count": len(submodels),
        },
        "document_artifacts": _artifact_names(
            "document",
            markdown_files=["document.md"] if markdown_files else [],
            yaml_files=["document.yaml"] if yaml_files else [],
            json_files=["document.json"] if json_files else [],
        ),
        "submodels": [],
    }
    if markdown_files:
        payload["document_markdown_file"] = "document.md"
    if yaml_files:
        payload["document_yaml_file"] = "document.yaml"
    if json_files:
        payload["document_json_file"] = "document.json"

    for index, submodel in enumerate(submodels):
        entry = {
            "id": submodel.id,
            "id_short": submodel.id_short,
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
        payload["submodels"].append(entry)
    return _apply_hooks("index", payload, document, hooks)


def build_document_payload(
    document: DocumentIR,
    submodels: list[SubmodelIR],
    view: str = "agent",
    hooks: list[PayloadHook] | None = None,
) -> dict[str, Any]:
    validation = build_validation_payload(document, submodels)
    base: dict[str, Any] = {
        "schema_version": document.source.schema_version,
        "view": view,
        "source": {
            "file": document.source.file,
            "input_kind": document.source.input_kind,
            "wrapper_kind": document.source.wrapper_kind,
        },
    }
    if document.optional_external_narrative:
        base["optional_external_narrative"] = document.optional_external_narrative.strip()

    if view == "lossless":
        payload = {
            **base,
            "asset_shells": [_asset_shell_lossless(asset_shell) for asset_shell in document.asset_shells],
            "submodels": [_submodel_lossless(submodel) for submodel in submodels],
            "element_index": {
                path: _element_lossless(element)
                for path, element in sorted(document.element_index.items())
            },
        }
    elif view == "agent":
        payload = {
            **base,
            "document": build_agent_document(document, submodels, validation, include_trace=False),
            "validation": validation,
        }
    elif view == "brief":
        agent_document = build_agent_document(document, submodels, validation, include_trace=False)
        payload = {
            **base,
            "brief_text": build_brief_text(agent_document, validation, document.optional_external_narrative),
            "document": agent_document,
            "validation": validation,
        }
    elif view == "review":
        payload = {
            **base,
            "document": build_agent_document(document, submodels, validation, include_trace=True),
            "validation": validation,
        }
    else:
        raise ValueError(f"Unsupported view: {view}")
    return _apply_hooks("document", payload, document, hooks)


def build_submodel_payload(submodel: SubmodelIR, view: str = "review") -> dict[str, Any]:
    if view == "lossless":
        return _submodel_lossless(submodel)
    sections = _submodel_agent_sections(submodel)
    payload = {
        "id": submodel.id,
        "id_short": submodel.id_short,
        "kind": submodel.kind,
        "semantic_refs": list(submodel.semantic_refs),
        "asset_shell_ids": list(submodel.asset_shell_ids),
        "description": submodel.description,
        "sections": sections,
    }
    if view == "review":
        payload["source_pointer"] = _source_pointer_payload(submodel.source_pointer)
        payload["elements"] = [_element_review(child) for child in submodel.elements]
    return _strip_empty(payload)


def build_validation_payload(document: DocumentIR, submodels: list[SubmodelIR]) -> dict[str, Any]:
    flat_elements = [element for submodel in submodels for element in iter_elements(submodel.elements)]
    missing_submodel_semantic_refs = [submodel.id_short for submodel in submodels if not submodel.semantic_refs]
    missing_element_semantic_refs = [element.path for element in flat_elements if not element.semantic_refs]
    empty_values = [
        element.path
        for element in flat_elements
        if not element.children and element.display_value == "" and element.typed_value in (None, "", [], {}, ())
    ]
    numeric_without_unit = [
        element.path for element in flat_elements if _element_has_numeric_fact(element) and not element.normalized_unit
    ]

    units_by_field: dict[str, set[str]] = defaultdict(set)
    for element in flat_elements:
        if element.normalized_unit:
            units_by_field[_normalize_name(element.id_short)].add(element.normalized_unit)
    unit_inconsistencies = [
        {"field": field, "units": sorted(units)}
        for field, units in sorted(units_by_field.items())
        if len(units) > 1
    ]

    known_submodels = {submodel.id for submodel in submodels if submodel.id}
    known_ids = {
        asset_shell.id for asset_shell in document.asset_shells if asset_shell.id
    } | {
        asset_shell.global_asset_id for asset_shell in document.asset_shells if asset_shell.global_asset_id
    } | known_submodels | {
        element.stable_key for element in flat_elements if element.stable_key
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
    if missing_submodel_semantic_refs:
        known_gaps.append(f"{len(missing_submodel_semantic_refs)} submodel(s) are missing semantic references.")
    if missing_element_semantic_refs:
        known_gaps.append(f"{len(missing_element_semantic_refs)} element(s) are missing semantic references.")
    if unit_inconsistencies:
        known_gaps.append(f"{len(unit_inconsistencies)} field group(s) use inconsistent units.")
    if missing_submodel_references or unresolved_references:
        known_gaps.append("Some references could not be resolved within the document.")

    return {
        "optional_external_narrative_present": bool(document.optional_external_narrative.strip()),
        "missing_semantic_refs": {
            "submodels": missing_submodel_semantic_refs,
            "elements": missing_element_semantic_refs[:25],
            "submodel_count": len(missing_submodel_semantic_refs),
            "element_count": len(missing_element_semantic_refs),
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


def build_agent_document(
    document: DocumentIR,
    submodels: list[SubmodelIR],
    validation: dict[str, Any],
    include_trace: bool,
) -> dict[str, Any]:
    element_entries = [(submodel, element) for submodel in submodels for element in iter_elements(submodel.elements)]
    identifiers: dict[str, Any] = {
        "assets": [_asset_shell_agent(asset_shell) for asset_shell in document.asset_shells],
        "fields": {},
    }
    compatibility: dict[str, list[dict[str, Any]]] = {
        "capabilities": [],
        "materials": [],
        "robots": [],
        "sensors": [],
        "end_effectors": [],
    }
    numeric_facts: list[dict[str, Any]] = []
    operations: list[dict[str, Any]] = []
    generic_facts: list[dict[str, Any]] = []

    for submodel, element in element_entries:
        normalized = _normalize_name(element.id_short)
        if normalized in _IDENTIFIER_FIELDS and element.display_value:
            identifiers["fields"].setdefault(
                _IDENTIFIER_FIELDS[normalized],
                _fact_entry(submodel, element, include_trace),
            )
            continue
        if normalized in _LIST_CATEGORY_FIELDS:
            compatibility[_LIST_CATEGORY_FIELDS[normalized]].extend(
                _fact_entries_from_element(submodel, element, include_trace)
            )
            continue
        if _element_has_numeric_fact(element):
            numeric_facts.append(_numeric_fact_entry(submodel, element, include_trace))
            continue
        if element.model_type == "Operation":
            operations.append(_fact_entry(submodel, element, include_trace))
            continue
        if element.display_value:
            generic_facts.append(_fact_entry(submodel, element, include_trace))

    for key, items in compatibility.items():
        compatibility[key] = _dedupe_fact_entries(items)
    numeric_facts = _dedupe_numeric_facts(numeric_facts)
    generic_facts = _dedupe_fact_entries(generic_facts)

    payload = {
        "identifiers": identifiers,
        "compatibility": compatibility,
        "numeric_facts": numeric_facts,
        "operations": operations,
        "generic_facts": generic_facts,
        "submodels": [_submodel_agent_summary(submodel, include_trace) for submodel in submodels],
        "gaps": validation.get("known_gaps", []),
    }
    if include_trace:
        payload["trace"] = {
            "element_count": len(document.element_index),
            "element_paths": sorted(document.element_index.keys()),
        }
    return _strip_empty(payload)


def build_brief_text(agent_document: dict[str, Any], validation: dict[str, Any], optional_external_narrative: str) -> str:
    lines: list[str] = []
    if optional_external_narrative:
        lines.append(optional_external_narrative.strip())
        lines.append("")

    fields = agent_document.get("identifiers", {}).get("fields", {})
    assets = agent_document.get("identifiers", {}).get("assets", [])
    if fields or assets:
        lines.append("Identifiers:")
        if "app_name" in fields:
            lines.append(f"- AppName: {fields['app_name']['value']}")
        if "app_id" in fields:
            lines.append(f"- AppID: {fields['app_id']['value']}")
        for asset in assets:
            if asset.get("id_short"):
                lines.append(f"- AssetShell: {asset['id_short']}")
            if asset.get("global_asset_id"):
                lines.append(f"- GlobalAssetId: {asset['global_asset_id']}")
        lines.append("")

    compatibility = agent_document.get("compatibility", {})
    label_map = {
        "capabilities": "Capabilities",
        "materials": "Materials",
        "robots": "Robots",
        "sensors": "Sensors",
        "end_effectors": "EndEffectors",
    }
    for key in ("capabilities", "materials", "robots", "sensors", "end_effectors"):
        items = compatibility.get(key, [])
        if not items:
            continue
        lines.append(f"{label_map[key]}:")
        for item in items:
            lines.append(f"- {item['value']}")
        lines.append("")

    numeric_facts = agent_document.get("numeric_facts", [])
    if numeric_facts:
        lines.append("NumericFacts:")
        for fact in numeric_facts:
            if fact.get("min_value") is not None and fact.get("max_value") is not None and fact["min_value"] != fact["max_value"]:
                value = f"{fact['min_value']} to {fact['max_value']}"
            else:
                value = stringify(fact.get("nominal_value"))
            unit = f" {fact['unit']}" if fact.get("unit") else ""
            lines.append(f"- {fact['label']}: {value}{unit}".rstrip())
        lines.append("")

    if validation.get("known_gaps"):
        lines.append("KnownGaps:")
        for gap in validation["known_gaps"]:
            lines.append(f"- {gap}")

    return "\n".join(lines).strip()


def iter_elements(elements: Iterable[ElementIR]) -> Iterable[ElementIR]:
    for element in elements:
        yield element
        yield from iter_elements(element.children)


def _asset_shell_lossless(asset_shell: AssetShellIR) -> dict[str, Any]:
    return _strip_empty(
        {
            "id": asset_shell.id,
            "id_short": asset_shell.id_short,
            "description": asset_shell.description,
            "asset_kind": asset_shell.asset_kind,
            "asset_type": asset_shell.asset_type,
            "global_asset_id": asset_shell.global_asset_id,
            "submodel_ids": list(asset_shell.submodel_ids),
        }
    )


def _asset_shell_agent(asset_shell: AssetShellIR) -> dict[str, Any]:
    return _strip_empty(
        {
            "id": asset_shell.id,
            "id_short": asset_shell.id_short,
            "global_asset_id": asset_shell.global_asset_id,
            "submodel_ids": list(asset_shell.submodel_ids),
        }
    )


def _submodel_lossless(submodel: SubmodelIR) -> dict[str, Any]:
    return _strip_empty(
        {
            "id": submodel.id,
            "id_short": submodel.id_short,
            "kind": submodel.kind,
            "semantic_refs": list(submodel.semantic_refs),
            "description": submodel.description,
            "asset_shell_ids": list(submodel.asset_shell_ids),
            "source_pointer": _source_pointer_payload(submodel.source_pointer),
            "elements": [_element_lossless(element) for element in submodel.elements],
        }
    )


def _submodel_agent_summary(submodel: SubmodelIR, include_trace: bool) -> dict[str, Any]:
    payload = {
        "id": submodel.id,
        "id_short": submodel.id_short,
        "description": submodel.description,
        "asset_shell_ids": list(submodel.asset_shell_ids),
        "sections": _submodel_agent_sections(submodel),
    }
    if include_trace:
        payload["source_pointer"] = _source_pointer_payload(submodel.source_pointer)
        payload["semantic_refs"] = list(submodel.semantic_refs)
    return _strip_empty(payload)


def _submodel_agent_sections(submodel: SubmodelIR) -> dict[str, Any]:
    sections: dict[str, list[dict[str, Any]]] = {
        "capabilities": [],
        "materials": [],
        "robots": [],
        "sensors": [],
        "end_effectors": [],
        "numeric_facts": [],
        "generic_facts": [],
    }
    for element in iter_elements(submodel.elements):
        normalized = _normalize_name(element.id_short)
        if normalized in _LIST_CATEGORY_FIELDS:
            category = _LIST_CATEGORY_FIELDS[normalized]
            sections[category].extend(_fact_entries_from_element(submodel, element, include_trace=False))
        elif _element_has_numeric_fact(element):
            sections["numeric_facts"].append(_numeric_fact_entry(submodel, element, include_trace=False))
        elif element.display_value:
            sections["generic_facts"].append(_fact_entry(submodel, element, include_trace=False))
    return {key: _dedupe_fact_entries(value) if key != "numeric_facts" else _dedupe_numeric_facts(value) for key, value in sections.items() if value}


def _element_lossless(element: ElementIR) -> dict[str, Any]:
    return _strip_empty(
        {
            "path": element.path,
            "stable_key": element.stable_key,
            "id_short": element.id_short,
            "display_label": element.display_label,
            "model_type": element.model_type,
            "value_kind": element.value_kind,
            "raw_value": element.raw_value,
            "display_value": element.display_value,
            "typed_value": element.typed_value,
            "value_type": element.value_type,
            "unit": element.unit,
            "normalized_unit": element.normalized_unit,
            "nominal_value": element.nominal_value,
            "min_value": element.min_value,
            "max_value": element.max_value,
            "semantic_refs": list(element.semantic_refs),
            "qualifiers": [_qualifier_payload(item) for item in element.qualifiers],
            "references": [_reference_payload(item) for item in element.references],
            "description": element.description,
            "category": element.category,
            "source_pointer": _source_pointer_payload(element.source_pointer),
            "children": [_element_lossless(child) for child in element.children],
        }
    )


def _element_review(element: ElementIR) -> dict[str, Any]:
    return _strip_empty(
        {
            "path": element.path,
            "id_short": element.id_short,
            "display_label": element.display_label,
            "model_type": element.model_type,
            "value_kind": element.value_kind,
            "display_value": element.display_value,
            "typed_value": element.typed_value,
            "unit": element.unit,
            "semantic_refs": list(element.semantic_refs),
            "references": [_reference_payload(item) for item in element.references],
            "source_pointer": _source_pointer_payload(element.source_pointer),
            "children": [_element_review(child) for child in element.children],
        }
    )


def _fact_entries_from_element(submodel: SubmodelIR, element: ElementIR, include_trace: bool) -> list[dict[str, Any]]:
    if isinstance(element.typed_value, list) and not element.children:
        values = [str(item) for item in element.typed_value if str(item)]
    elif element.display_value:
        values = _split_scalar_list(element.display_value)
    else:
        values = []
    return [_fact_entry(submodel, element, include_trace, forced_value=value) for value in values]


def _fact_entry(
    submodel: SubmodelIR,
    element: ElementIR,
    include_trace: bool,
    forced_value: str | None = None,
) -> dict[str, Any]:
    payload = {
        "label": element.display_label,
        "value": forced_value if forced_value is not None else element.display_value,
        "submodel": submodel.id_short,
    }
    if include_trace:
        payload["path"] = element.path
        payload["source_pointer"] = _source_pointer_payload(element.source_pointer)
    return _strip_empty(payload)


def _numeric_fact_entry(submodel: SubmodelIR, element: ElementIR, include_trace: bool) -> dict[str, Any]:
    payload = {
        "label": element.display_label,
        "submodel": submodel.id_short,
        "nominal_value": element.nominal_value,
        "min_value": element.min_value,
        "max_value": element.max_value,
        "unit": element.unit or element.normalized_unit,
    }
    if include_trace:
        payload["path"] = element.path
        payload["source_pointer"] = _source_pointer_payload(element.source_pointer)
    return _strip_empty(payload)


def _reference_payload(reference: ReferenceIR) -> dict[str, Any]:
    return {"type": reference.type, "value": reference.value}


def _qualifier_payload(qualifier: QualifierIR) -> dict[str, Any]:
    return {"type": qualifier.type, "value": qualifier.value}


def _source_pointer_payload(pointer: Any) -> dict[str, Any]:
    if not pointer:
        return {}
    return _strip_empty(
        {
            "file": getattr(pointer, "file", ""),
            "input_kind": getattr(pointer, "input_kind", ""),
            "submodel_id": getattr(pointer, "submodel_id", ""),
            "submodel_id_short": getattr(pointer, "submodel_id_short", ""),
            "element_path": getattr(pointer, "element_path", ""),
        }
    )


def _element_has_numeric_fact(element: ElementIR) -> bool:
    return any(value is not None for value in (element.nominal_value, element.min_value, element.max_value))


def _split_scalar_list(value: str) -> list[str]:
    if not value:
        return []
    if ", " not in value and "\n" not in value and ";" not in value:
        return [value]
    items = []
    for part in value.replace("\n", ",").replace(";", ",").split(","):
        clean = part.strip()
        if clean:
            items.append(clean)
    return items


def _dedupe_fact_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    result = []
    for entry in entries:
        key = (str(entry.get("label")), str(entry.get("value")), str(entry.get("submodel")))
        if key in seen:
            continue
        seen.add(key)
        result.append(entry)
    return result


def _dedupe_numeric_facts(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, Any, Any, Any, str]] = set()
    result = []
    for entry in entries:
        key = (
            str(entry.get("label")),
            entry.get("nominal_value"),
            entry.get("min_value"),
            entry.get("max_value"),
            str(entry.get("unit")),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(entry)
    return result


def _artifact_names(
    slug: str,
    markdown_files: list[str],
    yaml_files: list[str],
    json_files: list[str],
) -> dict[str, list[str] | str]:
    payload: dict[str, list[str] | str] = {
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


def _slug_for_submodel(submodel: SubmodelIR) -> str:
    return _normalize_name(submodel.id_short or submodel.id) or "submodel"


def _apply_hooks(
    kind: str,
    payload: dict[str, Any],
    document: DocumentIR,
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
    return "".join(char for char in value.lower() if char.isalnum())


def _strip_empty(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_empty(item)
            for key, item in value.items()
            if item not in ("", None, (), [], {}) and _strip_empty(item) not in ("", None, (), [], {})
        }
    if isinstance(value, list):
        return [_strip_empty(item) for item in value if item not in ("", None, (), [], {})]
    return value
