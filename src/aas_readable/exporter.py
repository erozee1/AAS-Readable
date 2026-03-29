"""Normalization and export pipeline for AAS, wrapped AAS JSON, and AASX inputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from .document import (
    AssetShellIR,
    BatchExportSummary,
    DocumentIR,
    ElementIR,
    ExportSummary,
    QualifierIR,
    ReferenceIR,
    SourceMetadata,
    SourcePointer,
    SubmodelIR,
)
from .markdown import render_document_markdown, render_index_markdown, render_submodel_markdown
from .payloads import PayloadHook, build_document_payload, build_index_payload, build_submodel_payload

_SCHEMA_VERSION = "2.0.0"


def export_input(
    input_path: Path,
    output_dir: Path,
    include: list[str] | None = None,
    overwrite: bool = False,
    output_format: str = "markdown",
    view: str = "review",
    hooks: list[PayloadHook] | None = None,
) -> ExportSummary:
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
    _validate_view(view=view, output_format=output_format)
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Output directory is not empty: {output_dir}. Use --overwrite to continue."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    document = load_document(input_path)
    bundle = render_submodels(document=document, include=include, format=output_format, view=view, hooks=hooks)
    _write_bundle(output_dir=output_dir, bundle=bundle, output_format=output_format)
    return ExportSummary(
        input_path=input_path,
        output_dir=output_dir,
        submodel_count=len(bundle["submodels"]),
        asset_shell_count=len(document.asset_shells),
        source_kind=document.source.input_kind,
    )


def export_input_to_markdown(
    input_path: Path,
    output_dir: Path,
    include: list[str] | None = None,
    overwrite: bool = False,
    output_format: str = "markdown",
    profile: str = "review",
    hooks: list[PayloadHook] | None = None,
) -> ExportSummary:
    """Legacy shim for callers still using the old export function name."""

    return export_input(
        input_path=input_path,
        output_dir=output_dir,
        include=include,
        overwrite=overwrite,
        output_format=output_format,
        view=_legacy_profile_to_view(profile),
        hooks=hooks,
    )


def export_path(
    input_path: Path,
    output_dir: Path,
    include: list[str] | None = None,
    overwrite: bool = False,
    output_format: str = "markdown",
    view: str = "review",
    hooks: list[PayloadHook] | None = None,
) -> ExportSummary | BatchExportSummary:
    input_path = input_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()

    if input_path.is_file():
        return export_input(
            input_path=input_path,
            output_dir=output_dir,
            include=include,
            overwrite=overwrite,
            output_format=output_format,
            view=view,
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
        summary = export_input(
            input_path=file_path,
            output_dir=target_dir,
            include=include,
            overwrite=overwrite,
            output_format=output_format,
            view=view,
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
        "view": view,
        "source_directory": input_path.name,
        "file_count": len(entries),
        "entries": entries,
    }
    (output_dir / "manifest.json").write_text(_dump_json(manifest), encoding="utf-8")
    if output_format in {"yaml", "both", "all"}:
        (output_dir / "manifest.yaml").write_text(render_payload_yaml(manifest), encoding="utf-8")
    return BatchExportSummary(
        input_path=input_path,
        output_dir=output_dir,
        file_count=len(entries),
        exported_submodel_count=total_submodels,
    )


def load_document(input_path: Path) -> DocumentIR:
    input_path = input_path.expanduser().resolve()
    if input_path.suffix.lower() == ".aasx":
        return _load_aasx_document(input_path)
    if input_path.suffix.lower() == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        return load_document_from_payload(payload, source_name=input_path.name)
    raise ValueError(f"Expected an .aasx or .json file, got: {input_path.name}")


def load_export_document(input_path: Path) -> DocumentIR:
    return load_document(input_path)


def load_document_from_payload(payload: Any, source_name: str = "memory.json") -> DocumentIR:
    source_path = Path(source_name)
    if isinstance(payload, dict) and "aas" in payload:
        aas_env = payload.get("aas") or {}
        legacy_canonical_text = _string_value(payload.get("canonical_text"))
        optional_external_narrative = _string_value(payload.get("narrative_summary")) or legacy_canonical_text
        wrapper_kind = "wrapped"
        input_kind = "json-wrapped"
    elif isinstance(payload, dict):
        aas_env = payload
        legacy_canonical_text = ""
        optional_external_narrative = _string_value(payload.get("narrative_summary"))
        wrapper_kind = "bare"
        input_kind = "json"
    else:
        raise ValueError("JSON input must be an AAS environment object or wrapper with an `aas` field.")

    if not isinstance(aas_env, dict):
        raise ValueError("The `aas` field must contain an AAS environment object.")

    source = SourceMetadata(
        file=source_path.name,
        input_kind=input_kind,
        wrapper_kind=wrapper_kind,
        schema_version=_SCHEMA_VERSION,
    )
    asset_shells = tuple(
        _asset_shell_from_json(aas) for aas in aas_env.get("assetAdministrationShells", []) if isinstance(aas, dict)
    )
    asset_shell_ids_by_submodel = _asset_shell_ids_by_submodel(asset_shells)
    submodels = tuple(
        _submodel_from_json(
            submodel,
            asset_shell_ids=asset_shell_ids_by_submodel.get(_string_value(submodel.get("id")), ()),
            source=source,
        )
        for submodel in aas_env.get("submodels", [])
        if isinstance(submodel, dict)
    )

    return DocumentIR(
        source_path=source_path,
        source=source,
        asset_shells=asset_shells,
        submodels=submodels,
        element_index=_build_element_index(submodels),
        optional_external_narrative=optional_external_narrative,
        legacy_canonical_text=legacy_canonical_text,
    )


def load_export_document_from_payload(payload: Any, source_name: str = "memory.json") -> DocumentIR:
    return load_document_from_payload(payload, source_name=source_name)


def render_document(
    document: DocumentIR,
    format: str = "markdown",
    view: str = "agent",
    hooks: list[PayloadHook] | None = None,
) -> str | dict[str, Any]:
    _validate_view(view=view, output_format=format if format in {"markdown", "yaml", "json"} else "json")
    if format == "markdown":
        return render_document_markdown(document=document, submodels=list(document.submodels), view=view)
    if format == "yaml":
        return render_payload_yaml(build_document_payload(document=document, submodels=list(document.submodels), view=view, hooks=hooks))
    if format == "json":
        return build_document_payload(document=document, submodels=list(document.submodels), view=view, hooks=hooks)
    raise ValueError(f"Unsupported format: {format}")


def render_llm_context(
    document: DocumentIR,
    format: str = "markdown",
    profile: str = "prompt-compact",
    hooks: list[PayloadHook] | None = None,
) -> str | dict[str, Any]:
    """Legacy shim kept for downstream compatibility."""

    view = _legacy_profile_to_view(profile)
    rendered = render_document(document=document, format=format, view=view, hooks=hooks)
    if format != "json" or not isinstance(rendered, dict):
        return rendered
    if view == "brief":
        return {
            **rendered,
            "prompt_text": rendered.get("brief_text", ""),
            "known_gaps": (rendered.get("validation") or {}).get("known_gaps", []),
        }
    return rendered


def render_submodels(
    document: DocumentIR,
    include: list[str] | None = None,
    format: str = "markdown",
    view: str = "review",
    hooks: list[PayloadHook] | None = None,
) -> dict[str, Any]:
    if format not in {"markdown", "yaml", "json", "both", "all"}:
        raise ValueError(f"Unsupported format: {format}")
    _validate_view(view=view, output_format=format)

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
            rendered["markdown"] = render_submodel_markdown(submodel=submodel, view=view)
            markdown_files.append(f"{slug}.md")
        if "yaml" in formats:
            rendered["yaml"] = render_payload_yaml(build_submodel_payload(submodel=submodel, view=view))
            yaml_files.append(f"{slug}.yaml")
        if "json" in formats:
            rendered["json"] = build_submodel_payload(submodel=submodel, view=view)
            json_files.append(f"{slug}.json")
        entries.append({"id": submodel.id, "id_short": submodel.id_short, "slug": slug, "content": rendered})

    index: dict[str, Any] = {}
    document_views: dict[str, Any] = {}
    if "markdown" in formats:
        index["markdown"] = render_index_markdown(document=document, submodels=submodels, markdown_files=markdown_files, view=view)
        document_views["markdown"] = render_document_markdown(document=document, submodels=submodels, view=view)
    if "yaml" in formats:
        index["yaml"] = render_payload_yaml(
            build_index_payload(
                document=document,
                submodels=submodels,
                markdown_files=markdown_files,
                yaml_files=yaml_files,
                json_files=json_files,
                view=view,
                hooks=hooks,
            )
        )
        document_views["yaml"] = render_payload_yaml(
            build_document_payload(document=document, submodels=submodels, view=view, hooks=hooks)
        )
    if "json" in formats:
        index["json"] = build_index_payload(
            document=document,
            submodels=submodels,
            markdown_files=markdown_files,
            yaml_files=yaml_files,
            json_files=json_files,
            view=view,
            hooks=hooks,
        )
        document_views["json"] = build_document_payload(document=document, submodels=submodels, view=view, hooks=hooks)

    return {"format": format, "view": view, "index": index, "document": document_views, "submodels": entries}


def render_submodel_bundle(
    document: DocumentIR,
    include: list[str] | None = None,
    format: str = "markdown",
    profile: str = "review",
    hooks: list[PayloadHook] | None = None,
) -> dict[str, Any]:
    return render_submodels(
        document=document,
        include=include,
        format=format,
        view=_legacy_profile_to_view(profile),
        hooks=hooks,
    )


def export_aasx_to_markdown(
    aasx_path: Path,
    output_dir: Path,
    include: list[str] | None = None,
    overwrite: bool = False,
    output_format: str = "markdown",
    profile: str = "review",
    hooks: list[PayloadHook] | None = None,
) -> ExportSummary:
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
    except ImportError as error:
        raise RuntimeError("PyYAML is required to render YAML output.") from error
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, default_flow_style=False)


def _write_bundle(output_dir: Path, bundle: dict[str, Any], output_format: str) -> None:
    formats = _expand_output_formats(output_format)
    for format_name in formats:
        suffix = {"markdown": ".md", "yaml": ".yaml", "json": ".json"}[format_name]
        (output_dir / f"index{suffix}").write_text(_serialize_output(bundle["index"][format_name], format_name), encoding="utf-8")
        (output_dir / f"document{suffix}").write_text(_serialize_output(bundle["document"][format_name], format_name), encoding="utf-8")
        for entry in bundle["submodels"]:
            (output_dir / f"{entry['slug']}{suffix}").write_text(
                _serialize_output(entry["content"][format_name], format_name),
                encoding="utf-8",
            )


def _serialize_output(content: Any, format_name: str) -> str:
    if format_name == "json":
        return _dump_json(content)
    return str(content)


def _dump_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def _expand_output_formats(output_format: str) -> list[str]:
    return {
        "markdown": ["markdown"],
        "yaml": ["yaml"],
        "json": ["json"],
        "both": ["markdown", "yaml"],
        "all": ["markdown", "yaml", "json"],
    }[output_format]


def _validate_view(view: str, output_format: str) -> None:
    if view not in {"lossless", "agent", "brief", "review"}:
        raise ValueError(f"Unsupported view: {view}")
    if output_format == "markdown" and view == "lossless":
        raise ValueError("The lossless view only supports JSON or YAML output.")


def _legacy_profile_to_view(profile: str) -> str:
    mapping = {
        "prompt-compact": "brief",
        "agent-structured": "agent",
        "diff-ready": "review",
        "review": "review",
    }
    if profile not in mapping:
        raise ValueError(f"Unsupported legacy profile: {profile}")
    return mapping[profile]


def _load_aasx_document(input_path: Path) -> DocumentIR:
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

    source = SourceMetadata(
        file=input_path.name,
        input_kind="aasx",
        wrapper_kind="aasx",
        schema_version=_SCHEMA_VERSION,
    )
    asset_shells: list[AssetShellIR] = []
    raw_submodels: list[object] = []
    for identifiable in object_store:
        class_name = identifiable.__class__.__name__
        if class_name == "AssetAdministrationShell":
            asset_shells.append(
                AssetShellIR(
                    id=_string_value(getattr(identifiable, "id", None)),
                    id_short=_string_value(getattr(identifiable, "id_short", None)),
                    description=_string_value(getattr(identifiable, "description", None)),
                    asset_kind=_string_value(getattr(getattr(identifiable, "asset_information", None), "asset_kind", None)),
                    asset_type=_string_value(getattr(getattr(identifiable, "asset_information", None), "asset_type", None)),
                    global_asset_id=_string_value(getattr(getattr(identifiable, "asset_information", None), "global_asset_id", None)),
                    submodel_ids=tuple(_reference_value(ref) for ref in getattr(identifiable, "submodel", set()) if _reference_value(ref)),
                )
            )
        elif class_name == "Submodel":
            raw_submodels.append(identifiable)

    asset_shell_ids_by_submodel = _asset_shell_ids_by_submodel(tuple(asset_shells))
    submodels = tuple(
        _submodel_from_basyx(
            submodel,
            asset_shell_ids=asset_shell_ids_by_submodel.get(_string_value(getattr(submodel, "id", None)), ()),
            source=source,
        )
        for submodel in raw_submodels
    )
    return DocumentIR(
        source_path=input_path,
        source=source,
        asset_shells=tuple(asset_shells),
        submodels=submodels,
        element_index=_build_element_index(submodels),
        optional_external_narrative="",
        legacy_canonical_text="",
    )


def _asset_shell_from_json(data: dict[str, Any]) -> AssetShellIR:
    asset_information = data.get("assetInformation") or {}
    submodel_ids = tuple(
        ref_id
        for ref_id in (_extract_reference_id(ref) for ref in data.get("submodels", []))
        if ref_id
    )
    return AssetShellIR(
        id=_string_value(data.get("id")),
        id_short=_string_value(data.get("idShort")),
        description=_normalize_lang_string(data.get("description")),
        asset_kind=_string_value(asset_information.get("assetKind")),
        asset_type=_string_value(asset_information.get("assetType")),
        global_asset_id=_string_value(asset_information.get("globalAssetId")),
        submodel_ids=submodel_ids,
    )


def _submodel_from_json(data: dict[str, Any], asset_shell_ids: tuple[str, ...], source: SourceMetadata) -> SubmodelIR:
    submodel_id = _string_value(data.get("id"))
    submodel_id_short = _string_value(data.get("idShort")) or submodel_id or "submodel"
    pointer = SourcePointer(file=source.file, input_kind=source.input_kind, submodel_id=submodel_id, submodel_id_short=submodel_id_short)
    return SubmodelIR(
        id=submodel_id,
        id_short=submodel_id_short,
        kind=_string_value(data.get("kind")),
        semantic_refs=tuple(_extract_semantic_refs(data.get("semanticId"), data.get("supplementalSemanticIds"))),
        description=_normalize_lang_string(data.get("description")),
        asset_shell_ids=asset_shell_ids,
        source_pointer=pointer,
        elements=tuple(
            _element_from_json(
                element,
                submodel_id=submodel_id,
                path_prefix=submodel_id_short,
                source=source,
                submodel_id_short=submodel_id_short,
            )
            for element in data.get("submodelElements", [])
            if isinstance(element, dict)
        ),
    )


def _element_from_json(
    data: dict[str, Any],
    submodel_id: str,
    path_prefix: str,
    source: SourceMetadata,
    submodel_id_short: str,
) -> ElementIR:
    id_short = _string_value(data.get("idShort")) or "element"
    path = f"{path_prefix}/{id_short}"
    stable_key = f"{submodel_id}/{path}"
    model_type = _extract_model_type(data.get("modelType"))
    raw_value = data.get("value")
    children: tuple[ElementIR, ...] = ()
    if _is_collection_like(data):
        child_items = []
        if isinstance(raw_value, list):
            child_items = [item for item in raw_value if isinstance(item, dict)]
        elif isinstance(raw_value, dict):
            child_items = [item for item in raw_value.values() if isinstance(item, dict)]
        children = tuple(
            _element_from_json(
                item,
                submodel_id=submodel_id,
                path_prefix=path,
                source=source,
                submodel_id_short=submodel_id_short,
            )
            for item in child_items
        )
        if children:
            raw_value = None

    typed_value, value_kind = _normalize_typed_value(raw_value, model_type=model_type, children=children)
    nominal_value, min_value, max_value = _extract_numeric_fact(raw_value, typed_value, model_type=model_type)
    unit = _string_value(data.get("unit"))
    return ElementIR(
        path=path,
        stable_key=stable_key,
        id_short=id_short,
        display_label=id_short,
        model_type=model_type,
        value_kind=value_kind,
        raw_value=raw_value,
        display_value=_display_value_from_typed(typed_value),
        typed_value=typed_value,
        value_type=_string_value(data.get("valueType")),
        unit=unit,
        normalized_unit=_normalize_unit(unit),
        nominal_value=nominal_value,
        min_value=min_value,
        max_value=max_value,
        semantic_refs=tuple(_extract_semantic_refs(data.get("semanticId"), data.get("supplementalSemanticIds"))),
        qualifiers=tuple(_qualifiers_from_json(data.get("qualifiers"))),
        references=tuple(_reference_documents_from_json(data)),
        description=_normalize_lang_string(data.get("description")),
        category=_string_value(data.get("category")),
        children=children,
        source_pointer=SourcePointer(
            file=source.file,
            input_kind=source.input_kind,
            submodel_id=submodel_id,
            submodel_id_short=submodel_id_short,
            element_path=path,
        ),
    )


def _submodel_from_basyx(submodel: object, asset_shell_ids: tuple[str, ...], source: SourceMetadata) -> SubmodelIR:
    submodel_id = _string_value(getattr(submodel, "id", None))
    submodel_id_short = _string_value(getattr(submodel, "id_short", None)) or submodel_id or "submodel"
    pointer = SourcePointer(file=source.file, input_kind=source.input_kind, submodel_id=submodel_id, submodel_id_short=submodel_id_short)
    return SubmodelIR(
        id=submodel_id,
        id_short=submodel_id_short,
        kind=_string_value(getattr(submodel, "kind", None)),
        semantic_refs=tuple(_extract_semantic_refs(getattr(submodel, "semantic_id", None), getattr(submodel, "supplemental_semantic_ids", None))),
        description=_string_value(getattr(submodel, "description", None)),
        asset_shell_ids=asset_shell_ids,
        source_pointer=pointer,
        elements=tuple(
            _element_from_basyx(
                element,
                submodel_id=submodel_id,
                path_prefix=submodel_id_short,
                source=source,
                submodel_id_short=submodel_id_short,
            )
            for element in _iter_basyx_elements(getattr(submodel, "submodel_element", None))
        ),
    )


def _element_from_basyx(
    element: object,
    submodel_id: str,
    path_prefix: str,
    source: SourceMetadata,
    submodel_id_short: str,
) -> ElementIR:
    id_short = _string_value(getattr(element, "id_short", None)) or element.__class__.__name__
    path = f"{path_prefix}/{id_short}"
    stable_key = f"{submodel_id}/{path}"
    child_candidates = [child for child in _iter_basyx_elements(getattr(element, "value", None)) if _looks_like_basyx_element(child)]
    children = tuple(
        _element_from_basyx(
            child,
            submodel_id=submodel_id,
            path_prefix=path,
            source=source,
            submodel_id_short=submodel_id_short,
        )
        for child in child_candidates
    )
    raw_value = None if children else getattr(element, "value", None)
    model_type = element.__class__.__name__
    typed_value, value_kind = _normalize_typed_value(raw_value, model_type=model_type, children=children)
    nominal_value, min_value, max_value = _extract_numeric_fact(raw_value, typed_value, model_type=model_type)
    unit = _string_value(getattr(element, "unit", None)) or _string_value(getattr(element, "unit_id", None))
    return ElementIR(
        path=path,
        stable_key=stable_key,
        id_short=id_short,
        display_label=id_short,
        model_type=model_type,
        value_kind=value_kind,
        raw_value=raw_value,
        display_value=_display_value_from_typed(typed_value),
        typed_value=typed_value,
        value_type=_string_value(getattr(element, "value_type", None)),
        unit=unit,
        normalized_unit=_normalize_unit(unit),
        nominal_value=nominal_value,
        min_value=min_value,
        max_value=max_value,
        semantic_refs=tuple(_extract_semantic_refs(getattr(element, "semantic_id", None), getattr(element, "supplemental_semantic_ids", None))),
        qualifiers=tuple(_qualifiers_from_basyx(getattr(element, "qualifier", None) or getattr(element, "qualifiers", None))),
        references=tuple(_reference_documents_from_basyx(element)),
        description=_string_value(getattr(element, "description", None)),
        category=_string_value(getattr(element, "category", None)),
        children=children,
        source_pointer=SourcePointer(
            file=source.file,
            input_kind=source.input_kind,
            submodel_id=submodel_id,
            submodel_id_short=submodel_id_short,
            element_path=path,
        ),
    )


def _build_element_index(submodels: tuple[SubmodelIR, ...]) -> dict[str, ElementIR]:
    index: dict[str, ElementIR] = {}
    for submodel in submodels:
        for element in _iter_elements(submodel.elements):
            index[element.path] = element
    return index


def _iter_elements(elements: Iterable[ElementIR]) -> Iterable[ElementIR]:
    for element in elements:
        yield element
        yield from _iter_elements(element.children)


def _asset_shell_ids_by_submodel(asset_shells: tuple[AssetShellIR, ...]) -> dict[str, tuple[str, ...]]:
    mapping: dict[str, list[str]] = {}
    for asset_shell in asset_shells:
        for submodel_id in asset_shell.submodel_ids:
            mapping.setdefault(submodel_id, [])
            if asset_shell.id and asset_shell.id not in mapping[submodel_id]:
                mapping[submodel_id].append(asset_shell.id)
    return {key: tuple(values) for key, values in mapping.items()}


def _filter_submodels(submodels: list[SubmodelIR], include: list[str]) -> list[SubmodelIR]:
    if not include:
        return submodels
    wanted = {_normalize_name(name) for name in include}
    return [submodel for submodel in submodels if _normalize_name(submodel.id_short or submodel.id) in wanted]


def _reference_documents_from_json(data: dict[str, Any]) -> Iterable[ReferenceIR]:
    for ref_type, ref_value in _collect_reference_pairs_from_json(data):
        yield ReferenceIR(type=ref_type, value=ref_value)


def _reference_documents_from_basyx(element: object) -> Iterable[ReferenceIR]:
    for ref_type, ref_value in _collect_reference_pairs_from_basyx(element):
        yield ReferenceIR(type=ref_type, value=ref_value)


def _collect_reference_pairs_from_json(data: dict[str, Any]) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    model_type = _extract_model_type(data.get("modelType"))
    if model_type == "ReferenceElement":
        refs.extend(_extract_reference_pairs(data.get("value")))
    elif model_type == "RelationshipElement":
        refs.extend(_extract_reference_pairs(data.get("first")))
        refs.extend(_extract_reference_pairs(data.get("second")))
    elif model_type == "AnnotatedRelationshipElement":
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


def _extract_semantic_refs(primary: Any, supplemental: Any = None) -> list[str]:
    values = []
    for source in (primary, supplemental):
        for _type, value in _extract_reference_pairs(source):
            if value and value not in values:
                values.append(value)
        single = _string_value(source)
        if single and single not in values and single != "[]":
            values.append(single)
    return values


def _qualifiers_from_json(value: Any) -> Iterable[QualifierIR]:
    if not isinstance(value, list):
        return []
    qualifiers = []
    for item in value:
        if not isinstance(item, dict):
            continue
        qualifiers.append(
            QualifierIR(
                type=_string_value(item.get("type")),
                value=_string_value(item.get("value")),
            )
        )
    return qualifiers


def _qualifiers_from_basyx(value: Any) -> Iterable[QualifierIR]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple, set, frozenset)):
        value = [value]
    qualifiers = []
    for item in value:
        qualifiers.append(
            QualifierIR(
                type=_string_value(getattr(item, "type", None)),
                value=_string_value(getattr(item, "value", None)),
            )
        )
    return qualifiers


def _normalize_typed_value(raw_value: Any, model_type: str, children: tuple[ElementIR, ...]) -> tuple[Any, str]:
    if children:
        return None, "collection"
    if model_type == "ReferenceElement":
        refs = [value for _type, value in _extract_reference_pairs(raw_value)]
        return refs, "reference"
    if model_type in {"RelationshipElement", "AnnotatedRelationshipElement"}:
        return stringify(raw_value), "relationship"
    if model_type == "File":
        return _string_value(raw_value), "file"
    if isinstance(raw_value, bool):
        return raw_value, "scalar"
    if isinstance(raw_value, (int, float)):
        return raw_value, "scalar"
    if isinstance(raw_value, str):
        return raw_value, "scalar"
    if isinstance(raw_value, list):
        if all(not isinstance(item, dict) for item in raw_value):
            return list(raw_value), "list"
        return raw_value, "object"
    if isinstance(raw_value, dict):
        if _looks_like_range_dict(raw_value):
            return {
                key: raw_value[key]
                for key in raw_value
                if _normalize_name(str(key)) in _RANGE_KEYS
            }, "range"
        return raw_value, "object"
    if raw_value is None:
        return None, "empty"
    return stringify(raw_value), "object"


def _display_value_from_typed(typed_value: Any) -> str:
    if typed_value is None:
        return ""
    if isinstance(typed_value, list):
        return ", ".join(_string_value(item) for item in typed_value if _string_value(item))
    if isinstance(typed_value, dict):
        return json.dumps(typed_value, ensure_ascii=False, sort_keys=True)
    return _string_value(typed_value)


def _extract_numeric_fact(raw_value: Any, typed_value: Any, model_type: str) -> tuple[float | None, float | None, float | None]:
    if isinstance(raw_value, bool):
        return None, None, None
    if isinstance(raw_value, (int, float)):
        value = float(raw_value)
        return value, value, value
    if isinstance(typed_value, dict) and model_type.lower() == "range":
        min_value = _coerce_number(_pick_dict_value(typed_value, "min", "minimum"))
        max_value = _coerce_number(_pick_dict_value(typed_value, "max", "maximum"))
        nominal = _coerce_number(_pick_dict_value(typed_value, "nominal", "value"))
        return nominal, min_value, max_value
    return None, None, None


def _pick_dict_value(data: dict[str, Any], *names: str) -> Any:
    for name in names:
        for key, value in data.items():
            if _normalize_name(str(key)) == _normalize_name(name):
                return value
    return None


def _looks_like_range_dict(value: dict[str, Any]) -> bool:
    normalized_keys = {_normalize_name(str(key)) for key in value}
    return bool({"min", "minimum"} & normalized_keys and {"max", "maximum"} & normalized_keys)


def _normalize_lang_string(value: Any) -> str:
    if isinstance(value, list):
        texts = [_string_value(item.get("text")) for item in value if isinstance(item, dict) and item.get("text")]
        return " | ".join(texts)
    return _string_value(value)


def _extract_model_type(model_type: Any) -> str:
    if isinstance(model_type, dict):
        return _string_value(model_type.get("name") or model_type.get("modelType"))
    return _string_value(model_type)


def _is_collection_like(data: dict[str, Any]) -> bool:
    model_type = _extract_model_type(data.get("modelType"))
    if model_type in {"SubmodelElementCollection", "SubmodelElementList", "Entity"}:
        return True
    value = data.get("value")
    if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
        return True
    if isinstance(value, dict) and value and all(isinstance(item, dict) for item in value.values()):
        return True
    return False


def _normalize_unit(unit: str) -> str:
    if not unit:
        return ""
    return unit.lower().replace("µ", "u").replace("μ", "u")


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


def _coerce_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = _string_value(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)
