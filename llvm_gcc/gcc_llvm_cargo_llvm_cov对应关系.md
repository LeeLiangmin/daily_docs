# GCC / LLVM / C++ ABI / cargo-llvm-cov 版本对应关系

> 整理人：技术参考文档  
> 最后更新：2025 年

---

## 一、GCC 与 LLVM 体系概述

### 1.1 GCC 体系

GCC（GNU Compiler Collection）是 GNU 项目的编译器套件，支持 C、C++、Fortran、Ada 等多种语言。

**关键组件：**

- `gcc` / `g++`：C / C++ 前端编译器
- `libgcc`：GCC 运行时支持库
- `libstdc++`：GNU C++ 标准库实现
- `libgcc_s`：GCC 共享运行时库（异常处理、整数运算等）
- `binutils`：链接器（`ld`）、汇编器（`as`）等工具链

**C++ ABI 相关：**

- GCC 使用 **Itanium C++ ABI**（x86-64 Linux 上通用）
- 名称修饰（name mangling）遵循 Itanium ABI 规范
- `libstdc++` 的 ABI 随 GCC 版本演进，但保持向后兼容

### 1.2 LLVM / Clang 体系

LLVM 是一套模块化的编译器基础设施，Clang 是其 C/C++/Objective-C 前端。

**关键组件：**

- `clang` / `clang++`：C / C++ 前端
- `lld`：LLVM 链接器
- `llvm-ar`、`llvm-nm`：工具链工具
- `libc++`（libcxx）：LLVM 的 C++ 标准库实现（与 `libstdc++` 并列）
- `libc++abi`（libcxxabi）：C++ ABI 支持库
- `compiler-rt`：编译器运行时（含 sanitizers、coverage instrumentation 等）
- `libclang`：Clang 的 C 接口库

**C++ ABI 相关：**

- Clang 在 Linux 上同样默认使用 **Itanium C++ ABI**，与 GCC 兼容
- 在 macOS 上使用与 Apple 的 Itanium ABI 变体兼容
- 在 Windows（MSVC 模式）上使用 **MSVC ABI**
- `libc++` 与 `libstdc++` ABI **不兼容**，不可混用

---

## 二、C++ ABI 详解

### 2.1 Itanium C++ ABI（Linux / macOS 通用）

| ABI 要素 | 说明 |
|----------|------|
| 名称修饰（Name Mangling） | 以 `_Z` 为前缀，编码命名空间、模板参数、函数签名 |
| 虚函数表（vtable） | 指针置于对象首部，遵循 Itanium 规范 |
| 异常处理 | 基于 DWARF CFI + `__cxa_*` 运行时接口 |
| RTTI | `type_info` 结构布局由 ABI 规定 |

### 2.2 MSVC ABI（Windows）

| ABI 要素 | 说明 |
|----------|------|
| 名称修饰 | 以 `?` 为前缀，微软私有格式 |
| 调用约定 | `__cdecl`、`__stdcall`、`__fastcall` 等 |
| 异常处理 | SEH（结构化异常处理） |

### 2.3 GCC libstdc++ ABI 版本演进

| GCC 版本 | ABI 变化说明 |
|----------|-------------|
| GCC 3.x | 早期 ABI，与现代版本不兼容 |
| GCC 4.x | 引入 `_GLIBCXX_USE_CXX11_ABI=0` 旧 ABI |
| GCC 5.0 | **重大 ABI 变更**：`std::string`、`std::list` 等切换到符合 C++11 标准的新 ABI（`_GLIBCXX_USE_CXX11_ABI=1`） |
| GCC 7.x | C++17 相关 ABI 补充 |
| GCC 10.x | C++20 支持，部分 ABI 扩展 |
| GCC 11.x | `std::string` 等的小对象优化（SSO）调整 |
| GCC 12+ | C++23 早期支持，进一步 ABI 稳定 |

> **重要提示：** 编译时设置 `-D_GLIBCXX_USE_CXX11_ABI=0` 可切换回旧 ABI，用于兼容预编译的旧库。

