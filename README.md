# AAS-Readable

`AAS-Readable` helps engineers use Asset Administration Shell content with LLMs and agents.

It converts machine-oriented AAS environments into compact Markdown and YAML outputs that are easier to inspect, diff, prompt with, and pass into downstream agent workflows.

Markdown is the default for review and prompt context. YAML is available when an agent or model benefits from a more explicitly structured export.

## One-Line Contract

Input:

- `.json` AAS environments
- wrapped `.json` records with AAS under `aas`
- `.aasx` packages with the `aasx` extra installed

Output:

- Markdown by default
- YAML with `--output yaml`
- both with `--output both`

Primary goal:

- help engineers use AAS data in LLMs, agents, and review workflows

## Why This Exists

AAS content is structured and interoperable, but it is not optimized for the way engineers actually use LLMs.

`AAS-Readable` makes a digital twin easier to:

- review in Git
- compare between revisions
- paste into an LLM without extra cleanup
- feed into agent workflows as readable Markdown or structured YAML

In practice, it turns AAS data into something that helps answer:

- What is this asset?
- What submodels does it expose?
- What is currently happening in the twin?
- What changed since the last export?
- What should an LLM know before summarizing or reasoning over it?

## Primary Use Case

This package is for engineers who already have AAS data and want to use it in:

- LLM prompts
- agent pipelines
- Git-based engineering review
- lightweight retrieval and documentation workflows

It is not trying to replace AAS-native servers, registries, or operational dashboards.

## Quick Decision Guide

Use `--output markdown` when you want:

- prompt-ready context
- Git-friendly diffs
- human review

Use `--output yaml` when you want:

- structured agent input
- explicit nesting
- downstream automation

Use `--output both` when you want:

- human-readable review output
- agent-friendly structured output from the same export

## What It Does

The exporter reads:

- `.aasx` packages
- plain AAS JSON environments
- wrapped JSON records where the AAS is stored under `aas`

It writes:

- one Markdown file per submodel
- `index.md` as a navigation page
- `llm-context.md` as a compact prompt-ready summary
- YAML files for the same artifacts when `--output yaml` or `--output both` is used

## Quick Start

Install from PyPI:

```bash
pip install aas-readable
```

If you want `.aasx` support:

```bash
pip install 'aas-readable[aasx]'
```

Export an AAS JSON file:

```bash
aas-readable app_aas.json out/
```

Export YAML for an agent pipeline:

```bash
aas-readable app_aas.json out/ --output yaml
```

Export an AASX package:

```bash
aas-readable machine.aasx out/
```

Verify the CLI:

```bash
aas-readable --help
```

## CLI Summary

```bash
aas-readable INPUT_PATH OUTPUT_DIR [--include SUBMODEL_NAME] [--overwrite] [--output {markdown,yaml,both}]
```

Defaults:

- `--output markdown`
- export all submodels
- fail if `OUTPUT_DIR` is non-empty unless `--overwrite` is used

## Output Files

Typical output:

```text
out/
  index.md
  llm-context.md
  staticdata.md
  functionaldata.md
  operationaldata.md
  lifecycledata.md
```

With `--output both`, the exporter also writes:

```text
out/
  index.yaml
  llm-context.yaml
  staticdata.yaml
  functionaldata.yaml
  operationaldata.yaml
  lifecycledata.yaml
```

`index.md` gives you a quick overview of the exported asset shells and submodels.

`llm-context.md` gives you a compact, structured summary intended to be pasted directly into an LLM prompt.

Each submodel file gives you a readable engineering view of the original structured content.

The YAML artifacts are intended for engineers building agentic tooling on top of AAS exports.

## Output Matrix

`--output markdown`

- per-submodel `.md`
- `index.md`
- `llm-context.md`

`--output yaml`

- per-submodel `.yaml`
- `index.yaml`
- `llm-context.yaml`

`--output both`

- all Markdown artifacts
- all YAML artifacts

## Example Workflow

Export a wrapped record with both structured AAS data and narrative context:

```bash
aas-readable app_aas_0001.json out/app_aas_0001
```

Then use the generated files for different jobs:

- read `index.md` to understand the twin structure
- inspect individual submodel Markdown files during engineering review
- paste `llm-context.md` into an LLM for summarization, comparison, or Q&A
- feed YAML output into an agent pipeline when structured context works better
- commit the output directory to Git to diff twin revisions over time

## Why This Is Useful For LLMs And Agents

LLMs and agents work better when the input is compact, hierarchical, and explicit about context.

`llm-context.md` is designed around that constraint. It keeps the most useful information in one predictable document:

- asset identity
- referenced submodels
- canonical narrative text when present
- condensed summaries of submodel elements

