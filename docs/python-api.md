# Python API

`AAS-Readable` now exposes a view-based API built on a lossless document IR.

## Preferred Entry Points

- `load_document(path)`
- `load_document_from_payload(payload, source_name=...)`
- `render_document(document, view=..., format=...)`
- `render_submodels(document, include=..., view=..., format=...)`

## Basic Example

```python
from pathlib import Path
from aas_readable import load_document, render_document

document = load_document(Path("app_aas.json"))
payload = render_document(document, format="json", view="agent")
```

## View Meanings

### `lossless`

Use for exact machine processing.

Properties:

- preserves source paths
- preserves semantic refs
- preserves references and qualifiers
- preserves exact typed values

### `agent`

Use for agent handoff and deterministic extraction.

Properties:

- exact identifiers
- grouped compatibility facts
- numeric facts without heuristic rewriting
- compact but still structured

### `brief`

Use for prompt context when you want fewer tokens.

Properties:

- derived from `agent`
- exact IDs and values stay exact
- omissions are explicit

### `review`

Use for engineering inspection and Git diff review.

Properties:

- includes provenance and trace detail
- deterministic ordering

## Wrapped Payloads

The package accepts:

- bare AAS environment JSON
- wrapped JSON with `{"aas": ...}`
- optional `narrative_summary`
- legacy `canonical_text` alias for compatibility

Example:

```python
from aas_readable import load_document_from_payload, render_document

document = load_document_from_payload(
    {
        "narrative_summary": "Optional external summary.",
        "aas": aas_json,
    },
    source_name="wrapped.json",
)

brief = render_document(document, format="markdown", view="brief")
```

## Compatibility Layer

The following names still exist as thin shims:

- `load_export_document`
- `load_export_document_from_payload`
- `render_llm_context`
- `render_submodel_bundle`
- `export_input_to_markdown`

New code should prefer the view-based API.
