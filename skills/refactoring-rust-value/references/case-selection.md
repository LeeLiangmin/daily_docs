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

4. **Rust-driven nature**
   - would this redesign naturally arise from Rust's constraints/idioms?
   - is a new invariant directly encoded/enforced?

5. **Representativeness**
   - is this an example of a broader project-wide pattern?

6. **Evidence quality**
   - old + new source available?
   - history/tests/issues/call graph available?

7. **Explanatory quality**
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
priority ≈ importance × semantic_change × value_strength × evidence_quality
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
