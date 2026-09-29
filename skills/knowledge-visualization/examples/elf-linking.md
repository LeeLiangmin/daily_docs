# ELF Relocation

## Question

Why does an object file contain relocation information?

## Cognitive target

Understand why addresses cannot always be finalized during compilation.

## Narrative

```text
source
  ↓
compiler
  ↓
object file
  ├── machine code
  ├── symbols
  └── relocation records
          ↓
        linker
          ↓
   final layout / resolved references
          ↓
     executable
```

The key visual idea is that information is carried forward because final placement is not yet known. Do not turn this into a catalog of ELF sections.