### 2.4 LLVM libc++ ABI 版本

LLVM 的 `libc++` ABI 由 `_LIBCPP_ABI_VERSION` 宏控制：

| ABI 版本 | 说明 |
|----------|------|
| v1（默认） | 兼容性优先，历史默认值 |
| v2 | 修复若干 ABI 问题（如 `std::string` 的 SSO 位布局在大端平台上的差异），LLVM 15+ 引入 |

---

## 三、GCC 版本与特性对照表

| GCC 版本 | 发布年份 | 默认 C++ 标准 | 重要特性 |
|----------|----------|--------------|---------|
| GCC 4.8 | 2013 | C++98 | C++11 基本支持 |
| GCC 4.9 | 2014 | C++98 | C++14 部分支持，regex 完整实现 |
| GCC 5.x | 2015 | C++98/C++14 | **新 C++11 ABI**，C++14 完整支持 |
| GCC 6.x | 2016 | C++14 | C++17 部分支持 |
| GCC 7.x | 2017 | C++14 | C++17 完整支持，`-std=c++17` |
| GCC 8.x | 2018 | C++14 | C++17 `<filesystem>`，C++2a 早期 |
| GCC 9.x | 2019 | C++14 | C++17 全面完善 |
| GCC 10.x | 2020 | C++14 | C++20 协程、概念（concepts）早期支持 |
| GCC 11.x | 2021 | C++17 | **默认切换 C++17**，C++20 大部分支持 |
| GCC 12.x | 2022 | C++17 | C++20 完整支持，C++23 早期 |
| GCC 13.x | 2023 | C++17 | C++23 大量支持（`std::print` 等） |
| GCC 14.x | 2024 | C++17 | C++23 进一步完善，C++26 早期 |

---

## 四、LLVM / Clang 版本与特性对照表

| LLVM/Clang 版本 | 发布年份 | 对应 GCC 兼容 ABI | 重要特性 |
|----------------|----------|-----------------|---------|
| LLVM 6.0 | 2018 | GCC 7 兼容 | C++17 基本支持 |
| LLVM 7.0 | 2018 | GCC 7/8 兼容 | coroutines TS |
| LLVM 8.0 | 2019 | GCC 8 兼容 | C++2a 早期 |
| LLVM 9.0 | 2019 | GCC 8/9 兼容 | 覆盖率（coverage）改进 |
| LLVM 10.0 | 2020 | GCC 9/10 兼容 | C++20 concepts 早期 |
| LLVM 11.0 | 2020 | GCC 10 兼容 | C++20 modules 实验性 |
| LLVM 12.0 | 2021 | GCC 10/11 兼容 | OpaquePointers 实验性 |
| LLVM 13.0 | 2021 | GCC 11 兼容 | `-fprofile-instr-generate` 改进 |
| LLVM 14.0 | 2022 | GCC 11/12 兼容 | OpaquePointers 默认启用 |
| LLVM 15.0 | 2022 | GCC 12 兼容 | **libc++ ABI v2** 引入，C++23 支持增强 |
| LLVM 16.0 | 2023 | GCC 12/13 兼容 | C++23 大量支持，`-std=c++23` 完善 |
| LLVM 17.0 | 2023 | GCC 13 兼容 | C++23 基本完整，OpaquePointers 全面切换 |
| LLVM 18.0 | 2024 | GCC 13/14 兼容 | C++26 早期，llvm-cov 改进 |
| LLVM 19.0 | 2024 | GCC 14 兼容 | C++26 进一步支持 |

---

## 五、cargo-llvm-cov 版本与 LLVM 版本对应关系

`cargo-llvm-cov` 是 Rust 的代码覆盖率工具，**本身是纯 Rust 编写的，不内嵌任何 LLVM**。它通过调用 `llvm-tools-preview` 组件中的 `llvm-profdata` 和 `llvm-cov` 二进制来工作。

### 5.1 工具链组成与依赖关系

