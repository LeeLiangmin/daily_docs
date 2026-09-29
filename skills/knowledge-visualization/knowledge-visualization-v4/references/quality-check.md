# Quality Check

Each item is either a measurement or a written artifact. "Looks fine" is not a result.

## Gate 0 — Question

[ ] Traced object, tracked quantity and end condition are written down.
[ ] Title of the image is the traceable question, not the topic name.
[ ] If Structural narrative: the note "no traced object" is written down with a reason.

## Gate 1 — Scope

[ ] Intended understanding fits in one sentence.
[ ] Everything in the image serves that one target. List of deferred content ("Next visuals") exists.
[ ] No misconception box, no summary strip, no standalone architecture panel.

## Gate 2 — Structure

[ ] Axes are named (x = __, y = __).
[ ] If the target mentions concurrency / waiting / ordering: a time axis exists and the claim is visible on it.
[ ] Each actor that can hold control has a lane or region.
[ ] Every crossing between lanes has a verb and one arrow style per crossing type.
[ ] Waiting and idle are drawn (queue slot, gap, hatch).
[ ] Every non-spine element is attached to a spine element by a visible connector.

## Gate 3 — Mask test (write it out)

Hide all prose. Using only node names, lane names and arrow verbs, write the story as numbered steps:

```text
1. ...
2. ...
```

[ ] Compare against the expected trace from Gate 0. Every expected step is present.
[ ] Loops / feedback / re-scheduling are visible as edges, not only as text.

## Gate 4 — Counts

[ ] Titled regions not on the spine: ___ (mechanism target: 0; max 1).
[ ] Callouts: ___ (each attached to a spine point; aim ≤ 5).
[ ] Arrows without verbs: ___ (target: 0).

## Gate 5 — Honesty at the drawn level

[ ] Resume vs. new invocation drawn correctly.
[ ] Which component actually performs each wait/operation is correct (thread pool vs. kernel readiness vs. hardware).
[ ] Push vs. poll direction correct.
[ ] No invented precision (timings, counts, phase details beyond what is claimed).

## Gate 6 — Visual

[ ] Model matches the structure (not chosen first).
[ ] Colors have one meaning each, stated in a legend if not obvious.
[ ] Decoration subordinate; the spine has the most visual weight and area.
[ ] Image spec contains explicit negative constraints (no numbered panels, no summary strip, no card grid).
