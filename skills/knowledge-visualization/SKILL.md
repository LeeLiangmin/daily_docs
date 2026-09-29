---
name: knowledge-visualization
description: Transform a user's question into a cognitively effective visual explanation. Use when the user asks to visualize, illustrate, diagram, explain, teach, or generate an image for a knowledge topic. First identify the intended understanding, build the minimum sufficient knowledge structure, construct a visual narrative, translate the key knowledge relationships into a visual structure, establish visual dominance and budget, choose a matching visual model, compose the scene, validate reconstructability and structural accuracy, and then produce the visual. Applies to technical, scientific, historical, economic, social, geographic, educational, and other knowledge domains.
---

# Knowledge Visualization

## Core purpose

Do not turn knowledge into a picture. Turn the **structure required to understand the knowledge** into a visual experience.

The central principle is:

> Do not put all the knowledge into the image. Build one visually reconstructable knowledge path around one cognitive target.

A visualization may contain many facts, but it must have **one cognitive dominant structure**. Supporting information exists to explain that structure, not to compete with it.

Core pipeline:

```text
User question
    ↓
Understanding goal
    ↓
Knowledge model
    ↓
Minimum sufficient structure
    ↓
Visual narrative
    ↓
Visual structure
    ↓
Visual dominance + visual budget
    ↓
Visual model
    ↓
Composition + visual encoding
    ↓
Reconstruction + dominance validation
    ↓
Factual / structural validation
    ↓
Visual output
```

The most important design work happens before styling. A good visualization makes the intended relationships visible rather than merely labeling the relevant concepts.

## 1. Identify the cognitive target

Before deciding what to draw, answer:

> What should the viewer be able to explain after seeing this?

Choose **one primary cognitive target**.

Typical targets:

- How something works
- How a system is organized
- How something happens step by step
- How state changes
- Why something happens
- What constrains a system
- How two things differ
- How something changed over time
- How actors, resources, or causes interact
- How things are related spatially

Do not allow every interesting fact to become a primary target.

Write the target as one sentence. If it cannot be stated clearly, do not begin visual design.

## 2. Build the knowledge model

Extract only knowledge relevant to the target.

Identify as applicable:

- Entity
- Concept
- Relation
- Process
- State
- Cause
- Constraint
- Hierarchy
- Change
- Evidence
- Perspective

For technical topics, explicitly consider control flow, data flow, call path, ownership, lifetime, dependency, type relationship, address mapping, build/runtime boundaries, and system boundaries.

The knowledge model is an internal model, not the final image.

## 3. Reduce to the minimum sufficient structure

For every candidate element ask:

> If this element is removed, can the viewer still form the intended understanding?

If yes, remove it or move it to supporting context. If no, keep it.

Use this reduction:

```text
Known knowledge
      ↓
Relevant knowledge
      ↓
Necessary knowledge
      ↓
Visually necessary relationships
```

Minimum sufficient structure is mandatory. Completeness is not the objective.

A useful rule:

> It is better to omit a related fact than to introduce a second competing knowledge path.

## 4. Construct the Visual Narrative

Visual Narrative answers:

> How should the viewer's attention move from the starting question to the intended understanding?

Common narratives:

### Mechanism
`Input → Mechanism → Transformation → Result`

### Execution
`User action → A → B → C → Outcome`

### Causal
`Condition → Behavior → Intermediate effect → Result → Feedback`

### State
`Initial state → Trigger → New state → Next trigger`

### Structural
`Whole → Major parts → Important relationships`

### Comparison
`Question → Comparison dimensions → A/B → Meaning of differences`

### Historical
`Background → Event → Immediate consequence → Longer-term change`

### Spatial
`Where → Spatial relationship → Distribution/movement → Effect`

The narrative is not necessarily a literal sequence. It is the intended path of understanding.

Complete:

> The viewer should follow ______ to understand ______.

If this sentence is vague, do not start visual styling.

## 5. Translate the narrative into Visual Structure

This is the bridge between knowledge and drawing.

Ask:

> Which relationships must be directly visible for the viewer to reconstruct the intended understanding?

Identify the **dominant relationship** first. Examples:

- drives
- flows through
- changes into
- causes
- contains
- depends on
- maps to
- selects
- wakes / triggers
- returns to

Then identify the minimum additional relationships required to reconstruct the mechanism.

For each important relationship decide how it should become visible:

- sequence → direction / ordered positions
- control → directed edge / caller-callee arrangement
- state transition → state nodes + transition
- causality → cause → effect
- feedback → return loop
- containment → nesting / boundary
- selection → branch / selected path
- parallelism → lanes / parallel branches
- dependency → directional dependency

Before choosing the visual model, write:

> The viewer must visually perceive **[relationship]** between **[A]** and **[B]**, because it is necessary to understand **[target]**.

