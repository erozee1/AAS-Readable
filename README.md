# AAS-Readable

`AAS-Readable` is a Python package and CLI for turning Asset Administration Shell (AAS) and AASX data into LLM-ready, agent-ready, and engineer-readable context.

It helps teams working with industrial digital twins, manufacturing software catalogs, GraphRAG pipelines, semantic search, and engineering review workflows convert raw AAS JSON or `.aasx` packages into compact Markdown, YAML, and JSON artifacts.

## What AAS-Readable Is

`AAS-Readable` is best described as:

- an **Asset Administration Shell to LLM context converter**
- an **AAS JSON and AASX normalization layer**
- a **Python API for AAS interpretation**
- a **CLI for exporting readable digital twin artifacts**
- a **bridge between machine-oriented AAS data and human/agent workflows**

If someone is looking for:

- "Python package for Asset Administration Shell"
- "AAS to Markdown"
- "AAS to JSON for LLMs"
- "AASX parser for prompt engineering"
- "digital twin context export for agents"
- "AAS readable summaries for GraphRAG"

this package is intended to be a direct fit.

## Why It Exists

Raw AAS data is interoperable and structurally useful, but it is not naturally shaped for:

- LLM prompts
- agent pipelines
- semantic retrieval corpora
- Git-based engineering review
- quick inspection by software, controls, integration, and manufacturing engineers

`AAS-Readable` keeps the original structure but repackages it into outputs that are easier to:

- inspect
- diff
- summarize
- validate
- pass into LLM orchestration
- feed into downstream tooling without scraping Markdown

## What It Does

Inputs:

- AAS JSON environments
- wrapped JSON records shaped like `{ "aas": ..., "narrative_summary": ... }`
- `.aasx` packages when the `aasx` extra is installed
- directories containing `.json` and `.aasx` files

Outputs:

- Markdown for review and prompt context
- YAML for structured handoff
- JSON for programmatic consumption
- batch manifests for corpus export

Profiles:

- `prompt-compact` for token-efficient LLM context
- `agent-structured` for richer machine-facing payloads
- `diff-ready` for deterministic review-oriented exports

## Key Capabilities

- Parses AAS JSON and AASX into a normalized in-memory document model
- Preserves graph-useful fields such as paths, stable keys, semantic IDs, references, numeric values, and normalized units
- Renders one artifact set into multiple formats from the same normalized source
- Generates `llm-context` outputs intended for LLM and agent orchestration
- Builds engineering views such as capability sheets, equipment compatibility sheets, material compatibility sheets, lifecycle digests, and operational KPI digests
- Emits validation signals for missing semantic IDs, empty values, unit inconsistencies, and unresolved references
- Supports both CLI workflows and direct Python API usage

## Installation

Install from PyPI:

```bash
pip install aas-readable
```

Install with `.aasx` support:

```bash
pip install 'aas-readable[aasx]'
```

## Python API

The package is no longer CLI-only. The recommended Python API is:

- `load_export_document(input_path)`
- `load_export_document_from_payload(payload, source_name=...)`
- `render_llm_context(document, format="markdown|yaml|json", profile=...)`
- `render_submodel_bundle(document, include=..., format=..., profile=...)`
- `export_path(input_path, output_dir, ...)`

### Example: Load a File and Build LLM Context

```python
from pathlib import Path
from aas_readable import load_export_document, render_llm_context

document = load_export_document(Path("app_aas.json"))
payload = render_llm_context(
    document,
    format="json",
    profile="prompt-compact",
)

print(payload["prompt_text"])
print(payload["known_gaps"])
```

### Example: Start from an In-Memory AAS Payload

```python
from aas_readable import load_export_document_from_payload, render_submodel_bundle

document = load_export_document_from_payload(
    {
        "aas": aas_json,
        "narrative_summary": narrative_summary,
    },
    source_name="memory.json",
)

bundle = render_submodel_bundle(
    document,
    format="json",
    profile="agent-structured",
)

print(bundle["index"]["json"]["validation"])
```

### Example: Export a Whole Directory

```python
from pathlib import Path
from aas_readable import export_path

summary = export_path(
    input_path=Path("examples/aas"),
    output_dir=Path("out/aas-readable"),
    output_format="all",
    profile="agent-structured",
    overwrite=True,
)
```

## CLI

Basic usage:

```bash
aas-readable INPUT_PATH OUTPUT_DIR \
  [--include SUBMODEL_NAME] \
  [--overwrite] \
  [--output {markdown,yaml,json,both,all}] \
  [--profile {prompt-compact,agent-structured,diff-ready}]
```

### Examples

Export readable Markdown:

```bash
aas-readable app_aas.json out/
```

Export structured JSON for a downstream agent:

```bash
aas-readable app_aas.json out/ --output json --profile agent-structured
```

Export Markdown, YAML, and JSON together:

```bash
aas-readable app_aas.json out/ --output all --profile prompt-compact
```

Export a directory of AAS files:

```bash
aas-readable app-training/ out/corpus --output all --overwrite
```

## Output Model

Typical single-file export:

```text
out/
  index.md
  index.yaml
  index.json
  llm-context.md
  llm-context.yaml
  llm-context.json
  staticdata.md
  staticdata.yaml
  staticdata.json
  operationaldata.md
  operationaldata.yaml
  operationaldata.json
```

Directory export additionally writes a manifest:

```text
out/
  manifest.json
  manifest.yaml
  app-aas-0001/
  app-aas-0002/
```

## Why It Is Useful for LLMs, Agents, and Search

LLM systems and retrieval systems work better when context is:

- compact
- explicit
- hierarchical
- stable across runs
- clear about gaps and uncertainty

`AAS-Readable` supports that by producing:

- a prompt-oriented summary text
- structured submodel and element payloads
- validation signals
- compact engineering digests
- deterministic filenames and manifests for corpus building

This makes it useful for:

- LLM query planning
- agentic manufacturing software search
- GraphRAG corpora derived from AAS
- ranking explanation generation
- engineering document review
- diffing digital twin snapshots over time

## Optional Narrative Field

Some pipelines attach a short narrative summary alongside the raw AAS payload.

`AAS-Readable` supports that as an optional extra:

- preferred field name: `narrative_summary`
- compatibility alias: `canonical_text`

This field is not part of standard AAS and is not required. If it is absent, the package still works normally and builds prompt-oriented context from the AAS structure itself.

## Who It Is For

Most useful for:

- software engineers working with AAS and digital twins
- controls and integration engineers consuming AAS exports
- teams building agentic workflows around AAS data
- teams building semantic search or GraphRAG over industrial asset data
- manufacturing software catalog and capability-matching projects

Less useful as a primary interface for:

- live controls operations
- real-time alarm dashboards
- AAS authoring or round-trip editing
- AAS hosting infrastructure

## Design Principles

- Parse once, render many ways
- Preserve enough structure for machines without making human outputs unreadable
- Keep Markdown compact and Git-friendly
- Keep JSON and YAML explicit and stable for automation
- Expose validation gaps so LLMs and engineers can ask better follow-up questions

## Documentation

- [CLI Contract](docs/cli-plan.md)
- [Python API Notes](docs/python-api.md)
- [Research Notes](docs/research.md)

## Development Status

Current package metadata is still marked alpha, but the package now supports both a Python API and a CLI export workflow.
