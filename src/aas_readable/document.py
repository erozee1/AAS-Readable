from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReferenceDocument:
    type: str
    value: str


@dataclass(frozen=True)
class ElementDocument:
    """Normalized submodel element used by the renderer for both JSON and AASX inputs."""

    id_short: str
    model_type: str
    value: Any = None
    value_type: str = ""
    semantic_id: str = ""
    semantic_ids: tuple[str, ...] = ()
    category: str = ""
    description: str = ""
    unit: str = ""
    normalized_unit: str = ""
    path: str = ""
    stable_key: str = ""
    value_text: str = ""
    number_value: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    references: tuple[ReferenceDocument, ...] = ()
    children: tuple["ElementDocument", ...] = ()


@dataclass(frozen=True)
class SubmodelDocument:
    id: str
    id_short: str
    kind: str = ""
    semantic_id: str = ""
    semantic_ids: tuple[str, ...] = ()
    description: str = ""
    asset_shell_ids: tuple[str, ...] = ()
    source_file: str = ""
    source_kind: str = ""
    elements: tuple[ElementDocument, ...] = ()


@dataclass(frozen=True)
class AssetShellDocument:
    id: str
    id_short: str
    description: str = ""
    asset_kind: str = ""
    asset_type: str = ""
    global_asset_id: str = ""
    submodel_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExportDocument:
    """Repository-local intermediate form between parsers and Markdown rendering."""

    source_path: Path
    source_kind: str
    asset_shells: tuple[AssetShellDocument, ...]
    submodels: tuple[SubmodelDocument, ...]
    canonical_text: str = ""
    optional_narrative: str = ""
    schema_version: str = "1.0.0"


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
