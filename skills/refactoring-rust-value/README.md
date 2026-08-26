# refactoring-rust-value

Portable Agent Skill for discovering and documenting the engineering value of a **C/C++ → Rust refactor**.

The skill compares real old/new implementations, identifies important architecture and design changes, distinguishes value from value origin, and writes a detailed Markdown report with concrete C/C++ vs Rust code evidence.

## Package layout

```text
refactoring-rust-value/
├── SKILL.md
├── README.md
├── references/
│   ├── value-taxonomy.md
│   ├── case-selection.md
│   ├── evidence-guide.md
│   ├── gitnexus-integration.md
│   └── example-case.md
├── assets/
│   ├── report-template.md
│   ├── case-template.md
│   └── finding.schema.yaml
└── scripts/
    └── collect-git-context.sh
```

`SKILL.md` is the portable entry point. Supporting material is loaded on demand.

## OpenCode installation

OpenCode discovers Agent Skills from several locations. For a project-local install, copy the **whole `refactoring-rust-value` directory** into one of these locations:

```text
.opencode/skills/refactoring-rust-value/
.agents/skills/refactoring-rust-value/
.claude/skills/refactoring-rust-value/
```

For a global OpenCode install, typical locations include:

```text
~/.config/opencode/skills/refactoring-rust-value/
~/.agents/skills/refactoring-rust-value/
~/.claude/skills/refactoring-rust-value/
```

The `.agents/skills/` location is a good portability-oriented choice when several compatible agents share the same repository.

## Generic Agent Skills installation

For an Agent Skills-compatible client, place the directory under that client's skills source. Keep the directory name exactly:

```text
refactoring-rust-value
```

because the `name:` in `SKILL.md` is also `refactoring-rust-value`.

## Example prompts

```text
Analyze this C++ → Rust migration with the refactoring-rust-value skill and produce the full value report.
```

```text
Use refactoring-rust-value. This repository contains the old implementation under legacy/ and the Rust implementation under rust/. Focus on core architectural changes, concurrency, ownership, and type modeling, but include any other important evidence-backed value you discover.
```

```text
Use refactoring-rust-value on commits OLD_TAG..NEW_TAG. Discover broadly first, then deep-dive only important and representative cases. Write the report to docs/rust-refactoring-value.md.
```

## GitNexus and code-graph tools

GitNexus is optional. For large repositories it can help discover central components, execution flows, and high-value candidate areas. It must not replace source-level evidence. See `references/gitnexus-integration.md`.

## Design principles

- Value first, feature second.
- Compare real old C/C++ and new Rust code.
- Rust can drive redesign; it is not merely an extra safety layer.
- Do not cap findings; do not pad findings.
- Focus deep analysis on important/core/representative cases.
- No evidence, no strong claim.
- Final output is a detailed, human-readable Markdown engineering report.


## v0.6 analysis principles

- Actual legacy C/C++ → actual Rust is the primary comparison.
- Modern C++ is only an optional counterfactual for attribution calibration.
- Strong cases should reconstruct a causal value chain and look for complexity collapse.
- Important claims distinguish observed evidence, inference, and counterfactual reasoning.
- Technical guardrails prevent common Rust/C++ overclaims.


## v0.6 analysis upgrades

- Root-cause clustering: merge local consequences into causal cases.
- Transformation Thesis: synthesize system-level migration stories.
- Value qualification: distinguish structural/safety gains from conditional simplification, compatibility change, and trade-offs.
- Complexity evidence: prefer concrete removed mechanisms/call sites over fake numeric scores.
- Reality-first comparison remains mandatory; modern C++ is calibration only.


## v0.6 writing contract

By default, generated reports are written in Chinese, retaining only necessary English technical terms, identifiers, and code. The report should follow “信、达、雅”: technically faithful, easy for engineers to understand, and concise without template-driven repetition.

The v0.6 analysis pipeline is:

```text
raw findings
→ root-cause clustering
→ value-density filtering
→ consequence suppression
→ thesis hierarchy
→ concise Chinese engineering narrative
```


## v0.6 convergence rules

- One root transformation normally maps to one main case; downstream consequences stay inside it.
- Reports default to six conceptual sections and remove redundant system-summary chapters.
- Quantitative claims include reproducible counting scope/method.
- Behavior parity claims require mapped, executed cross-implementation evidence for the covered cases.
- Claim wording remains consistent across summary, body, and conclusion.
