# Root-Cause Clustering and Case Consolidation

## Purpose

A migration often produces many local findings that are consequences of the same deeper redesign. Do not turn every local symptom into a separate case. Cluster findings by shared root cause and present the highest-value causal story.

## Core rule

> One root transformation may explain many local improvements.

Prefer:

```text
Root transformation: backing-buffer pointer model → owned semantic values
  ├─ string pool disappears
  ├─ pointer provenance checks disappear
  ├─ rollback machinery shrinks
  ├─ public pointer-lifetime warnings disappear
  └─ borrowed/owned API becomes explicit
```

Over five separate cases that repeat the same ownership argument.

## Clustering signals

Two findings likely belong in the same case when they share most of these:

- the same historical constraint or old representation;
- the same ownership/state/concurrency authority change;
- the same old proof obligation;
- the same new Rust model;
- one finding is a downstream consequence of another;
- the code changes occur across layers but form one causal chain (storage → API → rollback → tests);
- explaining one without the other would duplicate the same reasoning.

## Split signals

Keep findings as separate cases when:

- they have different root causes;
- they affect independent core subsystems;
- one is a distinct architectural redesign, not merely a consequence;
- they have different trade-offs or compatibility consequences;
- they require materially different evidence to prove;
- merging them would make the case too broad to understand.

## Procedure

1. Create raw findings without worrying about duplication.
2. For each finding, record:
   - historical constraint;
   - old mechanism;
   - new model;
   - value;
   - Rust role.
3. Group findings with the same root transformation.
4. Choose one cluster title that names the architectural or semantic change.
5. Keep cluster members as sub-findings/consequences inside the case.
6. Only promote a cluster member to its own case if it has independent causal importance.

## Root-cause test

Ask:

> If this deeper design change had not happened, would the local improvement still exist?

If **no**, the local improvement is probably a consequence and should usually be clustered.

Example:

```text
Finding A: GetValue no longer returns a raw pointer
Finding B: DeleteString disappears
Finding C: m_strings disappears
Finding D: Reset no longer invalidates external raw pointers
```

If all follow from `pointer-backed semantic model → owned values`, make one Critical case with four consequences.

## Avoid over-merging

Do not merge merely because two cases both use `enum`, `Result`, or ownership. Feature similarity is not root-cause similarity.

Bad merge:

```text
Protocol enum redesign + typed I/O errors
```

They use the type system but solve different semantic problems.

## v0.5 consequence suppression

Clustering is not complete until redundant consequences are suppressed from standalone-case status.

After choosing a root case, review every child finding and ask:

> Does this finding add an independent value chain, or is it evidence that the root transformation worked?

If it is mainly evidence, attach it to the root case. Do not promote it again just because it touches a different file/API.

A useful report can have many findings but relatively few full cases.
