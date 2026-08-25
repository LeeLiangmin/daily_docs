---
name: refactoring-rust-value
description: Analyze substantial C or C++ to Rust refactors and produce a detailed, evidence-backed engineering value report. Use when comparing an old C/C++ implementation with a new Rust implementation to discover architecture and redesign value, Rust-driven design value, ownership and lifetime improvements, type-system and state-modeling value, concurrency-model improvements, unsafe or FFI boundary improvements, API/error-model changes, testability, maintainability, and other important migration outcomes. Prioritize core and representative cases rather than mechanically reviewing every file.
compatibility: Portable Agent Skills format. Works best in coding agents with repository search, git history/diff, code navigation, and optional code-graph or GitNexus-like capabilities.
metadata:
  version: "0.6.0"
  category: "code-analysis"
  output: "markdown-report"
  focus: "c-cpp-to-rust-refactoring-value"
---

# Refactoring & Rust Value Discovery

Analyze a real C/C++ → Rust refactor and write a detailed, human-readable engineering document that explains **what value the refactor created, why that value exists, and which parts are driven or guaranteed by Rust**.

The final deliverable is a concise but substantial Markdown report with concrete old/new code comparisons. Unless the user explicitly requests another language, the report body must be written in Chinese, keeping only necessary English technical terms, identifiers, API names, and code. This is not a Rust feature inventory, a line-by-line port review, or a generic code-quality checklist.

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

## Output Language and Writing Standard

The report is written for humans, not for tool completeness. Apply these rules at the same priority as evidence and technical correctness.

### Chinese by default

Unless the user explicitly asks for another language, write the report body in Chinese. Keep English only where it improves precision or is the canonical technical form, such as:

- Rust/C++ keywords, types, traits, APIs, symbols, and code;
- fixed technical terms such as ownership, borrow checker, `Send`/`Sync`, RAII, ADT when translating them would be less precise;
- product/library/tool names.

Do not write sentence-level Chinese-English mixtures when clear Chinese exists. Prefer “数据表示从依赖底层缓冲区的指针视图转为由数据模型直接拥有的值” over “pointer-backed representation → owned semantic model” in prose.

### 信、达、雅

- **信 — accurate and trustworthy.** Do not overclaim Rust, do not turn inference into fact, and do not call every change a value. Strong claims need evidence.
- **达 — clear to engineers.** Explain the engineering meaning before introducing jargon. Prefer causal explanation over terminology stacking.
- **雅 — concise and well-shaped.** Use precise, natural prose. Avoid repetitive bullets, slogan-like advocacy, and mechanical template language.

### Structure serves understanding

Do not mechanically emit every possible heading from a template. A case normally needs only enough structure to explain the causal story. Merge sections when a short narrative is clearer.

Rules:

- Prefer 3–5 meaningful subsections for a major case, not 8–10 repeated headings.
- Do not repeat the same claim in the value map, case body, Rust-value section, and conclusion unless each occurrence adds a new level of synthesis.
- Small supporting findings should normally be summarized in a compact subsection or table, not promoted to full cases.
- Use tables only when comparison benefits from tabular form.
- If one paragraph can explain the point clearly, do not split it into many bullets.
- Every paragraph should advance the argument.
- Aim for **deep analysis, compressed expression**.

For detailed style rules see [writing-style.md](references/writing-style.md).

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

### 4. Rank and cluster candidates; do not analyze everything equally

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

Before promoting candidates into report cases, cluster findings that share the same root transformation. Storage ownership, API lifetime, rollback simplification, and pointer-pool removal may be consequences of one deeper redesign rather than four independent cases. See [root-cause-clustering.md](references/root-cause-clustering.md) and [case-selection.md](references/case-selection.md).

Apply a **value-density threshold** before creating a standalone case. A finding normally deserves a full case only if it is an architectural root cause, removes substantial complexity, improves a core invariant, changes a cross-cutting API contract, or removes a high-consequence failure/coordination class. Otherwise keep it as supporting evidence.

Apply **consequence suppression**: if a finding is mainly a downstream effect already explained by a stronger root case, incorporate it into that case instead of promoting it again.

