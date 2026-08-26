# Rust-native Design Patterns as Value Evidence

Use Rust design patterns as an analysis lens, not as a checklist and not as a dedicated feature-inventory chapter.

The question is not “which Rust patterns appear?” The question is:

> Did a Rust-native pattern materially reshape the migrated design, remove an old proof obligation, make a domain invariant explicit, or simplify a core path?

Only mention a pattern when the old/new code comparison supports a concrete value claim.

## 1. Ownership-oriented data model

Typical shape:

```text
borrowed/raw-pointer object graph
→
owned values + short-lived borrows
```

Possible value:
- lifetime becomes structural rather than procedural;
- pointer-stability protocols disappear;
- cleanup/rollback/provenance mechanisms become unnecessary;
- public API lifetime contracts become simpler.

Do not call this merely “using String/Vec/Box”. Show which old lifetime machinery disappeared.

## 2. Typestate / state encoded in types

Typical shape:

```text
flags + nullable fields + runtime checks
→
state-specific types / enum variants / transition APIs
```

Possible value:
- invalid transitions become unavailable or more explicit;
- state-dependent payloads move into the state representation;
- callers no longer maintain correlated fields manually.

Use “typestate” only when states are actually represented by distinct types/generic states. If the implementation uses an enum, describe it as enum/ADT state modeling rather than inflating the label.

## 3. Newtype pattern

Typical shape:

```text
primitive/string/id reused for many meanings
→
struct UserId(...), Port(...), Bytes(...)
```

Possible value:
- semantic confusion reduced;
- wrong-unit/wrong-identifier mixing becomes a type error;
- validation can be centralized at construction.

Do not count cosmetic wrappers with no invariant or API effect as value.

## 4. RAII / guard pattern

Typical shape:

```text
acquire → manual release on every path
→
resource/guard dropped at scope exit
```

Examples:
- file/socket/resource owner;
- `MutexGuard` / `RwLockGuard`;
- scoped transaction/temporary state guard;
- cleanup object.

Possible value:
- exceptional/early-return cleanup paths disappear;
- “must release” protocol becomes scope-bound;
- lock/resource ownership is represented by a value.

RAII also exists in C++; compare against the actual legacy code, not an idealized modern-C++ rewrite.

## 5. Builder / consuming builder

Typical shape:

```text
mutable object + many Set* calls + order-sensitive configuration
→
configuration value / consuming builder
```

Possible value:
- construction becomes explicit and testable;
- configuration becomes immutable after construction;
- order-sensitive setup state can disappear.

This is usually general redesign + Rust idiom, not a Rust-exclusive capability.

## 6. Iterator/dataflow pattern

Typical shape:

```text
manual index/pointer loop + temporary mutable state
→
iterator pipeline / adaptor-based dataflow
```

Possible value:
- localizes transformation intent;
- reduces loop-control state and boundary logic;
- enables borrow-safe streaming views.

Do not equate iterator use with performance improvement. Focus on control-flow and reasoning simplification unless benchmarks exist.

## 7. Trait-based composition

Typical shape:

```text
inheritance / virtual base / callback table / macro polymorphism
→
traits + generics / trait objects + composition
```

Possible value:
- behavior contracts become explicit;
- data ownership and polymorphism become separate concerns;
- implementation substitution/testing seams become clearer;
- closed/open extension choices become deliberate.

Do not claim traits are inherently better than inheritance. Explain the actual dependency or coupling that changed.

## 8. Enum-oriented dispatch

Typical shape:

```text
tag + payload pointer / sentinel values / container topology
→
enum variants with payloads + match
```

Possible value:
- domain cases become explicit;
- payload validity is tied to variant;
- exhaustive matching exposes unhandled states during change.

This is often a high-value Rust-driven redesign when legacy code reconstructs semantic state from incidental representation.

## 9. Single-owner task / message-passing pattern

Typical shape:

```text
shared mutable manager + locks + callbacks
→
single owner task/actor + channel messages
```

Possible value:
- shared mutable state shrinks;
- lock ordering/protocols disappear;
- mutation authority becomes explicit;
- cross-thread transfer is constrained by `Send`.

Only claim this when the migration actually changes the concurrency architecture. Ordinary `&self`/`&mut self` APIs are not enough.

## 10. Interior mutability as a controlled boundary

Typical shape:

```text
mutable global/shared object or ad-hoc synchronization
→
Cell / RefCell / Mutex / RwLock / OnceLock behind a narrow API
```

Possible value:
- mutation is localized behind an explicit abstraction;
- runtime borrow/synchronization rules are concentrated;
- callers see a smaller mutation surface.

This is not automatically safer or simpler. Evaluate contention, panic/poison/runtime-borrow failure modes and whether the boundary is actually narrower.

## 11. Type-state proof / capability token / guard value

Typical shape:

```text
caller must remember “lock held / initialized / registered / permission granted”
→
a value exists only while that capability is valid
```

Examples:
- lock guards;
- initialized handles;
- registration tokens;
- borrow-scoped access objects.

Possible value:
- a procedural precondition becomes possession of a proof/capability value;
- APIs can require the proof instead of trusting call order.

## 12. Safe abstraction over unsafe/FFI

Typical shape:

```text
raw operation assumptions spread across callers
→
small unsafe core + safe public abstraction
```

Possible value:
- proof obligations are localized;
- invariants are documented at one boundary;
- safe callers cannot directly violate the raw contract.

Count unsafe only as context. The value is the boundary and invariant ownership, not a low unsafe-LOC number by itself.

## 13. Pattern attribution rules

When a pattern appears, classify its role:

- **Design driver** — Rust made this architecture the natural/feasible path.
- **Invariant carrier** — the pattern directly represents an invariant.
- **Enforcement mechanism** — compiler/type/lifetime rules check part of it.
- **Implementation idiom** — improves local clarity but is not a primary migration value.

A report should normally name only patterns in the first three categories. Implementation-only idioms belong in supporting findings unless they remove substantial complexity.

## 14. Pattern evidence template

Use this compact reasoning model:

```text
Legacy mechanism:
  shared manager + lock discipline + callback lifetime notes

Rust-native pattern:
  single-owner task + channel

What changed:
  mutation authority moved to one owner

What disappeared:
  lock ordering + callback lifetime coordination on this path

Value:
  concurrency reasoning and shared-state surface reduced

Rust role:
  ownership transfer + Send + channel API shape the pattern
```

Do not write:

> The project uses the Actor pattern, Builder pattern, Iterator pattern and Newtype pattern.

That is a pattern inventory, not value discovery.
