# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

Personal technical knowledge base ("daily_helper") — a curated collection of deep-dive reference documents on low-level systems programming topics. This is a **documentation-only** repository: no build system, no tests, no executable code.

## Topic Areas

- **`abi/`** — ABI (Application Binary Interface) deep-dive research: C/C++/Rust ABI compatibility, Itanium vs MSVC ABI, symbol versioning, binary formats (ELF), linking and loading. Flagship document uses the Grothendieck-style (从指称语义到操作语义的完整映射).
- **`cpp2rust_shim/`** — Practical guides for building C++ shim layers when wrapping legacy C++ in Rust via FFI. Covers STL bridging, exception handling, inheritance mapping, and the layered architecture (raw binding → safe binding → business code).
- **`llvm_gcc/`** — Version correspondence between GCC, LLVM/Clang, C++ ABI standards, and Rust's cargo-llvm-cov.
- **`代码覆盖率/`** — Code coverage guides covering both GCC (gcov/lcov) and Clang/LLVM (profdata/llvm-cov) toolchains, including CMake/Makefile integration and CI/CD setup.
- **`配置/`** — Configuration guides (SSH key-based auth setup for VSCode remote development).
- **`rust/`** — Rust ecosystem reference (PDF).

## Document Conventions

- Primary language is Chinese, with technical terms kept in English. Code examples and CLI commands are in English.
- Documents are self-contained deep-dives; prefer cross-referencing via inline paths rather than duplicating content.
- Directory-per-topic organization. Each directory may contain multiple files (markdown overviews, practical guides, and occasionally rendered HTML versions).
- Markdown is the primary format. One HTML file exists as a styled web version of a markdown document. One PDF is a compiled reference.
