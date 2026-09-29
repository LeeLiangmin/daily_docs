# Visual Dominance

Visual Dominance is the layer that prevents a correct knowledge model from turning into a complete-but-flat knowledge poster.

## Core idea

A visualization can contain many correct elements while still failing because the viewer cannot tell which structure matters most.

> One visualization may contain many objects, but it must have one visually dominant explanatory structure.

## Primary visual

The primary visual is the smallest spatial structure that directly carries the cognitive target.

Examples:

### Rust async

```text
Executor
   ↓ poll
Task
   ↓
await
   ↓
Pending
   ↓
wake / reschedule
   ↓
poll again
```

### Node.js

```text
JS
 ↓
start I/O
 ↓
return without waiting
 ↓
libuv / OS performs I/O
 ↓
completion
 ↓
event loop
 ↓
callback
 ↓
JS continues
 ↺
```

Everything else should support this structure.

## Information layers

| Layer | Role | Visual weight |
|---|---|---|
| Primary | carries the cognitive target | strongest |
| Secondary | explains/modifies primary | clearly weaker |
| Context | gives orientation | peripheral |
| Reference | optional detail | restrained |
| Decoration | aesthetic only | minimal |

## Dominance mechanisms

Use a combination of:

- central or continuous placement
- larger scale
- stronger contrast
- thicker or clearer arrows
- uninterrupted spatial continuity
- consistent visual encoding
- reduced competition around the primary path

Do not use decoration as a substitute for dominance.

## Secondary attachment rule

Secondary concepts should be attached to the node or relationship they explain.

Prefer:

```text
        [secondary detail]
                │
                ▼
A ───────────→ B ───────────→ C
```

over:

```text
[A] [B] [C]

[secondary card]
[another card]
[another card]
```

The second structure encourages the viewer to read several independent topics instead of one mechanism.

## Visual Budget

Visual budget is qualitative, not a fixed percentage system.

The primary path should receive most of the available:

- area
- contrast
- line weight
- directional clarity
- text emphasis

If the viewer notices a supporting explanation before the mechanism, the budget is wrong.

## Dominance Test

### Primary-only test

Remove secondary information. The core understanding should survive.

### Competition test

Look for any secondary region that could be mistaken for the main explanation.

### One-path test

Describe the intended attention path in one sentence. If two unrelated paths are needed, either merge them into one explanatory structure or split the visualization.

## Anti-poster heuristic

The following combination is a warning sign:

```text
many numbered sections
+ equal-sized cards
+ several independent headings
+ bottom component inventory
+ side summary panel
+ central diagram
```

This can still be valid for a reference poster, but it is usually the wrong default for a mechanism explanation.

When the cognitive target is a mechanism, prefer one dominant mechanism diagram with annotations attached to it.
