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
