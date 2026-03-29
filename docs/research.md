# Research Notes

## Product Definition

`AAS-Readable` is a lossless semantic compilation layer for Asset Administration Shell data.

It converts AAS and AASX from an interoperability-oriented exchange format into deterministic engineering representations that agents and LLM systems can use without losing exact facts.

## Design Direction

The redesign in `0.4.0` follows four principles:

1. preserve before compressing
2. separate transport structure from engineering facts
3. keep source traceability
4. derive prompt views from structured views, never the other way around

## Why The Earlier Approach Failed

The earlier package centered prompt-oriented summaries and heuristic engineering digests. That caused:

- exact IDs to be dropped or rewritten
- numeric facts to be blurred
- sensors and end effectors to be confused
- unresolved semantic references to leak into prompt text

The new design instead treats the lossless document IR as the only source of truth.

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

- agentic manufacturing software search
- AAS-derived retrieval corpora
- digital twin review workflows
- GraphRAG preparation
- deterministic LLM evaluation against AAS facts
