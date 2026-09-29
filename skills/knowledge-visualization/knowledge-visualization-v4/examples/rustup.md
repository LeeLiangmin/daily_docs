# Rustup Toolchain

## Question

How does a `cargo`/`rustc` command reach the actual executable selected by rustup?

## Cognitive target

Understand command routing and toolchain resolution.

## Minimum sufficient structure

Primary: user command, PATH, rustup proxy, resolution, selected toolchain, real cargo/rustc.

Secondary: project toolchain configuration, environment override, directory override, default.

Omit unless asked: every rustup subcommand, installation internals, every component/target.

## Visual narrative

```text
User command
     ↓
PATH
     ↓
rustup proxy
     ↓
toolchain resolution
     ↓
selected toolchain
     ↓
real cargo/rustc
```

Configuration mechanisms enter around the resolution node. The main visual should be a mechanism/flow diagram, not a card grid.
