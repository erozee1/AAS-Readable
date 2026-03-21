# CLI Plan

## Command

```bash
aasx-md-exporter INPUT_PATH OUTPUT_DIR [--include SUBMODEL_NAME] [--overwrite]
```

## Behavior

- read a single `.aasx` package or AAS JSON environment
- extract all submodels from the contained AAS
- filter submodels by `--include` when requested
- write one Markdown file per submodel
- write an `index.md` summarizing the exported asset and linking to submodels
- write an `llm-context.md` file optimized for prompt input

## Output Conventions

### File naming

- slugified submodel display name
- deterministic lowercase filenames
- collision handling by suffixing `-2`, `-3`, and so on

### Markdown shape

Each submodel file should follow this structure:

```md
# Technical Data

## Metadata

- Identifier: `...`
- Kind: `INSTANCE`
- Semantic ID: `...`

## Elements

### Rated Voltage

- Type: `Property`
- Value: `400`
- Unit: `V`
```

The exact field set will vary by submodel element type, but the layout should stay stable so that diffs stay readable.

## Lightweight Architecture

### `cli.py`

Argument parsing and user-facing errors.

### `exporter.py`

Load the source file, normalize it into an internal document model, and write files.

### `markdown.py`

Pure rendering logic. This should stay independent of BaSyx-specific imports where possible.

## Parsing Strategy

Use the BaSyx Python SDK only at the package boundary for `.aasx` input:

1. `AASXReader` reads the package into an object store.
2. iterate identifiable objects and select `Submodel` instances
3. recursively walk submodel elements
4. project them into plain text sections

This keeps the repo light and avoids building a second AAS implementation.

## MVP Boundaries

Include:

- AASX read path
- AAS JSON read path
- per-submodel Markdown export
- recursive handling of common nested submodel elements
- stable filenames, index generation, and LLM context generation

Defer:

- full semantic-id aware formatting
- specialized renderers per IDTA template
- attachment extraction and image embedding
- reverse conversion from Markdown back to AAS
- live server or UI

## Suggested Next Milestones

1. Validate the reader against a real `.aasx` sample for the three target submodels.
2. Add submodel-specific formatters for Technical Data, Documentation, and Carbon Footprint.
3. Export referenced supplementary files into an `assets/` folder and link them from Markdown.
4. Add snapshot tests with representative AASX fixtures.
