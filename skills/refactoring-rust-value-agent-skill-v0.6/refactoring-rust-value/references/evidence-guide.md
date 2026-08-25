# Evidence Guide

## Evidence hierarchy

### Strong evidence
- paired old/new source showing the semantic change
- call graph/process trace supporting centrality or flow change
- tests demonstrating new behavior/contract
- git commits/messages documenting migration intent
- issue/CVE/bug history directly tied to the old design
- compiler-enforced constraint clearly visible in type signatures

### Supporting evidence
- architecture docs
- module dependency graph
- benchmark/CI results
- code comments
- code ownership/change frequency

### Weak evidence
- name similarity
- raw LOC reduction without semantic context
- language feature presence by itself
- generic claims about Rust

## Claim discipline

Use these labels mentally or explicitly when useful:

- **Observed:** directly visible in code/history.
- **Inferred:** strongly suggested by architecture and behavior.
- **Counterfactual:** hypothetical modern-C++ or alternate-design comparison used only for attribution calibration.
- **Hypothesis:** plausible but not sufficiently proven.

Example:

Bad:
> Rust eliminated use-after-free in this subsystem.

Better when evidence is partial:
> The new safe Rust path removes the raw-pointer lifetime relationship visible in the old callback path. This substantially narrows the UAF mechanism represented by this code, although the surrounding FFI/unsafe paths still require separate review.

## Before/after traceability

For every deep-dive case capture:

- old file + symbol
- new file + symbol
- relevant revision/commit where available
- old excerpt
- new excerpt
- optional process/call-chain references
- tests/issues/docs that support interpretation

## Quantitative claims

Use numbers only when collected from actual evidence.

Good:
- “The old manager had 37 call sites; the new interface exposes 8 public operations.”
- “Unsafe code is confined to 4 modules.”

Bad:
- “Safety improved by 85%.”
- “Maintenance cost is 60% lower.”

## Missing evidence

If old/new mapping is uncertain, state it and continue with well-supported cases rather than forcing a conclusion.


## Actual baseline vs counterfactual

The default evidence chain is:

1. actual legacy C/C++ code and behavior;
2. actual Rust code and behavior;
3. optional modern-C++ counterfactual.

Never write as though an idealized C++17/20/23 solution was present in the legacy system. If the old code predates those facilities, targets older toolchains, or carries compatibility constraints, preserve that historical reality.

A counterfactual answers only questions such as:
- Is this capability unique to Rust?
- Is the value language-independent but Rust made it idiomatic?
- Which guarantees would still rely on discipline in a comparable C++ design?

It does **not** answer whether the actual migration was valuable. That is established by actual-before/actual-after evidence.
