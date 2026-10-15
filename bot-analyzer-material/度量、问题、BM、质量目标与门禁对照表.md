# 度量、问题、BM 编号、质量目标与门禁：具体项与关系（bot-metric 1.2.3）

依据 bot-metric 1.2.3 源码与手册，数值为 ripgrep 实测（默认配置）。

## 1. 六个概念总览

| 概念 | 是什么 | 判不判对错 | 配置 | JSON 字段 | ripgrep |
|---|---|---|---|---|---|
| 度量 | 数值事实：值、分子/分母、状态 | 不判 | `[thresholds]` 只影响 *_huge_ratio 的口径 | `metrics[]` | 65 项（含规则覆盖率、遵从度各维度） |
| 规则 | 对单个函数、文件、区域或目标的检查，用 BM001–BM007 编号 | 判 | `[rules] set`、`duplication_findings`、`[thresholds]` | `rules[]`（目录） | 启用 4 条（BM001–BM004）；BM005 总是生效；BM006/BM007 默认关 |
| 问题（发现条目） | 规则的一次命中，带位置和证据 | 是判定结果 | 同上 | `findings[]` | 52 条 |
| 质量目标 | 对 7 项项目级度量设上限 | 判 | `[quality_targets]` | `quality_targets[]` | 1 项超标、5 项达标、1 项不适用 |
| 门禁 | 按阻塞策略对问题计数后的结论 | 结论 | `[rules] blocking_severities`、`blocking_rules` | `gate` | blocked，阻塞项 52 |
| 分析诊断 | 分析本身的缺口或错误，也用 BM 编号（BM1xx–BM4xx） | 不是问题 | — | `errors[]` | 0 |

## 2. BM 编号

### 2.1 规则（产生问题），严重级别全部为 warning

| BM | 名称 | rule_id | 检查对象 | 触发条件（默认阈值） | 位置种类 | 对应度量 | ripgrep |
|---|---|---|---|---|---|---|---:|
| BM001 | 函数过长 | rust.function.too_large | 每个函数 | 函数体 NLOC > `huge_function_lines`（50） | 源码区间 | function.lines.huge_ratio 的分子 | 38 |
| BM002 | unsafe 使用 | rust.safety.unsafe_usage | 每个 unsafe 区域 | 出现即报，无阈值 | 源码区间 | safety.unsafe_density（分子是行数，不是条数） | 5 |
| BM003 | 文件过大 | rust.file.too_large | 每个文件 | 文件 NLOC > `huge_file_lines`（2,000） | 文件 | file.lines.huge_ratio 的分子 | 2 |
| BM004 | 圈复杂度过高 | rust.function.too_complex | 每个函数 | CCN > `huge_complexity`（20） | 源码区间 | complexity.cyclomatic.huge_ratio 的分子 | 6 |
| BM005 | 质量目标未达标 | rust.metric.target_exceeded | 每个质量目标 | 目标状态为 exceeded | 整个项目（无文件、无行） | quality_targets | 1 |
| BM006 | 重复代码块 | rust.code.duplicated_block | 每组重复片段 | 连续 > `duplication_min_lines`（10）行相同；需 `duplication_findings = top/all` | 源码区间 | duplication.code_ratio | 未开启 |
| BM007 | 完全重复文件 | rust.file.exact_duplicate | 每组相同文件 | 文件字节完全相同；需 `duplication_findings = top/all` | 文件 | duplication.file_exact_ratio | 未开启 |

`rules.set = "none"` 关掉 BM001–BM004，BM005 照样产生。

### 2.2 分析诊断（不是问题，不进门禁计数，但会让分析不完整或失败）

| 段 | 编号 | 含义 | 对门禁的影响 |
|---|---|---|---|
| 输入与模块 | BM101–BM113 | 模块找不到、源码读取失败、Cargo metadata 失败、输入超预算等 | 分析不完整 → partial，或输入错误 → failed |
| 解析与预算 | BM201、BM202 | Rust 解析失败；重复检测超出预算 | partial |
| 编译器提供者 | BM301、BM302 | 编译器无法启动；超时或失败 | partial |
| 配置与契约 | BM401–BM404、BM499 | 配置无效、参数无效、格式不支持、基线不兼容、内部错误 | 退出码 2 |

