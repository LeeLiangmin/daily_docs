# Anti-Patterns

Detect these at planning time, not after rendering.

## Topic panorama ("知识全景图")
The input was a topic; the output gives each sub-area a panel (architecture, phases, steps, queues, reasons, misconceptions, summary). Every panel is correct; the viewer assembles the mechanism alone.
Fix: §0 — rewrite into a traceable question; one spine.
Example: `failure-examples/nodejs-panorama.md`.

## Numbered panels
`① ② ③ …` section headers are an alarm. They signal a table of contents, not a mechanism. Numbered *markers on the spine* are fine; numbered *panels* are not.

## Summary strip / "core insight" footer
A bottom band restating the chain in boxes, or a "一句话总结" box. If the main visual needed a recap, the main visual failed. Delete and strengthen the spine.

## Misconception box
"常见误区" is a correction target. Either put the correction on the spine exactly where the wrong idea would form (e.g., at the callback: "新调用栈，不是恢复 A"), or make a separate image.

## Architecture panel beside a mechanism
V8 / bindings / libuv drawn as a stack in its own panel while the mechanism is elsewhere. Make the layers the lanes the spine runs through.

## Concurrency without time
Claims "handles many requests at once" but has no time axis; concurrency is asserted by text. Add a time axis with a serial lane and overlapping lanes.

## Nine-card summary
Many cards, weak relationships. Find the narrative.

## Everything is important
Equal emphasis everywhere. Define primary / secondary / context.

## Template first
A familiar layout decides the content. Go knowledge → narrative → structure → model → composition.

## Decorative technical diagram
Icons, gradients and glow dominate. Style follows semantics.

## Complete but unreadable
Every true detail included. Use minimum sufficient structure.

## Summary instead of explanation
Says what exists, not how it works.

## Concept inventory disguised as a diagram

```text
Future   Executor   Waker   poll   Pending   Ready
```

Concepts present, relationships absent. Show the mechanism:

```text
Executor ──poll──→ Task/Future ──await──→ Pending ──wake──→ poll again
```

> If the viewer has to infer the main relationship from labels, the diagram is still an inventory.

## Resume illusion
Drawing "Task A continues" for a callback-based runtime. A callback runs on a new stack; context survives via closure. Only continuation-based code (async/await, coroutines) resumes. Draw what the chosen level of abstraction actually does.

## Uniform "the OS does it"
Labeling all async I/O as OS-asynchronous. Many runtimes use readiness notification for sockets and a thread pool for files/DNS/CPU work. If the lane exists, label it honestly.