```
┌─────────────────────────────────────────────────┐
│  rustc（内嵌了某版本 LLVM，用于编译和插桩）        │
└───────────────────────┬─────────────────────────┘
                        │ 编译时插桩，运行时生成
                        ▼
                   .profraw 文件
          （格式版本由 rustc 内嵌的 LLVM 决定）
                        │
          ┌─────────────▼──────────────┐
          │  llvm-profdata merge        │  ← 来自 llvm-tools-preview
          └─────────────┬──────────────┘    （随 rustup 安装，与 rustc
                        │                    内嵌 LLVM 版本严格匹配）
                        ▼
                   .profdata 文件
                        │
          ┌─────────────▼──────────────┐
          │  llvm-cov show/report       │  ← 同上，来自 llvm-tools-preview
          └─────────────┬──────────────┘
                        ▼
          覆盖率报告（HTML / lcov / JSON）

  cargo-llvm-cov（纯 Rust，无内嵌 LLVM）
  ────────────────────────────────────────
  负责编排上述流程：设置环境变量、调用 cargo test、
  触发 llvm-profdata / llvm-cov，最终汇总报告
```

### 5.2 为什么必须用 llvm-tools-preview 而非系统 llvm-cov

`.profraw` 是 LLVM 内部格式，**不保证跨主版本兼容**。若 `llvm-cov` 版本与 `rustc` 内嵌 LLVM 版本不一致，会报错：

```
error: Failed to load coverage: The given coverage data is out of date
       (profraw format version mismatch)
```

`llvm-tools-preview` 由 Rust 官方随每个 `rustc` 版本配套分发，保证版本严格匹配：

```bash
# 安装与当前 rustc 配套的 llvm-tools
rustup component add llvm-tools-preview

# 验证版本一致性
rustc --version --verbose | grep LLVM
# LLVM version: 18.1.7

~/.rustup/toolchains/stable-x86_64-unknown-linux-gnu/lib/rustlib/x86_64-unknown-linux-gnu/bin/llvm-cov --version
# LLVM version 18.1.7  ← 必须与上面一致
```

### 5.3 cargo-llvm-cov 与 rustc 最低版本要求对应

表中"要求的 llvm-tools LLVM 版本"即 `rustc` 内嵌的 LLVM 版本，**cargo-llvm-cov 本身不携带该 LLVM**，而是要求环境中通过 `llvm-tools-preview` 提供对应版本。

| cargo-llvm-cov 版本 | 最低 Rust 版本 | 要求的 llvm-tools LLVM 版本 | 重要变更 |
|--------------------|--------------|--------------------------|---------|
| 0.1.x | Rust 1.56 | LLVM 13 | 初始版本 |
| 0.2.x | Rust 1.57 | LLVM 13 | `--lcov` 输出格式 |
| 0.3.x | Rust 1.60 | LLVM 14 | 支持 `--branch` 分支覆盖 |
| 0.4.x | Rust 1.60 | LLVM 14 | `--json` 输出，workspace 支持改进 |
| 0.5.x | Rust 1.65 | LLVM 15 | 行覆盖率精度提升 |
| 0.6.x | Rust 1.70 | LLVM 16 | `nextest` 集成 |
| 0.7.x | Rust 1.75 | LLVM 17 | 覆盖率映射格式 v6 |
| 0.8.x | Rust 1.80 | LLVM 18 | MC/DC 覆盖率支持（条件覆盖） |

> **注意：** 表中版本对应关系反映各版本发布时的最低要求；实际使用时，`cargo-llvm-cov` 会自动探测当前 `rustc` 内嵌的 LLVM 版本，并调用匹配的 `llvm-tools-preview` 工具，无需手动指定。

### 5.4 Rust stable 与内嵌 LLVM 版本对应

