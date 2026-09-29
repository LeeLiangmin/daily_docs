# Visual Narrative

Visual Narrative is the bridge between the knowledge model and the viewer's attention.

It describes not just the order of facts, but the **path the viewer should mentally follow**.

## Narrative patterns

### Mechanism
Input → mechanism → output

### Execution
Action → A → B → C → result

### Causal
Condition → behavior → intermediate effect → outcome → feedback

### State
State → event → state → event → state

### Structural
Whole → major parts → critical relationships

### Comparison
Question → dimensions → alternatives → meaning of differences

### Historical
Context → event → consequence → later change

### Spatial
Location → relationship → distribution/movement → effect

## Narrative vs. visual structure

Narrative says:

> The viewer should follow **the task's execution and rescheduling** to understand **how async work progresses while waiting for I/O**.

Visual Structure then says what must be visible:

```text
Executor ──poll──→ Task
Task ──await──→ Pending
I/O ready ──→ wake
wake ──→ runnable Task
Executor ──poll again──→ Task
```

Do not skip this translation. A good narrative can still become a poor image if its relationships are not made spatially explicit.

## Narrative test

Complete:

> The viewer should follow ______ to understand ______.

Then complete:

> The viewer must visually perceive ______ between ______ and ______ because ______.

If either statement is vague, do not start visual styling yet.