## 3. 度量（插件展示的 15 项，加上没展示的）

| 度量 id | 名称(缩写) | 公式 | ripgrep | 对应规则 | 对应质量目标 |
|---|---|---|---|---|---|
| size.nbnc_lines | 代码行数(NLOC) | 非空非注释行 | 40,756 | — | 代码行数增长率 ≤ 0%（需基线） |
| file.lines.average | 平均文件代码行(AFS) | NLOC / 文件数 | 370.5 | — | ≤ 300 |
| file.lines.huge_ratio | 超大文件占比(OFR) | NLOC > 2,000 的文件 / 文件数 | 1.82%(2/110) | BM003 | — |
| directory.huge_ratio | 超大目录占比(ODR) | 直接子项 > 50 的目录 / 目录数 | 0%(0/60) | 无 | — |
| function.lines.average | 平均函数代码行(AFL) | 函数体 NLOC / 函数数 | 8.52 | — | ≤ 30 |
| function.lines.huge_ratio | 超长函数占比(LFR) | NLOC > 50 的函数 / 函数数 | 1.57%(38/2,414) | BM001 | — |
| rules.conformity.function | 函数达标率(FCR) | 没有函数级问题的函数 / 函数数 | 98.3%(2,372/2,414) | BM001、BM002、BM004 | — |
| complexity.cyclomatic.average | 平均圈复杂度(ACCN) | CCN 之和 / 函数数 | 2.10 | — | ≤ 5 |
| complexity.cyclomatic.huge_ratio | 高圈复杂度函数占比(HCFR) | CCN > 20 的函数 / 函数数 | 0.25%(6/2,414) | BM004 | — |
| complexity.cca.average | 平均修正圈复杂度(AMCC) | CCA 之和 / 函数数 | 2.02 | — | — |
| complexity.cca.huge_ratio | 高修正圈复杂度函数占比(HMCR) | CCA > 20 的函数 / 函数数 | 0.21%(5/2,414) | 无 | — |
| duplication.code_ratio | 代码重复率(DLD) | 重复行 / 参与窗口的 NLOC | 5.53%(2,249/40,689) | BM006（默认关） | ≤ 10% |
| duplication.file_exact_ratio | 完全重复文件占比(DFR) | 重复组内文件 / 文件数 | 0%(0/110) | BM007（默认关） | ≤ 4% |
| safety.unsafe_density | unsafe 代码密度(UCD) | unsafe 区域内 NLOC / NLOC | 0.022%(9/40,756) | BM002 | ≤ 10% |
| redundancy.commented_code_density | 注释掉的代码密度(CCD) | 注释掉的代码段 / 千行 NLOC | 0.098(4) | 无 | — |
| complexity.cca.adequacy | CCA 适足率 | CCA ≤ 20 的函数 / 函数数 | 99.8%(2,409/2,414) | 无 | — |
| diagnostic.static_warning_density | 静态告警密度 | BM001–BM004 问题数 / 千行 NLOC（不含 BM005） | 1.25(51) | BM001–BM004 | — |
| diagnostic.compiler_warning_density | 编译告警密度 | 编译器警告 / 千行 NLOC | 不适用（未开编译器） | 无 | — |
| rules.conformity.total | 文件达标率 | 没有任何问题的文件 / 文件数 | 77.3%(85/110) | 全部 | — |
| rules.conformity.project | 项目达标 | 项目里没有任何问题时为 1 | 0%(0/1) | 全部 | — |
| rules.conformity.*.<维度> | 各维度达标率 | 按 7 个质量维度分别计算（文件、函数、项目三级） | 例：security 97.3%(107/110) | 按规则映射的维度 | — |
| rules.coverage.* | 规则覆盖率 | 被规则评估的对象 / 对象数 | 全部 100% | — | — |

后 7 行插件目前没有展示。

## 4. 质量目标（7 项）

