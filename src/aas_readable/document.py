from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ElementDocument:
    """Normalized submodel element used by the renderer for both JSON and AASX inputs."""

    id_short: str
    model_type: str
    value: Any = None
    value_type: str = ""
    semantic_id: str = ""
    category: str = ""
    description: str = ""
    unit: str = ""
    children: tuple["ElementDocument", ...] = ()


@dataclass(frozen=True)
class SubmodelDocument:
    id: str
    id_short: str
    kind: str = ""
    semantic_id: str = ""
    description: str = ""
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


@dataclass(frozen=True)
class ExportSummary:
    input_path: Path
    output_dir: Path
    submodel_count: int
    asset_shell_count: int
    source_kind: str
