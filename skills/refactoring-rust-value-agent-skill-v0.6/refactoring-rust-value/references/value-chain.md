# Value Chain and Complexity Collapse

## Purpose

Use this guide to move beyond feature comparison and explain why a refactor changed engineering reality.

## Value chain

For a strong case, reconstruct:

```text
Historical problem / constraint
        ↓
Old design mechanism
        ↓
Complexity and proof obligations
        ↓
New Rust design model
        ↓
What became unnecessary
        ↓
Engineering value
        ↓
Rust's role in shaping/enforcing the result
```

## Complexity collapse

Complexity collapse occurs when changing a core representation or invariant makes a whole family of secondary mechanisms unnecessary.

Examples:

- backing-buffer pointer model → owned semantic values
  - removes pointer-stability rules
  - secondary allocation pools
  - copy/no-copy flags
  - lifetime warnings in public APIs
  - manual rollback tied to buffer replacement

- many lock-coordinated writers → single state owner
  - removes lock-order rules
  - some atomics
  - duplicated synchronization branches
  - callback races around mutation authority

- flags + nullable fields → enum state machine
  - removes invalid combinations
  - validation branches
  - defensive assertions
  - synchronization of duplicated state indicators

## Questions to ask

1. What historical constraint forced the old mechanism to exist?
2. Which code existed only to maintain that mechanism?
3. What did developers have to remember or prove manually?
4. Which of those obligations disappeared in the Rust design?
5. Which obligations remain, perhaps moved to an `unsafe`, FFI, lock, or runtime boundary?
6. Does the new design simplify only implementation, or also API usage and future modification?

## Good conclusion pattern

Avoid:

> Rust replaced raw pointers with String, improving safety.

Prefer:

> The redesign removed the requirement that semantic entries remain views into a stable backing buffer. Once that invariant disappeared, the allocation pool, copy/no-copy decision, pointer-lifetime API contract, and buffer-replacement rollback machinery also became unnecessary. Rust ownership helped shape this owned-value model and safe borrowing enforces the remaining lifetime relationships.