| Rust 版本 | 发布时间 | 内嵌 LLVM 版本 |
|-----------|---------|--------------|
| 1.56 | 2021-10 | LLVM 13 |
| 1.60 | 2022-04 | LLVM 14 |
| 1.65 | 2022-11 | LLVM 15 |
| 1.70 | 2023-06 | LLVM 16 |
| 1.73 | 2023-10 | LLVM 17 |
| 1.78 | 2024-05 | LLVM 18 |
| 1.82 | 2024-10 | LLVM 19 |
| 1.85+ | 2025 | LLVM 19/20 |

---

## 六、GCC / LLVM / Rust 互操作与 ABI 注意事项

### 6.1 Rust 的 C ABI 兼容性

Rust 的 `extern "C"` 使用平台原生 C ABI（Linux x86-64 上即 System V AMD64 ABI），与 GCC/Clang 完全兼容。

Rust 的 `extern "C++"` 不存在——Rust 通过 C 接口（`extern "C"`）与 C++ 互操作，复杂 C++ 对象需要手动封装或使用工具（如 `cxx` crate）。

### 6.2 常见互操作方案

| 方案 | 工具 | 适用场景 |
|------|------|---------|
| C 接口封装 | `bindgen` | Rust 调用 C/C++ 库 |
| C++ 类型安全桥接 | `cxx` crate | 双向 Rust ↔ C++ 调用 |
| 系统 C++ 库链接 | `pkg-config` + 链接标志 | 链接 `libstdc++` 或 `libc++` |

### 6.3 链接器选择

| 场景 | 推荐链接器 | 说明 |
|------|-----------|------|
| GCC 工具链 | `ld`（GNU ld）或 `gold` | 默认选择 |
| LLVM 工具链 | `lld` | 速度更快，尤其对大型项目 |
| Rust 项目 | `lld` 或 `mold` | 可通过 `.cargo/config.toml` 配置 |

### 6.4 混合使用 libstdc++ 与 libc++ 的风险

- **不可将 `libstdc++` 编译的对象与 `libc++` 编译的对象直接链接**，因为两者的 `std::string`、`std::vector` 等类型内存布局不同
- 可以通过 C 接口（`extern "C"`）隔离两侧

---

## 七、覆盖率工具链版本匹配速查表

### 7.1 按 Rust 工具链选择 cargo-llvm-cov

```bash
# 第一步：安装 llvm-tools-preview（与当前 rustc 版本自动匹配）
rustup component add llvm-tools-preview

# 第二步：安装 cargo-llvm-cov（建议使用最新稳定版）
cargo install cargo-llvm-cov

# 验证版本一致性（两者 LLVM 版本必须主版本号相同）
rustc --version --verbose | grep LLVM
cargo llvm-cov --version

# 运行覆盖率
cargo llvm-cov --html
```

### 7.2 CI 环境推荐配置

| 环境 | Rust 版本 | LLVM 版本 | cargo-llvm-cov 版本 |
|------|---------|---------|-------------------|
| Ubuntu 22.04 LTS | Stable ≥ 1.70 | LLVM 16 | ≥ 0.6 |
| Ubuntu 24.04 LTS | Stable ≥ 1.78 | LLVM 18 | ≥ 0.8 |
| macOS 13/14 | Stable ≥ 1.73 | LLVM 17 | ≥ 0.7 |
| Windows (MSVC) | Stable ≥ 1.78 | LLVM 18 | ≥ 0.8 |

---

## 八、参考资料

- [GCC 版本历史](https://gcc.gnu.org/releases.html)
- [LLVM 版本历史](https://releases.llvm.org/)
- [Itanium C++ ABI 规范](https://itanium-cxx-abi.github.io/cxx-abi/)
- [cargo-llvm-cov GitHub](https://github.com/taiki-e/cargo-llvm-cov)
- [Rust Platform Support](https://doc.rust-lang.org/rustc/platform-support.html)
- [rustc LLVM 版本历史](https://releases.rs/)
- [libstdc++ ABI Policy](https://gcc.gnu.org/onlinedocs/libstdc++/manual/abi.html)
- [libc++ ABI Stability](https://libcxx.llvm.org/ABIGuide.html)