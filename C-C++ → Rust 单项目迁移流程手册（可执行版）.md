# C/C++ → Rust 单项目迁移流程手册（可执行版）

## 0. 使用方式

这套流程用于管理一个 C/C++ → Rust 的迁移项目。

使用时只需要关注 4 个问题：

1. **现在处于哪个阶段？**
2. **这一阶段要做什么？**
3. **必须产出什么？**
4. **满足什么条件才能进入下一阶段？**

项目全过程分为 8 个阶段：

```text
0. 项目准入
   ↓
1. 基线建立
   ↓
2. 迁移设计
   ↓
3. 环境准备
   ↓
4. 实施控制
   ↓
5. 问题处置   ← 贯穿实施过程
   ↓
6. 验证准出
   ↓
7. 交付运维
```

---

# 1. 一页流程总览

| 阶段 | 要回答的问题 | 关键动作 | 核心产物 | 完成标志 |
|---|---|---|---|---|
| 0. 项目准入 | 为什么迁？适合迁吗？ | 明确诉求、范围、风险、验收目标 | Objective & Assessment | GO / Conditional GO |
| 1. 基线建立 | 迁之前是什么状态？ | 固定功能、性能、资源、安全现状 | Baseline Report | Baseline 可重复 |
| 2. 迁移设计 | 准备怎么迁？ | 明确架构、边界、顺序、FFI、回退 | Migration Design | 设计评审通过 |
| 3. 环境准备 | 能不能稳定开工？ | Toolchain、Build、CI、Test、Benchmark | Environment Checklist | Build/Test/CI Ready |
| 4. 实施控制 | 怎么把代码迁完？ | 开发、Review、持续验证 | Source + Execution Record | 实施完成 |
| 5. 问题处置 | 出问题怎么办？ | Issue、分析、升级、ADR | Issue / ADR | Blocker 关闭或接受 |
| 6. 验证准出 | Rust 能否替代原系统？ | 功能、集成、性能、安全、兼容验证 | Verification Report | 验收通过 |
| 7. 交付运维 | 接收方最终拿到什么？ | 打包、交付、回退、维护移交 | Delivery Package | Delivery Checklist 完成 |

---

# 2. Phase 0 — 项目准入

## 目标

回答两个问题：

> 为什么要迁 Rust？

以及：

> 这个项目是否值得、是否具备条件进行迁移？

---

## 输入

开始前需要：

- C/C++ 项目基本信息；
- 迁移方提出的需求；
- 源码；
- 构建方式；
- 测试情况；
- 目标平台；
- 关键约束。

---

## 要做的事

### Step 1：明确迁移诉求

不能只写：

> “需要迁 Rust。”

必须明确具体诉求，例如：

- 降低内存安全风险；
- 消除 UAF / OOB；
- 降低维护成本；
- 保持或提高性能；
- 降低内存占用；
- 减少 Binary Size；
- 提高跨平台能力；
- 改善并发安全；
- 降低依赖风险；
- 改善长期维护能力。

---

### Step 2：把诉求转成可验证目标

例如：

| 迁移诉求 | 当前状态 | 迁移目标 | 验证方式 | 验收标准 |
|---|---|---|---|---|
| 内存安全 | 存在 UAF | 消除迁移范围同类风险 | Security Review | 无 Critical |
| 性能保持 | p99 = 20 ms | 不退化超过 5% | Benchmark | ≤21 ms |
| 内存控制 | RSS = 500 MB | 不高于原系统 | Workload Test | ≤500 MB |
| API 兼容 | API v2 | 调用方无需修改 | Integration Test | 100% compatible |

规则：

> 没有验证方式和 Acceptance Criteria 的诉求，不能作为正式项目目标。

---

### Step 3：确认迁移范围

必须明确：

```text
In Scope
Out of Scope
```

例如：

```text
In Scope:
- parser
- storage
- cache

Out of Scope:
- UI
- legacy plugin
- deployment system
```

---

### Step 4：做迁移可行性评估

至少检查：

- 原项目是否可以稳定构建；
- 是否可以运行；
- 是否有测试或参考输出；
- C++ ABI 依赖是否严重；
- 是否存在 inline assembly；
- 是否有硬件强依赖；
- 是否有私有二进制依赖；
- 是否有实时性要求；
- 是否高度依赖 undefined behavior；
- 是否能建立迁移后的验证方式。

---

### Step 5：确定风险等级

建议只使用：

```text
Low
Medium
High
```

---

