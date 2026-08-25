# Changelog

## 0.6.0

Convergence release focused on report precision, de-duplication, and evidence discipline.

### Added

- Final case-consolidation pass: one root transformation should normally produce one main case.
- Reproducible quantitative-evidence rules for LOC/symbol/test/call-site counts.
- Canonical claim wording so Executive Summary, case body, and conclusion use the same evidence strength.
- Explicit memory-safety scope and concurrency-scope controls in the finding schema.
- Stronger cross-implementation behavior-parity requirements.

### Changed

- Default report skeleton reduced to six conceptual sections.
- API lifetime, parser purity, rollback removal, and Reset simplification are treated as consequences of an ownership root case unless independently important.
- Rust-only passing tests are no longer sufficient to claim C++↔Rust behavioral equivalence.
- “zero unsafe” no longer supports blanket memory-leak or zero-bug claims.
- Quantitative evidence must include scope and method or be rewritten qualitatively.
- Final prose pass removes repeated theses, low-value claims, and redundant headings.


## 0.5.0

Writing-quality and signal-density release based on the v0.4 `simpleini` evaluation.

### Added

- Chinese-first output as the default report language unless the user explicitly requests otherwise.
- “信、达、雅” as first-class writing rules: accurate, understandable, concise/natural.
- Dedicated `writing-style.md` with anti-template-bloat and claim-strength guidance.
- Value-density threshold before promoting a finding to a standalone case.
- Consequence suppression so downstream effects remain evidence of a root case instead of duplicate peer cases.
- Thesis hierarchy: Primary / Secondary / Consequence / Independent redesign.
- Claim-control fields in the finding schema for bug prevention, behavior parity, and performance evidence.

### Changed

- Report template is shorter and narrative-first; headings may be merged when they do not improve understanding.
- Case template reduced to a compact 3–5-part causal narrative.
- Supporting findings are explicitly separated from full Critical/Major cases.
- Technical guardrails strengthened for OOM, `Result`, `Send`/`Sync`, behavior parity, Big-O claims, legacy language labels, and bug-prevention claims.
- The default goal is now: **deeper analysis, shorter expression**.

## 0.4.0

- Root-cause clustering, Transformation Thesis, value qualification, domain-aligned representation, and complexity evidence.
