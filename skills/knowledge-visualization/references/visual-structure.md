# Visual Structure

Visual Structure is the bridge between a knowledge model and a visual model.

It answers:

> Which relationships must become directly visible so that the viewer can form the intended understanding without relying on explanatory prose?

A knowledge model describes what is true. A visual structure describes how those truths must be spatially organized to be understood.

## Why this layer exists

Without this step, a model can correctly identify many entities—such as `Future`, `Executor`, `Waker`, and `poll`—but still produce a picture that merely lists them.

The required transformation is:

```text
Knowledge
   ↓
Relationships that matter
   ↓
Relationships that must be visible
   ↓
Spatial / directional / containment / state representation
   ↓
Visual model
```

## Identify the dominant relation

For the primary cognitive target, identify the relation that the viewer must see first.

Examples:

- drives
- flows through
- changes into
- causes
- contains
- depends on
- maps to
- competes with
- is selected by
- returns to

Do not allow every relationship to have equal visual weight.

## Visual relationship inventory

Before choosing a diagram type, explicitly identify applicable relationships:

| Relationship | Visual expression examples |
|---|---|
| Sequence | direction, ordered positions |
| Control / invocation | directed arrow, caller above/caller side |
| State transition | state nodes + transition arrows |
| Causality | cause → effect |
| Feedback / wake-up | return arrow / loop |
| Containment | nesting / boundary |
| Selection | branching / highlighted path |
| Dependency | directional dependency edge |
| Parallel activity | lanes / parallel branches |
| Resource sharing | common boundary / shared node |
| Spatial mapping | position / region |

The exact representation depends on the subject. The table is a reasoning aid, not a fixed visual grammar.

## Primary / secondary / context hierarchy

### Primary

Relationships required to reconstruct the main mechanism. They must be visually dominant.

### Secondary

Relationships that explain or modify the primary mechanism. Attach them to the relevant primary element.

### Context

Background needed only to orient the viewer. Keep it peripheral or omit it.

### Reference detail

Useful for later lookup but not required for the first understanding. Use annotations or a separate visual when appropriate.

## Visual Structure statement

Before composition, complete:

> The viewer must visually perceive **[relationship]** between **[A]** and **[B]**, because that relationship is necessary to understand **[target]**.

Then list the minimum additional relationships needed to reconstruct the mechanism.

## Example: Rust async

Cognitive target:

> Understand how an async task is driven from execution to suspension, wake-up, rescheduling, and completion.

Knowledge facts:

```text
Future
Executor
poll
await
Pending
Waker
wake
Ready
I/O readiness
```

Primary visual relationships:

```text
Executor ──polls──→ Task/Future
Future ──reaches──→ await
await ──may produce──→ Pending
I/O readiness ──causes──→ wake
wake ──makes runnable──→ Task
Executor ──polls again──→ Task/Future
```

Secondary relationships:

```text
Future state ──is preserved across──→ await
Pending ──gives execution opportunity to──→ other tasks
```

The image should therefore make the executor/task loop visually dominant. `Future`, `poll`, `Pending`, and `Waker` should explain that loop rather than appear as independent cards.