### Step 6：提前建立 Delivery Checklist

项目启动时就明确最终要交什么。

不要等到项目结束再整理。

---

## 产物

### Objective & Assessment

至少包含：

- Migration Motivation
- Current Pain
- Scope
- Expected Outcome
- Acceptance Criteria
- Major Constraints
- Key Risks
- Risk Level
- Required Deliverables
- GO / Conditional GO / NO-GO

---

## 检查点

- [ ] 为什么迁已经明确
- [ ] Scope 已明确
- [ ] Out of Scope 已明确
- [ ] 迁移目标可验证
- [ ] Acceptance Criteria 已定义
- [ ] 主要风险已识别
- [ ] 最终交付内容已初步确定
- [ ] 项目得到 GO / Conditional GO

---

## 下一步

满足后：

> → Phase 1 基线建立

---

# 3. Phase 1 — 基线建立

## 目标

回答：

> 迁移前 C/C++ 系统到底是什么状态？

Baseline 是后面所有验证的比较基准。

---

## 输入

需要：

- Phase 0 的迁移目标；
- Acceptance Criteria；
- 原 C/C++ 系统；
- 测试环境；
- 性能测试环境。

---

## 要做的事

### Step 1：固定测试环境

记录：

- Hardware
- OS
- Compiler
- Compiler Flags
- Dataset
- Workload
- Runtime Configuration

---

### Step 2：建立功能基线

执行：

- Functional Test
- Regression Test
- Integration Test
- Golden Test（如适用）

记录：

```text
Test Count
Pass
Fail
Known Failure
```

---

### Step 3：建立性能基线

只测项目真正关心的指标。

例如：

- latency；
- throughput；
- CPU；
- RSS；
- peak memory；
- allocation；
- startup time。

---

### Step 4：记录 Binary Size

统一构建方式后记录：

```text
C++ Release Binary Size
```

后续 Rust 必须用对应 Release 条件比较。

---

### Step 5：建立资源和稳定性基线

按项目需要记录：

- memory；
- FD；
- thread；
- CPU；
- long-running stability；
- crash；
- leak。

---

### Step 6：建立安全基线

根据项目条件执行：

- ASan
- UBSan
- TSan
- static analysis
- dependency scan
- known CVE / CWE

---

### Step 7：记录 Known Issues

不要因为原系统存在缺陷就隐藏。

例如：

```text
B-01 Known UAF
B-02 Known Data Race
B-03 Memory Leak
B-04 Performance Bottleneck
```

后续可以验证 Rust 是否真正解决。

---

## 产物

### Baseline Report

建议只保留：

1. Test Environment
2. Functional Baseline
3. Integration Baseline
4. Performance Baseline
5. Binary Size
6. Resource Baseline
7. Security / Known Issues

---

## 检查点

- [ ] Phase 0 的每个关键验收指标都有 Baseline
- [ ] 测试环境已固定
- [ ] 功能结果可以重复
- [ ] 性能数据可以重复
- [ ] Binary Size 已记录
- [ ] 已知缺陷已记录
- [ ] 安全现状已记录

---

## 下一步

> → Phase 2 迁移设计

---

# 4. Phase 2 — 迁移设计

## 目标

回答：

> 到底怎么迁？

重点不是做一份完整的软件架构设计书，而是把迁移路径说清楚。

---

## 输入

- Objective & Assessment
- Baseline
- C/C++ Architecture
- API / ABI / Dependency Information

---

## 要做的事

### Step 1：确定迁移边界

说明：

```text
C/C++ 部分
Rust 部分
二者边界
```

---

### Step 2：确定迁移方式

例如：

- 整体替换；
- 模块替换；
- Library replacement；
- C ABI；
- FFI；
- IPC；
- transitional hybrid。

---

### Step 3：定义 Migration Sequence

明确顺序，例如：

```text
Utility
   ↓
Parser
   ↓
Storage
   ↓
Network
   ↓
Main
```

---

### Step 4：设计接口与兼容策略

重点说明：

- API 是否变化；
- ABI 怎么处理；
- C/C++ → Rust 如何调用；
- Rust → C/C++ 如何调用；
- protocol/file format 是否保持兼容。

---

### Step 5：设计 Unsafe Strategy

默认：

> Safe Rust first.

如果必须 unsafe，需要规定：

- 为什么需要；
- unsafe 放在哪里；
- Safety Invariant；
- 如何 Review；
- 如何验证。

---

### Step 6：设计 Rollback

必须回答：

> Rust 版本上线失败，怎么切回原版本？

