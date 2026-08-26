# Case — <工程变化标题>

> 本模板不是固定栏目。优先写成紧凑的技术叙事，通常 3–5 个小节即可。

## 为什么重要 / 旧设计

说明真实 legacy 设计、历史约束和主要复杂度。给出关键 C/C++ 代码。

```cpp
// focused real excerpt
```

解释代码证明了什么：哪些状态、生命周期、锁、rollback、error plumbing 或人工 invariant 必须被维护。

## Rust 重构后的模型

给出新设计与关键 Rust 代码。

```rust
// focused real excerpt
```

说明变化的本质，不要停留在语法替换。

## 根本变化与 Complexity Collapse

用一段因果关系回答：

```text
旧约束/表示
→ 旧机制
→ 旧证明义务
→ 新模型
→ 什么不再需要存在/推理
```

如果本 finding 只是另一根案例的 consequence，不应单独成案。

## 价值与 Rust 的作用

说明：

- 根工程价值是什么；
- value qualification：Structural / Safety / Maintainability / Conditional / Compatibility / Trade-off；
- 哪部分来自 general redesign；
- 哪部分由 Rust-driven design 推动；
- 哪些约束由 Rust ownership/type/concurrency/safe boundary 静态保证。

modern C++ 仅在归因不清时简短校准。

## Trade-off / Evidence

只写必要内容：剩余风险、性能/兼容成本、Observed / Inferred / Counterfactual 边界。

> 若案例中出现 LOC、引用次数、测试数量等数字，必须在同一段说明统计范围与方法；无法复现则改用定性结构证据。
