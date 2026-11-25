# 强模型时代 Agent Skill 消减与重写落地方案（4 组件 + 5 步流水线）

本方案面向希望将旧版弱模型 `SKILL.md` 迁移到目标强模型、实现**内容精简、能力不弱于原版、端到端成本不升反降**的工程团队。

核心原则只有一句话：**先量化再删减、先删原句再重写、用端到端通过率与含缓存真实账单联合验收。**

---

## 一、最小可用工具组合（4 个核心组件）

| 环节 | 推荐工具 | 承担的职责 |
| :--- | :--- | :--- |
| **1. 基线、沙箱实跑与门禁** | **[NVIDIA SkillEvaluator](https://github.com/NVIDIA/SkillEvaluator)**（底层封装 [Harbor](https://github.com/harbor-framework/harbor)） | Tier 1 静态/安全检查、Tier 2 内部去重、Tier 3 隔离沙箱实跑并输出五维分数（Correctness / Discoverability / Effectiveness / Efficiency / Security）、Skill Lift 及真实 Token/耗时 |
| **2. 原子新颖度体检** | **自写轻量脚本（约 80 行）** | 复现 [Intel Nikolay Petrov 的四象限法](https://finance.biggo.com/podcast/9d20bddbfd4db37d)：把 `SKILL.md` 拆为 25–30 个原子问答，在目标强模型上跑“有/无 Skill”双臂并由跨家族模型打分，定位哪些内容强模型“本来就会”（可借用 [systrim](https://github.com/joelvarun/systrim) 的 Markdown 切分与 `[KEEP]/[DROP]` 审计报告外壳） |
| **3. 分层重构与路由裁剪** | **[SkillReducer](https://arxiv.org/html/2603.29919v2) 思路 + [Anthropic `skill-creator`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/skill-creator/skills/skill-creator/SKILL.md)** | 将正文拆成“常驻核心规则 + `references/` 按需加载模块”，并用触发集校验 `description` 压缩后不漏触发 |
| **4. 失败轨迹局部重写（按需触发）** | **[DSPy GEPA](https://github.com/gepa-ai/gepa)** 或 **[SkillRevise](https://arxiv.org/html/2606.01139v1) 风格 Prompt** | 仅在裁剪掉分或原条款失效时介入，读取失败轨迹做带“保留台账（Preserve Ledger）”的 2–3 轮有界修订；若前面删原句与分层未掉分则完全跳过 |

### 推荐的 Skill 仓库目录结构

```text
my-skill/
├── SKILL.md                  # 常驻核心：极简 description + 核心规则 + 精确操作锚点 + references 索引
├── references/               # 按需加载层（仅在 Agent 触发 read_file 时注入上下文）
│   ├── examples.md           # 精选代表性示例（每概念保留 1 个）
│   ├── templates.md          # 脚手架/配置模板
│   └── background.md         # 压缩后的背景说明
├── scripts/                  # 可执行校验脚本 / Linter（承接从 Prompt 移出的确定性硬规则）
└── evals/
    ├── evals.json            # 自动生成的正/负例 + 手工补入的线上真实难例
    └── BENCHMARK.md          # 原版 vs 瘦身版五维分、轨迹步数与真实账单基线
```

---

## 二、端到端五步落地流程

### 第 1 步：建评测集与定强模型基线（先量再改）

1. **生成评测集并补入业务难例**：
   ```bash
   skillevaluator create-eval-dataset ./my-skill --full
   ```
   上述命令会生成包含显式、隐式、上下文、负例四类的 `evals/evals.json`。在此基础上，**手工补入 3–5 条来自近期线上日志的真实难例**，能写确定性断言（`pytest`、文件存在性、Schema 校验）的优先写硬断言。
2. **在目标强模型上跑原版基线**：
   ```bash
   skillevaluator tier3 evaluate ./my-skill \
     --agents <your-agent-harness> \
     --env-mode docker
   ```
   关键用例建议至少跑 **3 次重复**以平滑方差，产出原版基线 `BENCHMARK.md`（记录五维分数、Skill Lift、含 Prompt Caching 的真实费用以及探索/验证步数）。
3. **升级与瘦身解耦发布**：先用原版 Skill 把线上模型切到目标强模型并稳定运行，再进入下一步裁剪，避免换模型与瘦身混在同一版本里无法归因（[Joinloop, 2026](https://joinloop.co.in/blog/llm-scaffolding-ablation-model-upgrades)）。

---

### 第 2 步：双通道体检，把每条指令归入明确清单

1. **通道 A：静态去重 + 护栏锁定 + 过期流程扫雷**
   - 先跑静态校验与内部去重（无需重型沙箱）：
     ```bash
     skillevaluator tier1 validate ./my-skill
     skillevaluator tier2 dedup ./my-skill
     ```
   - 若使用 Claude Code，可顺手跑 `/doctor prompt-audit` 与 `/skill-doctor` 清理僵尸 Skill、互相冲突规则与仓库可推导内容（[Claude Code 文档](https://code.claude.com/docs/en/best-practices)）。
   - **可逆性检验与硬规则下沉**：对每条强约束问一句“错一次能不能撤回？”不能撤回的合规/安全红线（如禁读 `.env`、禁直推生产）优先迁出 Prompt 改为 **Hook / Linter / 权限白名单**；暂留文本的统一打上 `<!-- [GUARDRAIL] -->` 标记，豁免后续裁剪。
   - **重点标出“过度流程”拐杖**：专门标出无条件要求“全量跑测试 / 二轮自检复核 / 重型多步流水线”的条款——微软研究院实证显示，过度流程占 Skill 效率退化的 **62.6%**，其中过度验证一项就占 **36.8%**（[arXiv:2608.11888](https://arxiv.org/html/2608.11888v1)）。

2. **通道 B：原子新颖度四象限扫描（单份 Skill 成本通常 < $0.5）**
   - 运行 80 行轻量脚本，把除 `[GUARDRAIL]` 外的核心条款拆为 25–30 个原子问答对，在**目标强模型**上跑“无 Skill vs 有 Skill”双臂，由**跨家族裁判模型**打分，把条款分成四堆：

| 无 Skill | 有 Skill | 归因判定 | 处置动作 |
| :--- | :--- | :--- | :--- |
| **对** | **错** | 负贡献拐杖（过度约束或干扰强模型） | **最高优先级删除** |
| **对** | **对** | 强模型已内化的通用概念（约占通用内容 70%） | **列入候选删除清单** |
| **错** | **对** | 精确参数、专有契约、环境锚点（模型仅掌握约 22%） | **锁死原句保留，禁止概括改写** |
| **错** | **错** | 表述模糊或未生效条款 | **标记转入第 4 步局部重写** |

---

### 第 3 步：保守删句 + 渐进式披露分层（不急着让 LLM 全文重写）

1. **优先做“保留原句的删减”**：依据 [Xu & Wu (2026)](https://arxiv.org/html/2607.03048v2) 的实证，直接删掉第 2 步确认的负贡献项与已知通识、保留剩余条款原句，比一次性让大模型改写（尤其是改写为结构化 Schema）安全得多（后者在实证中掉分 5–13.3 个百分点）。
2. **拆分 `references/` 按需加载层**：参照 [SkillReducer](https://arxiv.org/html/2603.29919v2)，将大段背景、示例（按概念去重留 1 个代表）、模板迁出到 `references/` 子文件；主 `SKILL.md` 只保留**核心规则 + 操作锚点**（API 签名、验证命令、阈值边界）以及每个子文件的 `when` 触发条件：
   ```markdown
   ## On-Demand References
   - `references/examples.md` — 仅在需要参考具体调用示例时读取（关键词：...）
   - `references/templates.md` — 仅在需要生成配置/代码模板时读取（关键词：...）
   ```
3. **将强制校验改为按条件触发**：把第 2 步标出的无条件全量自检改为“仅在改动涉及核心路径或测试失败时执行”，减少多余验证步数。
4. **校验路由描述**：精简 `description` 后，用 `evals.json` 中的正/负触发用例或 [Anthropic `skill-creator`](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/skill-creator/skills/skill-creator/SKILL.md) 确认不漏触发、不误触发。

---

### 第 4 步：复跑 Tier 3，核对轨迹步数并按需“回升”或“局部修订”

1. **复跑同一套 `evals/evals.json`**：
   ```bash
   skillevaluator tier3 evaluate ./my-skill-pruned \
     --agents <your-agent-harness> \
     --env-mode docker
   ```
2. **双维度核查（弥补小样本统计功效不足）**：
   - 小样本（10–30 题）的 Pass/Fail 只能拦截明显硬崩坏，测不出 3%–5% 的微弱退化（[Khatri, 2026](https://levelup.gitconnected.com/spec-driven-development-an-agent-rules-file-agents-md-e47a650450a6)）。因此复跑时除五维分数外，**必须顺带核对轨迹中“探索（read/search）”与“验证（test/check）”步数是否异常上涨**——若步数飙升，说明误删了关键操作锚点。
3. **掉分用例按需修复（上限 2–3 轮，不通过即回滚该段）**：
   - **属于“隐式规范型示例”被迁出**：直接按 [SkillReducer](https://arxiv.org/html/2603.29919v2) Gate 2 机制，把对应示例**原样回升（Promote）**回主 `SKILL.md`（通常 1–2 轮即可恢复）。
   - **属于表述歧义或第 2 步的 `错→错` 条款**：把失败轨迹交给 **[SkillRevise](https://arxiv.org/html/2606.01139v1) 风格修订器**（要求先输出 `failure_ledger` 与 `preserve_ledger` 锁定已通过用例，再改写局部段落），或交给 **[DSPy GEPA](https://github.com/gepa-ai/gepa)** 在“通过率不降 + 总 Token 最小”的帕累托前沿上自动搜索 2–3 轮。

---

### 第 5 步：四条硬门禁合入 PR，并纳入周期 CI

将 **[NVIDIA SkillEvaluator](https://github.com/NVIDIA/SkillEvaluator)** 接入 GitHub Actions / GitLab CI，设定只有同时满足以下四条硬线才允许合并瘦身版 Skill：

- [ ] **1. 质量不退化（Correctness & Effectiveness）**：均值不低于原版基线，且按任务域/难度拆切片后无明显单点退化。
- [ ] **2. 触发与安全零退化（Discoverability & Security）**：触发准确率不降、安全扫描与运行安全分零退化。
- [ ] **3. 端到端真实成本与过程效率改善（Efficiency & Real Bill）**：含 Prompt Caching 的总账单、总耗时以及探索/验证步数持平或下降，确认精简没有诱发下游盲目探索（[Xing et al., 2026](https://arxiv.org/abs/2606.09421)）。
- [ ] **4. 小步可逆发布与周期复检**：本次 PR 独立于模型升级单独灰度，保留完整 `BENCHMARK.md` 与 `git diff` 以便随时 `git revert`；每次目标模型大版本升级时自动重跑这套流水线，持续清理新的脚手架债务。

---

## 参考来源

1. NVIDIA. [SkillEvaluator GitHub 仓库](https://github.com/NVIDIA/SkillEvaluator) 与 [官方文档](https://docs.nvidia.com/skills/skillevaluator)（三层评测、Harbor 沙箱与五维 Skill Lift）。
2. Nikolay Petrov (Intel). [Your SKILL.md Is 70% Stuff the Model Already Knows](https://finance.biggo.com/podcast/9d20bddbfd4db37d)（原子级双臂新颖度四象限法）。
3. Yudong Gao et al. [SkillReducer: Optimizing LLM Agent Skills for Token Efficiency](https://arxiv.org/html/2603.29919v2)（渐进式披露分层与 Gate 2 回升机制）。
4. Xiaonan Xu, Wenjing Wu. [Shortening agent skills leaves LLM agent cost unchanged](https://arxiv.org/html/2607.03048v2)（原句删减 vs 模型重写、Prompt Caching 真实账单实证）。
5. Gen Dong et al. (Microsoft Research & UIUC). [Agent Skills Can Be Harmful: An Empirical Study of Skill-Induced Failures in LLM Agents](https://arxiv.org/html/2608.11888v1)（过度流程 62.6% 占比与 SkillTriage 差分归因）。
6. Yuxuan Liu et al. [SkillRevise: Improving LLM-Authored Agent Skills via Trace-Conditioned Skill Revision](https://arxiv.org/html/2606.01139v1)（Diagnosis + Preserve Ledger 局部修订）。
7. Lakshya A. Agrawal et al. [GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning](https://arxiv.org/abs/2507.19457)（[gepa-ai/gepa](https://github.com/gepa-ai/gepa) 帕累托反思进化）。
8. Qinghua Xing et al. [What Should a Skill Remember? Quality–Cost Trade-offs in Cost-Aware Skill Rewriting](https://arxiv.org/abs/2606.09421)（成本感知操作锚点）。
9. Anthropic. [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices) 与 [Official Skill Creator Plugin](https://github.com/anthropics/claude-plugins-official/blob/main/plugins/skill-creator/skills/skill-creator/SKILL.md)。
10. Joinloop Engineering Blog. [Scaffolding Debt: How to Test Which Parts of Your LLM Pipeline Survive the Next Model](https://joinloop.co.in/blog/llm-scaffolding-ablation-model-upgrades)（模型升级与裁剪解耦发布）。
11. Joel Varun. [systrim](https://github.com/joelvarun/systrim)（轻量指令级切分与可审计报告架构参考）。