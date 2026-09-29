# Golden Example: Node.js Event Loop

A design reference, not a template. Rendered result: `nodejs-event-loop.png`. Pair it with `failure-examples/nodejs-panorama.md`, which shows the same topic rendered as a panorama.

Node.js is a good stress test because the topic invites a panorama (V8, bindings, libuv, six loop phases, micro/macrotasks, misconceptions), while the essential idea is one visible relationship: **one serial lane handing waits to parallel lanes**.

## §0 Topic → traceable question

User input: "Node.js 核心原理".

Rewrite:

> 三个请求同时进入 Node.js，只有一个 JS 线程 —— 控制权怎么流动，为什么没人被卡住？

- Traced object: HTTP requests A, B, C (three, because the claim is about concurrency)
- Tracked quantity: control of the JS main thread
- End condition: all three responses sent

## §1 Cognitive target

Understand how a single JS thread serves many requests: it hands every wait to libuv/OS, returns immediately, and runs callbacks one at a time when completions arrive.

## §3 Minimum sufficient structure

Primary: JS main thread; handler runs; I/O call returns immediately; libuv thread pool (file I/O); kernel + epoll (sockets); completion; ready-callback queue; callback runs on JS thread; JS idle while waiting.

Secondary: microtasks drained after each callback; callbacks run on a new stack (closure keeps context).

Deferred ("Next visuals"): six loop phases in order; V8 / bindings layering; setTimeout precision; `setImmediate` vs `setTimeout`; worker_threads; misconceptions list.

## §4 Spine

The viewer should follow **three requests through one JS thread** to understand **why none of them blocks the others while their I/O is pending**.

```text
request arrives → handler runs on JS → I/O call returns immediately (handoff)
→ JS serves next request → I/O proceeds elsewhere (overlapping)
→ completion → queued → JS free → callback runs → response sent
```

It repeats for each request; the repetition *is* the event loop.

## §5 Visual structure

- Axes: x = time; y = actor lanes.
- Lanes (top→bottom): JS main thread (serial) · ready-callback queue · libuv thread pool (parallel, sub-rows) · kernel / epoll (parallel).
- Dominant relationship: **JS hands off the wait and immediately continues**; completions come back through the queue.
- Crossings:
  - solid down arrow = 发起 I/O，立即返回 (hand off)
  - dashed up arrow = I/O 完成，回调入队 (notify)
  - short arrow queue → JS = 事件循环取出回调 (pick up)
- Waiting drawn as: a completed callback sitting in the queue while JS is busy (B's DB result arrives during A's callback); JS idle as a hatched segment ("poll：等待任意事件").
- Serial vs parallel: JS segments never overlap; I/O bars overlap each other.

Honesty checks at this level:

- File reads go to the **thread pool**; socket waits go to the **kernel via epoll**. Both lanes exist and are labeled accordingly.
- Callbacks run on a **new stack**; A's handler is not "resumed". Say so at A's callback.
- Request arrival is itself an epoll event, so arrivals also enter JS through the queue.

## §7 Model

Swimlane timeline with control handoffs. A ring labeled "event loop" is not used: a ring shows repetition but cannot show overlap, and overlap is the point.

## §8 Composition

- Title = the question. Subtitle = scenario (3 requests, 1 JS thread).
- ≤ 5 numbered callouts, each anchored to a spine point:
  1. handoff: readFile() returns immediately
  2. bracket over overlapping I/O bars: concurrency happens here, not in JS
  3. idle hatch: JS waits for *any* event
  4. queued B: done ≠ run immediately; waits for JS to be free
  5. A's callback: new stack, closure keeps `res`
- Small legend: arrow styles, hatch, microtask sliver.
- No architecture panel, no phase table, no misconceptions box, no summary strip.

## §9 Mask test (expected result)

From lane names, event labels and arrow verbs only:

1. A arrives (epoll) → queued → JS runs A's handler.
2. A's handler hands a file read to the thread pool and returns.
3. JS runs B's handler, hands a DB query to the kernel, returns.
4. JS runs C's handler, hands a file read to the thread pool, returns.
5. Three I/O operations run at the same time; JS is idle.
6. a.txt done → A's callback queued → JS runs it → response A.
7. DB result arrives while JS is busy → waits in queue → runs next.
8. c.txt done → C's callback → response C.

If any of these can only be learned from a paragraph, the structure is incomplete.

## General lesson

```text
Topic "Node.js 原理"
  → trace 3 requests, track control of the JS thread
  → claim is about simultaneity → time axis
  → actors that hold control → lanes
  → handoff / notify / pick-up → crossings with verbs
  → single-threaded = non-overlapping lane; async = overlapping lanes
```

The relationship between "single-threaded" and "asynchronous" is no longer two facts; it is the visible contrast between two lanes.
