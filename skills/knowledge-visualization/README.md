# knowledge-visualization v4

A knowledge-visualization Skill centered on **Visual Narrative + Visual Structure + Visual Dominance**.

## Core idea

> Do not turn knowledge into a picture. Turn the structure required to understand the knowledge into a visual experience.

A second rule makes the idea operational:

> One visualization may contain many objects, but it must have one visually dominant explanatory structure.

## Pipeline

```text
Question
→ Cognitive target
→ Knowledge model
→ Minimum sufficient structure
→ Visual Narrative
→ Visual Structure
→ Visual Dominance + Visual Budget
→ Visual model
→ Composition
→ Reconstruction + Dominance Test
→ Validation
→ Visual
```

## What v4 adds

### Visual Dominance

Explicitly identifies the one visual structure that owns the viewer's attention.

### Visual Budget

Prevents secondary explanations, component inventories, summaries, and decoration from consuming visual weight comparable to the primary mechanism.

### Dominance Test

Tests the image in three ways:

1. **Primary-only** — does the mechanism survive when supporting information is removed?
2. **Competition** — is any secondary region mistaken for the main explanation?
3. **One-path** — can the intended attention path be stated as one sentence?

## Why this matters

Without these constraints, a model can produce a technically correct but poster-like image:

```text
central diagram
+ architecture cards
+ component cards
+ summary panel
+ misconception panel
+ numbered sections
```

The result contains knowledge but makes the viewer reconstruct the hierarchy themselves.

v4 instead asks the image to communicate the hierarchy directly:

```text
                    secondary detail
                           │
                           ▼
START ───────→ PRIMARY MECHANISM ───────→ RESULT
                           ▲
                           │
                    secondary detail
```

## Included

- `SKILL.md`
- `references/knowledge-model.md`
- `references/visual-narrative.md`
- `references/visual-structure.md`
- `references/visual-dominance.md`
- `references/visual-models.md`
- `references/composition.md`
- `references/anti-patterns.md`
- `references/quality-check.md`
- `examples/`
- `golden-examples/rustup.md`
- `golden-examples/rust-async.md`
- `golden-examples/nodejs.md`
