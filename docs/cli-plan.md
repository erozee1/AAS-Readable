# CLI Notes

The CLI now renders one explicit document `view` at a time.

## Usage

```bash
aas-readable INPUT_PATH OUTPUT_DIR [--include SUBMODEL_NAME] [--overwrite] [--output {markdown,yaml,json,both,all}] [--view {lossless,agent,brief,review}]
```

## Recommended Commands

Lossless JSON:

```bash
aas-readable app_aas.json out/ --output json --view lossless
```

Agent YAML:

```bash
aas-readable app_aas.json out/ --output yaml --view agent
```

Brief Markdown:

```bash
aas-readable app_aas.json out/ --output markdown --view brief
```

Review bundle:

```bash
aas-readable app_aas.json out/ --output all --view review
```

## Output Files

Exports now use:

- `index.*`
- `document.*`
- one file per submodel

The old `llm-context.*` naming is no longer the primary artifact shape.

## View Rules

### `lossless`

- JSON and YAML only
- full canonical IR

### `agent`

- best for structured downstream tools

### `brief`

- best for explicit compact human-readable exports
- not recommended as the default reasoning input for modern frontier models

### `review`

- best for engineers and diffs
