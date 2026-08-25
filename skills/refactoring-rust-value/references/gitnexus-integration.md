# GitNexus Integration Guide

GitNexus is optional. Use it as a large-repository discovery accelerator, not as the source of truth for value claims.

## When to use

Especially useful when:
- repository is large
- subsystem mapping is unfamiliar
- there are many potential migration hotspots
- call/dependency flow matters
- old/new code contains renamed or reorganized modules

## Setup examples

From the repository root:

```bash
npx gitnexus analyze
```

For editor/MCP setup, GitNexus currently documents:

```bash
npx gitnexus setup
```

If already indexed, do not re-index unnecessarily.

## Useful discovery questions

Ask the graph/code-intelligence layer for:

- architectural clusters / functional communities
- core entry points
- major execution processes
- high fan-in/fan-out symbols
- central state holders
- cross-area dependencies
- scheduler/network/storage/runtime process traces
- impact radius around changed core symbols

## Recommended two-stage use

### Stage A — Graph discovery

Use graph results to build a candidate list:

```text
candidate: scheduler state ownership
why: central process + many callers + large redesign
old area: ...
new area: ...
```

### Stage B — Source verification

For every selected candidate, inspect:
- real old source
- real new source
- git diff/history
- tests/issues/docs

Only then write a value claim.

## What not to do

Do not write:
> “GitNexus says this module is important, therefore the refactor created high value.”

Instead write:
> “The scheduler is on the central request path. Source comparison shows the old implementation allowed multiple workers to mutate shared scheduler state under lock, while the new design gives state ownership to one task and uses channels for mutation requests...”

The graph explains *where to look*. The source explains *what value exists*.