---

### Step 7：定义验证策略

提前确定：

- Functional
- Integration
- Differential
- Performance
- Security
- Compatibility

---

## 产物

### Migration Design

建议控制在真正有用的内容：

1. Scope
2. Current / Target Architecture
3. Migration Boundary
4. Migration Sequence
5. API / ABI / FFI
6. Unsafe Strategy
7. Rollback
8. Verification Strategy

---

## 检查点

- [ ] Scope 与 Phase 0 一致
- [ ] C++ / Rust 边界明确
- [ ] Migration Sequence 明确
- [ ] API / ABI / FFI 已明确
- [ ] unsafe 管理方式明确
- [ ] Rollback 可执行
- [ ] Verification Strategy 已明确
- [ ] Design Review 通过

---

## 下一步

> → Phase 3 环境准备

---

# 5. Phase 3 — 环境准备

## 目标

回答：

> 现在具备正式开工条件了吗？

这个阶段只需要 Checklist，不需要长报告。

---

## 输入

- Migration Design
- Target Platform
- Baseline Test
- Required Toolchain

---

## 要做的事

准备：

- Rust toolchain；
- C/C++ toolchain；
- linker；
- target；
- dependency；
- build；
- test；
- CI；
- benchmark；
- security tools。

---

## Environment Checklist

- [ ] Rust version 固定
- [ ] Target triple 固定
- [ ] C/C++ compiler 固定
- [ ] Clean environment build 成功
- [ ] Release build 成功
- [ ] Rust test 可执行
- [ ] 原 C/C++ test 可执行
- [ ] Integration Test 可执行
- [ ] Benchmark 可执行
- [ ] Binary Size 可稳定测量
- [ ] Security Scan 可执行
- [ ] CI Pipeline 可用
- [ ] 构建产物可保存

---

## 产物

### Environment Checklist

以及必要的：

- build scripts；
- CI configuration；
- toolchain file。

---

## 检查点

Checklist 全部 Required 项通过。

---

## 下一步

> → Phase 4 实施控制

---

# 6. Phase 4 — 实施控制

## 目标

回答：

> 实际迁移工作按照什么流程完成？

---

## 标准实施流程

```text
确认本次迁移范围
        ↓
确认原 C++ 行为
        ↓
确认对应 Baseline
        ↓
Rust 实现
        ↓
Build
        ↓
Unit Test
        ↓
Code Review
        ↓
Integration / Differential Test
        ↓
Performance Check
        ↓
Security / Unsafe Check
        ↓
是否存在问题？
      ↙     ↘
    Yes      No
     ↓        ↓
 Phase 5    完成
```

---

## 实施中必须坚持

### 1. 不改变未确认的行为

如果发现：

> C++ 原实现行为很奇怪。

不要直接“顺手修掉”。

先确认：

- 这是 bug？
- 还是外部依赖的真实行为？
- 是否允许修改？

---

### 2. 优先行为等价，再做优化

推荐：

```text
First:
Behavior Equivalent

Then:
Optimize
```

避免迁移、重构、优化同时发生，导致问题无法定位。

---

### 3. Unsafe 必须显式管理

发现需要 unsafe：

```text
为什么需要？
    ↓
能否 Safe Rust？
    ↓
不能
    ↓
定义 Safety Invariant
    ↓
Review
    ↓
Test
```

---

### 4. 持续对比 Baseline

不要全部迁完以后才第一次 benchmark。

实施过程中持续看：

- 功能；
- 性能；
- binary size；
- integration；
- security。

---

## 实施完成 Checklist

- [ ] Scope 内实现完成
- [ ] Build 成功
- [ ] Code Review 完成
- [ ] Unit Test 通过
- [ ] Integration Test 通过
- [ ] Differential Test 通过（如适用）
- [ ] Performance 未超阈值
- [ ] Binary Size 已检查
- [ ] Unsafe 已 Review
- [ ] Critical / Blocker = 0
- [ ] 设计文档已同步

---

## 产物

- Rust Source
- Tests
- Build Configuration
- 必要 Execution Record

---

## 下一步

正常情况：

> → Phase 6 验证准出

发现问题：

> → Phase 5 问题处置

---

# 7. Phase 5 — 问题处置

## 目标

回答：

> 迁移过程中出现问题，怎么处理，而不是谁碰到谁自己决定？

---

## 常见问题

只需要简单分类：

```text
Functional
Performance
API / ABI / FFI
Unsafe
Build
Dependency
Security
Architecture
```

