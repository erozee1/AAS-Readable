# Research Notes

## AAS in Industry 4.0

The Asset Administration Shell (AAS) is the standard information model for an industrial digital twin. In practice, it provides:

- a stable identity for an asset
- a structured container for submodels
- a standard way to exchange and query industrial asset data

That matters because most factory data is fragmented across MES, SCADA, PLM, ERP, PDFs, spreadsheets, and vendor portals. AAS is the normalization layer that makes a digital thread portable instead of application-specific.

Plattform Industrie 4.0 described the AAS on September 24, 2020 as both the virtual image and interoperable communication interface of a hardware or software component in manufacturing. IDTA later described the AAS specification bundle on June 10, 2025 as the basis for the standardized digital twin in industry.

## What Eclipse BaSyx Adds

Eclipse BaSyx is the most obvious open source implementation layer for this project because it provides AAS-aligned infrastructure rather than only schema files. Relevant pieces:

- repositories and registries for AAS and submodels
- a Web UI for visualizing AAS content
- a Python SDK that can read and write AASX packages

As of March 21, 2026, PyPI shows `basyx-python-sdk` 2.0.0 released on December 5, 2025. The project description explicitly lists reading and writing AASX package files as a supported feature.

## Why Markdown Export Is Useful

An `.aasx` package is a good exchange artifact, but it is not an ergonomic review format for engineers, documentation teams, or Git-based workflows. Exporting each submodel to Markdown immediately enables:

- version control with normal Git diffs
- publication as a static wiki per asset
- indexing by enterprise search and document tooling

This is a useful complement to BaSyx, not a replacement for it.

## First-Pass Submodels

The first pass should focus on submodels that are already legible and useful as documentation:

- Technical Data
- Documentation
- Carbon Footprint

This selection is also aligned with the IDTA submodel-template ecosystem. IDTA announced on August 23, 2022 that published templates included "Generic Frame for Technical Data for Industrial Equipment in Manufacturing", with many more submodels under development. Product Carbon Footprint has since become one of the more visible AAS submodel use cases in the market.

## Open Source Projects Worth Borrowing From

These are not AAS exporters, but they show patterns that fit this repo:

### `json-schema-for-humans`

Strong example of turning structured machine-readable data into readable documentation using a normalized intermediate representation and templates. The main lesson is to keep rendering separate from schema traversal.

### `openapi-markdown`

Good precedent for a tiny CLI that converts a structured spec directly to Markdown and allows custom templates. The main lesson is that CLI ergonomics can stay very small if the rendering contract is clear.

### `yaml2doc`

Useful example of documentation-oriented Markdown generation from structured content. The main lesson is to favor deterministic, plain-text output over complex formatting.

### `aas-core3.0-cli-swiss-knife`

Not a Markdown exporter, but highly relevant because it already converts AAS content into static file structures of directories and JSON files. That validates the general direction: static exports are a legitimate AAS workflow, and Markdown is the next human-readable step.

## Recommended Technical Direction

Keep the first version narrow:

1. Use the BaSyx Python SDK only for loading the AASX package into memory.
2. Normalize the loaded submodels into a tiny internal document model.
3. Render deterministic Markdown files with stable headings and bullet lists.
4. Add template hooks only after the default output proves useful.

The project should not try to solve generic AAS authoring, server hosting, validation, or round-trip editing in the MVP.

## Sources

- BaSyx Python SDK on PyPI: [basyx-python-sdk](https://pypi.org/project/basyx-python-sdk/)
- BaSyx Python SDK AASX tutorial: [tutorial_aasx](https://basyx-python-sdk.readthedocs.io/en/latest/tutorials/tutorial_aasx.html)
- BaSyx Python SDK AASX adapter docs: [aasx adapter](https://basyx-python-sdk.readthedocs.io/en/latest/adapter/aasx.html)
- Eclipse BaSyx Web UI docs: [BaSyx Web UI](https://wiki.basyx.org/en/latest/content/user_documentation/basyx_components/web_ui/index.html)
- Eclipse BaSyx Submodel Registry docs: [BaSyx Submodel Registry](https://wiki.basyx.org/en/latest/content/user_documentation/basyx_components/v2/submodel_registry/index.html)
- Plattform Industrie 4.0 press release, September 24, 2020: [Soft shell, hard centre](https://www.plattform-i40.de/IP/Redaktion/EN/PressReleases/2020/2020-09-24-soft-shell-hard-centre.html)
- IDTA specification bundle announcement, June 10, 2025: [AAS receives security specification](https://industrialdigitaltwin.org/en/news-dates/milestone-for-industrial-digitalisation-asset-administration-shell-standard-receives-security-specification-7010)
- IDTA submodel-template announcement, August 23, 2022: [IDTA submodel templates published](https://industrialdigitaltwin.org/content-hub/idta-submodel-templates-veroeffentlicht-4431)
- `openapi-markdown`: [GitHub](https://github.com/vrerv/openapi-markdown)
- `yaml2doc`: [GitHub](https://github.com/ted-dunstone/yaml2doc)
- `awesome-aas` list including `aas-core3.0-cli-swiss-knife`: [GitHub](https://github.com/aas-core-works/awesome-aas)

