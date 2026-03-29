# AAS-Readable

`AAS-Readable` converts Asset Administration Shell (`AAS`) and `AASX` data from an interoperability-oriented exchange format into lossless, deterministic engineering representations for agents, LLMs, review, and retrieval preparation.

It is not a summarizer first. The package now works as:

1. parse AAS / AASX once
2. normalize into a lossless intermediate representation
3. render exact `lossless`, `agent`, `brief`, or `review` views from that source of truth

## What Problem It Solves

Raw AAS is useful for interoperability, but awkward for LLMs and agent systems because it mixes:

- transport structure
- metamodel boilerplate
- engineering facts
- references and trace metadata

`AAS-Readable` separates those concerns and produces views that are:

- exact enough for extraction and matching
- compact enough for prompt use
- traceable back to source paths
- deterministic enough for tests and Git review

## What It Is Not

`AAS-Readable` is not:

- an AAS authoring tool
- an AAS registry or repository
- a live controls dashboard
- a round-trip editor
- a semantic resolution service

## Core Views

### `lossless`

Full canonical IR in JSON or YAML.

Use this when you need:

- exact field preservation
- source traceability
- downstream transforms
- benchmark and agent test inputs

### `agent`

Deterministic machine-facing representation grouped into:

- identifiers
- capabilities
- materials
- robots
- sensors
- end effectors
- numeric facts
- operations
- generic facts
- gaps

Use this when an agent or evaluation task needs compact but extraction-safe context.

### `brief`

Compact prompt-oriented text generated from the `agent` view.

It is token-efficient, but it does not invent ranges, rewrite IDs, or flatten semantics before preservation.

### `review`

Deterministic review-oriented output for engineers and Git diffs.

It includes provenance and trace details that the `brief` view omits.

## Python API

```python
from pathlib import Path
from aas_readable import load_document, render_document

document = load_document(Path("app_aas.json"))

lossless = render_document(document, format="json", view="lossless")
agent = render_document(document, format="json", view="agent")
brief = render_document(document, format="markdown", view="brief")
review = render_document(document, format="yaml", view="review")
```

For wrapped in-memory payloads:

```python
from aas_readable import load_document_from_payload, render_document

document = load_document_from_payload(
    {
        "narrative_summary": "Optional external narrative.",
        "aas": aas_json,
    },
    source_name="memory.json",
)

payload = render_document(document, format="json", view="agent")
```

## CLI

```bash
aas-readable app_aas.json out/ --output json --view lossless
aas-readable app_aas.json out/ --output yaml --view agent
aas-readable app_aas.json out/ --output markdown --view brief
aas-readable app_aas.json out/ --output all --view review
```

## Output Layout

For file exports, `AAS-Readable` writes:

- `index.*`
- `document.*`
- one file per submodel

Example:

```text
out/
  index.json
  document.json
  staticdata.json
  functionaldata.json
  operationaldata.json
  lifecycledata.json
```

## Relevance Policy

`AAS-Readable` keeps exact engineering facts first-class:

- app and asset identifiers
- names
- property labels and values
- units
- numeric facts
- capabilities
- materials
- robots
- sensors
- end effectors
- operation-like elements
- source paths

It keeps raw semantic references and low-level trace metadata in canonical and review views, but does not force unresolved URNs into the compact prompt view by default.

It removes prompt-time noise after parsing, such as:

- AASX package scaffolding
- repeated metamodel wrappers
- transport-only containers
- thumbnail metadata
- repeated boilerplate that is no longer needed once facts are normalized

## Compatibility Notes

`0.4.0` is a breaking cleanup release.

The preferred API is now:

- `load_document(...)`
- `load_document_from_payload(...)`
- `render_document(document, view=..., format=...)`
- `render_submodels(document, view=..., format=...)`

Thin compatibility shims still exist for:

- `load_export_document(...)`
- `load_export_document_from_payload(...)`
- `render_llm_context(...)`
- `render_submodel_bundle(...)`
- `export_input_to_markdown(...)`

But new integrations should use the `view` API directly.

## Development

Run the package tests with the project venv that already has `PyYAML`:

```bash
PYTHONPATH=src /Users/ethanrozee/Documents/Projects/MEng\ project/.venv/bin/python -m unittest discover -s tests -v
```

## Search Terms

If you are looking for:

- Asset Administration Shell Python library
- AASX to JSON
- AAS to agent IR
- AAS LLM context
- digital twin prompt preprocessing
- manufacturing software search context layer
- AAS GraphRAG preprocessing

then `AAS-Readable` is intended to be a strong candidate.
