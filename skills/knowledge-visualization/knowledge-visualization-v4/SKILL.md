---
name: knowledge-visualization
description: Transform a user's question or topic into a cognitively effective visual explanation. Use when the user asks to visualize, illustrate, diagram, explain, teach, or generate an image for a knowledge topic. First turn a topic into one traceable question, build the minimum sufficient structure around a single spine, decide which relationships must be spatially visible (axes, lanes, boundary crossings), choose a matching visual model, compose, run operational validation, and only then write the image specification. Applies to technical, scientific, historical, economic, social, geographic, educational, and other knowledge domains.
---

# Knowledge Visualization

## Core purpose

Do not turn knowledge into a picture. Turn the **structure required to understand the knowledge** into a visual experience.

> Do not put all the knowledge into the image. Build one visually reconstructable path around one cognitive target — and make the image do the assembling, not the viewer.

Pipeline:

```text
User input (topic or question)
    ↓
0. Topic → traceable question        ← hard gate
    ↓
1. One cognitive target
    ↓
2. Knowledge model
    ↓
3. Minimum sufficient structure (one target per image)
    ↓
4. Visual narrative → one spine
    ↓
5. Visual structure (dominant relation, axes, lanes, crossings)
    ↓
6. Hierarchy + attachment
    ↓
7. Visual model
    ↓
8. Composition
    ↓
9. Operational validation
    ↓
10. Image specification (with negative constraints)
```

The most important work happens before styling. A failed visual usually fails at step 0 or step 5, not in the drawing.

## Why v4 exists

A v3 run on "Node.js 核心原理" produced a polished seven-panel panorama: architecture, loop phases, I/O steps, microtasks, concurrency reasons, misconceptions, summary strip. Every panel was correct; the viewer still had to assemble them. The principles were in v3; nothing forced them. v4 turns them into gates. See `failure-examples/nodejs-panorama.md`.

## 0. Topic → traceable question (hard gate)

A topic ("Node.js 原理", "Rust async", "the economy") is not a question. Topics invite inventories.

Rewrite every topic into a question that **follows one concrete thing through the system**:

> When **[one concrete object/event]** enters **[system]**, what happens to **[control / data / state / money / …]** until **[end condition]**?

Examples:

| Topic | Traceable question |
|---|---|
| Node.js 原理 | 三个请求同时进入 Node.js，只有一个 JS 线程，控制权怎么流动，为什么没人被卡住？ |
| Rust async | 一个 task 在 `.await` 上遇到未就绪的 I/O，它和 executor 之间发生了什么？ |
| rustup | 敲下 `cargo` 之后，命令是怎么到达被选中的真实可执行文件的？ |
| Economy | 一笔工资从企业发出后，经过谁、又如何回到企业？ |

If no single object can be traced (the target really is "how is X organized"), say so explicitly and use a Structural narrative (§4). This must be a decision, not a default.

Record: `Traced object: ___ · Tracked quantity: ___ · End condition: ___`.

See `references/topic-to-question.md`.

## 1. One cognitive target

> What should the viewer be able to explain after seeing this?

Choose one primary target (how it works / how it happens / how state changes / why / what constrains / how A differs from B / how it changed over time / how things are spatially related). Do not let every interesting fact become a target.

## 2. Knowledge model

Extract knowledge relevant to the target: entities, relations, processes, states, causes, constraints, hierarchy, change, evidence, perspective. For technical topics consider control flow, data flow, call path, ownership, lifetime, thread/process boundaries, build/runtime boundaries.

The knowledge model is internal. It is not the image.

## 3. Minimum sufficient structure — one target per image

For each candidate element: *if removed, can the viewer still form the intended understanding?* If yes, remove it.

**One-target rule.** Content that serves a *different* cognitive target does not go into this image, however true and useful:

- "Common misconceptions" → a correction target (separate image, or fold the correction into the spine where the wrong idea would arise).
- "One-sentence summary" / "core insight" strip → a recap target. If the spine is right, the image *is* the summary.
- Architecture inventory, module lists, phase tables → a reference target.
- History, ecosystem, pros/cons → other targets.

Deferred content goes into a "Next visuals" list in your reasoning, not into the corners of this image.

## 4. Visual narrative → one spine

> The viewer should follow ______ to understand ______.

Narrative types: Mechanism, Execution, Causal, State, Comparison, Historical, Spatial, Structural.

**Spine rule.** For Mechanism / Execution / Causal / State targets, the image has exactly one spine: the path of the traced object from §0. Everything else is placed *on* the spine where it participates.

- Architecture layers (V8, libuv, OS…) appear as the lanes/regions the spine passes through, not as a separate "architecture" panel.
- Phase lists appear as annotations at the point on the spine where they matter, or are deferred.

**Structural is not an escape hatch.** Use it only when §0 recorded that no object can be traced. A panorama of a mechanism topic is a failed Structural narrative.

## 5. Visual structure

This is the bridge between knowledge and drawing. Do these in order.

### 5a. Dominant relationship

> The viewer must visually perceive **[relationship]** between **[A]** and **[B]**, because it is necessary to understand **[target]**.

Examples: drives, hands off control to, flows through, changes into, causes, waits for, wakes, returns to.

### 5b. Choose the axes before choosing shapes

Decide what the two dimensions of the canvas *mean*. A diagram without axis semantics becomes a grid of cards.

| If the key claim is about… | Then an axis must be… |
|---|---|
| concurrency, overlap, "doesn't wait", latency, ordering | **time** (usually horizontal) |
| who holds control, which thread/process/actor acts | **actor / ownership lanes** (usually vertical stacking) |
| layers of abstraction, call depth | depth (vertical) |
| magnitude, rate | a measured axis |
| location | space |

