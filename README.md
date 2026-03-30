# AAS-Readable

`AAS-Readable` converts Asset Administration Shell (`AAS`) and `AASX` data into **lossless, deterministic, reviewable representations**.

For modern frontier models, raw AAS JSON is often already a strong direct reasoning input. `AAS-Readable` is therefore best treated as an **optional specialist tool**, not as the default runtime ingestion layer for every LLM workflow.

Use it when you explicitly need:
- normalized exports
- deterministic agent/tool inputs
- audit and review views
- benchmark fixtures
- controlled downstream transforms with source traceability

Do not assume it will automatically outperform raw AAS JSON for modern models.

## When To Use It

- You need a stable, machine-facing AAS representation for tooling or tests.
- You want review-friendly YAML or Markdown derived from the same source of truth.
- You want to export AAS content into a deterministic format for downstream systems.
- You want explicit, structured transforms instead of ad hoc prompt formatting.

## When Not To Use It

- You already have a strong frontier model reasoning directly over raw AAS JSON.
- You want a default runtime prompt format with guaranteed accuracy gains over raw JSON.
- You only need the original AAS for interoperability or storage.

`brief` Markdown is compact and useful when a human-readable transform is explicitly desired, but it is **not** the recommended default reasoning input for modern models.

## What The Package Does

1. Parse AAS / AASX once
2. Normalize into a lossless intermediate representation
3. Render explicit `lossless`, `agent`, `brief`, or `review` views from that source of truth

## Core Views

### `lossless`

Full canonical IR in JSON or YAML.

Use this for:
- exact field preservation
- source traceability
- downstream transforms
- benchmark and QA fixtures

### `agent`

Deterministic structured output for explicit agent or tool integrations.

Use this for:
- exact identifiers
- grouped compatibility facts
- numeric facts without heuristic rewriting
- compact but still structured machine-facing exports

### `brief`

Compact prompt-oriented text derived from `agent`.

Use this only when you explicitly want a compact human-readable transform. It preserves exact IDs and values when included, but it is not positioned as the default reasoning input for modern frontier models.

### `review`

Deterministic review-oriented output for engineers and Git diffs.

Use this for:
- provenance
- traceability
- human inspection
- change review

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

Wrapped in-memory payloads are also supported:

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

## Install

```bash
pip install aas-readable
```

With AASX support:

```bash
pip install "aas-readable[aasx]"
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

## Compatibility Notes

`0.4.0` is a breaking cleanup release.

Preferred API:
- `load_document(...)`
- `load_document_from_payload(...)`
- `render_document(document, view=..., format=...)`
- `render_submodels(document, view=..., format=...)`

Thin compatibility shims still exist for older names, but new integrations should use the view API directly.

## Development

Run the package tests:

```bash
PYTHONPATH=src /Users/ethanrozee/Documents/Projects/MEng\ project/.venv/bin/python -m unittest discover -s tests -v
```

Build and verify the release artifacts:

```bash
/Users/ethanrozee/Documents/Projects/MEng\ project/.venv/bin/python -m build --no-isolation
/Users/ethanrozee/Documents/Projects/MEng\ project/.venv/bin/python -m twine check dist/aas_readable-0.4.0*
```

## Search Terms

Relevant discovery terms:
- Asset Administration Shell Python library
- AASX to JSON
- AAS review export
- AAS agent export
- deterministic AAS transform
- digital twin review tooling
- AAS QA fixture generation
