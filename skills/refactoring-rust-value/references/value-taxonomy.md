# Value Taxonomy

This taxonomy is a discovery aid, not a checklist that must be filled.

## 1. Architecture and decomposition

Potential value:
- smaller responsibility domains
- reduced god-object/manager centralization
- clearer subsystem boundaries
- fewer hidden cross-layer dependencies
- reduced change blast radius
- better replacement/test seams

Possible origins:
- general redesign
- Rust composition/trait-oriented design
- ownership-driven decomposition

## 2. Ownership and lifetime design

Potential value:
- explicit owner/borrower relationships
- reduced dangling-reference risk
- easier lifecycle reasoning
- ownership transfers visible in APIs
- clearer resource destruction ordering

Rust mechanisms:
- ownership/move
- `&T`, `&mut T`
- lifetimes
- `Box`, `Arc`, `Rc`, `Weak`
- `Drop`

Questions:
- What lifetime relationship was previously implicit?
- Who owned destruction responsibility?
- Did asynchronous/callback code previously rely on timing assumptions?

## 3. State modeling and invariants

Potential value:
- fewer representable invalid states
- state-dependent data bound to the state that owns it
- exhaustive transition handling
- simpler state-space reasoning

Rust mechanisms:
- enums/ADTs
- pattern matching
- newtypes
- typestate
- private constructors/fields

Look for transformations such as:
- boolean flags + nullable fields → enum variants
- integer/string status → enum
- initialization flags → constructors/typestate

## 4. Concurrency design / fearless concurrency

Potential value:
- reduced shared mutable state
- fewer locks or narrower lock scope
- clearer synchronization ownership
- message-oriented data flow
- fewer possible data races in safe code
- clearer thread/task transfer contracts

Rust mechanisms:
- ownership transfer
- `Send` / `Sync`
- `MutexGuard` / `RwLock` guards
- channels
- task ownership
- `Arc`

Important: separate value caused by architectural concurrency redesign from direct type-system enforcement, while allowing both to contribute to the same outcome.

## 5. Error model

Potential value:
- error semantics visible in signatures
- fewer ignored errors
- consistent propagation
- domain-specific error taxonomy
- less sentinel/error-code ambiguity

Rust mechanisms:
- `Result<T,E>`
- `?`
- error enums
- `#[must_use]`

## 6. Nullability and optionality

Potential value:
- optional state is explicit
- callers must structurally handle absence
- less sentinel/null ambiguity

Rust mechanisms:
- `Option<T>`
- pattern matching
- combinators

## 7. API contract strength

Potential value:
- fewer loosely typed parameters
- valid input space narrowed
- units/IDs/roles separated by type
- mutability requirements visible
- ownership semantics visible

Rust mechanisms:
- newtypes
- enums
- references vs owned values
- traits/bounds
- visibility
- builders/typestate

## 8. Resource management

Potential value:
- cleanup tied to ownership
- fewer manual release paths
- fewer partial-initialization cleanup branches
- resource lifetime matches scope/object lifetime

Rust mechanisms:
- RAII/Drop
- owned handles
- guard types

## 9. Unsafe / FFI containment

Potential value:
- memory-safety proof obligations localized
- unsafe assumptions documented at narrow boundaries
- safe API protects the rest of the codebase
- easier targeted review/audit

Measures that may help:
- unsafe modules/functions/blocks count
- unsafe LOC as context only
- number of safe callers behind an unsafe abstraction
- FFI boundary centralization

Do not convert these metrics directly into invented “risk reduction percentages.”

## 10. Control-flow simplification

Potential value:
- callback chains replaced with structured flow
- less inverted control
- fewer hidden reentrancy assumptions
- linear error/resource handling

Possible Rust influences:
- async/await
- ownership-aware task structure
- Result propagation
- iterators

## 11. Data-flow clarity

Potential value:
- fewer mutable aliases
- clearer producer/consumer ownership
- fewer out-parameters
- immutable-by-default transformation pipelines

## 12. Polymorphism and extensibility

Potential value:
- reduced fragile inheritance
- behavior boundaries become explicit
- closed vs open variant sets modeled deliberately
- composition easier to reason about

Rust mechanisms:
- traits
- generics
- enums
- trait objects
- sealed/internal traits where used

## 13. Testability

Potential value:
- smaller units
- pure/state-transition functions
- trait seams
- deterministic task/state ownership
- fewer globals/singletons

Do not attribute this to Rust unless the new Rust design materially enabled it.

## 14. Build/dependency/tooling

Potential value:
- simpler dependency graph
- reproducible build setup
- fewer custom scripts
- integrated formatting/lint/testing/docs

Rust ecosystem mechanisms:
- Cargo
- rustfmt
- Clippy
- cargo test/doc

Treat as ecosystem value, not type-system value.

## 15. Maintainability / evolvability

Potential value:
- compiler points to incomplete changes when adding states/variants
- localized modifications
- explicit contracts reduce reviewer burden
- refactoring becomes safer because invariants are type-checked

Strong evidence may include:
- exhaustive match compiler impact
- trait-bound propagation
- ownership compiler failures during change
- smaller dependency blast radius
