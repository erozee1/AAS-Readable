from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from .document import (
    AssetShellDocument,
    ElementDocument,
    ExportDocument,
    ExportSummary,
    SubmodelDocument,
)
from .markdown import (
    render_index_markdown,
    render_llm_context_markdown,
    render_submodel_markdown,
)


def export_input_to_markdown(
    input_path: Path,
    output_dir: Path,
    include: list[str] | None = None,
    overwrite: bool = False,
) -> ExportSummary:
    """Export a single AAS source into a directory of Markdown files."""

    input_path = input_path.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    include = include or []

    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")
    if input_path.suffix.lower() not in {".aasx", ".json"}:
        raise ValueError(f"Expected an .aasx or .json file, got: {input_path.name}")
    if output_dir.exists() and any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Output directory is not empty: {output_dir}. Use --overwrite to continue."
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    document = _load_document(input_path)
    submodels = _filter_submodels(list(document.submodels), include)
    if not submodels:
        raise ValueError("No submodels matched the requested export.")

    written_files: list[str] = []
    used_names: set[str] = set()

    for submodel in submodels:
        filename = _unique_filename(_slugify(submodel.id_short or submodel.id), used_names)
        path = output_dir / f"{filename}.md"
        path.write_text(render_submodel_markdown(submodel), encoding="utf-8")
        written_files.append(path.name)

    index_path = output_dir / "index.md"
    index_path.write_text(
        render_index_markdown(document=document, submodels=submodels, markdown_files=written_files),
        encoding="utf-8",
    )

    llm_context_path = output_dir / "llm-context.md"
    llm_context_path.write_text(
        render_llm_context_markdown(document=document, submodels=submodels),
        encoding="utf-8",
    )

    return ExportSummary(
        input_path=input_path,
        output_dir=output_dir,
        submodel_count=len(submodels),
        asset_shell_count=len(document.asset_shells),
        source_kind=document.source_kind,
    )


def export_aasx_to_markdown(
    aasx_path: Path,
    output_dir: Path,
    include: list[str] | None = None,
    overwrite: bool = False,
) -> ExportSummary:
    return export_input_to_markdown(
        input_path=aasx_path,
        output_dir=output_dir,
        include=include,
        overwrite=overwrite,
    )


def _load_document(input_path: Path) -> ExportDocument:
    if input_path.suffix.lower() == ".aasx":
        return _load_aasx_document(input_path)
    return _load_json_document(input_path)


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
    submodels: list[SubmodelDocument] = []

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
            submodels.append(_submodel_from_basyx(identifiable))

    return ExportDocument(
        source_path=input_path,
        source_kind="aasx",
        asset_shells=tuple(asset_shells),
        submodels=tuple(submodels),
    )