Apply a **final case-consolidation pass** after drafting the candidate cases. Ask whether two cases share the same root cause, old proof obligation, and Rust redesign. If yes, merge them unless the second case changes a distinct public contract or has independent system importance. Public API lifetime changes are often consequences of an ownership-model redesign rather than peer cases.


### 5. Consolidate raw findings into causal cases

After discovery/ranking, group local findings by shared root cause. Prefer one strong case that explains a root transformation and its downstream consequences over several repetitive cases.

Use this test:

> If the deeper design change had not happened, would this local improvement still exist?

If not, treat it as a consequence of the root case unless it has independent architectural importance. Do not merge findings merely because they use the same Rust feature.

See [root-cause-clustering.md](references/root-cause-clustering.md).

### 6. Deep-dive each selected case

For the strongest cases, analyze a **value chain**, not just a before/after feature substitution:

```text
Historical problem / constraint
        ↓
Old design mechanism
        ↓
Complexity and proof obligations it creates
        ↓
New Rust design model
        ↓
What became unnecessary
        ↓
Engineering value created
        ↓
How Rust shaped or enforces the result
```

A particularly valuable finding is **complexity collapse**: one design change removes an entire family of mechanisms that previously existed only to maintain an old invariant or representation. Examples include buffer pools, copy/no-copy flags, rollback code, lock-order protocols, callback-lifetime rules, duplicated state flags, or widespread error-code plumbing.

Ask explicitly:

- What no longer needs to exist?
- What no longer needs to be reasoned about?
- Which old proof obligations disappeared, and which remain?
- Did one new design decision eliminate several secondary mechanisms?

See [value-chain.md](references/value-chain.md).



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

### 7. Attribute the value accurately

Use this comparison order:

```text
A. Actual legacy C/C++ baseline
        ↓
B. Actual Rust result
        ↓
C. Optional modern-C++ counterfactual
        ↓
D. Value-origin attribution
```

**A and B are the primary analysis. C is only a calibration tool.** Never replace the real legacy codebase with an idealized modern-C++ rewrite. The migration happened from the code that actually existed, including its historical constraints, conventions, APIs, compiler targets, compatibility burden, and engineering practices.

For each value claim, ask:

1. What problem, constraint, or complexity existed in the actual legacy C/C++ implementation?
2. What materially changed in the actual Rust implementation?
3. What complexity, proof obligation, coordination rule, rollback path, or special-case machinery no longer needs to exist?
4. Did Rust's constraints or idioms directly push the design toward this structure?
5. Which guarantees are now encoded/enforced by Rust rather than comments, review, tests, runtime checks, discipline, or external analysis?
6. Only if attribution is ambiguous: could modern C++ express a comparable design, and if so, what does that change about the origin claim?
7. What trade-offs were introduced?

A single value may have multiple origins. Do not force a false binary split between "refactoring" and "Rust".

Principle:

> Reality first. Counterfactual second. Attribution third.

### 8. Require evidence for strong claims

Classify important statements as:

- **Observed** — directly visible in source, tests, history, build output, or graph evidence.
- **Inferred** — a strong engineering interpretation derived from observed evidence.
- **Counterfactual** — a hypothetical comparison used only to calibrate value origin, never to replace the actual baseline.

Keep these categories mentally distinct even when the final prose is smooth. A counterfactual must never be presented as something the legacy project actually did or could have adopted without cost.


Use this evidence hierarchy:

1. old C/C++ code;
2. new Rust code;
3. call/type/dependency relationships;
4. tests demonstrating changed behavior or constraints;
5. git history and migration commits;
6. issues, bugs, CVEs, design docs, benchmarks, CI evidence.

Strong claims must be traceable to evidence.

> No evidence, no strong claim.

Any **quantitative structural claim** must state its counting method or scope. Do not write “removed ~200 lines”, “192 pointer sites”, or “700+ lines of conversion code” unless the report explains what was counted, which files/symbols/patterns were included, and whether comments/tests/generated code were excluded. Prefer reproducible counts over impressive-looking numbers.

