# Golden Example: Node.js Core Principle

This is a design reference, not a template to copy.

## 1. One cognitive target

> Understand why a single JavaScript thread can serve many I/O-bound tasks without waiting synchronously for each I/O operation.

Do not make the target “explain all of Node.js”.

## 2. Starting question

> When JavaScript starts an I/O operation, why can the JS thread continue doing other work instead of waiting for the I/O to finish?

## 3. Minimum sufficient knowledge

```text
JavaScript thread
Node API
libuv / underlying I/O mechanism
I/O completion
Event loop / runnable callback
```

V8 internals, every event-loop phase, detailed libuv thread-pool behavior, microtask ordering, and API inventories can be secondary unless the question specifically requires them.

## 4. Visual Narrative

The viewer should follow **one I/O request through submission, non-waiting continuation, completion, callback scheduling, and resumed JavaScript execution** to understand **how the JS thread avoids being blocked by the I/O operation**.

## 5. Visual Structure

Dominant relationship:

> **JavaScript starts I/O without synchronously waiting; the underlying system/libuv handles the waiting work, and completion causes JavaScript work to become runnable again.**

Required visible relationships:

```text
JS executes
   ↓
Node API
   ↓
submit I/O
   ↓
JS returns to event-loop-driven work
   ↓
other JS work can execute

libuv / OS
   ↓
I/O completes
   ↓
callback becomes runnable
   ↓
JS executes callback
   ↓
continues
```

The return to JavaScript should be visually connected to the original task rather than shown as an unrelated new box.

## 6. Recommended visual model

Use one large **execution loop / mechanism diagram**.

```text
                ┌──────────── JS thread ─────────────┐
                │                                     │
                │  execute JS                         │
                │      ↓                              │
                │  start I/O                          │
                │      ↓                              │
                │  do not wait                        │
                │      ↓                              │
                │  other runnable JS work             │
                │      ↑                              │
                │      │ callback                     │
                │      │                              │
                └──────┼──────────────────────────────┘
                       │
                       │ completion
                       ↑
                 libuv / OS
                       │
                    I/O work
```

The important fact is the separation between:

- JS execution
- waiting for I/O
- resumption after completion

## 7. Secondary information

Attach these to the main loop rather than making them equal-sized cards:

- V8 executes JavaScript
- Node API exposes filesystem/network/etc.
- libuv coordinates asynchronous operations
- event loop selects runnable callbacks/work
- microtasks have their own scheduling semantics

The exact implementation details should not visually compete with the core loop.

## 8. Visual Reconstruction Test

With most prose removed, the viewer should still see:

1. JS starts an I/O operation.
2. JS does not synchronously wait for completion.
3. I/O work proceeds outside the active JS execution path.
4. JS can execute other runnable work.
5. I/O completion leads back to runnable JavaScript work.
6. The original flow continues.

If the image instead looks like “V8 / Node API / libuv / Event Loop / Task Queue / OS” as six equally prominent boxes, it has failed this golden example.

## 9. Dominance Test

Primary-only:

> Hide V8 labels, component inventories, event-loop phase lists, misconceptions, and summaries. The I/O-to-callback loop must still explain the core idea.

Competition:

> No architecture panel or component list should be visually strong enough to become a second explanation.

One-path:

> “JS starts I/O → does other work → I/O completes → callback runs → JS continues.”

If that sentence is not also the obvious visual path, simplify the composition.
