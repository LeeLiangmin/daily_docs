# Value Qualification

## Purpose

Not every difference is an unconditional improvement. Qualify each claimed value so the report distinguishes structural gains from scope reductions, trade-offs, and compatibility changes.

## Primary value classes

### Structural Improvement

The system becomes simpler or clearer without intentionally removing required capability.

Examples:
- one owner replaces many lock-coordinated writers;
- duplicate state flags collapse into one state model;
- parser/storage responsibilities become separated.

### Safety / Correctness Improvement

A concrete class of misuse, invalid state, race, lifetime error, or proof obligation is removed or statically constrained.

Examples:
- borrowed reference cannot outlive owner in safe Rust;
- enum prevents invalid flag combinations;
- safe abstraction localizes unsafe FFI obligations.

### Maintainability / Reasoning Improvement

Human reasoning, review, rollback, synchronization, or change-impact burden is materially reduced.

Prefer evidence such as mechanisms removed, branches eliminated, ownership authority centralized, or tests made more local.

### Rust-Driven Redesign

Rust's ownership/type/concurrency/idiomatic model materially shaped the new design itself.

This is an origin/qualification, not a claim that another language could not express the design.

### Conditional Simplification

Complexity disappears because the product or compatibility scope was narrowed.

Example:

```text
MBCS + wchar_t + ICU support → UTF-8 only
```

The simplification is real, but its net value depends on whether the removed capability is actually unnecessary for the target users.

Always state the condition.

### Compatibility Change

Behavior/API/failure semantics changed. This may be acceptable, required, or beneficial, but is not automatically a value.

Examples:
- `SI_INSERTED` / `SI_UPDATED` no longer exposed;
- append-load semantics become replace-load semantics;
- newline format changes.

### Trade-off / Cost

A benefit introduces a cost or the migration accepts a cost.

Examples:
- cloning instead of zero-copy view;
- `Arc` reference counting;
- additional dependency;
- lost recoverable OOM semantics.

## Net-value rule

Do not write:

> Feature X was removed, therefore the design improved.

Write:

> Because the target scope is UTF-8-only, the converter/template subsystem is no longer required. This is a conditional simplification: it reduces maintenance complexity only if legacy encoding support is outside the required compatibility scope.

## Value versus consequence

A consequence is not necessarily a separate value.

Example:

```text
Root value: ownership model removes pointer-stability protocol
Consequences:
- DeleteString disappears
- rollback shrinks
- API warnings disappear
- UAF misuse path disappears
```

Use qualification at the root-value level, then list consequences as evidence.

## Suggested labels

Use labels only when they help the reader:

- Structural
- Safety
- Maintainability
- Rust-driven
- Conditional
- Compatibility
- Trade-off

Avoid fake scoring precision.