Treat **behavioral compatibility** as scoped evidence, not a binary property. Passing a Rust test suite proves only the exercised Rust behavior unless tests are mapped to the legacy implementation and executed with matching outcomes. Use wording such as “在已覆盖的 UTF-8 场景内提供兼容性证据” when full parity is not established.

If evidence is incomplete, label the conclusion as **potential value**, **likely interpretation**, or **requires validation**.

Read [evidence-guide.md](references/evidence-guide.md) when confidence is uncertain.

### 9. Extract code for humans, not for archival completeness

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

### 10. Qualify values and synthesize system-level patterns

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

Qualify each value before presenting it as an improvement. Distinguish structural/safety/maintainability improvements from conditional simplifications, compatibility changes, and trade-offs. Feature removal is not automatically value. See [value-qualification.md](references/value-qualification.md).

Then synthesize dominant **Transformation Theses** when the evidence supports them. Do not force a fixed number. Prefer a hierarchy over a flat list:

- **Primary transformation** — the deepest change that explains the largest part of the migration value;
- **Secondary transformation** — an independent but smaller systemic redesign;
- **Consequence** — a result of another thesis, not a peer thesis;
- **Independent redesign** — useful change that does not belong to the primary causal chain.

A thesis should connect historical constraints, the old design model, the root Rust redesign, complexity collapse, and system-level outcomes. See [transformation-thesis.md](references/transformation-thesis.md).

### 11. Write the final report

The output must be a human-readable Markdown document. Unless the user explicitly requests another language, write it in Chinese with only necessary English technical terms.

Recommended shape, not a rigid form:

1. 标题与分析范围
2. 执行摘要：先讲最核心的 Transformation Thesis
3. 旧系统与新系统的关键设计变化
4. 系统级 Transformation Thesis / 价值地图
5. 聚合后的核心案例
6. 必要的 supporting findings / Rust 驱动设计总结
7. Trade-offs、兼容性变化与剩余风险
8. 证据边界与结论

If the report becomes repetitive, merge sections. Do not preserve headings merely because the template contains them. Use [report-template.md](assets/report-template.md) as a starting point, not as a rigid form.

Before finalizing, perform a **compression pass**:

- merge a consequence case into its root case when the causal story is already established;
- remove repeated thesis statements from later sections;
- downgrade local implementation cleanups to Supporting Findings;
- delete claims that do not change the reader's engineering judgment;
- prefer one strong paragraph over multiple synonymous bullets.

The default report should normally fit into six conceptual sections: executive thesis, system before/after, core cases, supporting findings, trade-offs/evidence limits, and conclusion. Add more only when the repository genuinely requires it.

## Rules

