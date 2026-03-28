# CLI Contract

This document describes the current CLI behavior of `aas-readable`.

## Intent

The CLI is designed to help engineers turn AAS data into outputs that are easier to use with:

- LLM prompts
- agent pipelines
- Git review
- lightweight documentation

## Command

```bash
aas-readable INPUT_PATH OUTPUT_DIR [--include SUBMODEL_NAME] [--overwrite] [--output {markdown,yaml,both}]
```

## Defaults

- default output format: `markdown`
- default behavior: export all submodels
- output directory must be empty unless `--overwrite` is passed

## Inputs

Supported input types:

- `.json`: plain AAS environments
- `.json`: wrapped records with the AAS stored under `aas`
- `.aasx`: AASX packages when the `aasx` extra is installed

Wrapped JSON shape:

```json
{
  "canonical_text": "...",
  "aas": {
    "assetAdministrationShells": [],
    "submodels": []
  }
}
```

## Outputs

### `--output markdown`

Writes:

- one `.md` file per exported submodel
- `index.md`
- `llm-context.md`

Use this when the main goal is:

- review
- prompting
- Git diffs

### `--output yaml`

Writes:

- one `.yaml` file per exported submodel
- `index.yaml`
- `llm-context.yaml`

Use this when the main goal is:

- agent ingestion
- structured downstream processing
- workflows that benefit from explicit nesting

### `--output both`

Writes both artifact sets.

Use this when a workflow needs:

- human-readable review output
- structured agent-facing output

## Filtering

`--include` matches submodel names after normalization.

Normalization rules:

- lowercase the name
- remove non-alphanumeric characters

Example:

- `Operational Data`
- `operationaldata`
- `operational-data`

All match the same submodel.

## Output Conventions

- filenames are lowercase and slugified
- filename collisions are resolved with `-2`, `-3`, and so on
- nested submodel elements are rendered recursively
- wrapped `canonical_text` is included in the LLM-context artifact for the selected output format

## Internal Structure

The CLI uses a small pipeline:

1. load input
2. normalize it into an internal document model
3. render Markdown, YAML, or both

Current module responsibilities:

- `cli.py`: argument parsing and user-facing errors
- `exporter.py`: load, normalize, and write outputs
- `markdown.py`: Markdown rendering
- `yaml_render.py`: YAML rendering

## Non-Goals

The CLI does not currently try to provide:

- round-trip editing back into AAS
- live dashboards
- attachment extraction
- template-specific semantic formatting