---

## 标准问题处理流程

```text
发现问题
   ↓
确认影响
   ↓
是否阻塞迁移？
   ↓
分析 Root Cause
   ↓
制定解决方案
   ↓
是否影响架构/接口/验收？
        ↓
     Yes → ADR / 升级决策
        ↓
实现解决方案
   ↓
重新验证
   ↓
Close
```

---

## 普通 Issue 记录

只需要：

```text
Issue:
Impact:
Root Cause:
Solution:
Verification:
Status:
```

---

## 什么情况需要 ADR

只有重大决策，例如：

- 改变 Target Architecture；
- 修改公共 API；
- 改变兼容策略；
- 引入长期 unsafe；
- 更换关键依赖；
- 接受重大性能退化；
- 改变迁移范围；
- 改变迁移路线。

普通编译问题不要写 ADR。

---

## 检查点

进入 Phase 6 前：

- [ ] Critical Issue = 0
- [ ] Blocker = 0
- [ ] 未关闭 High Risk 已正式接受
- [ ] 重大设计变化已记录
- [ ] Issue 解决结果已重新验证

---

# 8. Phase 6 — 验证与准出

## 目标

回答：

> 有没有足够证据证明 Rust 可以替代原 C/C++？

---

## 输入

- Phase 0 Acceptance Criteria
- Baseline Report
- Rust Candidate
- Test Suite

---

## 验证顺序

建议固定：

```text
Build
  ↓
Functional
  ↓
Integration
  ↓
Compatibility
  ↓
Performance
  ↓
Resource
  ↓
Binary Size
  ↓
Security
  ↓
Reliability
  ↓
Acceptance
```

---

## Verification Summary

最终报告第一页建议只有这张表：

| Dimension | C++ Baseline | Rust Result | Acceptance | Result |
|---|---:|---:|---:|---|
| Functional | 1260 PASS | 1260 PASS | 100% | PASS |
| Integration | 45/45 | 45/45 | 100% | PASS |
| p99 | 20 ms | 19.2 ms | ≤21 ms | PASS |
| Throughput | 80K | 84K | ≥76K | PASS |
| RSS | 500 MB | 460 MB | ≤500 MB | PASS |
| Binary Size | 32 MB | 28 MB | ≤32 MB | PASS |
| API | v2 | v2 | Compatible | PASS |
| Critical Security | 2 | 0 | 0 | PASS |
| Unsafe Review | N/A | 5/5 | 100% | PASS |

---

## 准出规则

建议：

### PASS

全部 Mandatory Acceptance Criteria 通过。

### CONDITIONAL PASS

存在非 Critical 偏差，但：

- 风险明确；
- 接收方接受；
- 有后续计划。

### FAIL

以下任意出现：

- Critical 功能问题；
- Blocker；
- Mandatory Acceptance 未通过；
- Security Critical 未解决；
- 回退不可用。

---

## 产物

### Verification Report

正文保持简洁，详细日志作为附件。

---

## 下一步

PASS：

> → Phase 7 交付运维

FAIL：

> → Phase 4 / Phase 5

---

# 9. Phase 7 — 交付与运维

## 目标

回答：

> 接收方拿到以后，是否真的可以构建、部署、运行、维护？

---

## 第一步：检查 Delivery Checklist

正式交付建议包括 8 类。

| 类别 | 核心交付内容 |
|---|---|
| 设计 | Migration Design、Target Architecture、接口/FFI设计 |
| 软件 | Rust Source、构建配置、Release Binary |
| 构建 | Toolchain、Build方式、Binary Size Report |
| 测试 | Unit、Regression、Integration、Differential Test |
| 性能 | Latency、Throughput、CPU、Memory 等报告 |
| 安全 | Security Report、Unsafe Inventory、Dependency Audit、SBOM |
| 运维 | Build、Deploy、Config、Monitor、Troubleshooting、Rollback |
| 价值 | Migration Value Report |

---

## Delivery Checklist 示例

| ID | Deliverable | Required | Acceptance | Status |
|---|---|---|---|---|
| D01 | Migration Design | Y | Review Passed | DONE |
| D02 | Rust Source | Y | Build Passed | DONE |
| D03 | Release Binary | Y | Target Verified | DONE |
| D04 | Binary Size Report | Y | Baseline Compared | DONE |
| D05 | Integration Test | Y | 100% PASS | DONE |
| D06 | Performance Report | Y | Threshold Passed | DONE |
| D07 | Security Report | Y | Security Review | DONE |
| D08 | Unsafe Inventory | Y | 100% Reviewed | DONE |
| D09 | SBOM | Y | Generated | DONE |
| D10 | Operations Guide | Y | Handover Passed | DONE |
| D11 | Migration Value Report | Y | Objective Reviewed | DONE |