- **Value first, feature second.** Never lead with a Rust feature inventory.
- **Compare actual old and new code.** Major claims require both sides whenever possible.
- **Prioritize semantics.** Syntax substitutions alone are usually not valuable findings.
- **No artificial case limit.** Let the evidence determine the count.
- **No artificial case inflation.** Merge duplicate or weak findings.
- **Cluster by root cause, not Rust feature.** Multiple local improvements caused by one representation/ownership/state redesign normally belong in one causal case.
- **Separate root value from consequences.** Removed helpers, warnings, rollback branches, and misuse paths may be evidence/consequences of one deeper value rather than independent values.
- **Qualify simplifications.** Scope reduction can create real complexity collapse, but label it conditional when value depends on removed capabilities being unnecessary.
- **Build a transformation thesis.** For substantial migrations, explain the dominant causal redesign story before listing individual values.
- **Focus on important/core/representative paths.** Do not spend equal effort on every file.
- **Actual legacy baseline first.** The primary comparison is the real old C/C++ code versus the real Rust result; modern C++ is only an optional attribution calibration.
- **Do not over-credit Rust.** Identify language-independent redesign honestly.
- **Do not under-credit Rust.** Rust may directly reshape architecture and design patterns, not merely add checks afterward.
- **Treat concurrency as architecture, not just mutex replacement.** Analyze ownership, task boundaries, message flow, `Send`/`Sync`, aliasing, and state authority together.
- **Treat types as design.** Enums, newtypes, `Option`, `Result`, traits, typestate, and lifetimes may change what states and APIs are expressible.
- **Audit `unsafe` specially.** Ask which proof obligations remain, where they live, and whether unsafety is more localized than before.
- **Explain trade-offs.** Do not write advocacy copy.
- **Use evidence-mode language.** Distinguish Observed, Inferred, and Counterfactual reasoning, and use confidence language for uncertain claims.
- **Look for complexity collapse.** Prefer findings where a redesign removes a family of mechanisms, proof obligations, or coordination rules—not merely a syntax construct.
- **Do not confuse language safety with impossibility of using escape hatches.** Safe Rust guarantees apply where code remains in safe Rust; `unsafe` and FFI require separate proof obligations.
- **Use technically precise Rust claims.** `Result` can still be deliberately discarded; `Send`/`Sync` do not mean shared mutation needs no synchronization; ordinary allocation failure is not simply a normal recoverable panic; `std::variant`/`std::expected` and similar modern-C++ facilities may provide comparable representations.
- **Do not claim quantitative risk reduction without quantitative evidence.** Smaller unsafe surface is not automatically equal to a precise percentage reduction in risk.
- **Write for humans.** Prefer clear narrative and focused code excerpts over raw tool dumps.
- **Chinese by default.** Unless the user asks otherwise, write the report body in Chinese; keep only necessary English technical terms and identifiers.
- **信、达、雅.** Accurate first, understandable second, concise and natural throughout.
- **Analysis deeper, expression shorter.** Do not confuse analytical depth with document length.
- **Use value-density threshold.** Weak or local findings belong under Supporting Findings, not as full cases.
- **Suppress duplicate consequences.** Do not restate one root transformation as multiple peer cases.
- **Prefer thesis hierarchy.** Distinguish primary/secondary transformations from consequences and independent redesigns.
- **Complexity reduction is not observed bug prevention.** Say a state dimension or proof obligation disappears unless bugs/issues/tests prove a concrete failure class.
- **Performance complexity claims require care.** Do not present O(n) → O(n) representation cleanup as an asymptotic improvement; describe semantic alignment or reasoning simplification instead.
- **Behavioral equivalence requires evidence.** Similar test names or source structure are not enough to claim parity; say “supports compatibility” unless tests were mapped and run.
- **Quantitative claims require a method.** Every LOC/count/frequency claim must name the counted files, symbols, patterns, or test set; otherwise keep it qualitative.
- **Do not conflate safe Rust with zero memory leaks or zero bugs.** State the specific old failure modes removed by the current representation.
- **Concurrency claims must distinguish type safety from architecture.** `&mut self`/auto traits can restrict unsynchronized mutation without constituting a new concurrent design.
- **One root transformation should usually produce one main case.** API consequences, parser consequences, rollback removal, and helper deletion are supporting evidence unless independently important.

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
- [Root-cause clustering](references/root-cause-clustering.md) — consolidate related findings into causal cases.
- [Value qualification](references/value-qualification.md) — distinguish structural gains, conditional simplifications, compatibility changes, and trade-offs.
- [Transformation thesis](references/transformation-thesis.md) — synthesize system-level causal stories.
- [Evidence guide](references/evidence-guide.md) — confidence, evidence modes, and claim discipline.
- [Value-chain guide](references/value-chain.md) — complexity collapse and causal value analysis.
- [Technical guardrails](references/technical-guardrails.md) — precise Rust/C++ comparison rules and common overclaims to avoid.
- [Writing style](references/writing-style.md) — Chinese-first, 信达雅, concise narrative, and anti-template-bloat rules.
- [GitNexus integration](references/gitnexus-integration.md) — large-repository discovery strategy.
- [Example case](references/example-case.md) — example analytical depth.
- [Report template](assets/report-template.md) — final Markdown report structure.
- [Case template](assets/case-template.md) — per-case deep-dive structure.
- [Finding schema](assets/finding.schema.yaml) — optional structured working representation.
