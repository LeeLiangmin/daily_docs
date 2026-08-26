# C/C++ → Rust 重构项目流程与交付管理手册

> **版本：v1.0 Draft**  
> **用途：团队内部可复用的项目流程与交付 SOP**  
> **适用范围：模块级、子系统级及全量级 C/C++ 向 Rust 的迁移项目**

---

## 1. 使用说明

本手册用于指导一个 C/C++ → Rust 重构项目从立项、实施到最终交付的全过程。

它不是 Rust 编码规范，也不是某个具体项目的技术方案，而是一套项目级执行框架。

使用本手册时，项目团队应做到：

1. 项目启动时复制本手册，并根据项目实际情况裁剪不适用项；
2. 每个阶段按规定完成执行事项和阶段产物；
3. 阶段未满足准出条件时，原则上不得进入下一阶段；
4. 所有例外、重大偏差和变更必须留痕；
5. 项目开始时明确最终验收方式和交付清单；
6. 项目结束时必须回到最初迁移诉求，验证迁移价值是否实现。

本手册遵循四项基本原则：

> **诉求明确、基线先行、过程受控、结果可证。**

整个迁移过程形成如下闭环：

```text
迁移诉求
   ↓
验收标准
   ↓
基线建立
   ↓
迁移实施
   ↓
结果验证
   ↓
价值确认
   ↓
正式交付
```

---

# 2. 流程总览

整个项目划分为六个阶段。

| 阶段 | 名称 | 核心问题 | 主要结果 |
|---|---|---|---|
| 0 | 立项与准入 | 为什么迁？是否值得迁？ | 立项决策、目标与验收标准 |
| 1 | 基线建立 | 迁移前系统是什么状态？ | 可重复的 C/C++ Baseline |
| 2 | 迁移准备 | 准备怎么迁？是否具备开工条件？ | 迁移方案与工程环境 |
| 3 | 实施与过程控制 | 如何按计划完成迁移？ | Rust 实现及过程记录 |
| 4 | 验证与交付验收 | 如何证明 Rust 可以替代原实现？ | 验证证据与交付验收 |
| 5 | 上线、价值验证与复盘 | 最初迁移诉求是否真正实现？ | 价值报告与项目复盘 |

流程关系如下：

```text
┌──────────────────────┐
│ 0. 立项与准入         │
│ 为什么迁？是否值得迁？ │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ 1. 基线建立           │
│ 原系统是什么状态？     │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ 2. 迁移准备           │
│ 怎么迁？能开工了吗？   │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ 3. 实施与过程控制      │
│ 按计划实施并控制偏差   │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ 4. 验证与交付验收      │
│ 是否满足技术验收要求？ │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ 5. 上线与价值验证      │
│ 是否实现最初迁移价值？ │
└──────────────────────┘
```

---

# 3. 阶段 0：立项与准入

## 3.1 目的

阶段 0 首先回答的不是“Rust 怎么写”，而是：

> **为什么要进行这次迁移？**

必须先明确迁移方的真实诉求，再判断 Rust 是否适合解决这些问题，以及项目是否具备迁移条件。

没有明确迁移诉求和可验证成功标准的项目，不应直接进入实施阶段。

---

## 3.2 进入条件

至少具备：

- 待迁移 C/C++ 项目的基本信息；
- 迁移需求提出方；
- 基本源码和构建信息；
- 初步目标范围；
- 项目技术负责人。

---

## 3.3 迁移诉求定义

首先记录迁移方诉求。

### 迁移目标表

| ID | 迁移诉求 | 当前问题 | 期望结果 | 优先级 |
|---|---|---|---|---|
| OBJ-01 |  |  |  | Must / Should |
| OBJ-02 |  |  |  | Must / Should |
| OBJ-03 |  |  |  | Must / Should |

常见迁移诉求包括：

- 降低内存安全风险；
- 消除某类历史 CWE / CVE；
- 提高系统可靠性；
- 改善并发安全；
- 降低维护复杂度；
- 减少遗留 C/C++ 技术债；
- 保持或改善性能；
- 降低内存或 CPU 使用；
- 减小 Binary Size；
- 提升跨平台能力；
- 改善依赖和供应链安全。

“提升安全性”“提高质量”等不可验证的描述不能直接作为验收目标。

---

## 3.4 定义验收标准

每一个 Must 级迁移目标必须对应可验证的 Acceptance Criteria。

| ID | 对应目标 | 指标 | 当前状态 | 目标 / 阈值 | 验证方法 |
|---|---|---|---|---|---|
| AC-01 | OBJ-01 |  |  |  |  |
| AC-02 | OBJ-02 |  |  |  |  |

示例：

| 目标 | 当前状态 | 目标 | 验证方法 | 验收标准 |
|---|---|---|---|---|
| 保持性能 | P99 = 20 ms | 不明显退化 | Benchmark | ≤21 ms |
| 内存控制 | RSS = 500 MB | 不高于原版本 | Workload Test | ≤500 MB |
| API兼容 | API v2 | 调用方无修改 | Integration Test | 100%兼容 |
| 内存安全 | 存在 UAF 风险 | 消除同类风险 | Security Review | 无 Critical |

原则：

> **没有明确验证方法和验收标准的目标，不作为正式验收目标。**

---

## 3.5 范围确认

必须明确：

### In Scope

本次迁移包含：

- ____________________
- ____________________

### Out of Scope

本次明确不包含：

- ____________________
- ____________________

范围一旦签署，后续扩大范围必须作为变更处理。

---

## 3.6 可迁移性评估

| 评估维度 | 检查内容 | 结果 | 风险说明 |
|---|---|---|---|
| 可构建性 | 原系统是否可稳定构建 | 高 / 中 / 低 | |
| 可测试性 | 是否有测试或参考行为 | 高 / 中 / 低 | |
| 模块边界 | 是否可隔离迁移 | 清晰 / 一般 / 混乱 | |
| API / ABI | 是否存在复杂 ABI 依赖 | 低 / 中 / 高 | |
| 第三方依赖 | Rust 生态或 FFI 可行性 | 高 / 中 / 低 | |
| 内存模型 | 裸指针、共享所有权复杂度 | 低 / 中 / 高 | |
| 并发模型 | 锁、原子、多线程复杂度 | 低 / 中 / 高 | |
| 平台约束 | OS、硬件、编译器绑定 | 低 / 中 / 高 | |
| 性能约束 | 是否存在严格延迟/吞吐要求 | 低 / 中 / 高 | |
| 团队能力 | Rust 开发与 Review 能力 | 充足 / 一般 / 不足 | |

综合风险等级：

```text
□ Low
□ Medium
□ High
```

---

## 3.7 初步迁移策略

根据项目特点选择：

- [ ] 全量替换
- [ ] 模块级增量迁移
- [ ] C/C++ 与 Rust 长期混合
- [ ] 其他：____________________

选择理由：

________________________________________

此处只确定**总体迁移策略**，详细边界和实施方案在阶段 2 完成。

---

## 3.8 初始交付清单

项目启动时必须同步建立最终交付清单。

至少确认：

- 设计文档；
- Rust 源码；
- Release Binary；
- Binary Size 对比；
- 功能与回归测试结果；
- 集成测试结果；
- 性能测试结果；
- 安全验证结果；
- Unsafe 审计；
- SBOM / Dependency List；
- 部署与运维说明；
- Migration Value Report。

---

## 3.9 阶段产物

- **项目立项与准入记录**
- **Migration Objective**
- **Acceptance Criteria**
- **Scope**
- **可迁移性评估**
- **初始 Delivery Checklist**

---

## 3.10 准出签单

| 角色 | 确认事项 | 结论 | 日期 |
|---|---|---|---|
| 迁移负责人 | 迁移目标与实施可行性 | 通过 / 不通过 | |
| 架构负责人 | 范围与技术风险 | 通过 / 不通过 | |
| 安全负责人 | 安全风险与目标 | 通过 / 不适用 / 不通过 | |
| 需求/业务方 | 诉求与验收标准 | 通过 / 不通过 | |

项目决策：

```text
□ GO
□ CONDITIONAL GO
□ NO-GO
```

**未通过阶段 0，不进入阶段 1。**

---

# 4. 阶段 1：基线建立

## 4.1 目的

基线用于回答：

> **迁移之前，原 C/C++ 系统究竟是什么状态？**

后续所有“性能提高”“资源下降”“安全改善”“功能等价”的判断，都必须基于统一的 Baseline。

没有可靠 Baseline，就无法客观判断迁移结果。

---

## 4.2 进入条件

- 阶段 0 已通过；
- Scope 已确认；
- Acceptance Criteria 已定义；
- 原 C/C++ 系统可运行，或存在可信参考结果。

---

## 4.3 固定基线环境

记录：

| 项目 | 基线环境 |
|---|---|
| Hardware | |
| Operating System | |
| Compiler | |
| Compiler Flags | |
| Build Type | Release / Debug |
| Dataset | |
| Workload | |
| Runtime Configuration | |

后续 Rust 对比原则上应使用等价条件。

---

## 4.4 功能与接口基线

- [ ] 对外接口清单已确认
- [ ] 核心功能用例已确认
- [ ] Integration Test 已执行
- [ ] 边界路径已覆盖
- [ ] 异常路径已覆盖
- [ ] 已知行为差异已记录
- [ ] Golden Data / Snapshot 已建立（适用时）

已知缺陷必须单独记录。

> 重构不应默认顺手修改原系统行为。  
> 如需修复原有缺陷，应明确纳入项目范围或作为独立变更。

---

## 4.5 性能与资源基线

只测与项目目标相关的指标。

| 指标 | 测量方法 | Baseline | Acceptance Threshold |
|---|---|---:|---:|
| Throughput | | | |
| P50 Latency | | | |
| P99 Latency | | | |
| CPU | | | |
| RSS | | | |
| Peak Memory | | | |
| Startup Time | | | |
| Binary Size | | | |

Binary Size 必须使用明确、可重复的 Release 构建条件。

---

## 4.6 质量与安全基线

按项目适用情况执行：

- [ ] Existing Test Coverage 已记录
- [ ] ASan 结果已归档
- [ ] UBSan 结果已归档
- [ ] TSan 结果已归档
- [ ] Static Analysis 已归档
- [ ] Known CWE 已记录
- [ ] Known CVE 已记录
- [ ] Known Crash / Leak 已记录

目的不是单纯做扫描，而是建立：

> **Before Migration**

后续与 Rust 版本进行对比。

---

## 4.7 Acceptance Criteria 覆盖检查

必须逐项确认：

| AC ID | 验收项 | 是否存在 Baseline | Baseline Evidence |
|---|---|---|---|
| AC-01 | | Yes / No | |
| AC-02 | | Yes / No | |

所有需要 Before/After 对比的 Mandatory AC 必须存在 Baseline。

---

## 4.8 阶段产物

统一形成：

### Baseline Package

至少包括：

- Functional Baseline
- Interface Contract
- Integration Baseline
- Performance Baseline
- Resource Baseline
- Binary Size Baseline
- Security / Known Issues Baseline

具体物理文件可按项目规模合并，不强制“一项一文档”。

---

## 4.9 准出条件

- [ ] Mandatory AC 均已有对应 Baseline
- [ ] 功能参考结果可重复
- [ ] 性能数据可重复
- [ ] 测试环境已记录
- [ ] Binary Size 已记录
- [ ] Known Issues 已归档
- [ ] Baseline 已评审确认

---

# 5. 阶段 2：迁移准备

## 5.1 目的

阶段 2 回答两个问题：

> **准备怎么迁？**

以及：

> **工程上是否已经具备正式开工条件？**

本阶段同时完成 Migration Design 和 Environment Readiness。

---

## 5.2 进入条件

- Baseline 已建立；
- 关键接口和依赖已识别；
- 迁移目标和范围未发生未批准变更。

---

## 5.3 迁移方案设计

Migration Design 至少明确以下内容：

### 迁移边界

```text
Current C/C++ System
        │
        ├── 保留部分
        │
        └── 迁移部分
               ↓
             Rust
```

必须说明：

- 哪些代码迁；
- 哪些代码保留；
- Rust 与 C/C++ 在哪里交界。

---

### 迁移顺序

例如：

```text
基础工具
   ↓
Parser
   ↓
Storage
   ↓
Network
   ↓
Main Component
```

迁移顺序应有技术依据，不以 LOC 大小简单决定。

---

### API / ABI / FFI 策略

明确：

- API 是否保持兼容；
- C ABI 是否需要稳定；
- 是否依赖 C++ ABI；
- FFI 方向；
- 数据所有权；
- Error Handling；
- Callback；
- Thread Safety。

---

### Unsafe 策略

原则：

> **Safe Rust by default.**

需要 unsafe 时，应：

1. 明确为什么需要；
2. 尽量集中封装；
3. 定义 Safety Invariant；
4. 明确 invariant 由谁保证；
5. 完成独立 Review；
6. 配套必要测试或验证。

不建议以单纯“unsafe LOC 比例”作为安全 KPI。

---

### 回滚策略

必须提前明确：

- 是否支持旧实现切回；
- 是否采用 Feature Flag；
- 数据兼容方式；
- 回滚步骤；
- 回滚触发条件。

---

## 5.4 工程环境准备

### Toolchain

- [ ] Rust version 已固定
- [ ] Rust edition 已固定
- [ ] Target triple 已确认
- [ ] C/C++ compiler 已固定
- [ ] Linker 已确认
- [ ] 关键 dependency 已确认
- [ ] License / Dependency Risk 已检查

---

### Build

- [ ] Clean Build 可重复
- [ ] Release Build 可重复
- [ ] C/C++ 与 Rust 混合构建可用（适用时）
- [ ] 目标平台构建成功

---

### Verification Infrastructure

- [ ] Unit Test 可运行
- [ ] Integration Test 可运行
- [ ] Regression Test 可运行
- [ ] Differential Test 可运行（适用时）
- [ ] Benchmark 可运行
- [ ] Binary Size 可重复测量
- [ ] Security Scan 可运行

---

### CI

- [ ] Rust Build
- [ ] C/C++ Build
- [ ] Test
- [ ] clippy / rustfmt
- [ ] dependency scan
- [ ] 必要的 baseline regression check

CI 工具选择根据项目需要，不强制绑定具体工具。

---

## 5.5 阶段产物

- **Migration Design**
- **Environment Readiness Record**
- 构建与 CI 配置
- 必要的 FFI / Interface Design
- Rollback Plan

---

## 5.6 准出条件

- [ ] 迁移边界明确
- [ ] 迁移顺序明确
- [ ] API / ABI / FFI 策略明确
- [ ] Unsafe 策略明确
- [ ] Rollback 可执行
- [ ] Clean Build 成功
- [ ] CI 可运行
- [ ] 测试环境可运行
- [ ] Benchmark 可运行
- [ ] 设计评审通过

---

# 6. 阶段 3：实施与过程控制

## 6.1 目的

按照已批准的 Migration Design 完成 Rust 实现，并确保实施过程中的功能、性能、兼容性和安全偏差得到及时发现和处理。

---

## 6.2 进入条件

- 阶段 2 已完成；
- Migration Design 已批准；
- 工程环境 Ready；
- Baseline 可用于持续比较。

---

## 6.3 标准实施循环

迁移工作遵循：

```text
理解原 C/C++ 行为
        ↓
确认对应 Baseline
        ↓
Rust 实现
        ↓
Build
        ↓
Code Review
        ↓
Functional Verification
        ↓
Integration / Differential Test
        ↓
Performance / Resource Check
        ↓
Security / Unsafe Review
        ↓
是否存在偏差？
   ┌────┴────┐
  Yes        No
   ↓          ↓
问题处理     完成
```

原则：

> **先保证行为等价，再进行非必要优化。**

避免同时进行：

- 语言迁移；
- 架构重构；
- 功能修改；
- 性能优化。

如果必须同时发生，应作为明确 Change 记录。

---

## 6.4 实施过程控制

应持续关注：

- Build 状态；
- Functional Test；
- Integration Test；
- Performance；
- Memory / Resource；
- Binary Size；
- Unsafe Surface；
- Open Issues；
- Technical Debt。

LOC 转换比例可作为辅助统计，但不作为主要完成度判断依据。

---

## 6.5 问题分级处理

普通问题直接记录 Issue。

涉及以下内容的，应升级为重大 Migration Issue 或 ADR：

- 改变公共 API；
- 改变 ABI / FFI 方案；
- 改变 Target Architecture；
- 引入长期 unsafe 边界；
- 更换关键 dependency；
- 接受超出原阈值的性能退化；
- 修改迁移范围；
- 修改 Acceptance Criteria；
- 修改 Rollback Strategy。

---

## 6.6 Issue 记录最小要求

| 字段 | 内容 |
|---|---|
| Issue ID | |
| 问题描述 | |
| 影响 | |
| Root Cause | |
| 解决方案 | |
| Verification | |
| Status | |

---

## 6.7 变更控制

以下内容发生变化时必须留痕：

- Scope；
- Acceptance Criteria；
- Target Architecture；
- Delivery Requirement；
- Key Dependency；
- Release Plan。

未经确认，不允许通过“实现过程中发现更方便”直接改变原项目目标。

---

## 6.8 实施完成条件

- [ ] Scope 内目标实现完成
- [ ] Code Review 完成
- [ ] Functional Test 通过
- [ ] Integration Test 通过
- [ ] Differential Test 通过（适用时）
- [ ] Performance 未出现未处理超阈值退化
- [ ] Binary Size 已检查
- [ ] Unsafe 已 Review
- [ ] Critical Issue = 0
- [ ] Blocker = 0
- [ ] 设计变化已更新文档
- [ ] Technical Debt 已记录

---

# 7. 阶段 4：验证与交付验收

## 7.1 目的

阶段 4 回答：

> **Rust 实现是否已经满足最初定义的技术验收要求，并具备正式交付条件？**

验证不是重新发明指标。

所有最终判断原则上应追溯到阶段 0 的 Acceptance Criteria 和阶段 1 的 Baseline。

---

## 7.2 进入条件

- Implementation Complete；
- Critical / Blocker 已关闭；
- Candidate Release 可构建；
- Verification Environment 已冻结。

---

## 7.3 验证内容

根据项目 Acceptance Criteria 执行：

### 功能

- Functional Test
- Regression Test
- Differential Test

### 集成

- Integration Test
- System Test
- External Consumer Verification

### 兼容性

- API
- ABI
- Protocol
- File Format
- Persistent Data

### 性能与资源

- Throughput
- Latency
- CPU
- Memory
- Peak Memory
- Startup

### Binary

- Release Binary Size
- Before / After Comparison

### 安全

- Unsafe Inventory Review
- Dependency Security
- Fuzzing（适用时）
- Sanitizer / Miri 等适用工具
- Known Security Finding Closure

---

## 7.4 Verification Summary

最终验收报告必须提供统一摘要。

| AC ID | Metric | C/C++ Baseline | Rust Result | Acceptance | Result |
|---|---|---:|---:|---:|---|
| AC-01 | P99 Latency | 20 ms | 19.4 ms | ≤21 ms | PASS |
| AC-02 | RSS | 500 MB | 470 MB | ≤500 MB | PASS |
| AC-03 | Integration | 46/46 | 46/46 | 100% | PASS |

结果只使用：

```text
PASS
CONDITIONAL PASS
FAIL
```

Conditional Pass 必须附：

- 偏差；
- 风险；
- 接受人；
- 后续措施。

---

# 8. 正式交付清单

交付清单在阶段 0 建立，在阶段 4 完成最终确认。

## 8.1 交付矩阵

| ID | 类别 | 交付内容 | 要求 | 验收方式 | Evidence | 状态 |
|---|---|---|---|---|---|---|
| DEL-01 | 设计 | Migration Design | Mandatory | Design Review | | |
| DEL-02 | 软件 | Rust Source | Mandatory | Build + Review | | |
| DEL-03 | 软件 | Release Binary | Mandatory | Target Verification | | |
| DEL-04 | 构建 | Build / Toolchain Definition | Mandatory | Clean Build | | |
| DEL-05 | Binary | Binary Size Comparison | Mandatory | Baseline Compare | | |
| DEL-06 | 功能 | Functional / Regression Report | Mandatory | Baseline Compare | | |
| DEL-07 | 集成 | Integration Test Report | Mandatory | Target Environment | | |
| DEL-08 | 性能 | Performance & Resource Report | Mandatory | Threshold Validation | | |
| DEL-09 | 安全 | Security Assessment | Mandatory | Security Review | | |
| DEL-10 | 安全 | Unsafe Inventory | Conditional | 100% Reviewed | | |
| DEL-11 | 供应链 | SBOM / Dependency List | Mandatory | Dependency Review | | |
| DEL-12 | 运维 | Deployment / Operations Guide | Mandatory | Handover Review | | |
| DEL-13 | 运维 | Rollback Plan | Mandatory | Procedure Review | | |
| DEL-14 | 项目 | Known Issues / Technical Debt | Mandatory | Review | | |
| DEL-15 | 价值 | Migration Value Report | Mandatory | Objective Review | | |

Requirement 统一使用：

```text
Mandatory
Conditional
Optional
```

原则：

> **“文件存在”不等于“交付完成”。**

每个 Mandatory Deliverable 必须同时明确：

- 验收方式；
- 验收证据；
- 最终状态。

---

## 8.2 交付签核

| 角色 | 确认事项 | 结果 | 日期 |
|---|---|---|---|
| 技术负责人 | 实现与设计符合要求 | | |
| Verification / QA | 功能与集成验证通过 | | |
| 性能负责人 | 性能与资源满足阈值 | | |
| 安全负责人 | 安全相关交付满足要求 | | |
| 运维/接收方 | 构建、部署、回滚可执行 | | |
| 迁移需求方 | 交付范围符合约定 | | |

---

# 9. 阶段 5：上线、价值验证与复盘

## 9.1 目的

阶段 4 证明：

> **Rust 实现技术上合格。**

阶段 5 进一步回答：

> **这次迁移是否真正实现了项目开始时承诺的价值？**

二者不能混为一谈。

---

## 9.2 上线准备

- [ ] Release Plan 已确认
- [ ] 灰度策略已确认（适用时）
- [ ] Monitoring 指标已确认
- [ ] Rollback 条件已确认
- [ ] Rollback Procedure 已验证
- [ ] Known Issues 已交接

---

## 9.3 上线观察

重点观察与 Migration Objective 直接相关的指标。

例如：

- crash rate；
- security incident；
- P99 latency；
- throughput；
- memory；
- CPU；
- Binary Size / deployment footprint；
- production regression；
- operational complexity。

观察指标不得在项目结束时临时选择，应优先来自阶段 0 的原始 Migration Objective。

---

# 10. Migration Value Report

## 10.1 目的

Migration Value Report 用于回答：

> **最初为什么迁 Rust，以及最终这些诉求是否得到实现？**

它不是 Verification Report 的重复。

Verification 关注：

> **是否合格。**

Migration Value 关注：

> **是否值得。**

---

## 10.2 Value Summary

| Objective ID | 原始诉求 | Before | After | 结果 | 价值结论 |
|---|---|---|---|---|---|
| OBJ-01 | | | | Achieved / Partial / Not Achieved | |
| OBJ-02 | | | | | |

示例：

