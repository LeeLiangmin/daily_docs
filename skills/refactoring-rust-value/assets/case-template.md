# Case <N> — <Title>

**Priority:** Critical | Major | Supporting  
**Primary area:** <module/subsystem>  
**Confidence:** High | Medium | Low

## Why this case matters

Explain its architectural/runtime importance and why it was selected.

## Before — C/C++ design

Describe the old structure, ownership, state, control flow, or concurrency model.

### Old code

```cpp
// focused real excerpt
```

Source: `<path>:<symbol>`

## Old constraints, assumptions, or problems

Explain concrete issues. When useful:

```text
Implicit invariant:
...
```

## After — Rust design

Describe the new model before discussing Rust features.

### New code

```rust
// focused real excerpt
```

Source: `<path>:<symbol>`

## What changed semantically

Explain the transformation in plain engineering terms.

## Value created

Explain concrete benefits, e.g. architecture, state-space, lifecycle, concurrency, API, testability, maintainability.

## Why this value appeared

### General redesign

What would remain valuable in another language?

### Rust-driven design

Did Rust's model push the architecture/data model toward this shape?

### Rust language/type/ownership/concurrency guarantees

Which constraints are now encoded or enforced, and how?

## Counterfactual: same design in modern C++

Explain which benefits would remain and which guarantees would rely more on conventions, runtime checks, analyzers, or discipline.

## Trade-offs and remaining risks

Be explicit about allocations, Arc/lock overhead, unsafe/FFI, complexity, ergonomics, or limitations.

## Evidence

- old source:
- new source:
- git history:
- tests/issues/docs:
- graph/process evidence:
