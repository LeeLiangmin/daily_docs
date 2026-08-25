---
name: refactoring-rust-value
description: Analyze substantial C or C++ to Rust refactors and produce a detailed, evidence-backed engineering value report. Use when comparing an old C/C++ implementation with a new Rust implementation to discover architecture and redesign value, Rust-driven design value, ownership and lifetime improvements, type-system and state-modeling value, concurrency-model improvements, unsafe or FFI boundary improvements, API/error-model changes, testability, maintainability, and other important migration outcomes. Prioritize core and representative cases rather than mechanically reviewing every file.
compatibility: Portable Agent Skills format. Works best in coding agents with repository search, git history/diff, code navigation, and optional code-graph or GitNexus-like capabilities.
metadata:
  version: "0.2.0"
  category: "code-analysis"
  output: "markdown-report"
  focus: "c-cpp-to-rust-refactoring-value"
---

# Refactoring & Rust Value Discovery

Analyze a real C/C++ → Rust refactor and write a detailed, human-readable engineering document that explains **what value the refactor created, why that value exists, and which parts are driven or guaranteed by Rust**.

The final deliverable is a narrative Markdown report with concrete old/new code comparisons. This is not a Rust feature inventory, a line-by-line port review, or a generic code-quality checklist.

## Use When

Use this skill when the task involves one or more of the following:

- comparing an old C or C++ implementation with its Rust replacement;
- explaining the engineering value of a migration or rewrite;
- identifying architectural or design improvements introduced during refactoring;
- determining where Rust's ownership model, type system, ADTs, traits, lifetimes, `Send`/`Sync`, message passing, or safe abstractions materially changed the design;
- finding representative migration cases in a large repository;
- producing a reviewable migration-value document for architects, senior engineers, reviewers, or technical leadership.

## Do Not Use When

Do not use this skill for:

- generic Rust-vs-C++ language comparisons without a real migration;
- syntax translation or mechanical source conversion;
- exhaustive review of every changed line when the goal is not value discovery;
- claiming Rust value from feature occurrence alone, such as counting `Option`, `Result`, `Arc`, `Mutex`, enums, or traits;
- pure performance benchmarking unless it is part of a broader refactoring-value analysis.

## Core Model

Analyze the migration in this order:

```text
Old C/C++ design and code
        ↓
New Rust design and code
        ↓
What materially changed?
        ↓
What engineering value was created?
        ↓
Why did that value appear?
        ↓
What evidence proves the claim?
```

Separate **value** from **value origin**.

A value may be architecture simplification, reduced shared state, clearer ownership, fewer invalid states, safer concurrency, clearer API contracts, explicit error semantics, improved resource lifetime, reduced synchronization complexity, localized unsafety, improved testability, or improved maintainability.

A value may originate from one or several sources:

- **General redesign** — language-independent architecture or refactoring improvement.
- **Rust-driven design** — the design changed because Rust naturally encourages or requires a different model.
- **Rust ownership/lifetime model** — ownership, borrowing, moves, lifetimes, RAII/Drop.
- **Rust type system** — ADTs/enums, exhaustive matching, `Option`, `Result`, newtypes, traits, generic bounds, typestate.
- **Rust concurrency model** — `Send`, `Sync`, ownership transfer, task/thread isolation, channels, guards, structured resource ownership.
- **Rust safe/unsafe boundary** — proof obligations become explicit and localized behind safe abstractions.
- **Rust idioms/patterns** — composition, enum-oriented state modeling, iterator/dataflow patterns, actor/task ownership, builder/typestate, trait-based abstraction.
- **Rust ecosystem/tooling** — Cargo, Clippy, rustfmt, tests/docs/build integration, but only when there is concrete engineering impact.

Do not frame Rust merely as an "extra layer" added after redesign. Rust may directly cause or shape the redesign.

## Workflow

### 1. Establish the comparison boundary

Identify, from available repository context:

- old C/C++ source, revision, branch, tag, or commit range;
- new Rust source, revision, branch, tag, or commit range;
- subsystem or migration boundary;
- architecture docs, issues, tests, benchmarks, CI data, or migration notes when available;
- intended report scope and audience if already specified.

Do not block the analysis waiting for a perfect one-to-one file mapping. Refine the mapping as evidence accumulates.

### 2. Build a migration map before deep analysis

For a non-trivial repository, first establish a coarse system map:

- top-level modules and subsystems;
- core entry points and execution flows;
- high fan-in/fan-out components;
- important public/internal APIs;
- central state holders and managers;
- thread/task boundaries and synchronization points;
- FFI and `unsafe` boundaries;
- large deletions, additions, renames, and structural changes in git history.

Use repository search, symbol/reference navigation, git history, call graphs, dependency graphs, or code-graph tools. If GitNexus or a similar graph/indexing tool is available, use it for **discovery and prioritization**, not as the sole proof of a value claim. See [GitNexus integration](references/gitnexus-integration.md).

For quick git context, the optional helper is [scripts/collect-git-context.sh](scripts/collect-git-context.sh).

### 3. Discover value candidates broadly

Look for semantically meaningful changes such as:

- shared mutable object graphs → explicit ownership graphs;
- manager-heavy designs → smaller responsibility/ownership boundaries;
- callback-driven lifecycle → structured task/resource lifetime;
- lock discipline → single-owner or message-passing models;
- flag/null combinations → explicit enums/ADTs/state machines;
- raw/weak lifetime assumptions → owned or borrowed relationships;
- error codes/sentinels → typed errors and explicit propagation;
- inheritance-heavy structures → traits/composition/enum dispatch;
- global or mutable state → scoped state ownership;
- scattered unsafe operations → contained FFI/unsafe abstractions;
- manually coordinated resources → RAII/Drop-owned resources;
- broad APIs → narrower typed contracts;
- tangled tests/integration setup → smaller testable units.

Use [value-taxonomy.md](references/value-taxonomy.md) as a discovery aid, not a checklist that must be filled.

### 4. Rank candidates; do not analyze everything equally

Large migrations may contain hundreds of changes. Rank candidates by:

- architectural/core-path importance;
- semantic magnitude of the design change;
- relevance to reliability, concurrency, lifecycle, state, API, or maintainability;
- Rust-specific or Rust-driven significance;
- representativeness across the migration;
- evidence quality;
- ability to explain the change clearly with code.

Prefer deep analysis of high-value cases. Supporting cases can be shorter. There is **no fixed number of cases**.

Rules:

> Do not cap findings. Do not pad findings.

If there are 4 strong cases, write 4. If there are 18 genuinely important, distinct, evidence-backed cases, write 18.

See [case-selection.md](references/case-selection.md).

### 5. Deep-dive each selected case

For every important case, reconstruct both sides of the change.

#### Old C/C++ side

Explain:

- responsibility and architecture;
- relevant data ownership/lifetime relationships;
- state representation;
- concurrency/synchronization model;
- error/resource semantics;
- hidden assumptions and invariants;
- concrete risks or complexity caused by the design.

Include a concise code excerpt from the real old implementation.

#### New Rust side

Explain:

- new responsibility and architecture;
- ownership/lifetime/data-flow model;
- state and type representation;
- concurrency/task model;
- error/resource semantics;
- which assumptions became explicit or impossible to violate.

Include a concise code excerpt from the real new implementation.

#### Compare the semantics

Do not merely describe syntax. State what changed conceptually:

```text
Before: mutation allowed from many owners under lock discipline
After: state is mutated only by its owning task
```

or:

```text
Before: valid state depended on combinations of flags and nullable pointers
After: valid states are represented directly by enum variants
```

### 6. Attribute the value accurately

For each value claim, ask:

1. What would remain valuable if the new design were implemented in modern C++?
2. Did Rust's constraints or idioms actually push the design toward this structure?
3. Which guarantees are enforced by Rust rather than review, tests, comments, conventions, runtime checks, or external static analysis?
4. Is the benefit architectural, local, or both?
5. What trade-offs were introduced?

A single value may have multiple origins. Do not force a false binary split between "refactoring" and "Rust".

### 7. Require evidence for strong claims

Use this evidence hierarchy:

1. old C/C++ code;
2. new Rust code;
3. call/type/dependency relationships;
4. tests demonstrating changed behavior or constraints;
5. git history and migration commits;
6. issues, bugs, CVEs, design docs, benchmarks, CI evidence.

Strong claims must be traceable to evidence.

> No evidence, no strong claim.

If evidence is incomplete, label the conclusion as **potential value**, **likely interpretation**, or **requires validation**.

Read [evidence-guide.md](references/evidence-guide.md) when confidence is uncertain.

### 8. Extract code for humans, not for archival completeness

For each major case, include a real Before/After comparison.

Prefer 10–40 lines per side where possible. Remove unrelated logging, metrics, boilerplate, and repetitive branches while preserving the semantics required to support the claim. Clearly mark omissions or simplifications. Never invent pseudo-code and present it as source code.

Use this sequence:

```text
Why this case matters
→ Old design
→ Old C/C++ code
→ Hidden assumption / complexity / invariant
→ New Rust design
→ New Rust code
→ What fundamentally changed
→ Value created
→ Why Rust matters here
→ Trade-offs / remaining risks
→ Evidence and confidence
```

Use [case-template.md](assets/case-template.md) for detailed cases and [example-case.md](references/example-case.md) as a depth reference.

### 9. Synthesize system-level patterns

After the case analysis, identify patterns that recur across cases, for example:

- ownership becoming the dominant architecture boundary;
- shared mutation being replaced by message passing;
- state validity moving from conventions to types;
- callback lifetime coupling disappearing;
- error handling becoming part of API contracts;
- unsafe obligations collapsing into a small number of boundaries;
- class hierarchies being replaced by composition/traits/enums;
- clearer testing seams created by responsibility separation.

