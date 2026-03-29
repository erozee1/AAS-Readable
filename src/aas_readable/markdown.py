"""Markdown renderers for review and brief-oriented AAS outputs."""

from __future__ import annotations

from .document import AssetShellIR, DocumentIR, ElementIR, SubmodelIR
from .payloads import build_brief_text, build_document_payload, build_validation_payload
from .util import stringify


def render_index_markdown(
    document: DocumentIR,
    submodels: list[SubmodelIR],
    markdown_files: list[str],
    view: str,
) -> str:
    lines = [
        "# AAS-Readable Export",
        "",
        "## Source",
        "",
        f"- File: `{document.source.file}`",
        f"- Input Kind: `{document.source.input_kind}`",
        f"- Wrapper Kind: `{document.source.wrapper_kind}`",
        f"- Schema Version: `{document.source.schema_version}`",
        f"- View: `{view}`",
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
    lines.extend(["", "## Document", "", "- [document.md](document.md)", ""])
    return "\n".join(lines)


def render_document_markdown(
    document: DocumentIR,
    submodels: list[SubmodelIR],
    view: str = "review",
) -> str:
    validation = build_validation_payload(document, submodels)
    if view == "brief":
        brief_payload = build_document_payload(document=document, submodels=submodels, view="brief")
        return "\n".join(
            [
                "# AAS Engineering Brief",
                "",
                "This compact view is derived from the lossless document and only includes exact engineering facts.",
                "",
                str(brief_payload.get("brief_text") or "_No brief content generated._"),
                "",
            ]
        )
    if view == "lossless":
        raise ValueError("The lossless view only supports JSON or YAML output.")

    payload = build_document_payload(document=document, submodels=submodels, view="review" if view == "review" else "agent")
    doc = payload["document"]
    lines = [
        "# AAS Engineering Review" if view == "review" else "# AAS Agent View",
        "",
        f"- Source file: `{document.source.file}`",
        f"- Input kind: `{document.source.input_kind}`",
        f"- Wrapper kind: `{document.source.wrapper_kind}`",
        f"- View: `{view}`",
        "",
    ]
    if document.optional_external_narrative:
        lines.extend(["## Optional External Narrative", "", document.optional_external_narrative.strip(), ""])

    lines.extend(["## Identifiers", ""])
    identifiers = doc.get("identifiers", {})
    for asset in identifiers.get("assets", []):
        lines.extend(_render_asset_identifier(asset))
    for key, entry in identifiers.get("fields", {}).items():
        lines.append(f"- {key}: `{entry['value']}`")
    lines.append("")

    compatibility = doc.get("compatibility", {})
    for section_name, label in (
        ("capabilities", "Capabilities"),
        ("materials", "Materials"),
        ("robots", "Robots"),
        ("sensors", "Sensors"),
        ("end_effectors", "End Effectors"),
    ):
        lines.extend(_render_fact_section(label, compatibility.get(section_name, []), include_trace=view == "review"))

    lines.extend(["## Numeric Facts", ""])
    numeric_facts = doc.get("numeric_facts", [])
    if not numeric_facts:
        lines.append("_No numeric facts captured._")
    else:
        for fact in numeric_facts:
            if fact.get("min_value") is not None and fact.get("max_value") is not None and fact["min_value"] != fact["max_value"]:
                value = f"{fact['min_value']} to {fact['max_value']}"
            else:
                value = stringify(fact.get("nominal_value"))
            unit = f" {fact['unit']}" if fact.get("unit") else ""
            lines.append(f"- `{fact['label']}`: `{value}{unit}`")
            if view == "review" and fact.get("path"):
                lines.append(f"  - Path: `{fact['path']}`")
    lines.append("")

    lines.extend(["## Generic Facts", ""])
    generic_facts = doc.get("generic_facts", [])
    if not generic_facts:
        lines.append("_No uncategorized scalar facts captured._")
    else:
        for fact in generic_facts:
            lines.append(f"- `{fact['label']}`: `{fact['value']}`")
            if view == "review" and fact.get("path"):
                lines.append(f"  - Path: `{fact['path']}`")
    lines.append("")

    if view == "review":
        lines.extend(["## Submodels", ""])
        for submodel in submodels:
            lines.extend(_render_submodel_summary(submodel))
        lines.extend(["", "## Known Gaps", ""])
        if validation.get("known_gaps"):
            for gap in validation["known_gaps"]:
                lines.append(f"- {gap}")
        else:
            lines.append("_No major validation gaps detected._")
        lines.append("")
    return "\n".join(lines)


def render_submodel_markdown(submodel: SubmodelIR, view: str = "review") -> str:
    lines = [
        f"# {submodel.id_short or submodel.id}",
        "",
        "## Metadata",
        "",
        f"- Identifier: `{submodel.id or 'n/a'}`",
        f"- Id Short: `{submodel.id_short or 'n/a'}`",
        f"- Kind: `{submodel.kind or 'n/a'}`",
    ]
    if submodel.description:
        lines.append(f"- Description: {submodel.description}")
    if submodel.semantic_refs:
        lines.append(f"- Semantic Refs: `{', '.join(submodel.semantic_refs)}`")
    if submodel.asset_shell_ids:
        lines.append(f"- Asset Shell IDs: `{', '.join(submodel.asset_shell_ids)}`")
    if view == "review":
        lines.append(f"- Source File: `{submodel.source_pointer.file}`")
    lines.extend(["", "## Elements", ""])
    if not submodel.elements:
        lines.append("_No submodel elements found._")
    else:
        for element in submodel.elements:
            lines.extend(_render_element(element, level=3, include_trace=view == "review"))
    lines.append("")
    return "\n".join(lines)


def _render_asset_shell(asset_shell: AssetShellIR) -> list[str]:
    lines = [f"### {asset_shell.id_short or asset_shell.id}", "", f"- Identifier: `{asset_shell.id or 'n/a'}`"]
    if asset_shell.global_asset_id:
        lines.append(f"- Global Asset ID: `{asset_shell.global_asset_id}`")
    if asset_shell.asset_kind:
        lines.append(f"- Asset Kind: `{asset_shell.asset_kind}`")
    if asset_shell.asset_type:
        lines.append(f"- Asset Type: `{asset_shell.asset_type}`")
    if asset_shell.submodel_ids:
        lines.append(f"- Referenced Submodels: `{', '.join(asset_shell.submodel_ids)}`")
    lines.append("")
    return lines


def _render_asset_identifier(asset: dict[str, str]) -> list[str]:
    lines = []
    if asset.get("id_short"):
        lines.append(f"- AssetShell: `{asset['id_short']}`")
    if asset.get("id"):
        lines.append(f"  - Identifier: `{asset['id']}`")
    if asset.get("global_asset_id"):
        lines.append(f"  - Global Asset ID: `{asset['global_asset_id']}`")
    return lines


def _render_fact_section(title: str, items: list[dict[str, str]], include_trace: bool) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.append(f"_No {title.lower()} captured._")
        lines.append("")
        return lines
    for item in items:
        lines.append(f"- {item['value']}")
        if include_trace and item.get("path"):
            lines.append(f"  - Path: `{item['path']}`")
    lines.append("")
    return lines


def _render_submodel_summary(submodel: SubmodelIR) -> list[str]:
    lines = [f"### {submodel.id_short or submodel.id}", "", f"- Identifier: `{submodel.id}`"]
    if submodel.description:
        lines.append(f"- Description: {submodel.description}")
    for element in submodel.elements[:8]:
        lines.extend(_render_element_brief(element))
    lines.append("")
    return lines


def _render_element(element: ElementIR, level: int, include_trace: bool) -> list[str]:
    heading = "#" * min(level, 6)
    lines = [f"{heading} {element.display_label}", "", f"- Type: `{element.model_type or 'n/a'}`", f"- Value Kind: `{element.value_kind}`"]
    if element.display_value:
        lines.append(f"- Value: `{element.display_value}`")
    if element.unit:
        lines.append(f"- Unit: `{element.unit}`")
    if element.semantic_refs:
        lines.append(f"- Semantic Refs: `{', '.join(element.semantic_refs)}`")
    if include_trace:
        lines.append(f"- Path: `{element.path}`")
        lines.append(f"- Stable Key: `{element.stable_key}`")
    if element.children:
        lines.extend(["", "#### Children", ""])
        for child in element.children:
            lines.extend(_render_element(child, level=min(level + 1, 6), include_trace=include_trace))
    lines.append("")
    return lines


def _render_element_brief(element: ElementIR) -> list[str]:
    if element.children:
        return [f"- `{element.display_label}` ({element.value_kind})"]
    if element.display_value:
        return [f"- `{element.display_label}`: `{element.display_value}`"]
    return [f"- `{element.display_label}` ({element.value_kind})"]
