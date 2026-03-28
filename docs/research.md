# Research Notes

This document records the reasoning behind the project direction.

## Current Thesis

`AAS-Readable` is useful because raw AAS data is interoperable but not convenient for engineers using:

- LLMs
- agents
- Git review
- lightweight documentation workflows

The project is not trying to replace AAS-native infrastructure. It is a translation layer between machine-oriented AAS content and engineer-oriented AI workflows.

## Why AAS Matters

The Asset Administration Shell (AAS) is the standard information model for an industrial digital twin. In practice it provides:

- a stable identity for an asset
- a structured container for submodels
- a standard exchange model for industrial asset data

That matters because factory data is normally fragmented across many systems. AAS is the normalization layer that makes the digital twin portable rather than application-specific.

## Why BaSyx Matters

Eclipse BaSyx is the most relevant implementation layer for this project because it provides:

- repositories and registries for AAS and submodels
- a Web UI for AAS content
- a Python SDK that can read and write AASX packages

The project uses BaSyx only at the package boundary for `.aasx` input. It does not try to embed BaSyx concepts deep into the rendering layer.

## Why This Project Exists

An `.aasx` package is a valid exchange artifact, but it is not a good format for:

- prompt context
- Git-based review
- compact engineer-facing summaries

This project adds value by converting AAS into outputs that are easier to:

- inspect
- diff
- summarize
- pass into LLM or agent workflows

## Why Markdown And YAML

Markdown is useful when the priority is:

- readability
- prompting
- manual review

YAML is useful when the priority is:

- explicit structure
- nested data handoff
- downstream agent processing

The project keeps both formats behind one normalization layer so the parsing logic stays separate from presentation.

## Direction Chosen

The project stays intentionally narrow:

1. load `.json` or `.aasx`
2. normalize into a small internal document model
3. render deterministic Markdown, YAML, or both

The project does not currently aim to solve:

- generic AAS authoring
- hosting
- validation tooling
- full semantic-template interpretation
- round-trip editing

## Useful External References

- BaSyx Python SDK on PyPI: [basyx-python-sdk](https://pypi.org/project/basyx-python-sdk/)
- BaSyx Python SDK AASX tutorial: [tutorial_aasx](https://basyx-python-sdk.readthedocs.io/en/latest/tutorials/tutorial_aasx.html)
- BaSyx Python SDK AASX adapter docs: [aasx adapter](https://basyx-python-sdk.readthedocs.io/en/latest/adapter/aasx.html)
- Eclipse BaSyx Web UI docs: [BaSyx Web UI](https://wiki.basyx.org/en/latest/content/user_documentation/basyx_components/web_ui/index.html)
- Eclipse BaSyx Submodel Registry docs: [BaSyx Submodel Registry](https://wiki.basyx.org/en/latest/content/user_documentation/basyx_components/v2/submodel_registry/index.html)
- Plattform Industrie 4.0 press release, September 24, 2020: [Soft shell, hard centre](https://www.plattform-i40.de/IP/Redaktion/EN/PressReleases/2020/2020-09-24-soft-shell-hard-centre.html)
- IDTA specification bundle announcement, June 10, 2025: [AAS receives security specification](https://industrialdigitaltwin.org/en/news-dates/milestone-for-industrial-digitalisation-asset-administration-shell-standard-receives-security-specification-7010)
- IDTA submodel-template announcement, August 23, 2022: [IDTA submodel templates published](https://industrialdigitaltwin.org/content-hub/idta-submodel-templates-veroeffentlicht-4431)