If the answer is only a list of concepts, Visual Structure has not been completed.

## 6. Establish Visual Dominance

Visual Dominance answers a question that Visual Structure alone does not:

> What single structure must own the viewer's attention?

Define:

```text
Primary visual
  = the one mechanism / path / relationship that carries the cognitive target

Secondary visual
  = information that explains or modifies the primary visual

Context
  = useful background that can remain peripheral

Reference detail
  = optional information that should never compete with the primary visual
```

The primary visual must have the strongest combination of:

- position
- size
- contrast
- line weight
- directional clarity
- spatial continuity

Secondary information should be physically attached to the relevant primary node or relationship whenever possible.

### Dominance rule

> One visualization may contain many objects, but it must have one visually dominant explanatory structure.

Do not create a row of equally important cards for a mechanism that has one causal or execution path.

Do not let architecture, terminology, caveats, common misconceptions, or component inventories become competing visual centers unless they are themselves the cognitive target.

## 7. Define the Visual Budget

Visual Budget controls how much visual attention each information layer is allowed to consume.

Use this qualitative budget:

```text
Primary mechanism / relationship   → most of the visual attention
Secondary explanation              → clearly less
Context / reference                → peripheral and restrained
Decoration                         → minimum
```

Do not treat the image as a knowledge container with unlimited space.

A useful diagnostic is:

> If the supporting content can be removed without breaking the primary visual, it must not occupy comparable visual weight.

Prefer removing content over shrinking every element until everything becomes equally small.

## 8. Select the visual model after Visual Structure and Dominance

Select the visual model from the knowledge structure, not from aesthetics.

- Mechanism → mechanism diagram
- Execution → flow
- State changes → state diagram
- Composition → architecture
- Causality → causal model
- Network → relationship graph
- Differences → comparison
- Temporal change → timeline
- Spatial relationship → map/spatial model
- Mechanism + controls → layered mechanism

Do not default to an infographic, dashboard, poster, or card grid.

If a simple schematic communicates the mechanism better, use the schematic.

## 9. Compose around the primary visual

Prefer:

```text
                 SECONDARY DETAIL
                        │
                        ▼
START → PRIMARY MECHANISM → RESULT
                        ▲
                        │
                 SECONDARY DETAIL
```

over an arbitrary grid of equal cards.

Secondary information should attach to the primary mechanism. Do not create independent cards unless the information is genuinely independent and necessary.

If crowded:

1. remove irrelevant content
2. remove secondary detail that does not aid reconstruction
3. remove any competing narrative
4. group related elements
5. simplify labels
6. strengthen the primary path
7. split the visual only when one visual cannot preserve the intended narrative

Do not simply shrink everything.

## 10. Validate visual reconstructability

A correct diagram is not automatically an explanatory diagram.

Perform the **Visual Reconstruction Test**:

> If the explanatory prose and most labels were removed, could a viewer still reconstruct the intended primary relationship from the visual structure?

For a mechanism, the viewer should be able to answer as applicable:

- What starts the process?
- Who drives whom?
- What changes state?
- What causes the change?
- Where does control/data flow?
- What event causes a loop or return?
- What is the result?

If these answers require reading a paragraph, the visual structure is insufficient.

## 11. Validate visual dominance

Perform the **Dominance Test**:

### Test A — Primary-only

Hide secondary information, context, labels, and decorative elements.

Ask:

> Does the remaining visual still communicate the intended mechanism or relationship?

If not, the primary structure is too weak.

### Test B — Competition

Look at the full image and ask:

> Is there another region that could plausibly be mistaken for the main explanation?

If yes, reduce or attach that region to the primary path.

### Test C — Attention path

Ask:

> Can I describe the intended visual reading path in one sentence without mentioning a second independent path?

If not, simplify or split the visualization.

## 12. Validate factual and semantic accuracy

Also validate:

- factual accuracy
- correct direction of arrows
- semantic meaning of colors
- correct state transitions
- no invented precision
- no decorative element competing with the primary path
- no visual metaphor that contradicts the real mechanism

For technical topics, distinguish clearly between:

- conceptual model
- implementation detail
- runtime behavior
- platform-specific behavior

Do not use visual simplification to imply a technically false causal relationship.

## 13. Generate the visual

Construct the image specification from the preceding reasoning. Do not use the raw user question as the image prompt.

The visual specification should contain:

- subject
- cognitive target
- starting question
- visual narrative
- minimum sufficient structure
- dominant visual relationship
- primary visual
- primary path
- secondary information
- context
- visual dominance rules
- visual budget
- visual model
- composition
- semantic encoding
- style
- text requirements
- factual/structural accuracy constraints

The generation instruction should explicitly state:

> The primary mechanism is the visual center. Supporting information must attach to it and must not form a competing card-grid or poster-like narrative.

Styling is subordinate to structure.
