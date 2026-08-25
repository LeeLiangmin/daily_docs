# Technical Guardrails for Rust/C++ Value Claims

Use these rules to avoid advocacy-style overclaims.

## Result and ignored errors

Do not say `Result` makes ignored errors impossible. A `Result` can be deliberately discarded. Prefer:

> `Result<T, E>` makes failure part of the signature and, together with `#[must_use]`, `?`, and pattern matching, makes accidental error loss more visible and explicit.

## Send / Sync

Do not say `Send + Sync` means shared mutable access needs no lock.

- `Send`: values of the type may be transferred across threads when the trait holds.
- `Sync`: shared references may be used across threads when the trait holds.
- shared mutation still needs an appropriate synchronization/ownership model such as `Mutex`, `RwLock`, atomics, interior synchronization, or single-owner message passing.

If the migration contains no real concurrency redesign, do not invent a fearless-concurrency benefit.

## Safe Rust and raw pointers

Do not say Rust cannot write raw-pointer code. Rust has raw pointers, FFI, and `unsafe`. Prefer:

> The analyzed implementation remains in safe Rust for this path, so raw-pointer lifetime proof obligations are not distributed through ordinary code. Any `unsafe`/FFI escape hatches must be audited separately.

## Allocation failure

Do not describe ordinary Rust heap OOM as simply a normal recoverable panic. The default allocation-error path is generally treated as unrecoverable and may abort. Compare the actual policies:

> legacy code explicitly represented OOM as a recoverable error; the Rust implementation uses ordinary infallible allocation APIs and does not preserve that recovery contract.

Treat this primarily as a failure-policy change/trade-off unless it removes substantial real complexity.

## Modern C++ facilities

Do not claim Rust has capabilities that modern C++ plainly offers in another form. Examples include:

- `std::variant` for sum-type-like representation;
- `std::optional` for optional values;
- `std::expected` in C++23 for expected/error representation;
- RAII, smart pointers, and move semantics.

The useful comparison is usually not “C++ cannot.” Instead ask:

- Did the actual legacy code use such facilities?
- Did Rust make the model more idiomatic or pervasive?
- Are exhaustiveness, lifetime, aliasing, thread-transfer, or safe-code guarantees stronger/different?
- What historical compatibility/toolchain constraints mattered?

## Counterfactual discipline

Modern C++ is an attribution calibration, not the baseline. Keep it short unless the user explicitly asks for language comparison.

Good:

> Modern C++ could represent the same Single/Multi state using `std::variant`; therefore the representation itself is not Rust-exclusive. The real migration value remains that the legacy multimap convention was replaced by an explicit state model, while Rust enums and exhaustive matching made that model natural and compiler-visible.

Bad:

> The old C++ could simply have used `std::variant`, so this migration did not add value.


## Complexity and performance claims

Do not confuse representation simplification with asymptotic performance improvement. If both implementations are O(n), say the new representation removes reconstruction/comparison logic or better matches the domain model; do not imply a Big-O gain.

Do not infer faster/slower behavior from LOC, allocation style, container choice, or fewer branches without benchmark evidence.

## Bug-prevention claims

A reduced state space or immutable configuration is a structural/reasoning improvement. Call it “prevents a class of bugs” only when the failure mode is directly implied by a language guarantee or supported by bugs, tests, issues, or concrete unsafe behavior. Otherwise prefer:

> removes a mutable state dimension / reduces proof obligations / makes the invalid combination unrepresentable.

## Behavioral equivalence and test parity

Similar test names, broad scenario coverage, source comments, or a migration goal do not prove behavioral equivalence.

Use:

> tests provide evidence toward compatibility within the analyzed scope

unless tests were actually mapped to corresponding legacy scenarios and executed with matching outcomes. Only then claim verified parity **for those covered cases**. A passing Rust-only suite is not evidence of cross-language equivalence by itself.

## Legacy language labels

Do not label a legacy codebase “C++17” merely because it currently builds with a C++17 toolchain if its design and compatibility target are much older. Prefer:

> legacy C++ codebase, currently buildable with <toolchain>, with compatibility constraints dating to <known targets>

when evidence supports that distinction.

## Quantitative structural evidence

Numbers make a report more persuasive only when reproducible. Any claim such as “192 pointer-related sites”, “~200 LOC removed”, “700+ lines of converter code”, or “200+ assertions” must include the counting scope/method.

Good:

> 在 `SimpleIni.h` 中按 `m_pData|m_strings|CopyString|DeleteString|UndoIncrementalLoadData` 五类生命周期机制统计，共有 N 处引用；统计不含注释和测试。

Weak:

> 删除了约 200 行复杂内存管理代码。

If a clean counting method is unavailable, prefer qualitative structural evidence: name the removed symbols, call paths, state variables, or proof obligations.

## Memory-safety wording

Do not infer “no memory leaks” or “no memory bugs” merely from safe Rust or zero `unsafe`. State the failure modes that the current representation removes.

Prefer:

> 当前 owned-value + safe Rust 路径不再包含旧实现的手工 `new[]`/`delete[]`、指针归属判断和可逃逸内部裸指针，因此这些路径上的 UAF、悬空指针和重复释放证明义务消失。

Avoid:

> Rust 消除了 memory leak / 所有内存安全 bug。

## Concurrency wording

Separate four questions:

1. can a value move across threads (`Send`)?
2. can shared references cross threads (`Sync`)?
3. can shared mutation occur without synchronization?
4. did the architecture actually become concurrent or change its concurrency model?

Do not call an ordinary `&self`/`&mut self` API a “fearless concurrency redesign” when no concurrent architecture exists. At most describe the type-level mutation boundary.

## Case-level claim discipline

If a claim is already a consequence of a selected root transformation, do not re-prove it as a peer case. Reuse it as evidence inside the root case. This applies especially to:

- public API lifetime safety caused by owned storage;
- parser purity caused by abandoning pointer-backed parsing;
- rollback/helper deletion caused by building fresh owned state;
- Reset simplification caused by the same ownership model.
