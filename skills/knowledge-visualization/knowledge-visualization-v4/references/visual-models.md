# Visual Models

Select the model after §5 (axes, lanes, crossings). Never as the first step.

| Narrative / structure | Model | Use when |
|---|---|---|
| Execution across actors; concurrency; waiting | **Swimlane timeline with control handoffs** | the claim involves "while", "without waiting", "single X serves many Y" |
| A driver repeatedly advances a task | Loop on a spine | executor/task, game loop, control loop; one task in focus |
| Mechanism | Mechanism diagram | input → transformation → output |
| Execution (single actor) | Flow | one path, few actors |
| State changes | State diagram | the object's state is the point |
| Causality / feedback | Causal loop diagram | reinforcing/balancing loops |
| Composition | Architecture | only if §0 recorded "no traced object" |
| Differences | Comparison on shared dimensions | A vs B |
| Temporal change | Timeline | history, evolution |
| Spatial relationship | Map | location matters |
| Mechanism + controls | Layered mechanism | a core path plus the knobs that select/modify it |

`Infographic` is not a knowledge model. If a schematic communicates the mechanism better, use the schematic.

## Swimlane timeline with control handoffs

```text
            time ─────────────────────────────────────────────▶
JS thread   [A: handler→readFile()] [B: handler→query()] [C…]  ░░idle░░ [A cb] [B cb] [C cb]
                        │ hand off           │ hand off                  ▲       ▲      ▲
queue       ··········· │ ·················· │ ··········· ● A done ─────┘  ●B ──┘  ●C ─┘
                        ▼                    ▼               ▲            ▲       ▲
thread pool             [──── read a.txt ────────────────────┘            │       │
OS / epoll                                   [──── wait DB socket ────────┘       │
```

What it makes visible without prose:

- The top lane never overlaps itself → single-threaded.
- Bottom lanes overlap → I/O is concurrent.
- Handoff edges go down and the top lane immediately continues → non-blocking.
- Completion edges go up into a queue and wait if the top lane is busy → callbacks are not preemptive.
- Idle is visible → the thread waits for *any* event, not *a specific* one.

## Loop on a spine

Use when one task and its driver are the whole story (Rust async golden example). If the target adds "others run meanwhile", upgrade to a swimlane timeline.
