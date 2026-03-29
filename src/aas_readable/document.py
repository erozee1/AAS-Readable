from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceMetadata:
    file: str
    input_kind: str
    wrapper_kind: str
    schema_version: str


@dataclass(frozen=True)
class SourcePointer:
    file: str
    input_kind: str
    submodel_id: str = ""
    submodel_id_short: str = ""
    element_path: str = ""


@dataclass(frozen=True)
class ReferenceIR:
    type: str
    value: str


@dataclass(frozen=True)
class QualifierIR:
    type: str
    value: str


@dataclass(frozen=True)
class ElementIR:
    path: str
    stable_key: str
    id_short: str
    display_label: str
    model_type: str
    value_kind: str
    raw_value: Any = None
    display_value: str = ""
    typed_value: Any = None
    value_type: str = ""
    unit: str = ""
    normalized_unit: str = ""
    nominal_value: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    semantic_refs: tuple[str, ...] = ()
    qualifiers: tuple[QualifierIR, ...] = ()
    references: tuple[ReferenceIR, ...] = ()
    description: str = ""
    category: str = ""
    children: tuple["ElementIR", ...] = ()
    source_pointer: SourcePointer = field(default_factory=lambda: SourcePointer(file="", input_kind=""))


@dataclass(frozen=True)
class SubmodelIR:
    id: str
    id_short: str
    kind: str = ""
    semantic_refs: tuple[str, ...] = ()
    description: str = ""
    asset_shell_ids: tuple[str, ...] = ()
    source_pointer: SourcePointer = field(default_factory=lambda: SourcePointer(file="", input_kind=""))
    elements: tuple[ElementIR, ...] = ()


@dataclass(frozen=True)
class AssetShellIR:
    id: str
    id_short: str
    description: str = ""
    asset_kind: str = ""
    asset_type: str = ""
    global_asset_id: str = ""
    submodel_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DocumentIR:
    source_path: Path
    source: SourceMetadata
    asset_shells: tuple[AssetShellIR, ...]
    submodels: tuple[SubmodelIR, ...]
    element_index: dict[str, ElementIR]
    optional_external_narrative: str = ""
    legacy_canonical_text: str = ""


@dataclass(frozen=True)
class ExportSummary:
    input_path: Path
    output_dir: Path
    submodel_count: int
    asset_shell_count: int
    source_kind: str


@dataclass(frozen=True)
class BatchExportSummary:
    input_path: Path
    output_dir: Path
    file_count: int
    exported_submodel_count: int


# Thin aliases retained so downstream code can migrate in one release.
ReferenceDocument = ReferenceIR
ElementDocument = ElementIR
SubmodelDocument = SubmodelIR
AssetShellDocument = AssetShellIR
ExportDocument = DocumentIR