These patterns should be supported by multiple cases or strong architecture evidence. Do not generalize from a single incidental syntax change.

### 10. Write the final report

The output must be a detailed Markdown document suitable for human review. Use the user's language unless they request another language.

Recommended structure:

1. Title and comparison scope
2. Executive summary
3. Old vs new system overview
4. Value map / index
5. Detailed cases, with as many cases as evidence justifies
6. Cross-case Rust-driven design findings
7. Cross-case general redesign findings
8. Remaining risks and trade-offs
9. Evidence limits and open questions
10. Conclusion

Use [report-template.md](assets/report-template.md) as a starting point, not as a rigid form.

## Rules

- **Value first, feature second.** Never lead with a Rust feature inventory.
- **Compare actual old and new code.** Major claims require both sides whenever possible.
- **Prioritize semantics.** Syntax substitutions alone are usually not valuable findings.
- **No artificial case limit.** Let the evidence determine the count.
- **No artificial case inflation.** Merge duplicate or weak findings.
- **Focus on important/core/representative paths.** Do not spend equal effort on every file.
- **Do not over-credit Rust.** Identify language-independent redesign honestly.
- **Do not under-credit Rust.** Rust may directly reshape architecture and design patterns, not merely add checks afterward.
- **Treat concurrency as architecture, not just mutex replacement.** Analyze ownership, task boundaries, message flow, `Send`/`Sync`, aliasing, and state authority together.
- **Treat types as design.** Enums, newtypes, `Option`, `Result`, traits, typestate, and lifetimes may change what states and APIs are expressible.
- **Audit `unsafe` specially.** Ask which proof obligations remain, where they live, and whether unsafety is more localized than before.
- **Explain trade-offs.** Do not write advocacy copy.
- **Use confidence language.** Distinguish proven, strongly supported, likely, and speculative conclusions.
- **Do not claim quantitative risk reduction without quantitative evidence.** Smaller unsafe surface is not automatically equal to a precise percentage reduction in risk.
- **Write for humans.** Prefer clear narrative and focused code excerpts over raw tool dumps.

## Examples

### Good finding

**Value:** Protocol state is easier to reason about and invalid combinations are no longer representable.

**Before:** C++ encoded state through `state_`, `worker_`, and `stopping_`, with validity maintained by branch logic.

**After:** Rust encodes states as `Idle | Running(Worker) | Stopping`.

**Origins:** Rust-driven redesign + Rust type system + general simplification.

**Evidence:** old struct and transition code, new enum and match-based transition code, state-transition tests.

### Weak finding to reject

> The Rust version uses `Vec`, so it is safer and more maintainable than `std::vector`.

This is normally a mechanical translation, not an engineering-value finding.

### Concurrency finding

**Value:** Scheduler mutation has one authority instead of many lock-coordinated writers.

**Before:** multiple worker threads mutate shared scheduler state under mutex/atomic discipline.

**After:** one Rust task owns the scheduler state; other tasks transfer commands through a channel.

**Origins:** Rust-driven redesign + ownership model + concurrency model + general architecture simplification.

The analysis must explain what `Send`, ownership transfer, exclusive mutation, and task boundaries actually guarantee in this codebase.

## Edge Cases

- **Separate repositories:** Build an old↔new subsystem map from names, responsibilities, APIs, tests, and history. Do not require file-level correspondence.
- **Partial migration:** Analyze only migrated boundaries and explicitly note remaining C/C++ interactions.
- **Heavy FFI:** Treat the safe wrapper boundary and proof obligations as a primary case if architecturally important.
- **Mostly mechanical translation:** Say so. A migration may have limited redesign value while still gaining specific Rust guarantees.
- **Radical redesign:** Do not force line-by-line correspondence. Compare responsibilities, invariants, data flow, state authority, and behavior.
- **Performance trade-off:** If ownership or safety changes add allocation, reference counting, copies, synchronization, or indirection, include the trade-off when evidenced.
- **Insufficient evidence:** Produce a partial report with explicit evidence gaps rather than inventing certainty.
- **Very large repositories:** Use graph/index tools and git history to narrow attention, then verify each final case in source.

## References

Load these only as needed:

- [Value taxonomy](references/value-taxonomy.md) — candidate/value discovery categories.
- [Case selection](references/case-selection.md) — prioritization and depth rules.
- [Evidence guide](references/evidence-guide.md) — confidence and claim discipline.
- [GitNexus integration](references/gitnexus-integration.md) — large-repository discovery strategy.
- [Example case](references/example-case.md) — example analytical depth.
- [Report template](assets/report-template.md) — final Markdown report structure.
- [Case template](assets/case-template.md) — per-case deep-dive structure.
- [Finding schema](assets/finding.schema.yaml) — optional structured working representation.
