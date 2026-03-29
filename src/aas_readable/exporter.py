"""Normalization and export pipeline for AAS, wrapped AAS JSON, and AASX inputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from .document import (
    AssetShellDocument,
    BatchExportSummary,
    ElementDocument,
    ExportDocument,
    ExportSummary,
    ReferenceDocument,
    SubmodelDocument,
)
from .markdown import render_index_markdown, render_llm_context_markdown, render_submodel_markdown
from .payloads import PayloadHook, build_index_payload, build_llm_context_payload, build_submodel_payload
from .yaml_render import render_index_yaml, render_llm_context_yaml, render_submodel_yaml

_SCHEMA_VERSION = "1.0.0"


def export_input_to_markdown(
    input_path: Path,
    output_dir: Path,
    include: list[str] | None = None,
    overwrite: bool = False,
    output_format: str = "markdown",
    profile: str = "agent-structured",
    hooks: list[PayloadHook] | None = None,
) -> ExportSummary:
    """Legacy-compatible single-input export entrypoint.

    The function name is kept for compatibility, but it now supports Markdown,
    YAML, JSON, and combined bundle outputs depending on ``output_format``.
    """

    input_path = input_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")
    if input_path.is_dir():
        raise ValueError("Use `export_path` for directory inputs.")
    if input_path.suffix.lower() not in {".aasx", ".json"}:
        raise ValueError(f"Expected an .aasx or .json file, got: {input_path.name}")
    if output_format not in {"markdown", "yaml", "json", "both", "all"}:
        raise ValueError(f"Unsupported output format: {output_format}")
    if profile not in {"prompt-compact", "agent-structured", "diff-ready"}:
        raise ValueError(f"Unsupported profile: {profile}")
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Output directory is not empty: {output_dir}. Use --overwrite to continue."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    document = load_export_document(input_path)
    bundle = render_submodel_bundle(
        document=document,
        include=include,
        format=output_format,
        profile=profile,
        hooks=hooks,
    )
    _write_bundle(output_dir=output_dir, bundle=bundle, output_format=output_format)

    submodels = bundle["submodels"]
    return ExportSummary(
        input_path=input_path,
        output_dir=output_dir,
        submodel_count=len(submodels),
        asset_shell_count=len(document.asset_shells),
        source_kind=document.source_kind,
    )


def export_path(
    input_path: Path,
    output_dir: Path,
    include: list[str] | None = None,
    overwrite: bool = False,
    output_format: str = "markdown",
    profile: str = "agent-structured",
    hooks: list[PayloadHook] | None = None,
) -> ExportSummary | BatchExportSummary:
    input_path = input_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()

    if input_path.is_file():
        return export_input_to_markdown(
            input_path=input_path,
            output_dir=output_dir,
            include=include,
            overwrite=overwrite,
            output_format=output_format,
            profile=profile,
            hooks=hooks,
        )
    if not input_path.is_dir():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Output directory is not empty: {output_dir}. Use --overwrite to continue."
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        path for path in input_path.iterdir() if path.is_file() and path.suffix.lower() in {".json", ".aasx"}
    )
    if not files:
        raise ValueError(f"No .json or .aasx files found in {input_path}")

    entries = []
    total_submodels = 0
    for file_path in files:
        target_dir = output_dir / _slugify(file_path.stem)
        summary = export_input_to_markdown(
            input_path=file_path,
            output_dir=target_dir,
            include=include,
            overwrite=overwrite,
            output_format=output_format,
            profile=profile,
            hooks=hooks,
        )
        total_submodels += summary.submodel_count
        entries.append(
            {
                "source_file": file_path.name,
                "source_kind": summary.source_kind,
                "output_dir": target_dir.name,
                "submodel_count": summary.submodel_count,
                "asset_shell_count": summary.asset_shell_count,
            }
        )

    manifest = {
        "schema_version": _SCHEMA_VERSION,
        "profile": profile,
        "source_directory": input_path.name,
        "file_count": len(entries),
        "entries": entries,
    }
    (output_dir / "manifest.json").write_text(_dump_json(manifest), encoding="utf-8")
    if output_format in {"yaml", "both", "all"}:
        (output_dir / "manifest.yaml").write_text(
            render_payload_yaml(manifest),
            encoding="utf-8",
        )

    return BatchExportSummary(
        input_path=input_path,
        output_dir=output_dir,
        file_count=len(entries),
        exported_submodel_count=total_submodels,
    )


def export_input(
    input_path: Path,
    output_dir: Path,
    include: list[str] | None = None,
    overwrite: bool = False,
    output_format: str = "markdown",
    profile: str = "agent-structured",
    hooks: list[PayloadHook] | None = None,
) -> ExportSummary:
    """Preferred name for exporting one AAS input path to disk."""

    return export_input_to_markdown(
        input_path=input_path,
        output_dir=output_dir,
        include=include,
        overwrite=overwrite,
        output_format=output_format,
        profile=profile,
        hooks=hooks,
    )


def load_export_document(input_path: Path) -> ExportDocument:
    """Load a single JSON or AASX input into the normalized export document."""

    input_path = input_path.expanduser().resolve()
    if input_path.suffix.lower() == ".aasx":
        return _load_aasx_document(input_path)
    if input_path.suffix.lower() == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        return load_export_document_from_payload(payload, source_name=input_path.name)
    raise ValueError(f"Expected an .aasx or .json file, got: {input_path.name}")


def load_export_document_from_payload(payload: Any, source_name: str = "memory.json") -> ExportDocument:
    """Build the normalized export document from an in-memory payload."""

    source_path = Path(source_name)
    if isinstance(payload, dict) and "aas" in payload:
        aas_env = payload.get("aas") or {}
        canonical_text = _string_value(payload.get("canonical_text"))
        source_kind = "json-wrapped"
    elif isinstance(payload, dict):
        aas_env = payload
        canonical_text = ""
        source_kind = "json"
    else:
        raise ValueError("JSON input must be an AAS environment object or wrapper with an `aas` field.")

    if not isinstance(aas_env, dict):
        raise ValueError("The `aas` field must contain an AAS environment object.")

    asset_shells = tuple(
        _asset_shell_from_json(aas) for aas in aas_env.get("assetAdministrationShells", []) if isinstance(aas, dict)
    )
    asset_shell_ids_by_submodel = _asset_shell_ids_by_submodel(asset_shells)
    submodels = tuple(
        _submodel_from_json(
            submodel,
            asset_shell_ids=asset_shell_ids_by_submodel.get(_string_value(submodel.get("id")), ()),
            source_file=source_path.name,
            source_kind=source_kind,
        )
        for submodel in aas_env.get("submodels", [])
        if isinstance(submodel, dict)
    )

    return ExportDocument(
        source_path=source_path,
        source_kind=source_kind,
        asset_shells=asset_shells,
        submodels=submodels,
        canonical_text=canonical_text,
        schema_version=_SCHEMA_VERSION,
    )


def render_llm_context(
    document: ExportDocument,
    format: str = "markdown",
    profile: str = "agent-structured",
    hooks: list[PayloadHook] | None = None,
) -> str | dict[str, Any]:
    """Render the top-level LLM or agent context in memory."""

    if format == "markdown":
        return render_llm_context_markdown(document=document, submodels=list(document.submodels), profile=profile)
    if format == "yaml":
        return render_llm_context_yaml(document=document, submodels=list(document.submodels), profile=profile)
    if format == "json":
        return build_llm_context_payload(document=document, submodels=list(document.submodels), profile=profile, hooks=hooks)
    raise ValueError(f"Unsupported format: {format}")


def render_submodel_bundle(
    document: ExportDocument,
    include: list[str] | None = None,
    format: str = "markdown",
    profile: str = "agent-structured",
    hooks: list[PayloadHook] | None = None,
) -> dict[str, Any]:
    """Render the full export bundle in memory without writing files."""

    if format not in {"markdown", "yaml", "json", "both", "all"}:
        raise ValueError(f"Unsupported format: {format}")
    if profile not in {"prompt-compact", "agent-structured", "diff-ready"}:
        raise ValueError(f"Unsupported profile: {profile}")

    include = include or []
    submodels = _filter_submodels(list(document.submodels), include)
    if not submodels:
        raise ValueError("No submodels matched the requested export.")

    formats = _expand_output_formats(format)
    used_names: set[str] = set()
    entries = []
    markdown_files: list[str] = []
    yaml_files: list[str] = []
    json_files: list[str] = []

    for submodel in submodels:
        slug = _unique_filename(_slugify(submodel.id_short or submodel.id), used_names)
        rendered: dict[str, Any] = {}
        if "markdown" in formats:
            rendered["markdown"] = render_submodel_markdown(submodel)
            markdown_files.append(f"{slug}.md")
        if "yaml" in formats:
            rendered["yaml"] = render_submodel_yaml(submodel, profile=profile)
            yaml_files.append(f"{slug}.yaml")
        if "json" in formats:
            rendered["json"] = build_submodel_payload(submodel=submodel, profile=profile)
            json_files.append(f"{slug}.json")
        entries.append(
            {
                "id": submodel.id,
                "id_short": submodel.id_short,
                "slug": slug,
                "content": rendered,
            }
        )

    index: dict[str, Any] = {}
    llm_context: dict[str, Any] = {}
    if "markdown" in formats:
        index["markdown"] = render_index_markdown(document=document, submodels=submodels, markdown_files=markdown_files)
        llm_context["markdown"] = render_llm_context_markdown(document=document, submodels=submodels, profile=profile)
    if "yaml" in formats:
        index["yaml"] = render_index_yaml(
            document=document,
            submodels=submodels,
            markdown_files=markdown_files,
            yaml_files=yaml_files,
            json_files=json_files,
            profile=profile,
        )
        llm_context["yaml"] = render_llm_context_yaml(document=document, submodels=submodels, profile=profile)
    if "json" in formats:
        index["json"] = build_index_payload(
            document=document,
            submodels=submodels,
            markdown_files=markdown_files,
            yaml_files=yaml_files,
            json_files=json_files,
            profile=profile,
            hooks=hooks,
        )
        llm_context["json"] = build_llm_context_payload(
            document=document,
            submodels=submodels,
            profile=profile,
            hooks=hooks,
        )

    return {
        "format": format,
        "profile": profile,
        "index": index,
        "llm_context": llm_context,
        "submodels": entries,
    }


def export_aasx_to_markdown(
    aasx_path: Path,
    output_dir: Path,
    include: list[str] | None = None,
    overwrite: bool = False,
    output_format: str = "markdown",
    profile: str = "agent-structured",
    hooks: list[PayloadHook] | None = None,
) -> ExportSummary:
    """Legacy helper retained for callers that export `.aasx` inputs directly."""

    return export_input_to_markdown(
        input_path=aasx_path,
        output_dir=output_dir,
        include=include,
        overwrite=overwrite,
        output_format=output_format,
        profile=profile,
        hooks=hooks,
    )


def render_payload_yaml(payload: dict[str, Any]) -> str:
    try:
        import yaml
    except ImportError as error:  # pragma: no cover - mirrors package dependency
        raise RuntimeError("PyYAML is required to render YAML output.") from error
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, default_flow_style=False)


def _write_bundle(output_dir: Path, bundle: dict[str, Any], output_format: str) -> None:
    formats = _expand_output_formats(output_format)

    for format_name in formats:
        suffix = {"markdown": ".md", "yaml": ".yaml", "json": ".json"}[format_name]
        index_content = bundle["index"][format_name]
        llm_content = bundle["llm_context"][format_name]
        (output_dir / f"index{suffix}").write_text(_serialize_output(index_content, format_name), encoding="utf-8")
        (output_dir / f"llm-context{suffix}").write_text(_serialize_output(llm_content, format_name), encoding="utf-8")
        for entry in bundle["submodels"]:
            content = entry["content"][format_name]
            (output_dir / f"{entry['slug']}{suffix}").write_text(_serialize_output(content, format_name), encoding="utf-8")


def _serialize_output(content: Any, format_name: str) -> str:
    if format_name == "json":
        return _dump_json(content)
    return str(content)


def _dump_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def _expand_output_formats(output_format: str) -> list[str]:
    mapping = {
        "markdown": ["markdown"],
        "yaml": ["yaml"],
        "json": ["json"],
        "both": ["markdown", "yaml"],
        "all": ["markdown", "yaml", "json"],
    }
    return mapping[output_format]


def _load_aasx_document(input_path: Path) -> ExportDocument:
    try:
        from basyx.aas import model
        from basyx.aas.adapter import aasx
    except ImportError as error:
        raise RuntimeError(
            "The Eclipse BaSyx Python SDK is required for .aasx input. Install it with `pip install -e '.[aasx]'`."
        ) from error

    object_store = model.DictObjectStore()
    file_store = aasx.DictSupplementaryFileContainer()

    with aasx.AASXReader(input_path) as reader:
        reader.read_into(object_store=object_store, file_store=file_store)

    asset_shells: list[AssetShellDocument] = []
    raw_submodels: list[object] = []

    for identifiable in object_store:
        class_name = identifiable.__class__.__name__
        if class_name == "AssetAdministrationShell":
            asset_shells.append(
                AssetShellDocument(
                    id=_string_value(getattr(identifiable, "id", None)),
                    id_short=_string_value(getattr(identifiable, "id_short", None)),
                    description=_string_value(getattr(identifiable, "description", None)),
                    asset_kind=_string_value(getattr(getattr(identifiable, "asset_information", None), "asset_kind", None)),
                    asset_type=_string_value(getattr(getattr(identifiable, "asset_information", None), "asset_type", None)),
                    global_asset_id=_string_value(
                        getattr(getattr(identifiable, "asset_information", None), "global_asset_id", None)
                    ),
                    submodel_ids=tuple(
                        _reference_value(ref) for ref in getattr(identifiable, "submodel", set()) if _reference_value(ref)
                    ),
                )
            )
        if class_name == "Submodel":
            raw_submodels.append(identifiable)

    asset_shell_ids_by_submodel = _asset_shell_ids_by_submodel(tuple(asset_shells))
    submodels = tuple(
        _submodel_from_basyx(
            submodel,
            asset_shell_ids=asset_shell_ids_by_submodel.get(_string_value(getattr(submodel, "id", None)), ()),
            source_file=input_path.name,
            source_kind="aasx",
        )
        for submodel in raw_submodels
    )

    return ExportDocument(
        source_path=input_path,
        source_kind="aasx",
        asset_shells=tuple(asset_shells),
        submodels=submodels,
        schema_version=_SCHEMA_VERSION,
    )


def _asset_shell_from_json(data: dict[str, Any]) -> AssetShellDocument:
    asset_information = data.get("assetInformation") or {}
    submodel_ids = tuple(
        ref_id
        for ref_id in (_extract_reference_id(ref) for ref in data.get("submodels", []))
        if ref_id
    )
    return AssetShellDocument(
        id=_string_value(data.get("id")),
        id_short=_string_value(data.get("idShort")),
        description=_normalize_lang_string(data.get("description")),
        asset_kind=_string_value(asset_information.get("assetKind")),
        asset_type=_string_value(asset_information.get("assetType")),
        global_asset_id=_string_value(asset_information.get("globalAssetId")),
        submodel_ids=submodel_ids,
    )


def _submodel_from_json(
    data: dict[str, Any],
    asset_shell_ids: tuple[str, ...],
    source_file: str,
    source_kind: str,
) -> SubmodelDocument:
    submodel_id = _string_value(data.get("id"))
    submodel_id_short = _string_value(data.get("idShort")) or submodel_id
    semantic_ids = tuple(_extract_semantic_ids(data.get("semanticId")))
    return SubmodelDocument(
        id=submodel_id,
        id_short=submodel_id_short,
        kind=_string_value(data.get("kind")),
        semantic_id=semantic_ids[0] if semantic_ids else "",
        semantic_ids=semantic_ids,
        description=_normalize_lang_string(data.get("description")),
        asset_shell_ids=asset_shell_ids,
        source_file=source_file,
        source_kind=source_kind,
        elements=tuple(
            _element_from_json(
                element,
                submodel_id=submodel_id,
                path_prefix=submodel_id_short or "submodel",
            )
            for element in data.get("submodelElements", [])
            if isinstance(element, dict)
        ),
    )


def _element_from_json(
    data: dict[str, Any],
    submodel_id: str,
    path_prefix: str,
) -> ElementDocument:
    id_short = _string_value(data.get("idShort")) or "element"
    path = f"{path_prefix}/{id_short}"
    stable_key = f"{submodel_id}/{path}"
    children: tuple[ElementDocument, ...] = ()
    raw_value = data.get("value")

    if _is_collection_like(data):
        child_items: list[dict[str, Any]] = []
        if isinstance(raw_value, list):
            child_items = [item for item in raw_value if isinstance(item, dict)]
        elif isinstance(raw_value, dict):
            child_items = [item for item in raw_value.values() if isinstance(item, dict)]
        children = tuple(
            _element_from_json(item, submodel_id=submodel_id, path_prefix=path)
            for item in child_items
        )
        if children:
            raw_value = None

    semantic_ids = tuple(_extract_semantic_ids(data.get("semanticId")))
    value_text = _value_to_text(raw_value)
    number_value, min_value, max_value = _extract_numeric(raw_value, value_text)
    unit = _string_value(data.get("unit"))
    normalized_unit = _normalize_unit(unit)
    references = tuple(_reference_documents_from_json(data))
    return ElementDocument(
        id_short=id_short,
        model_type=_extract_model_type(data.get("modelType")),
        value=raw_value,
        value_type=_string_value(data.get("valueType")),
        semantic_id=semantic_ids[0] if semantic_ids else "",
        semantic_ids=semantic_ids,
        category=_string_value(data.get("category")),
        description=_normalize_lang_string(data.get("description")),
        unit=unit,
        normalized_unit=normalized_unit,
        path=path,
        stable_key=stable_key,
        value_text=value_text,
        number_value=number_value,
        min_value=min_value,
        max_value=max_value,
        references=references,
        children=children,
    )


def _submodel_from_basyx(
    submodel: object,
    asset_shell_ids: tuple[str, ...],
    source_file: str,
    source_kind: str,
) -> SubmodelDocument:
    submodel_id = _string_value(getattr(submodel, "id", None))
    submodel_id_short = _string_value(getattr(submodel, "id_short", None)) or submodel_id
    semantic_ids = tuple(_extract_semantic_ids(getattr(submodel, "semantic_id", None)))
    elements = tuple(
        _element_from_basyx(
            element,
            submodel_id=submodel_id,
            path_prefix=submodel_id_short or "submodel",
        )
        for element in _iter_basyx_elements(getattr(submodel, "submodel_element", None))
    )
    return SubmodelDocument(
        id=submodel_id,
        id_short=submodel_id_short,
        kind=_string_value(getattr(submodel, "kind", None)),
        semantic_id=semantic_ids[0] if semantic_ids else "",
        semantic_ids=semantic_ids,
        description=_string_value(getattr(submodel, "description", None)),
        asset_shell_ids=asset_shell_ids,
        source_file=source_file,
        source_kind=source_kind,
        elements=elements,
    )


def _element_from_basyx(
    element: object,
    submodel_id: str,
    path_prefix: str,
) -> ElementDocument:
    id_short = _string_value(getattr(element, "id_short", None)) or element.__class__.__name__
    path = f"{path_prefix}/{id_short}"
    stable_key = f"{submodel_id}/{path}"
    child_candidates = [child for child in _iter_basyx_elements(getattr(element, "value", None)) if _looks_like_basyx_element(child)]
    children = tuple(
        _element_from_basyx(child, submodel_id=submodel_id, path_prefix=path)
        for child in child_candidates
    )
    raw_value = None if children else getattr(element, "value", None)
    semantic_ids = tuple(_extract_semantic_ids(getattr(element, "semantic_id", None)))
    unit = _string_value(getattr(element, "unit", None)) or _string_value(getattr(element, "unit_id", None))
    value_text = _value_to_text(raw_value)
    number_value, min_value, max_value = _extract_numeric(raw_value, value_text)
    return ElementDocument(
        id_short=id_short,
        model_type=element.__class__.__name__,
        value=raw_value,
        value_type=_string_value(getattr(element, "value_type", None)),
        semantic_id=semantic_ids[0] if semantic_ids else "",
        semantic_ids=semantic_ids,
        category=_string_value(getattr(element, "category", None)),
        description=_string_value(getattr(element, "description", None)),
        unit=unit,
        normalized_unit=_normalize_unit(unit),
        path=path,
        stable_key=stable_key,
        value_text=value_text,
        number_value=number_value,
        min_value=min_value,
        max_value=max_value,
        references=tuple(_reference_documents_from_basyx(element)),
        children=children,
    )


def _asset_shell_ids_by_submodel(asset_shells: tuple[AssetShellDocument, ...]) -> dict[str, tuple[str, ...]]:
    mapping: dict[str, list[str]] = {}
    for asset_shell in asset_shells:
        for submodel_id in asset_shell.submodel_ids:
            mapping.setdefault(submodel_id, [])
            if asset_shell.id and asset_shell.id not in mapping[submodel_id]:
                mapping[submodel_id].append(asset_shell.id)
    return {key: tuple(values) for key, values in mapping.items()}


def _filter_submodels(submodels: list[SubmodelDocument], include: list[str]) -> list[SubmodelDocument]:
    if not include:
        return submodels

    wanted = {_normalize_name(name) for name in include}
    return [
        submodel
        for submodel in submodels
        if _normalize_name(submodel.id_short or submodel.id) in wanted
    ]


def _reference_documents_from_json(data: dict[str, Any]) -> Iterable[ReferenceDocument]:
    for ref_type, ref_value in _collect_reference_pairs_from_json(data):
        yield ReferenceDocument(type=ref_type, value=ref_value)


def _reference_documents_from_basyx(element: object) -> Iterable[ReferenceDocument]:
    for ref_type, ref_value in _collect_reference_pairs_from_basyx(element):
        yield ReferenceDocument(type=ref_type, value=ref_value)


def _collect_reference_pairs_from_json(data: dict[str, Any]) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    model_type = _extract_model_type(data.get("modelType"))
    if model_type == "ReferenceElement":
        refs.extend(_extract_reference_pairs(data.get("value")))
    elif model_type == "RelationshipElement":
        refs.extend(_extract_reference_pairs(data.get("first")))
        refs.extend(_extract_reference_pairs(data.get("second")))
    else:
        refs.extend(_extract_reference_pairs(data.get("value")))
    return refs


def _collect_reference_pairs_from_basyx(element: object) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for attr_name in ("value", "first", "second"):
        refs.extend(_extract_reference_pairs(getattr(element, attr_name, None)))
    return refs


def _extract_reference_pairs(reference: Any) -> list[tuple[str, str]]:
    if reference is None:
        return []
    if isinstance(reference, dict):
        keys = reference.get("keys") or reference.get("key") or []
        values = []
        for key in keys:
            if not isinstance(key, dict):
                continue
            ref_type = _string_value(key.get("type")) or "Reference"
            ref_value = _string_value(key.get("value"))
            if ref_value:
                values.append((ref_type, ref_value))
        if values:
            return values
        nested = []
        for item in reference.values():
            nested.extend(_extract_reference_pairs(item))
        return nested
    if isinstance(reference, (list, tuple, set, frozenset)):
        values: list[tuple[str, str]] = []
        for item in reference:
            values.extend(_extract_reference_pairs(item))
        return values

    keys = getattr(reference, "key", None) or getattr(reference, "keys", None)
    if keys:
        values = []
        for key in keys:
            ref_type = _string_value(getattr(key, "type", None)) or "Reference"
            ref_value = _string_value(getattr(key, "value", None))
            if ref_value:
                values.append((ref_type, ref_value))
        return values
    return []


def _extract_reference_id(reference: Any) -> str:
    for _type, value in _extract_reference_pairs(reference):
        if value:
            return value
    return ""


def _extract_semantic_ids(semantic_id: Any) -> list[str]:
    values = []
    for _type, value in _extract_reference_pairs(semantic_id):
        if value and value not in values:
            values.append(value)
    if not values:
        single = _string_value(semantic_id)
        if single:
            values.append(single)
    return values


def _normalize_lang_string(value: Any) -> str:
    if isinstance(value, list):
        texts = [
            _string_value(item.get("text"))
            for item in value
            if isinstance(item, dict) and item.get("text")
        ]
        return " | ".join(texts)
    return _string_value(value)


def _extract_model_type(model_type: Any) -> str:
    if isinstance(model_type, dict):
        return _string_value(model_type.get("name") or model_type.get("modelType"))
    return _string_value(model_type)


def _is_collection_like(data: dict[str, Any]) -> bool:
    model_type = _extract_model_type(data.get("modelType"))
    if model_type in {"SubmodelElementCollection", "SubmodelElementList"}:
        return True
    value = data.get("value")
    if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
        return True
    if isinstance(value, dict) and value and all(isinstance(item, dict) for item in value.values()):
        return True
    return False


def _value_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, (list, tuple, set, frozenset)):
        return ", ".join(_string_value(item) for item in value if _string_value(item))
    return _string_value(value)


def _extract_numeric(raw_value: Any, value_text: str) -> tuple[float | None, float | None, float | None]:
    if isinstance(raw_value, bool):
        return None, None, None
    if isinstance(raw_value, (int, float)):
        numeric = float(raw_value)
        return numeric, numeric, numeric
    text = (value_text or "").strip()
    if not text:
        return None, None, None

    normalized = (
        text.replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
        .replace(",", "")
        .strip()
        .lower()
    )
    range_match = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:to|-)\s*(-?\d+(?:\.\d+)?)", normalized)
    if range_match:
        first = float(range_match.group(1))
        second = float(range_match.group(2))
        return max(first, second), min(first, second), max(first, second)

    single_match = re.search(r"(-?\d+(?:\.\d+)?)", normalized)
    if not single_match:
        return None, None, None
    numeric = float(single_match.group(1))
    return numeric, numeric, numeric


def _normalize_unit(unit: str) -> str:
    if not unit:
        return ""
    normalized = unit.lower()
    normalized = normalized.replace("µ", "u").replace("μ", "u")
    return normalized


def _iter_basyx_elements(value: Any) -> Iterable[Any]:
    if value is None:
        return []
    if isinstance(value, dict):
        return value.values()
    if isinstance(value, (list, tuple, set, frozenset)):
        return value
    return [value]


def _looks_like_basyx_element(value: Any) -> bool:
    return hasattr(value, "id_short") or hasattr(value, "semantic_id")


def _reference_value(reference: Any) -> str:
    for _type, value in _extract_reference_pairs(reference):
        if value:
            return value
    return ""


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _unique_filename(slug: str, used_names: set[str]) -> str:
    if slug not in used_names:
        used_names.add(slug)
        return slug

    suffix = 2
    while f"{slug}-{suffix}" in used_names:
        suffix += 1
    unique = f"{slug}-{suffix}"
    used_names.add(unique)
    return unique


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "submodel"


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)
