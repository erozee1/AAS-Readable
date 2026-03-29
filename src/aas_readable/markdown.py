"""Markdown renderers for engineer-facing AAS exports."""

from __future__ import annotations

from .document import AssetShellDocument, ElementDocument, ExportDocument, SubmodelDocument
from .payloads import build_engineering_views, build_llm_context_payload, build_submodel_synopsis, build_validation_payload
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
        f"- Schema Version: `{document.schema_version}`",
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
        synopsis = build_submodel_synopsis(submodel)
        lines.append(f"- [{submodel.id_short or submodel.id}]({markdown_file})")
        if synopsis:
            lines.append(f"  - {synopsis}")

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


def render_llm_context_markdown(
    document: ExportDocument,
    submodels: list[SubmodelDocument],
    profile: str = "agent-structured",
) -> str:
    """Render the compact artifact intended to be pasted into an LLM prompt."""

    payload = build_llm_context_payload(document=document, submodels=submodels, profile=profile)
    engineering_views = build_engineering_views(submodels)
    validation = build_validation_payload(document, submodels)

    lines = [
        "# AAS LLM Context",
        "",
        "This file is optimized for pasting into an LLM as compact, structured context.",
        "",
        "## Source",
        "",
        f"- File: `{document.source_path.name}`",
        f"- Format: `{document.source_kind}`",
        f"- Profile: `{profile}`",
        f"- Schema Version: `{document.schema_version}`",
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

    if payload.get("prompt_text"):
        lines.extend(
            [
                "## Prompt Summary",
                "",
                payload["prompt_text"],
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

    lines.extend(["", "## Engineering Views", ""])
    lines.extend(_render_sheet("Capabilities", engineering_views.get("capability_sheet", {}).get("items", [])))
    lines.extend(_render_sheet("Equipment Compatibility", engineering_views.get("equipment_compatibility_sheet", {}).get("items", [])))
    lines.extend(_render_sheet("Material Compatibility", engineering_views.get("material_compatibility_sheet", {}).get("items", [])))
    lines.extend(_render_sheet("Sensor Compatibility", engineering_views.get("sensor_compatibility_sheet", {}).get("items", [])))
    lines.extend(_render_digest("Lifecycle Digest", engineering_views.get("lifecycle_digest", [])))
    lines.extend(_render_digest("Operational KPI Digest", engineering_views.get("operational_kpi_digest", [])))
    lines.extend(_render_numeric_facts(engineering_views.get("numeric_facts", [])))

    lines.extend(["", "## Known Gaps", ""])
    if validation.get("known_gaps"):
        for gap in validation["known_gaps"]:
            lines.append(f"- {gap}")
    else:
        lines.append("_No major validation gaps detected._")

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
        f"- Synopsis: {build_submodel_synopsis(submodel)}",
    ]

    if submodel.semantic_id:
        lines.append(f"- Semantic ID: `{submodel.semantic_id}`")
    if submodel.semantic_ids:
        lines.append(f"- Semantic IDs: `{', '.join(submodel.semantic_ids)}`")
    if submodel.asset_shell_ids:
        lines.append(f"- Asset Shell IDs: `{', '.join(submodel.asset_shell_ids)}`")
    if submodel.source_file:
        lines.append(f"- Source File: `{submodel.source_file}`")
    if submodel.source_kind:
        lines.append(f"- Source Kind: `{submodel.source_kind}`")
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
        f"- Synopsis: {build_submodel_synopsis(submodel)}",
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
    if element.value_text:
        lines.append(f"- Value Text: `{element.value_text}`")
    if element.path:
        lines.append(f"- Path: `{element.path}`")
    if element.stable_key:
        lines.append(f"- Stable Key: `{element.stable_key}`")
    if element.value_type:
        lines.append(f"- Value Type: `{element.value_type}`")
    if element.semantic_id:
        lines.append(f"- Semantic ID: `{element.semantic_id}`")
    if element.semantic_ids:
        lines.append(f"- Semantic IDs: `{', '.join(element.semantic_ids)}`")
    if element.category:
        lines.append(f"- Category: `{element.category}`")
    if element.description:
        lines.append(f"- Description: {element.description}")
    if element.unit:
        lines.append(f"- Unit: `{element.unit}`")
    if element.number_value is not None:
        lines.append(f"- Number Value: `{element.number_value}`")
    if element.min_value is not None:
        lines.append(f"- Min Value: `{element.min_value}`")
    if element.max_value is not None:
        lines.append(f"- Max Value: `{element.max_value}`")
    if element.references:
        lines.append("- References:")
        for reference in element.references:
            lines.append(f"  - `{reference.type}` -> `{reference.value}`")

    if element.children:
        lines.extend(["", f"{heading}# Children", ""])
        for child in element.children:
            lines.extend(_render_element(child, level=min(level + 1, 6)))

    lines.append("")
    return lines


def _render_element_brief(element: ElementDocument, depth: int) -> list[str]:
    indent = "  " * depth
    lines = []
    detail_parts = [f"type={element.model_type or 'n/a'}"]
    if element.value_text:
        detail_parts.append(f"value={element.value_text}")
    if element.unit:
        detail_parts.append(f"unit={element.unit}")
    if element.path:
        detail_parts.append(f"path={element.path}")
    lines.append(f"{indent}- `{element.id_short}`: " + ", ".join(detail_parts))
    for child in element.children:
        lines.extend(_render_element_brief(child, depth + 1))
    return lines


def _render_sheet(title: str, items: list[str]) -> list[str]:
    lines = [f"### {title}", ""]
    if not items:
        lines.append("_No items extracted._")
    else:
        for item in items:
            lines.append(f"- {item}")
    lines.append("")
    return lines


def _render_digest(title: str, items: list[dict]) -> list[str]:
    lines = [f"### {title}", ""]
    if not items:
        lines.append("_No digest entries extracted._")
    else:
        for item in items:
            lines.append(f"- `{item.get('path', 'n/a')}`: {item.get('value', '')}")
    lines.append("")
    return lines


def _render_numeric_facts(items: list[dict]) -> list[str]:
    lines = ["### Numeric Facts", ""]
    if not items:
        lines.append("_No numeric facts extracted._")
    else:
        for item in items:
            unit = f" {item['unit']}" if item.get("unit") else ""
            if item.get("min_value") is not None and item.get("max_value") is not None and item["min_value"] != item["max_value"]:
                lines.append(
                    f"- `{item.get('path', 'n/a')}`: {item['min_value']} to {item['max_value']}{unit}"
                )
            elif item.get("number_value") is not None:
                lines.append(f"- `{item.get('path', 'n/a')}`: {item['number_value']}{unit}")
    lines.append("")
    return lines


def _value(value: object) -> str:
    rendered = stringify(value)
    return rendered.replace("\n", " ").strip()