---

# 10. Migration Value Report

这是最终非常重要的一份交付件。

它不是重复 Verification Report。

Verification 回答：

> 合不合格？

Value Report 回答：

> 值不值得？

---

## 推荐格式

| Original Objective | Before | After | Value | Result |
|---|---|---|---|---|
| 内存安全 | 存在 UAF | ownership + unsafe isolation | 风险下降 | Achieved |
| 性能保持 | p99 20 ms | 19.2 ms | -4% | Achieved |
| 内存控制 | 500 MB | 460 MB | -8% | Achieved |
| Binary Size | 32 MB | 28 MB | -12.5% | Achieved |
| API兼容 | v2 | v2 | 无调用方修改 | Achieved |
| 可维护性 | 生命周期复杂 | ownership 明确 | 改善 | Partially Achieved |

最后回到 Phase 0：

```text
Original Objectives: 6

Achieved: 5
Partially Achieved: 1
Not Achieved: 0

Overall Migration Result:
SUCCESS
```

这样整个项目真正形成首尾闭环。

---

# 11. Project Flow Control

项目负责人日常只需要维护这一张流程状态表：

| Phase | Status | Exit Condition | Blocker | Result |
|---|---|---|---|---|
| 0 项目准入 | DONE | 诉求/范围/验收明确 | - | PASS |
| 1 基线建立 | DONE | Baseline 可重复 | - | PASS |
| 2 迁移设计 | DONE | Design Review | - | PASS |
| 3 环境准备 | DONE | Build/Test/CI Ready | - | PASS |
| 4 实施控制 | DOING | 实施 Checklist 完成 | MIG-12 | - |
| 5 问题处置 | ACTIVE | Blocker Closed | MIG-12 | - |
| 6 验证准出 | TODO | Acceptance PASS | - | - |
| 7 交付运维 | TODO | Delivery Checklist 完成 | - | - |

状态统一：

```text
TODO
READY
DOING
BLOCKED
DONE
```

---

# 12. Gate

最终 Gate 也保持简单。

```text
G0 — Migration Approved
诉求、范围、验收标准明确

        ↓

G1 — Baseline Ready
原系统参考状态可重复

        ↓

G2 — Design Ready
迁移路线和边界明确

        ↓

G3 — Environment Ready
Build / Test / CI / Benchmark 可用

        ↓

G4 — Implementation Ready for Acceptance
实现完成、Blocker 清零

        ↓

G5 — Verification Passed
Rust 满足 Acceptance Criteria

        ↓

G6 — Delivery Accepted
交付清单完成、接收方具备维护能力
```

---

# 13. 最终实际使用时，只需要维护 4 个核心对象

## A. Objective & Assessment

用于项目开始：

> 为什么迁、能不能迁、如何判断成功。

## B. Project Flow Control

用于项目过程中：

> 现在在哪、是否阻塞、能不能进入下一阶段。

## C. Delivery Checklist

从项目启动一直维护到最终交付：

> 最后要交什么、现在准备到哪里。

## D. Verification & Value Report

用于最终验收：

> 是否合格、是否实现迁移价值。

---

# 14. 最终流程闭环

```text
                  Migration Request
                         │
                         ↓
                明确迁移方诉求
                         │
                         ↓
               Objective & Assessment
                         │
             ┌───────────┴───────────┐
             ↓                       ↓
      Acceptance Criteria      Delivery Checklist
             │                       │
             ↓                       │
          Baseline                   │
             │                       │
             ↓                       │
      Migration Design               │
             │                       │
             ↓                       │
      Environment Ready              │
             │                       │
             ↓                       │
          Migration                  │
             │                       │
       ┌─────┴─────┐                 │
       ↓           ↓                 │
     Issue       Verify              │
       │           │                 │
       └─────┬─────┘                 │
             ↓                       │
      Verification Report            │
             │                       │
             ↓                       │
      Migration Value Report         │
             │                       │
             └───────────┬───────────┘
                         ↓
                  Delivery Sign-off
```

这套流程的核心不是增加管理工作，而是保证每个人始终知道：

> **为什么做 → 现在做什么 → 做到什么程度算完成 → 最终用什么证据证明 → 最后交什么。**