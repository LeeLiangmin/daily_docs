# Golden Example: Rust Async

This is a design reference, not a template to copy.

Rust async is a useful stress test because the knowledge contains several related concepts—`Future`, `Executor`, `poll`, `.await`, `Pending`, `Waker`, I/O readiness, and task state—but the goal is not to display all of them equally.

## 1. One cognitive target

> Understand how an async task is driven from execution to suspension, wake-up, rescheduling, and completion.

Do not make the target “explain Rust async”. That invites a feature inventory.

## 2. Starting question

> When an async task reaches an I/O `.await` and the result is not ready, what happens to the task and who gets to run next?

This question naturally exposes the executor/task relationship.

## 3. Minimum sufficient knowledge

The essential concepts are:

```text
Executor
Task / Future
poll
await
Pending
I/O readiness
wake
Ready
```

`Pin`, `Context`, runtime implementation details, and specific runtime APIs can be omitted from the primary visual unless the question specifically requires them.

## 4. Visual Narrative

The viewer should follow **one task through execution, suspension, wake-up, and another poll** to understand **how async work progresses without blocking the executor on an unfinished I/O operation**.

The narrative is a loop, not just a one-way pipeline:

```text
Executor
   ↓ poll
Task / Future
   ↓
await I/O
   ↓
Pending
   ↓
other tasks may run
   ↓
I/O ready
   ↓
wake
   ↓
Task becomes runnable
   ↓
Executor polls again
   ↓
Future continues
   ↓
Ready
```

## 5. Visual Structure

Dominant relationship:

> **Executor drives the task by polling it; an unfinished I/O operation causes the task to return `Pending`, while readiness eventually causes the task to be scheduled for polling again.**

Required visible relationships:

```text
Executor ──poll──→ Task/Future
Task/Future ──reaches──→ await
await ──not ready──→ Pending
Pending ──returns control to──→ Executor
I/O readiness ──triggers──→ wake
wake ──makes runnable──→ Task
Executor ──poll again──→ Task/Future
```

Secondary relationship:

```text
Future state ──is preserved across suspension──→ next poll
```

This should be shown as part of the task/Future path, not as a separate concept card.

## 6. Recommended visual model

Use a **looping execution/mechanism diagram** with an executor boundary and a small set of task states.

The executor should be visually identifiable as the driver. The task should visibly leave the active execution path at `Pending` and re-enter it after `wake`/rescheduling.

A useful structure is:

```text
                    ┌──────────── Executor ────────────┐
                    │                                  │
                    │ poll                             │
                    ▼                                  │
                 Task A                                │
                    │                                  │
                    ▼                                  │
               await I/O                               │
                    │                                  │
              not ready                                │
                    ▼                                  │
                 Pending ─────→ other tasks            │
                    │                                  │
                    │ I/O ready → wake                 │
                    └────────────────────→ Task A ─────┘
                                              │
                                            poll
                                              │
                                              ▼
                                            Ready
```

The exact layout can vary, but the loop and executor/task relationship must remain visually obvious.

## 7. Primary / secondary / context

### Primary

- Executor
- Task/Future
- poll
- await
- Pending
- wake/rescheduling
- Ready

### Secondary

- I/O readiness
- preserved Future state
- other tasks getting execution opportunities

### Context / omit from primary visual

- `Pin`
- `Context<'_>`
- specific runtime internals
- Tokio-specific implementation details

These can be introduced in a later visual if the learning goal changes.

## 8. Visual Reconstruction Test

After removing most labels, a viewer should still be able to see:

1. Executor drives Task A.
2. Task A reaches a waiting point.
3. Task A leaves the active path rather than blocking the executor.
4. Other work can run.
5. An external readiness event causes Task A to become runnable again.
6. Executor polls Task A again.
7. Task A eventually reaches completion.

If the image instead looks like a row of boxes named `Future`, `Waker`, `Executor`, and `poll`, it has failed this golden example.

## 9. General lesson

Rust Async demonstrates why **Visual Structure** is necessary:

```text
Knowledge facts
     ↓
Future / Executor / Waker / poll / Pending
     ↓
Dominant relationship
     ↓
Executor drives Future through repeated poll
     ↓
Spatial loop + state change + wake-up edge
     ↓
Mechanism becomes visually reconstructable
```

The goal is not to draw all async concepts. The goal is to make the execution mechanism visible.
