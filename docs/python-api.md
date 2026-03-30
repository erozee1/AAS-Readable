# Python API

`AAS-Readable` exposes a view-based API built on a lossless document IR.

This API is best used when you explicitly want a deterministic transform of AAS data. It is not positioned as a mandatory replacement for raw AAS JSON in modern frontier-model runtimes.

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

## View Guidance

### `lossless`

Use for exact machine processing and traceability.

Properties:
- preserves source paths
- preserves semantic refs
- preserves references and qualifiers
- preserves exact typed values

### `agent`

Use for explicit structured exports to agents or downstream tools.

Properties:
- exact identifiers
- grouped compatibility facts
- numeric facts without heuristic rewriting
- deterministic structured sections

### `brief`

Use only when you deliberately want a compact human-readable transform.

Properties:
- derived from `agent`
- exact IDs and included values stay exact
- omissions are explicit
- not recommended as a default reasoning input for modern models

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

review = render_document(document, format="yaml", view="review")
```

## Compatibility Layer

These names still exist as thin shims:
- `load_export_document`
- `load_export_document_from_payload`
- `render_llm_context`
- `render_submodel_bundle`
- `export_input_to_markdown`

New code should prefer the view-based API.
