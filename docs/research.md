# Research Notes

## Current Conclusion

For modern frontier models, raw AAS JSON is the default baseline for direct reasoning.

`AAS-Readable` should therefore be treated as an **optional specialist transform layer**, not as an automatically superior runtime replacement for raw JSON.

## What The Benchmark Changed

The recent MEng evaluation showed:
- raw AAS JSON remains very strong for direct reasoning on frontier models
- transformed views are not automatically better just because they are cleaner
- `agent` can still be useful for explicit structured export and controlled downstream tasks
- `brief` is compact, but the metrics do not justify it as the default reasoning input

That shifts the product position:
- keep the package for control, traceability, and deterministic transforms
- stop claiming default runtime superiority over raw JSON

## Product Definition

`AAS-Readable` is a lossless transformation and export layer for Asset Administration Shell data.

It converts AAS and AASX from an interoperability-oriented exchange format into deterministic engineering representations for:
- export
- audit
- benchmarking
- explicit tool and agent integrations
- controlled downstream transforms

## Design Direction

The `0.4.0` design still follows these principles:

1. preserve before compressing
2. separate transport structure from engineering facts
3. keep source traceability
4. derive compact views from structured views, never the other way around

## Relevance Policy

First-class engineering facts:
- identifiers and names
- exact property values
- units and numeric values
- compatibility lists
- operation-like elements
- source paths

Canonical-only facts unless requested:
- raw semantic refs
- qualifiers
- low-level references
- wrapper metadata

Prompt-time noise to remove after parsing:
- AASX package scaffolding
- repetitive metamodel wrappers
- thumbnail metadata
- transport-only containers

## Intended Users

The package is primarily useful for:
- deterministic AAS exports
- engineering review workflows
- AAS-derived QA fixtures and benchmarks
- agent/tool handoff formats
- controlled downstream processing where reproducibility matters
