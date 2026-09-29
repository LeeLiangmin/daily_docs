# knowledge-visualization v4

A knowledge-visualization Skill that turns a topic into one traceable path and makes the image — not the viewer — assemble the mechanism.

## Pipeline

```text
Topic → traceable question (gate)
→ one cognitive target
→ knowledge model
→ minimum sufficient structure (one target per image)
→ one spine
→ visual structure: axes, lanes, crossings
→ hierarchy + attachment
→ visual model
→ composition
→ operational validation
→ image spec with negative constraints
```

## What changed from v3

v3 had the right principles ("no independent cards", "visual reconstruction test") but nothing enforced them. A v3 run on "Node.js 核心原理" produced a polished seven-panel panorama in which every panel was correct and the mechanism still had to be assembled by the viewer.

| v3 gap | v4 fix |
|---|---|
| Topics went straight to "cognitive target" | **§0 hard gate**: rewrite into a question that traces one concrete object; record traced object / tracked quantity / end condition |
| "Structural" narrative sat beside "Mechanism" and became the escape hatch for panoramas | **Spine rule**: mechanism targets get exactly one spine; Structural only when nothing can be traced |
| Relation→mark table, but no meaning for the canvas itself | **Spatial grammar**: choose axes first; lanes = actors; crossings = knowledge events; waiting is a place; simultaneity needs a time axis |
| Misconceptions / summary strips allowed in | **One-target rule**: content for another target is deferred, not squeezed in |
| "Attach secondary info" was advice | **Attachment rule**: every non-spine element needs a visible connector to a spine element, or it is removed |
| Reconstruction test was self-assessed | **Operational validation**: written mask test, panel count, arrow audit, axis audit, mechanism-honesty check |
| Image spec had no defense against generator defaults | **Negative constraints** in the spec; fall back to SVG when precision matters |
| Only positive golden examples | Added `golden-examples/nodejs-event-loop.md` and `failure-examples/nodejs-panorama.md` |

## Files

- `SKILL.md`
- `references/topic-to-question.md` (new)
- `references/knowledge-model.md`
- `references/visual-narrative.md`
- `references/visual-structure.md` (spatial grammar added)
- `references/visual-models.md` (swimlane timeline added)
- `references/composition.md`
- `references/anti-patterns.md` (panorama, numbered panels, summary strip, resume illusion…)
- `references/quality-check.md` (operational gates)
- `examples/`
- `golden-examples/rustup.md`, `rust-async.md`, `nodejs-event-loop.md` (new)
- `failure-examples/nodejs-panorama.md` (new)
