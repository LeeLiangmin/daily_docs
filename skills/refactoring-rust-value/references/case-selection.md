# Case Selection and Ranking

## Goal

Find the cases that best explain the value of the migration. Do not merely find the largest diffs.

## Signals

Score qualitatively (Low / Medium / High / Critical) across:

1. **System importance**
   - core path?
   - central state/API?
   - affects many callers/processes?

2. **Semantic change**
   - architecture/state/ownership/control-flow changed?
   - or mostly syntax/translation?

3. **Value magnitude**
   - correctness/safety/maintainability/concurrency impact?
   - does it remove an entire family of supporting mechanisms or only simplify one local expression?

4. **Complexity collapse**
   - what code, state, synchronization, rollback, lifetime protocol, or special-case logic became unnecessary?
   - did one redesign eliminate several secondary mechanisms?
   - did the amount of human reasoning required shrink materially?

5. **Rust-driven nature**
   - would this redesign naturally arise from Rust's constraints/idioms?
   - is a new invariant directly encoded/enforced?

6. **Representativeness**
   - is this an example of a broader project-wide pattern?

7. **Evidence quality**
   - old + new source available?
   - history/tests/issues/call graph available?

8. **Explanatory quality**
   - can a human understand the before/after in a focused excerpt?

## Classification

### Critical
Use when a case is core to the architecture or demonstrates a high-consequence redesign with strong evidence.

### Major
Use for substantial subsystem/API/state/lifecycle improvements with clear evidence.

### Supporting
Use for smaller cases that reinforce a broader theme. Keep treatment concise.

## Suggested ranking heuristic

Do not present a fake mathematical precision score to the user. Internally, a useful heuristic is:

```text
priority ≈ importance × semantic_change × complexity_removed × value_strength × evidence_quality
```

Use Rust-specificity as a tie-breaker, not as a reason to discard valuable general redesign.

## Avoid over-selection

Low-value examples unless tied to a larger change:
- container substitutions
- string/type spelling changes
- formatting/tooling-only edits
- mechanical FFI wrappers
- API renames
- one-off `Option`/`Result` conversions without meaningful contract change


## Ranking correction: legacy reality over language novelty

Do not rank a case highly merely because the Rust construct is distinctive. Rank the real engineering consequence. A historical raw-pointer ownership subsystem that disappears may be Critical; a visible Rust allocation-policy difference may only be Supporting if it removes little real complexity.

Modern-C++ counterfactuals do not lower the importance of a real migration outcome. They only calibrate whether the value should be attributed to general redesign, Rust-driven design, or a direct Rust guarantee.

## v0.4 consolidation rule

Ranking happens before and after clustering:

1. rank raw findings enough to discard weak noise;
2. cluster related findings by root transformation;
3. rank the resulting causal cases again.

A cluster can outrank each individual finding because the combined evidence shows system-wide complexity collapse.

Prefer a case whose root transformation explains several downstream mechanisms over several feature-centric cases that repeat the same argument.

## Value qualification during ranking

Do not rank conditional simplifications as high-value merely because much code disappeared. Ask whether the removed capability is outside the required product scope.

Treat compatibility changes and trade-offs as important findings when consequential, but do not count them automatically as positive value.


## v0.5 value-density threshold

A standalone detailed case should normally satisfy at least one of these:

- explains an architectural/root transformation;
- removes a substantial family of mechanisms or proof obligations;
- strengthens a core invariant or ownership/state authority boundary;
- changes a cross-cutting public/internal API contract;
- removes or localizes a high-consequence safety/concurrency/resource failure class;
- represents a pattern repeated across an important subsystem.

If none apply, keep the finding as **Supporting** even when the code difference is interesting. Numeric parsing helpers, one-off conversions, small wrappers, local container substitutions, or isolated formatting/tooling changes usually do not deserve a full case.

## Consequence suppression

After clustering, suppress standalone cases that are mostly consequences of an already-selected root case. Attach them as evidence or sub-findings instead.

Examples:

```text
Root case: pointer-backed storage -> owned values
  ├─ public API lifetime warnings disappear
  ├─ rollback helpers disappear
  ├─ parser can build fresh state
  └─ Reset no longer invalidates external raw pointers
```

These are normally one causal case, not four peer cases.

## Claim-strength correction

Do not rank a case higher merely because the prose can claim a bug was prevented. Without bug/test/issue evidence, describe the structural gain: fewer states, fewer proof obligations, less mutable configuration, clearer domain representation, or smaller unsafe surface.

## v0.6 final consolidation pass

After drafting candidate cases, run one more merge test:

1. Do two cases share the same root transformation?
2. Do they remove the same proof obligation?
3. Would the second case mostly disappear if the first redesign had not happened?
4. Does the second case change an independent public/system contract?

If answers are yes / yes / yes / no, merge the second into the first.

Typical merge:

```text
Root: pointer-backed storage -> owned values
  ├─ public getter lifetime contract
  ├─ parser no longer mutates backing storage
  ├─ rollback helper disappears
  └─ Reset no longer invalidates escaped raw pointers
```

These normally form one ownership/lifetime case.

## Quantitative-evidence correction

A high count does not make a case important. Counts support scope only when the method is explicit. Rank by architectural consequence first; use reproducible counts as evidence, not as the value itself.
