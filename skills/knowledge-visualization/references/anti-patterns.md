# Anti-Patterns

## Nine-card summary

Many numbered cards, weak relationships. Find the main narrative.

## Knowledge poster for a mechanism

A central diagram is surrounded by architecture, component lists, misconceptions, summaries, and several equally prominent panels.

Why it fails:

- the viewer must decide what matters
- several independent reading paths appear
- supporting knowledge competes with the mechanism

Fix:

> Make the mechanism the dominant visual. Attach supporting knowledge to the relevant point on that mechanism.

## Everything is important

Every object has equal emphasis. Define primary, secondary, and context layers.

## Template first

A familiar template determines the content. Use knowledge → narrative → visual structure → dominance → model → composition.

## Decorative technical diagram

Visual effects dominate content. Style follows semantics.

## Complete but unreadable

Every true detail is included. Use minimum sufficient structure and a visual budget.

## Summary instead of explanation

The image says what exists but not how it works. Make mechanism/causal/temporal relationships the visual center.

## Concept inventory disguised as a diagram

A set of correctly named technical concepts can still fail to explain the mechanism.

Example failure:

```text
Future   Executor   Waker   poll   Pending   Ready
```

The concepts are present, but the important relationships are not visible.

Instead, show the dominant mechanism:

```text
Executor ──poll──→ Task/Future
                         │
                       await
                         │
                      Pending
                         │
                    wake / reschedule
                         │
                         └────→ poll again
```

## Supporting information becomes a second main line

Example:

```text
Main mechanism: A → B → C

Independent architecture path: X → Y → Z
```

If both are equally prominent, the viewer has two stories to follow.

Fix by attaching X/Y/Z to A/B/C as context, or make a separate visualization if architecture is itself the target.

## Shrink-to-fit

Too much content is packed into a small canvas by reducing font size, node size, and spacing.

Fix:

1. remove nonessential content
2. remove competing narratives
3. simplify labels
4. split only when the cognitive target cannot survive one visual

## Anti-dominance diagnostic

If a viewer can point to several regions and reasonably say “this looks like the main point,” the visualization has failed the dominance requirement.

The rule is:

> One visualization → one cognitive target → one dominant explanatory structure.
