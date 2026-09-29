# Golden Example: Rustup

This is a design reference, not a template to copy.

## Why the earlier Rustup visualization worked

It did not attempt to teach everything about rustup. It answered:

> What happens between typing `cargo`/`rustc` and executing the selected real tool?

### 1. One cognitive target

The image has a single dominant question.

### 2. One visual narrative

```text
command
  ↓
proxy
  ↓
resolution
  ↓
toolchain
  ↓
real executable
```

### 3. Supporting information attaches to the mechanism

Configuration mechanisms appear around toolchain resolution rather than becoming unrelated cards.

### 4. The visual model matches the knowledge

This is a mechanism/flow problem, so the image is organized around flow and selection.

### 5. The image is selective

Many true facts about rustup are intentionally absent.

### 6. The viewer can reconstruct the mechanism

After looking at the image, the viewer can explain the path without reading a long explanation.

## General lesson

Copy the reasoning, not the appearance:

```text
Question
→ target understanding
→ minimum sufficient structure
→ visual narrative
→ matching visual model
```
