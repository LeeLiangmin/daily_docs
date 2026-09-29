# Visual Structure

Visual Structure is the bridge between a knowledge model and a visual model.

> Which relationships must become directly visible so that the viewer can form the intended understanding without relying on explanatory prose — and what do the canvas dimensions mean?

A knowledge model describes what is true. A visual structure describes how those truths must be spatially organized to be understood.

```text
Knowledge
   ↓
Relationships that matter
   ↓
Relationships that must be visible
   ↓
Axes + lanes + crossings + marks
   ↓
Visual model
```

## 1. Dominant relation

Identify the relation the viewer must see first: drives, hands off control to, flows through, changes into, causes, waits for, wakes, returns to, maps to, is selected by.

Do not give every relation equal weight.

## 2. Spatial grammar

v3 had a relation→mark table. That is necessary but not sufficient: marks sit *in* a space, and the space itself must mean something.

### 2.1 Axes first

Decide what x and y mean before drawing any box.

| Claim | Axis |
|---|---|
| concurrency, "doesn't wait", overlap, latency, ordering, queuing | time |
| who acts / holds control / owns the resource | actor lanes |
| abstraction layer, call depth | depth |
| amount, rate | measured scale |
| place | geography |

**Simultaneity needs time.** If the target contains "while", "at the same time", "without waiting", "concurrently", the image needs a time axis on which overlap is literally visible.

A circle ("the event loop") is a good symbol for *repetition* but a poor surface for *overlap*. If you need both, show the repetition as the repeated pattern along the time axis, not as a separate ring.

### 2.2 Lanes = actors

Give each actor that can hold control its own lane (thread, process, kernel, thread pool, client, server, executor, reactor, household, firm).

- A lane is serial if the actor can do one thing at a time → draw it as non-overlapping segments. This *is* the "single-threaded" claim.
- A lane is parallel if it can do many things → overlapping bars, sub-rows.
- Idle is drawn as empty/hatched segments, never only described.

### 2.3 Crossings = knowledge events

The spine moves between lanes. Each crossing is where the mechanism lives:

- hand off (JS → libuv: "发起 I/O，立即返回")
- complete / notify (OS → queue)
- pick up (event loop → JS: "执行回调")
- wake (reactor → executor)

Each crossing gets a directed edge with a verb. Use one arrow style per crossing type.

### 2.4 Waiting is a place

If something waits, give it a place: a queue band between lanes, a hatched gap, a parked token. "I/O finished but the callback hasn't run yet" should be a visible item sitting in a queue, not a sentence.

### 2.5 Relation → mark reference

| Relationship | Visual expression |
|---|---|
| Sequence | position along time/direction |
| Control / invocation | directed edge between lanes |
| Handoff / return | crossing edge, paired styles |
| State transition | state nodes + transitions |
| Causality | cause → effect edge |
| Feedback / wake-up | return edge / loop |
| Containment | boundary / nesting |
| Selection | branch + highlighted path |
| Dependency | directional edge |
| Parallel activity | overlapping bars in one lane / multiple lanes |
| Exclusive activity | non-overlapping segments in one lane |
| Waiting | queue slot, gap, hatch |
| Resource sharing | shared node / common boundary |

The table is a reasoning aid, not a fixed grammar.

## 3. Primary / secondary / context

- **Primary** — required to reconstruct the mechanism; visually dominant; on the spine.
- **Secondary** — explains or modifies a spine element; attached with a connector.
- **Context** — orientation only; peripheral or omitted.
- **Reference detail** — deferred to another visual.

## 4. Visual Structure statement

Before composition, write:

> Axes: x = ___, y = ___.
> Lanes: ___.
> The viewer must visually perceive **[relationship]** between **[A]** and **[B]**, because it is necessary to understand **[target]**.
> Crossings: ___ (each with verb and arrow style).
> Waiting is shown as: ___.

## Example: Rust async

Primary relationships:

```text
Executor ──polls──→ Task/Future
Future ──reaches──→ await
await ──not ready──→ Pending ──returns control──→ Executor
I/O readiness ──wake──→ Task runnable
Executor ──polls again──→ Task/Future
```

Secondary: Future state preserved across await; other tasks polled meanwhile.

Structure: executor/task loop dominant; if the target stresses "other tasks run meanwhile", add an executor lane on a time axis showing polls of Task B/C in the gap.

## Example: Node.js

Axes: x = time; y = actor lanes.
Lanes: JS main thread (serial) · ready-callback queue · libuv thread pool (parallel) · OS kernel/epoll (parallel).
Dominant: JS thread **hands off** I/O and **immediately returns** to serve the next request; completions **queue** and are **picked up** when the JS thread is free.
Waiting: a completed I/O sits in the queue while JS is busy; JS idle is a hatched gap ("poll: waiting for any event").

See `golden-examples/nodejs-event-loop.md`.
