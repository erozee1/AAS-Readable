from __future__ import annotations

from .document import AssetShellDocument, ElementDocument, ExportDocument, SubmodelDocument
from .util import stringify


def render_index_markdown(
    document: ExportDocument,
    submodels: list[SubmodelDocument],
    markdown_files: list[str],
) -> str:
    lines = [
        "# Asset Administration Shell Export",
        "",
        "## Source",
        "",
        f"- File: `{document.source_path.name}`",
        f"- Format: `{document.source_kind}`",
        f"- Asset administration shells: `{len(document.asset_shells)}`",
        f"- Exported submodels: `{len(submodels)}`",
        "",
        "## Assets",
        "",
    ]

    if not document.asset_shells:
        lines.append("_No asset administration shells found._")
    else:
        for asset_shell in document.asset_shells:
            lines.extend(_render_asset_shell(asset_shell))

    lines.extend(["", "## Submodels", ""])
    for submodel, markdown_file in zip(submodels, markdown_files):
        lines.append(f"- [{submodel.id_short or submodel.id}]({markdown_file})")

    lines.extend(
        [
            "",
            "## LLM Context",
            "",
            "- [llm-context.md](llm-context.md)",
            "",
        ]
    )
    return "\n".join(lines)


def render_llm_context_markdown(document: ExportDocument, submodels: list[SubmodelDocument]) -> str:
    """Render the compact artifact intended to be pasted into an LLM prompt."""

    lines = [
        "# AAS LLM Context",
        "",
        "This file is optimized for pasting into an LLM as compact, structured context.",
        "",
        "## Source",
        "",
        f"- File: `{document.source_path.name}`",
        f"- Format: `{document.source_kind}`",
        "",
    ]

    if document.canonical_text:
        lines.extend(
            [
                "## Canonical Description",
                "",
                document.canonical_text.strip(),
                "",
            ]
        )

    lines.extend(["## Asset Administration Shells", ""])
    if not document.asset_shells:
        lines.append("_No asset administration shells found._")
    else:
        for asset_shell in document.asset_shells:
            lines.extend(_render_asset_shell(asset_shell))

    lines.extend(["", "## Submodel Summaries", ""])
    for submodel in submodels:
        lines.extend(_render_submodel_summary(submodel))

    lines.append("")
    return "\n".join(lines)


def render_submodel_markdown(submodel: SubmodelDocument) -> str:
    lines = [
        f"# {submodel.id_short or submodel.id}",
        "",
        "## Metadata",
        "",
        f"- Identifier: `{submodel.id or 'n/a'}`",
        f"- Id Short: `{submodel.id_short or 'n/a'}`",
        f"- Kind: `{submodel.kind or 'n/a'}`",
    ]

    if submodel.semantic_id:
        lines.append(f"- Semantic ID: `{submodel.semantic_id}`")
    if submodel.description:
        lines.append(f"- Description: {submodel.description}")

    lines.extend(["", "## Elements", ""])

    if not submodel.elements:
        lines.append("_No submodel elements found._")
    else:
        for element in submodel.elements:
            lines.extend(_render_element(element, level=3))

    lines.append("")
    return "\n".join(lines)


def _render_asset_shell(asset_shell: AssetShellDocument) -> list[str]:
    lines = [
        f"### {asset_shell.id_short or asset_shell.id}",
        "",
        f"- Identifier: `{asset_shell.id or 'n/a'}`",
    ]
    if asset_shell.description:
        lines.append(f"- Description: {asset_shell.description}")
    if asset_shell.asset_kind:
        lines.append(f"- Asset Kind: `{asset_shell.asset_kind}`")
    if asset_shell.asset_type:
        lines.append(f"- Asset Type: `{asset_shell.asset_type}`")
    if asset_shell.global_asset_id:
        lines.append(f"- Global Asset ID: `{asset_shell.global_asset_id}`")
    if asset_shell.submodel_ids:
        lines.append(f"- Referenced Submodels: `{len(asset_shell.submodel_ids)}`")
        for submodel_id in asset_shell.submodel_ids:
            lines.append(f"  - `{submodel_id}`")
    lines.append("")
    return lines


def _render_submodel_summary(submodel: SubmodelDocument) -> list[str]:
    lines = [
        f"### {submodel.id_short or submodel.id}",
        "",
        f"- Identifier: `{submodel.id}`",
    ]
    if submodel.description:
        lines.append(f"- Description: {submodel.description}")
    if submodel.semantic_id:
        lines.append(f"- Semantic ID: `{submodel.semantic_id}`")
    lines.extend(["", "#### Key Elements", ""])

    if not submodel.elements:
        lines.append("_No submodel elements found._")
    else:
        for element in submodel.elements:
            lines.extend(_render_element_brief(element, depth=0))
    lines.append("")
    return lines


def _render_element(element: ElementDocument, level: int) -> list[str]:
    heading = "#" * min(level, 6)
    lines = [
        f"{heading} {element.id_short}",
        "",
        f"- Type: `{element.model_type or 'n/a'}`",
    ]

    value = _value(element.value)
    if value:
        lines.append(f"- Value: `{value}`")
    if element.value_type:
        lines.append(f"- Value Type: `{element.value_type}`")
    if element.semantic_id:
        lines.append(f"- Semantic ID: `{element.semantic_id}`")
    if element.category:
        lines.append(f"- Category: `{element.category}`")
    if element.description:
        lines.append(f"- Description: {element.description}")
    if element.unit:
        lines.append(f"- Unit: `{element.unit}`")

    if element.children:
        lines.extend(["", f"{heading}# Children", ""])
        for child in element.children:
            lines.extend(_render_element(child, level=min(level + 1, 6)))

    lines.append("")
    return lines


def _render_element_brief(element: ElementDocument, depth: int) -> list[str]:
    indent = "  " * depth
    lines = []
    value = _value(element.value)
    # Keep the brief view dense: this file is meant for prompt context, not as a
    # complete engineering report.
    detail_parts = [f"type={element.model_type or 'n/a'}"]
    if value:
        detail_parts.append(f"value={value}")
    if element.unit:
        detail_parts.append(f"unit={element.unit}")
    lines.append(f"{indent}- `{element.id_short}`: " + ", ".join(detail_parts))
    for child in element.children:
        lines.extend(_render_element_brief(child, depth + 1))
    return lines


def _value(value: object) -> str:
    rendered = stringify(value)
    return rendered.replace("\n", " ").strip()
