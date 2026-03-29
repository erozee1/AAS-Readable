# Python API Notes

This document describes the recommended Python API for `aas-readable`.

## Why Use the Python API

Use the Python API when you want to:

- consume AAS exports in a Python application
- generate LLM-ready context without writing files first
- build a retrieval corpus from AAS data
- integrate AAS-readable summaries into a search, ranking, or agent orchestration pipeline

## Main Entry Points

### `load_export_document(input_path)`

Loads a `.json` or `.aasx` file and returns an `ExportDocument`.

Use this when your source is already on disk.

### `load_export_document_from_payload(payload, source_name="memory.json")`

Builds the same normalized document from an in-memory Python payload.

Use this when your AAS data was fetched from an API, database, or another pipeline stage.

### `render_llm_context(document, format="markdown|yaml|json", profile=...)`

Builds the top-level LLM or agent context for a normalized document.

Typical uses:

- `format="json", profile="prompt-compact"` for orchestration
- `format="yaml", profile="agent-structured"` for tool handoff
- `format="markdown"` for human prompt review

### `render_submodel_bundle(document, include=..., format=..., profile=...)`

Renders the full export bundle in memory:

- per-submodel artifacts
- index artifact
- `llm-context` artifact

Use this when you want all outputs without writing to disk.

### `export_path(input_path, output_dir, ...)`

Writes either:

- a single-file export
- or a batch directory export with a manifest

This is the preferred file-writing API.

## Format and Profile Guidance

### Pick JSON when

- a machine will consume the output
- you want stable schema-like payloads
- you are building agent tools, search indexes, or validation steps

### Pick Markdown when

- a human will read the output
- you want prompt copy/paste
- you want Git-friendly diffs

### Pick YAML when

- you want a structured text artifact that is still easy to inspect manually

### Pick `prompt-compact` when

- token budget matters
- you want one concise summary plus key extracted views

### Pick `agent-structured` when

- you want detailed element-level fields
- you care about semantic IDs, references, and numeric preservation

## Example: Use JSON in an LLM Orchestrator

```python
from aas_readable import load_export_document_from_payload, render_llm_context

document = load_export_document_from_payload(
    {
        "aas": aas_json,
        "narrative_summary": narrative_summary,
    },
    source_name="live-record.json",
)

context_payload = render_llm_context(
    document,
    format="json",
    profile="prompt-compact",
)

prompt_text = context_payload["prompt_text"]
known_gaps = context_payload["known_gaps"]
```

## Example: Build a Structured Search Corpus

```python
from pathlib import Path
from aas_readable import export_path

summary = export_path(
    input_path=Path("training-data"),
    output_dir=Path("out/aas-corpus"),
    output_format="all",
    profile="agent-structured",
    overwrite=True,
)
```

## Stability Notes

- `ExportDocument` is the normalized internal contract used across renderers
- JSON output is the clearest machine-facing representation
- the package now includes a schema version in exported payloads
- the legacy function name `export_input_to_markdown(...)` is still supported for compatibility, but it now writes more than Markdown depending on `output_format`
- if a wrapped record includes an optional narrative field, prefer `narrative_summary`; `canonical_text` remains supported as a compatibility alias
