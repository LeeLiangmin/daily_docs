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


## 16. Complexity collapse / deleted reasoning burden

Potential value:
- an old representation invariant disappears entirely
- several helper mechanisms become unnecessary together
- rollback/state synchronization/manual lifetime protocols are deleted
- reviewers no longer need to reason across distant code paths to prove correctness

Look for clusters of deleted or simplified mechanisms, not just LOC reduction. Ask what old code existed solely because of the previous design model.

This category often deserves higher priority than a locally strong Rust feature substitution because it captures system-level refactoring value.

## Domain-aligned representation

Look for migrations where the new representation expresses the domain concept directly instead of inferring it from incidental storage/container topology.

Examples:

```text
adjacent equal keys in multimap → EntryValue::Single | Multi
integer tag + payload pointer → enum variant with payload
flag combinations → state enum
nullptr sentinel → Option<T>
container position/order convention → explicit relationship/state
```

Potential value:
- fewer implicit representation invariants;
- state transitions concentrated in one model;
- less defensive checking and topology-dependent logic;
- code review can reason in domain terms rather than storage mechanics.

Do not claim this is Rust-exclusive. Attribute Rust when ADTs/pattern matching/ownership materially shaped the design or enforce the representation.

## Conditional simplification

Look for complexity collapse caused by intentionally narrowing requirements, such as dropping old encodings, platforms, ABI modes, dynamic plugin formats, or recovery semantics.

This is real engineering simplification, but qualify it as conditional on the removed capability being unnecessary for the target scope.

## Rust-native design-pattern lens

When the new design appears to follow a Rust-native pattern, use [rust-design-patterns.md](rust-design-patterns.md) to decide whether that pattern is a real value source or only an implementation idiom. Patterns should strengthen causal analysis, not create a separate checklist chapter.
