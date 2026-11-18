# Skill 裁剪验证方法

## 简介

模型能力提升后，Skill 中的部分内容可能不再产生收益，甚至拉低表现。本文先介绍评测工具 SkillEvaluator，再给出判断“是否下线、是否裁剪、裁剪后是否退化”的方法及其实施步骤。

## SkillEvaluator

### 定位

SkillEvaluator 是 NVIDIA 开源的 Python 命令行工具（包名 `skillevaluator`，Apache-2.0，Python 3.12–3.14，支持级别为 Experimental），用于评测 AI Agent 的 Skill 和 Plugin。Skill 指遵循 [Agent Skills 规范](https://agentskills.io/)、包含 `SKILL.md` 的指令文件夹。

- 仓库：<https://github.com/NVIDIA/SkillEvaluator>
- 文档：<https://docs.nvidia.com/skills/skillevaluator/>
- 安装：`pip install skillevaluator`；运行全部层级需安装 `skillevaluator[all]`。

### 三层评测

工具按成本由低到高分为三个相互独立的层级，可单独运行，也可由 `skillevaluator validate` 串联。

| 层级 | 回答的问题 | 实现方式 | 依赖 |
| --- | --- | --- | --- |
| Tier 1：验证 | Skill 是否合规、安全，Agent 能否加载 | 静态检查器（schema、密钥、PII、恶意代码、Unicode 走私等），输出满分 100 的质量分；按各 Agent 的加载规则做兼容检查 | 无需 LLM key；外部扫描器补充覆盖 |
| Tier 2：去重 | 内容是否重复或与其他 Skill 重叠 | 内容切块后比较 embedding 相似度 | embedding 与 chat 模型 |
| Tier 3：在线评测 | Skill 是否提升 Agent 的任务结果 | 有 Skill 与无 Skill 两组对照运行，grader 打分 | 模型 API、Agent、Docker 沙箱 |

扫描器无法运行或证据缺失时，结果标记为 `INCOMPLETE` 并以非零退出码返回，不视为通过。

### Tier 3 原理

Tier 3 是本文方法的基础。它以 Skill 为唯一实验变量：

1. 使用 `evals/evals.json` 中经人工审核的任务用例，每个用例包含请求和期望结果。
2. 在同一 Agent、同一模型下，分别运行无 Skill 组（基线）和有 Skill 组，每个用例可尝试多次。默认后端为 Harbor，沙箱支持 Docker、本地和 GKE。
3. grader 结合确定性检查和 LLM judge，对每次尝试按多个维度打分。
4. 按用例配对两组得分，差值为 Skill Lift，取值范围为 -1.0 到 +1.0。同时输出 pass@k 和整体 verdict。

此外，Tier 3 支持与历史运行的有 Skill 组做版本对比（`--compare-to`），并可复用历史基线（`--reuse-baseline`）。裁剪验证依赖这两项能力。

## 方法论

### 对照条件

| 条件 | 含义 |
| --- | --- |
| 基线 | 不安装 Skill，反映当前模型自身能力 |
| 原版 | 完整 Skill |
| 裁剪版 | 删除部分内容后的 Skill |

三者使用同一数据集、同一 Agent 与模型、同一 judge 和尝试次数。

### 判据

按顺序判断，前一步不成立才进入下一步。

1. 原版不如基线：Skill 在当前模型上是负收益，直接下线，不做裁剪。
2. 原版优于基线：Skill 仍有价值，进入裁剪。裁剪版相对原版没有回归，则采用裁剪版；出现回归则恢复被删内容。

```text
原版 vs 基线
  ├─ 原版 ≤ 基线 ──→ 下线
  └─ 原版 > 基线 ──→ 裁剪 → 裁剪版 vs 原版
                            ├─ 无回归 ──→ 采用裁剪版
                            └─ 有回归 ──→ 恢复被删内容或缩小范围
```

“不如”和“无回归”需要有量化口径。SkillEvaluator 的 Skill Lift 分级为：+0.05 及以上为 PASS，-0.10 至 +0.05 为 NEUTRAL，-0.10 及以下为 FAIL。NEUTRAL 区间内的差异可能来自运行波动，建议在多次尝试后取均值判断，并由使用者自行确定下线与回归的阈值。

### 前提

- 数据集需要覆盖被删内容。被删内容没有被任何用例触及时，得分不变不能证明可以删除。
- 单次运行存在模型与 judge 的波动，需要多次尝试（建议 `--n-attempts` 不少于 3）。
- 一次只删一段内容，才能把回归归因到具体改动。多段候选逐项评测，最后叠加删除并整体复测一次。
- SkillEvaluator 不提供 Skill 内容的自动消融。删哪一段、生成哪些裁剪版本，由候选生成环节完成，SkillEvaluator 只负责评测和对比每个版本。Plugin 评测中的 ablation（完整 Plugin 与拆散组件的对比）衡量的是 Plugin 的整合收益，与 Skill 内容裁剪无关。

### 候选生成：skill-ablation

裁剪分为两个环节：提出可删内容（候选生成）和验证删除无退化（实测验证）。[skill-ablation](https://github.com/siyangsun/skill-ablation) 是一个 Claude Code 插件，覆盖候选生成环节，与 SkillEvaluator 互补。

工作方式：插件读取 Skill 和新模型的 release notes，由模型对 `SKILL.md` 逐块给出判定：

- `CUT`：可删除。
- `SOFTEN`：可弱化表述。
- `KEEP`：保留。
- `UNSURE`：无法判断，附带一条用于人工测试的种子提示词。

判定严格程度随目标模型调整：opus 激进，sonnet 适中，haiku 保守。

命令：

- `/skill-ablation:scan [path]`：只读，按预计可删比例对 Skill 排序。该比例仅用于排序。
- `/skill-ablation:triage <skill>`：生成逐块判定报告、精简版 Skill、diff 和启用提示。
- `/skill-ablation:prune [--dry-run]`：删除标记为 `obsolete: true` 的 Skill，执行前需确认。

版本切换：原版移至 `variants/full.md`，`SKILL.md` 改为指向当前启用版本的符号链接，回退只需重新链接。这样原版与裁剪版同时保留，可作为 SkillEvaluator 的两个待测版本。SkillEvaluator 的 Tier 1 和 Tier 2 工作流拒绝符号链接形式的 `SKILL.md`，harness 检查也指出 Codex、Hermes、OpenClaw 会跳过此类文件。评测前需用实际文件替换符号链接。

安装：

```bash
claude plugin marketplace add siyangsun/skill-ablation
```

```bash
claude plugin install skill-ablation@skill-ablation
```

安装后重启 Claude Code。

局限：

- 判定来自模型判断，不是实测。README 说明插件尚未实现有无被删文本的对照运行，节省的 token 数为估算值（±20%）。因此 triage 的结果只能作为候选，需按本文判据用 SkillEvaluator 验证。
- 只处理 `SKILL.md`，不处理 `references/` 目录。
- 仅 `scan` 和 opus 下的 `triage` 经过作者测试；`prune`、sonnet/haiku 以及项目级 Skill 未经测试。插件管理的 Skill 和从 claude.ai 同步的 Skill 只生成报告。
- 插件更新可能覆盖符号链接。
- 项目早期阶段（截至 2026-11 约 5 次提交，0 star），仓库页面未注明许可证。

## 实施方法

### 步骤 1：评测原版与基线

```bash
# ./my-skill 含 SKILL.md 与已审核的 evals/evals.json；结果统一写入 ./results
skillevaluator tier3 evaluate ./my-skill \
  --agents codex --n-attempts 3 --pass-threshold 0.5 --results-dir ./results
```

检查方法：记录运行 ID（下文记为 `<PRIOR>`）和报告中的 Skill Lift。按判据 1 判断是否下线。继续裁剪前，先将原版提交到版本控制或另存。

### 步骤 2：生成裁剪候选

在 Claude Code 中对目标 Skill 运行：

```text
/skill-ablation:triage my-skill
```

检查方法：阅读报告和 diff，从 `CUT` 和 `SOFTEN` 块中挑出本轮要验证的一段，`UNSURE` 块需补充对应的评测用例。将选定的修改写入 `./my-skill/SKILL.md`，保持其为实际文件而非符号链接。也可以不用插件，人工选取要删除的段落。

### 步骤 3：评测裁剪版

在原目录中删除内容后运行：

```bash
# 与 <PRIOR> 的有 Skill 组做版本对比，并复用其基线
skillevaluator tier3 evaluate ./my-skill \
  --agents codex --n-attempts 3 --pass-threshold 0.5 --results-dir ./results \
  --compare-to <PRIOR> --reuse-baseline <PRIOR>
```

参数说明：

- `--compare-to`：按用例配对，计算裁剪版相对 `<PRIOR>` 有 Skill 组的差值，负值标记为回归。
- `--reuse-baseline`：复用 `<PRIOR>` 的无 Skill 基线，省去重跑。

检查方法：

```bash
# <CURRENT> 为步骤 3 的运行 ID
skillevaluator tier3 compare-versions ./my-skill \
  --current <CURRENT> --prior <PRIOR> --results-dir ./results --json
```

查看回归用例是否与被删内容相关，并确认裁剪版的 Skill Lift 仍优于基线。

### 模型升级后重测

基线复用要求解析后的模型一致，换模型后需重测基线。只测基线的命令如下：

```bash
skillevaluator tier3 evaluate ./my-skill --agents codex --skip-with-skill --results-dir ./results
```

该运行不产生 Skill Lift，用于了解新模型在任务集上的自身水平；完整的原版对比仍需按步骤 1 重新运行。

## 注意事项

- 版本对比要求两次运行的数据集、Agent 与模型、judge、尝试次数和评估器版本一致，不兼容时会在启动前被拒绝。
- 复用的基线是历史观测，不计为本次运行的独立尝试。
- 文档中未见内置的显著性检验，负差值即标记为回归，不区分波动与真实退化，需要人工结合多次运行判断。
- 改写 Skill 的描述可能影响激活，可用 Tier 3 的激活实验检查。
- Tier 3 产生模型和沙箱费用。
- 本文命令来自 SkillEvaluator 官方文档、CLI 参考与 skill-ablation 的 README，步骤 2 和步骤 3 未在本机运行验证。