| Objective | Before | After | 结果 |
|---|---|---|---|
| 内存安全 | 存在历史 UAF | 相关生命周期由 ownership 约束，unsafe 集中审查 | Achieved |
| 性能保持 | P99 20 ms | P99 19.4 ms | Achieved |
| 内存控制 | RSS 500 MB | RSS 470 MB | Achieved |
| Binary Size | 32 MB | 28 MB | Achieved |
| API兼容 | API v2 | API v2 | Achieved |

---

## 10.3 Overall Result

```text
Original Objectives: ___

Achieved: ___
Partially Achieved: ___
Not Achieved: ___
```

总体结论：

```text
□ SUCCESS
□ PARTIAL SUCCESS
□ NOT ACHIEVED
```

---

# 11. 项目复盘

复盘不应只回答“项目延期了吗”，而应重点沉淀迁移经验。

建议回答：

1. 哪些准入判断是准确的？
2. 哪些风险在阶段 0 没有识别？
3. Baseline 是否足够？
4. 哪些 Migration Design 决策有效？
5. FFI / unsafe 是否产生新的长期负担？
6. 哪些验证最能发现问题？
7. 哪些交付件实际有价值？
8. 哪些流程属于不必要负担？
9. 下一个项目应修改什么？

复盘结果用于更新组织级 Migration SOP，而不是留在单一项目中。

---

# 12. 项目过程状态

单个项目建议维护统一状态记录：

| 阶段 | 状态 | 主要产物 | Blocker | 准出结果 |
|---|---|---|---|---|
| 0 立项与准入 | | | | |
| 1 基线建立 | | | | |
| 2 迁移准备 | | | | |
| 3 实施与过程控制 | | | | |
| 4 验证与交付验收 | | | | |
| 5 上线与价值验证 | | | | |

阶段状态统一使用：

```text
NOT STARTED
IN PROGRESS
BLOCKED
COMPLETED
```

---

# 13. 推荐项目目录

不强制要求完全一致，但建议项目交付结构能够清晰对应流程和证据。

```text
project/
│
├── src/
│   ├── rust/
│   └── legacy/                 # 如存在保留 C/C++
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   ├── differential/
│   └── benchmark/
│
├── docs/
│   └── migration/
│       │
│       ├── 00-project-initiation.md
│       │
│       ├── baseline/
│       │   ├── baseline-report.md
│       │   └── test-assets/
│       │
│       ├── migration-design.md
│       ├── environment-readiness.md
│       │
│       ├── decisions/
│       ├── issues/
│       │
│       ├── verification-report.md
│       ├── security-report.md
│       ├── performance-report.md
│       ├── binary-size-report.md
│       │
│       ├── delivery-checklist.md
│       ├── migration-value-report.md
│       └── acceptance-signoff.md
│
├── sbom/
│
└── ci/
```

小型项目允许合并文档。

原则是：

> **减少文件数量可以，但不能丢失关键证据。**

---

# 14. 全流程追溯关系

整个流程必须保持以下逻辑链：

```text
OBJ-xx
迁移诉求
    ↓
AC-xx
验收标准
    ↓
Baseline
迁移前状态
    ↓
Migration Design
如何实现
    ↓
Rust Implementation
实际结果
    ↓
Verification Evidence
是否达标
    ↓
Migration Value
是否实现预期价值
    ↓
Delivery Acceptance
正式交付
```

任何一个关键验收结论，都应该能够回答：

> 它对应哪个原始诉求？  
> Baseline 是什么？  
> Rust 的实际结果是什么？  
> 用什么证据验证？  
> 是否达到约定标准？

这是本手册最重要的质量原则。

---

# 15. 核心原则总结

一个 C/C++ → Rust 迁移项目，不应以：

> “Rust 代码写完了”

作为完成标准。

完整的项目应满足：

```text
目标明确
   +
Baseline 可信
   +
迁移过程受控
   +
技术结果可验证
   +
交付内容完整
   +
迁移价值得到确认
```

最终才能称为：

> **Migration Complete**

本手册的目标不是增加流程负担，而是让参与者在项目全过程始终清楚：

> **为什么做、现在做什么、做到什么算完成、用什么证明、最后交什么。**