| 目标 id | 名称(缩写) | 读取的度量 | 默认目标 | ripgrep 当前 | 状态 | 后果 |
|---|---|---|---|---|---|---|
| max_average_file_lines | 平均文件代码行(AFS) | file.lines.average | ≤ 300 | 370.5 | exceeded | 生成 1 条 BM005 |
| max_average_function_lines | 平均函数代码行(AFL) | function.lines.average | ≤ 30 | 8.52 | passed | — |
| max_average_cyclomatic | 平均圈复杂度(ACCN) | complexity.cyclomatic.average | ≤ 5 | 2.10 | passed | — |
| max_code_duplication_ratio | 代码重复率(DLD) | duplication.code_ratio | ≤ 10% | 5.53% | passed | — |
| max_file_duplication_ratio | 完全重复文件占比(DFR) | duplication.file_exact_ratio | ≤ 4% | 0% | passed | — |
| max_unsafe_density | unsafe 代码密度(UCD) | safety.unsafe_density | ≤ 10% | 0.022% | passed | — |
| max_code_size_growth_ratio | 代码行数增长率(NLOC) | size.nbnc_lines 与基线比较 | ≤ 0% | 无基线 | not_applicable | check 时让门禁变 partial |

目标状态共 5 种：passed、exceeded、partial、unknown、not_applicable。可用 `disabled_targets` 关闭某项目标。

## 5. 门禁

### 5.1 gate 字段

| 字段 | 含义 | ripgrep |
|---|---|---|
| status | passed / blocked / partial / failed | blocked |
| blocking_findings | 同时命中 blocking_severities 和 blocking_rules 的问题条数 | 52 |
| required_evidence_missing | 缺少证据无法判定的目标数（增长率无基线） | 1 |
| excluded_count | unknown_policy = exclude 时排除的未知目标数 | 0 |
| findings_by_severity | 按严重级别计数 | warning 52 |
| findings_by_rule | 按规则计数 | BM001 38、BM004 6、BM002 5、BM003 2、BM005 1 |
| blocking_severities / blocking_rules | 生效的阻塞策略 | warning、error / 空 |

### 5.2 判定顺序与退出码

| 顺序 | 条件 | gate.status | check 退出码 |
|---:|---|---|---:|
| 1 | 致命错误：输入、配置、参数无效等，没有可用报告 | failed | 2 |
| 2 | blocking_findings > 0 | blocked | 1 |
| 3 | 没有阻塞项，且：分析不完整；或增长率目标没有基线；或目标为 partial/unknown 且 unknown_policy ≠ exclude | partial | 3 |
| 4 | 其余情况 | passed | 0 |

analyze 的退出码不受问题影响（为 0），但输出的 JSON 里照样按 check 口径写出 gate。有阻塞项时，即使分析不完整也判 blocked（判定有先后）。关系图见设计稿「问题、质量目标与门禁的关系」画板。

## 6. 关系一览

| 从 | 到 | 关系 |
|---|---|---|
| `[thresholds]` | 规则 BM001、BM003、BM004 | 同一个阈值：对单个函数或文件判严格超过 |
| `[thresholds]` | 度量 *_huge_ratio | 同一个阈值，所以 LFR 的分子 = BM001 条数，OFR 的分子 = BM003 条数，HCFR 的分子 = BM004 条数 |
| 度量 | 质量目标 | 6 项目标直接读度量的值；增长率读 NLOC 和基线 |
| 质量目标 exceeded | 问题 BM005 | 每超标一项生成一条 BM005 |
| 质量目标无法判定 | 门禁 | check 时门禁变 partial |
| 问题 | 门禁 | 按阻塞策略计数；> 0 则 blocked |
| 问题 | 度量 | 计入 static_warning_density（不含 BM005）和 rules.conformity.* |
| 分析诊断 BM1xx–BM4xx | 门禁 | 分析不完整 → partial，失败 → failed |
| 规则与质量目标 | — | 层级不同：规则看单个对象（函数 > 50 行），目标看项目整体（平均 ≤ 30）；ripgrep 有 38 个函数过长，平均却只有 8.52 |
