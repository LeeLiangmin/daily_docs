# Topic → Traceable Question

Most requests arrive as topics: "Node.js 核心原理", "explain Rust async", "how does the economy work". A topic has no path, so the natural output is an inventory: every sub-area gets a panel.

A **traceable question** has a path built in, because it follows one concrete thing.

## Template

> When **[one concrete object/event]** enters **[system]**, what happens to **[tracked quantity]** until **[end condition]**?

| Slot | Meaning | Node.js example |
|---|---|---|
| Traced object | something concrete that moves | three HTTP requests A, B, C |
| System | the boundary it moves through | one Node.js process |
| Tracked quantity | what the viewer watches change hands | control of the single JS thread |
| End condition | where the trace stops | every response has been sent |

## Choosing the traced object

Prefer the object whose journey **crosses the most important boundary** of the topic.

- Node.js: the important boundary is JS thread ↔ libuv/OS. A request crosses it twice (handoff, completion). A "module" or "phase" crosses nothing.
- Rust async: a task crosses executor ↔ reactor (Pending, wake).
- rustup: a command crosses shell → proxy → toolchain.
- Economy: a unit of money crosses firm → household → firm.

Prefer **more than one instance** when the claim is about concurrency or contention (three requests, not one). A single instance cannot show that others proceed while it waits.

## Choosing the tracked quantity

Ask: what is the *surprising* thing about this system? Track that.

- Node.js: surprising = one thread serves many requests → track **control of the thread**.
- mmap: surprising = file bytes appear as memory → track **an address** being resolved.
- Linking: surprising = addresses unknown at compile time → track **one reference** until it is resolved.

## When nothing can be traced

Sometimes the target really is organizational ("what are the parts of Kubernetes' control plane?"). Then record:

> No traced object: the target is composition. Using Structural narrative.

Even then, show relationships between parts (who calls whom, who owns what), not a list of parts.

## Rewriting the user's framing

If the user's own framing is a topic, show them the question you chose in one line before drawing. That line becomes the image title.
