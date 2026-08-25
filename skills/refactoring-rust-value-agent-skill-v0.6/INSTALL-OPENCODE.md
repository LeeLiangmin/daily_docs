# Install in OpenCode

Unzip the package. Copy the contained `refactoring-rust-value/` directory into one of OpenCode's skill locations.

## Project-local

Preferred portable location:

```bash
mkdir -p .agents/skills
cp -R refactoring-rust-value .agents/skills/
```

OpenCode-specific location:

```bash
mkdir -p .opencode/skills
cp -R refactoring-rust-value .opencode/skills/
```

Claude-compatible project location also recognized by OpenCode:

```bash
mkdir -p .claude/skills
cp -R refactoring-rust-value .claude/skills/
```

## Global OpenCode

```bash
mkdir -p ~/.config/opencode/skills
cp -R refactoring-rust-value ~/.config/opencode/skills/
```

Keep `SKILL.md` uppercase and keep the parent directory named `refactoring-rust-value`.
