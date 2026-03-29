# CLI Contract

This document describes the current command-line contract for `aas-readable`.

## Purpose

The CLI exists for engineers who want a straightforward way to export Asset Administration Shell (AAS) data into artifacts that are easier to use with:

- LLM prompts
- agent pipelines
- digital twin review workflows
- Git diffs
- semantic search and corpus preparation

## Command

```bash
aas-readable INPUT_PATH OUTPUT_DIR \
  [--include SUBMODEL_NAME] \
  [--overwrite] \
  [--output {markdown,yaml,json,both,all}] \
  [--profile {prompt-compact,agent-structured,diff-ready}]
```

## Inputs

Supported inputs:

- `.json` AAS environment files
- wrapped `.json` records that contain AAS under `aas`
- `.aasx` packages when `aas-readable[aasx]` is installed
- directories containing `.json` and `.aasx` files

Wrapped JSON example:

```json
{
  "canonical_text": "Short natural-language summary",
  "aas": {
    "assetAdministrationShells": [],
    "submodels": []
  }
}
```

## Defaults

- default output format: `markdown`
- default profile: `agent-structured`
- default behavior: export all submodels
- output directory must be empty unless `--overwrite` is passed

## Output Formats

### `--output markdown`

Writes:

- one `.md` file per exported submodel
- `index.md`
- `llm-context.md`

Best for:

- human review
- prompt copy/paste
- Git diffs

### `--output yaml`

Writes:

- one `.yaml` file per exported submodel
- `index.yaml`
- `llm-context.yaml`

Best for:

- structured downstream workflows
- tool handoff
- systems that prefer nested text formats over Markdown

### `--output json`

Writes:

- one `.json` file per exported submodel
- `index.json`
- `llm-context.json`

Best for:

- Python applications
- agent runtimes
- search indexing
- programmatic validation

### `--output both`

Writes:

- all Markdown artifacts
- all YAML artifacts

### `--output all`

Writes:

- all Markdown artifacts
- all YAML artifacts
- all JSON artifacts

This is the recommended option for building reusable AAS corpora.

## Profiles

### `prompt-compact`

Optimized for:

- low-token LLM context
- orchestration prompts
- retrieval summaries

Behavior:

- keeps the highest-signal fields
- emphasizes `prompt_text`, compact key elements, and known gaps

### `agent-structured`

Optimized for:

- machine-facing pipelines
- automation
- richer element payloads

Behavior:

- preserves fields such as path, stable key, semantic IDs, references, numeric facts, and normalized units

### `diff-ready`

Optimized for:

- deterministic review
- Git-based inspection
- structured change comparison

## Directory Exports

When `INPUT_PATH` is a directory, `aas-readable` exports each `.json` or `.aasx` file into a deterministic subdirectory and writes:

- `manifest.json`
- `manifest.yaml` when YAML is requested

This mode is useful for:

- prompt corpora
- retrieval corpora
- AAS dataset audits
- bulk engineering review

## Filtering

`--include` filters submodels by normalized name.

Normalization rules:

- lowercase the name
- remove non-alphanumeric characters

Examples that all match the same submodel:

- `Operational Data`
- `operationaldata`
- `operational-data`

## Output Conventions

- filenames are lowercase and slugified
- collisions are resolved with `-2`, `-3`, and so on
- nested submodel elements are rendered recursively
- wrapped `canonical_text` is carried into the `llm-context` artifact
- directory exports produce deterministic per-file folders plus a manifest

## Non-Goals

The CLI does not try to provide:

- AAS authoring
- round-trip editing back into AAS
- live dashboards
- AAS repository hosting
- registry synchronization
