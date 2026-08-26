# C/C++ → Rust 重构价值分析

> v0.6 默认采用紧凑叙事。模板是骨架，不是表单；能合并就合并。

## 1. 执行摘要：核心转型

用 2–4 段回答：

- 真实 legacy C/C++ 的根设计/历史约束是什么；
- Rust 实现最根本改变了什么；
- 哪一组复杂机制、证明义务或误用路径因此整体消失；
- Rust 在这里是设计推动力、类型保证，还是主要只是实现语言；
- 最重要的 trade-off / compatibility change 是什么。

不要先列 Rust feature。必要时再给 3–6 个高密度结论。

## 2. 系统 Before / After

简洁说明真实 baseline、范围和最关键设计变化。只保留会影响后文价值判断的信息。

可选使用一张对比表。modern C++ counterfactual 不作为 baseline。

## 3. 核心案例

先完成 root-cause clustering 与 consequence suppression。**同一根转型通常只保留一个主案例。**

### 案例 1：<用工程变化命名>

自然组织 3–5 个部分即可：

- 旧设计为何需要这些机制，并给 Before 代码；
- 新 Rust 如何重新建模，并给 After 代码；
- 什么复杂度/证明义务不再需要；
- 工程价值与 Rust 的作用；
- 必要的 trade-off / evidence boundary。

不要把同一 ownership 根因的 API lifetime、parser、rollback、Reset 等后果再写成平级案例，除非它们有独立系统重要性。

### 案例 2：...

按价值密度继续，不设数量指标。

## 4. 支持性发现

用短段落或紧凑表格收纳低密度但有帮助的发现，例如局部 parser 简化、测试/构建生态、非核心 API 变化。

不重复核心案例。

## 5. 权衡、兼容性与证据边界

合并处理：

- conditional simplification / scope reduction；
- API/行为/failure-policy 变化；
- clone/allocation/lock/FFI/unsafe 成本；
- 尚未验证的性能或兼容性；
- Observed / Inferred / Counterfactual 边界。

所有数字都必须说明统计口径。没有 mapped + executed parity evidence 时，不声称“行为等价”。

## 6. 结论

用 2–4 段回到核心转型：

> 这次重构到底改变了什么工程现实？什么不再需要维护？Rust 为什么推动或保证了这种变化？代价是什么？

不要逐条重复前文价值列表。
