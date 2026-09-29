# Failure Example: Node.js Panorama

A v3 output for "Node.js 核心原理". Visually polished, factually mostly right, and still a failure against this skill's goal.

## What was drawn

```text
[Header banner + "一条话理解" box]
① 为什么需要 Node.js（阻塞 vs 事件循环 two cards）
② 整体架构（用户 → V8 → 绑定层 → libuv, + module list）
③ 事件循环六阶段（table + "循环执行" bracket）
④ 非阻塞 I/O 四步（fs.readFile example + actor strip）
⑤ 同步 / microtask / macrotask / 事件循环（vertical list）
⑥ 为什么能高效处理并发（four checkmarks）
⑦ 常见误区（four red rows）
[Footer: 核心认知 chain of 7 boxes + "一句话总结"]
```

## Why it fails

| Check | Result |
|---|---|
| §0 traceable question | None. The title is the topic. Nothing is traced. |
| Spine | Seven independent narratives. The actual mechanism is split across ②, ③, ④, ⑤ and the footer. |
| One target per image | ⑥ is a recap target, ⑦ a correction target, footer a recap target. |
| Axes | No time axis, yet the central claim ("单线程高效处理大量并发") is about simultaneity. Concurrency is asserted by checkmark text, never shown. |
| Lanes / crossings | ④'s actor strip is the only place control crosses between JS and libuv/OS, and it is a small sub-panel. |
| Attachment | Architecture ②, phases ③ and queues ⑤ are not connected to each other or to ④. |
| Panel count | 7 titled panels + header + footer (target: 0). |
| Mask test | Without prose: "there is V8, there is libuv, there are six phases, there are queues". The viewer cannot read off that JS continues while I/O is pending, or that callbacks wait for JS to be free. |
| Honesty | ④ says "OS 负责实际的 I/O" for `fs.readFile`; in libuv, file I/O runs on the **thread pool**, and only sockets use kernel readiness (epoll/kqueue/IOCP). A proposed "Task A 继续" redraw would also imply resumption; callbacks run on a new stack. |

## Root cause

The v3 skill had the rules ("do not create independent cards", "visual reconstruction test") but:

1. the topic was never rewritten into a question, so the target defaulted to "explain Node.js";
2. "Structural" narrative was an accepted option, so a panorama looked compliant;
3. no rule said that a concurrency claim needs a time axis;
4. validation was self-assessed, not measured;
5. the image spec did not push back on the generator's default layout (banner + numbered cards + footer).

## Redraw

See `golden-examples/nodejs-event-loop.md`: one swimlane timeline, three requests, one JS lane, overlapping I/O lanes, a queue band, five anchored callouts.

## Lesson

> Correct panels do not add up to an explanation. If the viewer has to connect the panels, the image has handed its main job to the viewer.