Rule: **a claim about simultaneity needs a time axis.** "Single-threaded yet concurrent" cannot be seen in a circle or a box diagram; it is seen when one lane is serial and another lane has overlapping bars.

### 5c. Lanes and boundary crossings

When different actors hold control (JS thread vs. kernel, client vs. server, executor vs. reactor, household vs. firm), give each actor a lane or region. Then:

- The spine **crosses** lane boundaries. Each crossing is a knowledge event (hand off, return, wake, pay) and gets an arrow labeled with a verb.
- Idle and waiting are drawn, not described (empty or hatched lane segments, queued items waiting).
- What does *not* cross is also information (e.g., the JS lane never blocks on I/O).

See `references/visual-structure.md` → Spatial grammar.

### 5d. Supporting relationships

List the minimum additional relationships needed to reconstruct the mechanism. For each, pick its expression: sequence → position/direction; control → directed edge; state → nodes + transitions; feedback → return edge; containment → boundary; parallelism → lanes; waiting → queue/gap.

If the output of §5 is a list of concepts rather than a list of relationships with spatial expressions, §5 is not done.

## 6. Hierarchy and attachment

- **Primary** — on the spine; strongest weight.
- **Secondary** — attached to a specific spine node or crossing.
- **Context** — peripheral or omitted.
- **Reference detail** — deferred.

**Attachment rule.** Every non-spine element must have a visible connector (leader line, bracket, adjacency inside the same lane) to a specific spine element. An element that cannot be attached is deleted or deferred. Titled standalone panels are not attachment.

## 7. Visual model

Select after §5, never before. `Infographic` is never the default.

| Narrative / structure | Model |
|---|---|
| Execution across actors, concurrency | **Swimlane timeline with control handoffs** |
| Driver repeatedly advancing a task | Loop on a spine (driver ↔ task) |
| Mechanism | Mechanism diagram |
| State changes | State diagram |
| Causality / feedback | Causal loop diagram |
| Composition (only if §0 found nothing to trace) | Architecture |
| Differences | Comparison with shared dimensions |
| Temporal change | Timeline |
| Spatial | Map |

See `references/visual-models.md`.

## 8. Composition

- The spine gets the most visual weight and the most area.
- Secondary information sits next to the spine element it modifies, with a connector.
- Numbered callouts are allowed only as markers *on* the spine; numbered *panels* are not.
- Title = the traceable question from §0, not the topic name.

If crowded: remove off-target content → remove secondary detail → group → shorten labels → split into a second image. Do not shrink everything.

## 9. Operational validation

Do not "imagine whether it works". Run these checks and write down the results.

1. **Mask test.** Hide every sentence of prose; keep only node names, lane names and arrow verbs. Write the story you can read from that alone as numbered steps. Compare it line by line with the expected trace from §0. Any missing step is a structural gap, not a labeling gap.
2. **Panel count.** Count titled regions that are not on the spine. Mechanism image target: 0. More than 1 → revisit §3/§6.
3. **Arrow audit.** Every arrow has a verb and a consistent meaning; arrow styles map 1:1 to relationship types (e.g., solid = hand off, dashed = completion/notify).
4. **Axis audit.** If the image claims concurrency, overlap, waiting or ordering, verify it has a time axis where that claim is visible.
5. **Mechanism honesty at the drawn level.** Check the image does not imply a mechanism that is wrong at the level of detail you chose. Common traps:
   - "Task A continues/resumes" when the runtime actually runs a *new* callback on a fresh stack (callbacks) vs. resuming a continuation (async/await, coroutines).
   - "The OS does the I/O asynchronously" when the runtime actually uses a thread pool for that operation (e.g., libuv file I/O) and readiness notification only for sockets.
   - Arrows that suggest a push where the real mechanism is polling, or vice versa.
6. **Facts.** Entities, directions, colors, state transitions correct; no invented precision.

Record the results. If any check fails, fix the structure before writing the image spec.

## 10. Image specification

Build the spec from the reasoning. Never pass the raw user question to the image model.

The spec contains: title (= traceable question), cognitive target, traced object, axes and their meanings, lanes, spine events in order with their crossings, secondary attachments (each with its anchor), semantic encoding (color and arrow meanings), text budget, factual constraints, and **negative constraints**.

Image models default to "header banner + numbered cards + summary footer". Counter this explicitly:

```text
Layout: ONE main visual occupying ≥ 80% of the canvas: [describe axes/lanes].
Do NOT: numbered section panels, card grids, a summary/insight strip,
a "misconceptions" box, logo/banner header, icon decoration unrelated to the spine.
Text: only lane names, event labels, arrow verbs, and ≤ N short callouts attached to spine points.
```

If the image generator cannot respect lanes and precise overlaps, draw the diagram as SVG/HTML instead and use the generator only for style, or not at all. A precise schematic beats a pretty inventory.

## References

- `references/topic-to-question.md` — §0 in depth
- `references/visual-narrative.md` — narratives and the spine
- `references/visual-structure.md` — dominant relation, spatial grammar, lanes
- `references/visual-models.md` — model table
- `references/composition.md` — layout
- `references/anti-patterns.md` — failure shapes to detect early
- `references/quality-check.md` — the §9 checklist
- `golden-examples/` — rustup, rust-async, nodejs-event-loop
- `failure-examples/nodejs-panorama.md` — a beautiful image that failed, and why