That makes it useful for tasks such as:

- status summarization
- maintenance brief generation
- comparing twin snapshots
- spotting missing fields
- building retrieval corpora from AAS exports

When a downstream workflow needs a stricter structure, `--output yaml` or `--output both` provides the same normalized content in YAML.

## Who It Is For

Most useful for:

- software and integration engineers working with AAS data
- teams building LLM or agent workflows around digital twins
- people using Git to review twin changes
- teams preparing AAS content for search, retrieval, or prompt pipelines

Less useful, in its current form, as a primary interface for:

- live controls operations
- alarm monitoring
- high-frequency operational dashboards

This tool makes AAS easier to use with AI systems. It does not replace a live operational UI.

## Installation

### Recommended

Standard install from PyPI:

```bash
pip install aas-readable
```

With optional `.aasx` support:

```bash
pip install 'aas-readable[aasx]'
```

The `aasx` extra installs the Eclipse BaSyx Python SDK.

### Install From GitHub

If you want the latest repository version instead of the latest package release:

```bash
pip install "git+https://github.com/erozee1/AAS-Readable.git"
```

With `.aasx` support:

```bash
pip install "git+https://github.com/erozee1/AAS-Readable.git#egg=aas-readable[aasx]"
```

### Install From A Local Clone

Clone the repository first:

```bash
git clone https://github.com/erozee1/AAS-Readable.git
cd AAS-Readable
```

Standard local install:

```bash
pip install .
```

Editable local install for development:

```bash
pip install -e .
```

Editable local install with `.aasx` support:

```bash
pip install -e '.[aasx]'
```

### Recommended Virtual Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Then run one of the install commands above.

## Examples

Export a JSON environment:

```bash
aas-readable app_aas.json out/
```

Default behavior writes Markdown, which is the recommended starting point for engineers reviewing and prompting over AAS content.

Export a packaged twin:

```bash
aas-readable machine.aasx out/
```

Export selected submodels only:

```bash
aas-readable machine.aasx out/ \
  --include "Technical Data" \
  --include "Operational Data"
```

Reuse an existing output directory:

```bash
aas-readable machine.aasx out/ --overwrite
```

Export YAML only for agent and LLM workflows:

```bash
aas-readable machine.aasx out/ --output yaml
```

Export both Markdown and YAML:

```bash
aas-readable machine.aasx out/ --output both
```

## Input Shapes

### Plain AAS JSON

The exporter supports environments that directly contain:

- `assetAdministrationShells`
- `submodels`

### Wrapped Records

It also supports records like this:

```json
{
  "canonical_text": "...",
  "aas": {
    "assetAdministrationShells": [],
    "submodels": []
  }
}
```

If `canonical_text` is present, it is included in `llm-context.md` for Markdown outputs and `llm-context.yaml` for YAML outputs.

## Behavior Summary

- the exporter reads one input file per invocation
- submodel names can be filtered with repeated `--include`
- submodel filenames are slugified and deduplicated
- nested submodel elements are rendered recursively
- Markdown and YAML are generated from the same normalized internal model

## Example Export

The repository includes a generated example in [examples/meng-app-aas](examples/meng-app-aas).

That folder contains:

- [index.md](examples/meng-app-aas/index.md)
- [llm-context.md](examples/meng-app-aas/llm-context.md)
- one Markdown file per submodel

When YAML output is selected, exports also include:

- `index.yaml`
- `llm-context.yaml`
- one YAML file per submodel

The example was generated from a related AAS dataset containing plain JSON environments and wrapped JSON records with `canonical_text`.

## Internal Model

The exporter follows a deliberately small pipeline:

1. Load the input source.
2. Normalize it into an internal document model.
3. Render deterministic Markdown, YAML, or both.

This keeps parsing concerns separate from rendering concerns, which is important for stable diffs and stable AI context.

Renderer responsibilities:

- `markdown.py`: human-readable review and prompt outputs
- `yaml_render.py`: structured outputs for agents and automation
- `exporter.py`: input loading, normalization, and file writing

## Current Scope

Included:

- AAS JSON export
- wrapped JSON export with `canonical_text`
- optional `.aasx` export via BaSyx
- recursive rendering of nested submodel elements
- `index.md`
- `llm-context.md`
- YAML exports for agent and LLM ingestion

Not included yet:

- specialized renderers for specific IDTA templates
- supplementary file extraction from `.aasx`
- round-trip editing back into AAS
- UI or hosting components

## Development

Run the tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Show CLI help:

```bash
PYTHONPATH=src python3 -m aas_readable.cli --help
```

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE).

## Further Reading

- [docs/research.md](docs/research.md)
- [docs/cli-plan.md](docs/cli-plan.md)
