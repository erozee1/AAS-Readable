# AAS-Readable

`AAS-Readable` converts Asset Administration Shell content into clean Markdown for engineers, analysts, and LLM workflows.

It is meant for the gap between machine-readable digital twins and human-readable insight.

## What It Does

The exporter reads:

- `.aasx` packages
- plain AAS JSON environments
- wrapped JSON records where the AAS is stored under `aas`

It writes:

- one Markdown file per submodel
- `index.md` as a navigation page
- `llm-context.md` as a compact prompt-ready summary

## Why Markdown

AAS content is structured and interoperable, but it is not always easy to inspect directly during engineering work.

Markdown makes a digital twin easier to:

- review in Git
- publish as internal documentation
- index with standard search tools
- compare between revisions
- paste into an LLM without extra cleanup

In practice, this means you can turn an operational twin into something that explains what is currently happening, what changed recently, and which submodels matter.

## Why This Is Useful For LLMs

LLMs work better when the input is compact, hierarchical, and explicit about context.

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

## Installation

`pip install -e .` is only for a local clone of the repository. It is useful for development, but it is not the normal install command for users downloading the tool from GitHub.

### Install From GitHub

JSON-only usage:

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

### Optional `.aasx` Support

If you are installing from a local clone and want `.aasx` support:

```bash
pip install -e '.[aasx]'
```

The optional `aasx` extra installs the Eclipse BaSyx Python SDK.

### Recommended Virtual Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Then run one of the install commands above.

## CLI

```bash
aas-readable INPUT_PATH OUTPUT_DIR [--include SUBMODEL_NAME] [--overwrite]
```

### Examples

Export a JSON environment:

```bash
aas-readable app_aas.json out/
```

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

After installation, verify that the CLI is available:

```bash
aas-readable --help
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

If `canonical_text` is present, it is included in `llm-context.md`.

## Output Layout

```text
out/
  index.md
  llm-context.md
  staticdata.md
  functionaldata.md
  operationaldata.md
  lifecycledata.md
```

Filenames are derived from submodel names and normalized to stable lowercase slugs.

## Example Export

The repository includes a generated example in [examples/meng-app-aas](examples/meng-app-aas).

That folder contains:

- [index.md](examples/meng-app-aas/index.md)
- [llm-context.md](examples/meng-app-aas/llm-context.md)
- one Markdown file per submodel

The example was generated from a related AAS dataset containing plain JSON environments and wrapped JSON records with `canonical_text`.

## How It Works

The exporter follows a deliberately small pipeline:

1. Load the input source.
2. Normalize it into an internal document model.
3. Render deterministic Markdown.

This keeps parsing concerns separate from rendering concerns, which is important for stable diffs and stable LLM context.

## Current Scope

Included:

- AAS JSON export
- wrapped JSON export with `canonical_text`
- optional `.aasx` export via BaSyx
- recursive rendering of nested submodel elements
- `index.md`
- `llm-context.md`

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