def _load_json_document(input_path: Path) -> ExportDocument:
    payload = json.loads(input_path.read_text(encoding="utf-8"))

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

    asset_shells = tuple(_asset_shell_from_json(aas) for aas in aas_env.get("assetAdministrationShells", []) if isinstance(aas, dict))
    submodels = tuple(_submodel_from_json(submodel) for submodel in aas_env.get("submodels", []) if isinstance(submodel, dict))

    return ExportDocument(
        source_path=input_path,
        source_kind=source_kind,
        asset_shells=asset_shells,
        submodels=submodels,
        canonical_text=canonical_text,
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


def _submodel_from_json(data: dict[str, Any]) -> SubmodelDocument:
    return SubmodelDocument(
        id=_string_value(data.get("id")),
        id_short=_string_value(data.get("idShort")) or _string_value(data.get("id")),
        kind=_string_value(data.get("kind")),
        semantic_id=_extract_semantic_id(data.get("semanticId")),
        description=_normalize_lang_string(data.get("description")),
        elements=tuple(
            _element_from_json(element)
            for element in data.get("submodelElements", [])
            if isinstance(element, dict)
        ),
    )


def _element_from_json(data: dict[str, Any]) -> ElementDocument:
    children: tuple[ElementDocument, ...] = ()
    value = data.get("value")

    if _is_collection_like(data):
        # Some generators serialize collections as arrays while others use keyed maps.
        # Normalize both shapes before rendering so Markdown stays deterministic.
        child_items = []
        if isinstance(value, list):
            child_items = [item for item in value if isinstance(item, dict)]
        elif isinstance(value, dict):
            child_items = [item for item in value.values() if isinstance(item, dict)]
        children = tuple(_element_from_json(item) for item in child_items)
        if children:
            value = None

    return ElementDocument(
        id_short=_string_value(data.get("idShort")) or "element",
        model_type=_string_value(data.get("modelType")),
        value=value,
        value_type=_string_value(data.get("valueType")),
        semantic_id=_extract_semantic_id(data.get("semanticId")),
        category=_string_value(data.get("category")),
        description=_normalize_lang_string(data.get("description")),
        unit=_string_value(data.get("unit")),
        children=children,
    )


def _submodel_from_basyx(submodel: object) -> SubmodelDocument:
    elements = tuple(_element_from_basyx(element) for element in _iter_basyx_elements(getattr(submodel, "submodel_element", None)))
    return SubmodelDocument(
        id=_string_value(getattr(submodel, "id", None)),
        id_short=_string_value(getattr(submodel, "id_short", None)) or _string_value(getattr(submodel, "id", None)),
        kind=_string_value(getattr(submodel, "kind", None)),
        semantic_id=_string_value(getattr(submodel, "semantic_id", None)),
        description=_string_value(getattr(submodel, "description", None)),
        elements=elements,
    )


def _element_from_basyx(element: object) -> ElementDocument:
    children = tuple(
        _element_from_basyx(child)
        for child in _iter_basyx_elements(getattr(element, "value", None))
        if _looks_like_basyx_element(child)
    )
    value = None if children else getattr(element, "value", None)
    return ElementDocument(
        id_short=_string_value(getattr(element, "id_short", None)) or element.__class__.__name__,
        model_type=element.__class__.__name__,
        value=value,
        value_type=_string_value(getattr(element, "value_type", None)),
        semantic_id=_string_value(getattr(element, "semantic_id", None)),
        category=_string_value(getattr(element, "category", None)),
        description=_string_value(getattr(element, "description", None)),
        unit=_string_value(getattr(element, "unit", None)) or _string_value(getattr(element, "unit_id", None)),
        children=children,
    )


def _filter_submodels(submodels: list[SubmodelDocument], include: list[str]) -> list[SubmodelDocument]:
    if not include:
        return submodels

    wanted = {_normalize_name(name) for name in include}
    return [
        submodel
        for submodel in submodels
        if _normalize_name(submodel.id_short or submodel.id) in wanted
    ]


def _extract_reference_id(reference: Any) -> str:
    if not isinstance(reference, dict):
        return ""
    keys = reference.get("keys") or []
    if not isinstance(keys, list):
        return ""
    for key in reversed(keys):
        if isinstance(key, dict) and key.get("value"):
            return _string_value(key["value"])
    return ""


def _extract_semantic_id(semantic_id: Any) -> str:
    if isinstance(semantic_id, dict):
        return _extract_reference_id(semantic_id)
    return _string_value(semantic_id)


def _normalize_lang_string(value: Any) -> str:
    if isinstance(value, list):
        texts = [
            _string_value(item.get("text"))
            for item in value
            if isinstance(item, dict) and item.get("text")
        ]
        return " | ".join(texts)
    return _string_value(value)


def _is_collection_like(data: dict[str, Any]) -> bool:
    model_type = _string_value(data.get("modelType"))
    if model_type in {"SubmodelElementCollection", "SubmodelElementList"}:
        return True
    value = data.get("value")
    if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
        return True
    if isinstance(value, dict) and value and all(isinstance(item, dict) for item in value.values()):
        return True
    return False


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
    keys = getattr(reference, "key", None) or getattr(reference, "keys", None)
    if not keys:
        return ""
    # BaSyx references can be multi-hop; the terminal key is the most useful
    # identifier for file naming and cross-linking in the Markdown export.
    for key in reversed(tuple(keys)):
        value = _string_value(getattr(key, "value", None))
        if value:
            return value
    return ""


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "submodel"


def _unique_filename(base: str, used_names: set[str]) -> str:
    candidate = base
    suffix = 2
    while candidate in used_names:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used_names.add(candidate)
    return candidate


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)
