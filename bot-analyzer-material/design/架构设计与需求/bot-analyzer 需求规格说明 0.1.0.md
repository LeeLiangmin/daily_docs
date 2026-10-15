---
title: Bot Analyzer 需求规格说明 0.1.0
subtitle: 对应扩展 0.1.0 · 集成 bot-metric 1.2.1+（推荐 1.2.3）
date: 2026-10-15
---

# 1 目的与范围

Bot Analyzer 是一个面向 Rust 项目的 VS Code 扩展。它把代码度量工具 [bot-metric](https://gitcode.com/xuanwu/bot-metric) 的检测结果接入编辑器：在侧栏、状态栏与编辑器中就地呈现度量、问题与门禁结论，帮助开发者定位需要重构的函数、判断项目是否通过质量门禁。分析数据全部由 bot-metric 计算，扩展只负责展示、定位与交互，不自行计算或修改判定口径。

本文描述 bot-analyzer 0.1.0 已实现的功能与验收标准，作为对当前交付版本的核对基准。结构、模块与接口见《bot-analyzer 架构设计 0.1.0》。

**范围内**：含 `Cargo.toml` 的 Rust 项目的检测与展示；侧栏（当前文件 / 整个项目两页、规则说明页签）；编辑器标记、CodeLens、悬停、快速修复与右键菜单；状态栏两项；代码项检测；Markdown 报告导出；VS Code 设置；VSIX 打包。

**范围外**：非 Cargo 构建系统；第二个度量工具；编辑器内忽略 / 抑制机制（仓库级插件配置文件，本版不存在）；自动重构与修复；网页版 VS Code 之外的编辑器（server 走 LSP 可复用，但不在验收内）；修改源码或 `bot-metric.toml`（扩展只读配置，从不写仓库文件）。

# 2 术语

| 术语 | 含义 |
| --- | --- |
| 检测 | 调用一次 bot-metric 并把结果并入当前模型。分三种：整个项目、单个文件、代码项 |
| 整个项目检测 | `bot-metric analyze <项目根> --format json`，并行追加一次「全部函数」取数（`--huge-function-lines 1 --huge-complexity 1`，把函数上限降为 1，从而拿到全部函数的行数与复杂度） |
| 单文件检测 | `bot-metric analyze <文件> --format json`，保存后先更新这个文件 |
| 代码项检测 | `bot-metric --item-at <相对路径>:<行>[:<列>]`，只检测包住某个位置的语法项（函数、impl、类型、trait、内联模块） |
| 全部函数 | 「全部函数」取数得到的项目里每个函数的 NLOC、CCN 与范围，侧栏「全部函数」分节的数据来源 |
| 问题 / 规则命中 | bot-metric 规则（BM001–BM007）产生的发现条目（finding） |
| 质量目标 | `bot-metric.toml` 里 `[quality_targets]` 对项目级度量设的目标，未达标报 BM005 |
| 门禁 | bot-metric 报告里的 `gate` 结论（通过 / 未通过 / 无法判定 / 检测失败），与 CI 同口径 |
| 待更新 | 上次项目检测超过 `botAnalyzer.analyze.projectAfterSave` 秒时，保存后不自动检测项目，状态栏给出待更新提示 |
| 波浪线 / 竖线 | 编辑器装饰：函数名、unsafe 关键字或文件首行的橙色波浪线；重复代码块整段左侧的竖线 |

# 3 用户与场景

| 用户 | 场景 | 关心什么 |
| --- | --- | --- |
| 开发者 | 在 Cargo 项目里写 Rust | 保存后立即看到这个文件的问题，超了多少；与 rust-analyzer 不冲突 |
| 代码评审人 | 看某个函数或某个类型 | 光标处的度量数字、问题原因与规则说明，能复制成报告 |
| 技术负责人 | 维护团队质量口径 | 编辑器与 CI 同口径（阈值、目标只在 `bot-metric.toml`）；门禁结论与阻塞项 |
| 平台维护者 | 分发扩展 | 平台包开箱即用；出错时能自助定位（输出日志、明确错误文案） |

# 4 功能需求

以下条目均为 0.1.0 **已实现**的行为；每条给出验收标准（AC）与对应的自动化测试（`test/` 下文件）或人工验收项。

## 4.1 工程与工具

**FR-1 工程发现（P0）**。只分析含 `Cargo.toml` 的工作区：根目录有清单就用它，没有则向下找两层（跳过 `target/`、`node_modules/`、`.git/` 与隐藏目录），取第一个找到的清单；整个项目检测只针对这一个项目。清单用 `cargo metadata --no-deps --offline` 读取（只读，不写 `Cargo.lock`、不碰 `target/`）；cargo 不可用时退回按目录归组，功能不中断。

- AC-1.1 没有 Cargo 项目时侧栏写明没有项目，不出结果。
- AC-1.2 模块路径（如 `ignore::dir::Ignore::matched_ignore`）来自 cargo metadata；取不到时按目录归组并在界面不误标模块。
- 测试：`botconfig.test.ts`（检测范围与配置指纹）、人工（无清单文件夹）。

**FR-2 二进制解析与版本要求（P0）**。查找顺序：用户设置 `botAnalyzer.botMetric.binaryPath` → 扩展自带 `bin/bot-metric(.exe)`（平台包）→ `PATH` → `~/.cargo/bin`。每个候选跑 `--version` 验证；版本须 ≥ 1.2.1。设置指定的路径不可用时直接报错，不再查其他位置；工作区设置里的路径不认（防执行仓库指定的程序）。路径两端引号自动去掉。

- AC-2.1 找不到或版本太旧时给出明确文案与「指定路径」入口。
- AC-2.2 `binaryPath` 只在用户 / 机器（machine 作用域）设置中生效。
- 测试：`layout.test.ts`（binaryPath 只认 machine 作用域）、`engine.test.ts`、手册 09 章故障排查 9.1–9.3。

**FR-3 报告契约（P0）**。只按 bot-metric 的 `analysis-report-1.2.1` 与 `1.2.3` 两种 JSON 契约读报告；读前校验身份（`tool === "bot-metric"`），不是则报「输出不是 bot-metric 的分析报告」。规则编号 BM001–BM007；1.2.3 用报告的 `rules[]` 映射，1.2.1 退回内置对照。指标状态区分 available / partial / unknown / not_applicable，「未知」显示为「—」，partial 标「部分」。

- AC-3.1 1.2.1 与 1.2.3 的真实报告（夹具）解析结果一致地驱动界面。
- AC-3.2 单次调用超时 300 秒、输出上限 128 MiB、取消信号，三者都终止整个进程树并给出明确错误。
- 测试：`process.test.ts`（取消与输出超限）、`sidebar.test.ts`（1.2.3 真实结果逐句核对）、`fixtures/`（rg-1.2.1-* 与 rg-1.2.3-*）。

## 4.2 检测时机

**FR-4 自动检测（P0）**。`botAnalyzer.analyze.on = "save"`（缺省）时：

- 打开项目时检测一次整个项目（常规分析与「全部函数」两次调用并行）；
- 首次切换到某个文件时补取这个文件的度量；
- 保存 `.rs` 后先检测这个文件（约 0.1 秒级），2 秒内没有再保存就在后台检测整个项目；
- `Cargo.toml`、`bot-metric.toml` 变化，或一次性变化 ≥ 20 个 `.rs`（切分支、生成代码等编辑器之外的变化）时重新检测整个项目；
- 项目检测进行中保存的文件，检测结束后逐个补检测。

- AC-4.1 内容与上次分析完全一样的保存：不重跑 bot-metric、不把项目结果标成过期（按内容摘要 sha256 判断）。
- AC-4.2 新的项目检测开始时取消在飞的上一轮；同一文件后发起的检测作废先发起的结果。
- AC-4.3 `analyze.on = "manual"` 时不自动检测（打开项目时仍检测一次）；文件监视触发的重检在手动模式下不生效。
- 测试：`engine.test.ts`（监视取舍、内容没变不算过期）、`lsp.test.ts`（端到端保存链路，需 BA_TEST_BINARY / BA_TEST_PROJECT）。

**FR-5 待更新（P0）**。上次项目检测用时超过 `botAnalyzer.analyze.projectAfterSave` 秒（缺省 3，0 表示从不自动）时，保存后不自动检测项目；状态栏项目项显示「待更新」，点击或执行「重新检测整个项目」即更新。仅 `save` 模式生效。

- AC-5.1 重新检测单个文件、内容没变的保存都不会让项目进入待更新。
- 测试：`engine.test.ts`、手册 04 章。

**FR-6 手动检测（P0）**。命令面板「重新检测当前文件 / 整个项目」（快捷键 `Ctrl+Alt+Shift+M`，macOS `Cmd+Alt+Shift+M`）、侧栏标题栏刷新按钮、编辑器右键菜单、状态栏悬停链接。重新检测当前文件不代表项目内容变了，不写「待更新」。

**FR-7 单元测试口径（P1）**。`botAnalyzer.analyze.includeTests`（缺省 false）为 true 时每次调用加 `--include-tests`。`bot-metric.toml` 写了 `[analysis] include_tests = true` 时插件关不掉（bot-metric 无关闭参数），侧栏「单元测试」行变灰，点击打开该文件。侧栏「单元测试」行可点击切换（写工作区设置，无文件夹时写用户设置）。切换设置后重检项目，且第一次不显示「与上次相比」（口径不同不比）。

- AC-7.1 `tests/`、`benches/`、`examples/` 下的代码无论开关都会检测；开关只决定 `#[cfg(test)]` 代码（悬停与界面写明这一口径）。
- AC-7.2 文件页能显示这个文件里测试函数的个数（含 / 不含测试两次取数之差；toml 已包含时取不到，不显示）。
- 测试：`sidebar.test.ts`（--include-tests 场景）、`botconfig.test.ts`（toml 三字段）。

## 4.3 侧栏

侧栏是活动栏「Bot Analyzer」容器下的**单一 Webview 视图**，两个页签：当前文件、整个项目；另有独立的「规则说明」编辑器面板。所有显示文字由服务端算好（中文、术语括号、上限写法），客户端只画。

**FR-8 当前文件页（P0）**。自上而下四块：

- 概览：文件路径、模块、代码行数、各类问题条数；函数分有问题 / 没有问题两组（与函数达标率 FCR 同口径）；「单元测试」行（FR-7）；
- 度量：当前文件适用的度量（文件页 12 项），默认收起，悬停写口径；
- 问题详情：这个文件的问题，点击跳到源码并选中；
- 全部函数：按 impl 块分组、内联模块成组放最后；表头标注上限（NLOC、CCN），超限橙色、接近（≥ 90% 上限）黄色。

- AC-8.1 行与行号可点击跳转；与光标所在函数对应的行高亮（跟随编辑器选区）。
- AC-8.2 保存后这个文件的问题与函数立即更新（不必等项目检测）。
- 测试：`sidebar.test.ts`（ripgrep dir.rs 场景逐句核对）。

**FR-9 整个项目页（P0）**。概览块：规模（项目名、包数、文件数、代码行数；包只算工作区内 Cargo 包）、检测（时间、用时、工具版本、重新检测链接）、配置（条件编译、单元测试、集成测试口径）、门禁（结论与阻塞项）、问题（各类条数，含质量目标未达标）、质量目标（未达标 / 达标 / 无法判定分组；「不适用」不显示）、函数统计、最长函数与最高圈复杂度（可点跳转）。下方：项目级 16 项度量（默认收起）与问题详情。

- AC-9.1 问题详情分组由 `botAnalyzer.sidebar.problemGrouping` 决定：`module`（缺省，crate → 模块 → 函数）、`dir`（包 → 文件 → 函数）、`both`（两种都提供，标题右侧可切换，切换不写回设置）。
- AC-9.2 质量目标列目标值与当前值（如「平均文件代码行(AFS 目标 ≤ 300)」），状态分未达标 / 达标 / 无法判定。
- 测试：`sidebar.test.ts`（默认配置、门禁四种结论、重复 top 等场景）。

**FR-10 规则说明（P0）**。命令「查看规则说明」打开规则面板（编辑器区 Webview）：左侧全部规则（BM001–BM007）与本项目条数（未开启的规则写「未开启」），右侧何时报出、上限由哪项配置决定、为什么、怎么改，以及本项目最严重的一处（可点跳转）。

- AC-10.1 规则条数与侧栏一致；上限取自当前生效配置（没有 `bot-metric.toml` 时注明「bot-metric 默认配置」）。
- AC-10.2 「列出位置」列出该项目这一类问题（1 条直跳，多条选择框）。
- 测试：`rules.test.ts`。

## 4.4 编辑器与状态栏

**FR-11 编辑器标记（P0）**。橙色波浪线画在：函数名（函数超限）、unsafe 关键字（精确到列）、过大文件的第 1 行；重复代码块整段左侧画竖线。标记基于项目级与单文件结果，编辑器内容变化后 300 ms 合并重推；有未保存改动时状态栏文件项变淡（数字是上次保存时的）。

- AC-11.1 波浪线位置避开注释、字符串与字符字面量。
- 测试：`items.test.ts`（语法项范围）、`editor.test.ts`。

**FR-12 CodeLens（P0）**。只挂在真正超限的函数（NLOC、CCN）与过大文件上方，以警告图标开头，两项合成一条：`$(warning) 函数过长(NLOC)：119 行（上限 50）　·　圈复杂度过高(CCN)：27（上限 20）`。点击在侧栏中定位。`botAnalyzer.codeLens.enabled` 可关。

- 测试：`editor.test.ts`。

**FR-13 悬停（P0）**。三种形态：

- 函数：卡片写位置、NLOC、CCN 与问题（数字来自项目结果，不起进程）；行号可点击跳转并选中；
- impl / struct / enum / union / trait 的名字上：只检测这一项（`--item-at`），给出这一项的度量；类型连同同文件 impl 块合计，带泛型参数的类型关联不到 impl，写明「未统计」；有未保存改动时不给（bot-metric 读磁盘）；
- 重复代码块上：这一段的行数与另几处位置（可点跳转）。

右键「检测光标所在的代码项」的结果也以悬停形式在光标处弹出（保留 60 秒或直到编辑）。

- AC-13.1 光标不在任何可检测项上时给出一句提示，不出卡片。
- 测试：`editor.test.ts`（悬停①–⑧、重复悬停）、`lsp.test.ts`（端到端）。

**FR-14 快速修复与右键菜单（P0）**。灯泡只挂在本扩展诊断上，两项：「查看规则说明 · BMxxx」与「在 Bot Analyzer 视图中显示」。编辑器右键菜单为「Bot Analyzer」子菜单五项：检测光标所在的代码项、在视图中显示、查看规则说明、重新检测当前文件、重新检测整个项目。

- 测试：`editor.test.ts`、`layout.test.ts`（命令面板 11 条）。

**FR-15 状态栏两项（P0）**。左侧项目项：盾牌图标即门禁结论（未通过 / 通过带勾 / 无法判定带问号），后接问题总数，未通过用警告底色；「待更新」时点击重新检测。右侧文件项：当前文件问题条数。悬停列问题分类与增减（新增橙、消除绿），问题可点（1 条直跳、多条选择框），底部链接重新检测、导出报告、输出日志。`statusBar.showProject / showFile` 可分别隐藏。

- AC-15.1 门禁结论变化且 `notify.gateChanged` 为 true 时弹通知。
- 测试：`status.test.ts`（52 条打开 → 保存 dir.rs 加 16 行等真实场景）。

**FR-16 代码项检测（P0）**。右键「检测光标所在的代码项」检测包住光标的可检测项：函数（含关联函数、方法、trait 方法、过程宏）、impl、struct / enum / union（连同同文件 impl 块，逐块检测）、trait、内联 `mod x { … }`（声明 `mod x;` 不算）。光标在 use、字段、常量、宏调用等上时向上找包住它的可检测项。有未保存改动先询问保存；不含单元测试时光标在 `#[cfg(test)]` 里则提示可切换。

- 测试：`items.test.ts`（8 项）、`engine.test.ts`。

## 4.5 报告与配置

**FR-17 报告导出（P0）**。导出当前文件 / 整个项目为 Markdown：保存对话框默认项目根目录，文件名 `bot-analyzer-<项目名>-<YYYYMMDD>-<HHmm>.md`。项目报告含规模、检测信息、配置口径、门禁、问题、质量目标（含不适用项）、函数统计与全部度量（每项写口径）；文件报告含概览、度量、问题详情与全部函数。未成功检测过不能导出；文件报告需当前活动编辑器在检测范围内。

- AC-17.1 导出内容与界面文字同源（同在服务端生成），与样张逐字一致。
- 测试：`export.test.ts`（与两份样张逐字比对）。

**FR-18 个人设置（P0）**。9 项 `botAnalyzer.*` 设置（见手册 05 章）：`analyze.on`、`analyze.projectAfterSave`、`analyze.includeTests`、`codeLens.enabled`、`notify.gateChanged`、`botMetric.binaryPath`（machine 作用域）、`statusBar.showProject`、`statusBar.showFile`、`sidebar.problemGrouping`。影响检测的设置变化经 LSP 下发服务端；只影响显示的（状态栏显隐）客户端自理。

- AC-18.1 设置缺省值客户端与服务端一致（两端共用解析）。
- 测试：`layout.test.ts`、`wiring`（含在 layout/layout 内约定的检查）。

**FR-19 与 bot-metric.toml 配合（P0）**。扩展只读 3 个字段：`[rules] duplication_findings`（top / all 时展示重复问题并画竖线）、`[thresholds] duplication_max_findings`、`[analysis] include_tests`。其余字段全部交给 bot-metric（阈值、质量目标、阻塞策略、范围），写错由 bot-metric 报 BM401。配置变化保存后自动重检项目。扩展从不写仓库文件。

- AC-19.1 编辑器与 CI 同口径：阈值、范围、质量目标、门禁只来自 bot-metric 与同一份配置。
- 测试：`botconfig.test.ts`。

**FR-20 失败呈现（P0）**。每种失败有一句话与恢复动作，**已有成功结果时保留旧数**：项目检测失败不清空结果，侧栏与状态栏显示失败原因（配置错误 BM401 给出「打开 bot-metric.toml」入口）；单文件检测失败保留该文件上一次结果并写明原因（如 BM201 解析失败）；分析不完整（partial / BM2xx）标「部分」；门禁无法判定写明原因（缺基线、数据不完整）。

- 测试：`engine.test.ts`（BM401 / BM201 保留结果）、`sidebar.test.ts`（其他状态场景）。

# 5 非功能需求

| 编号 | 类别 | 要求 | 验收 |
| --- | --- | --- | --- |
| NFR-1 | 性能 | 单文件检测约 0.1 秒级（ripgrep 实测约 0.09–0.2 s）；打开项目（常规 + 全部函数两次并行）约 0.5 秒级 | `sidebar.test.ts` 附带实测数据；人工 |
| NFR-2 | 资源 | 子进程统一管理：超时 300 秒、stdout 上限 128 MiB、取消信号，均终止整个进程树并等待退出 | `process.test.ts` |
| NFR-3 | 共存 | 不与 rust-analyzer 抢位置：不发编辑器诊断集合（诊断以波浪线装饰呈现）、CodeLens 只挂超限项、不跑 `cargo check`、cargo 只用 `metadata --no-deps --offline` | `layout.test.ts`、人工 |
| NFR-4 | 一致性 | 数值与同版本 bot-metric、同一份 `bot-metric.toml` 的命令行结果一致；门禁直接取报告 `gate` | `sidebar.test.ts`（真实报告驱动） |
| NFR-5 | 安全 | 未信任工作区不运行；可执行文件路径只认用户 / 机器设置；Webview 有 CSP 与 nonce，内容经转义；从不写仓库文件 | `layout.test.ts`（machine 作用域、受限模式） |
| NFR-6 | 可靠性 | 检测失败永不崩溃：失败也是一次有文案的结果；旧结果保留 | `engine.test.ts` |
| NFR-7 | 可维护性 | 全插件只有 `server/src/process.ts` 起子进程；客户端不出现 bot-metric / cargo / BM 编号字样（文字全由服务端给） | `layout.test.ts` |
| NFR-8 | 兼容性 | VS Code ≥ 1.90；Node ≥ 20（建议）；bot-metric ≥ 1.2.1，推荐 1.2.3；Windows 平台包内置二进制，其他平台通用包自备 | `package.json`、手册 02 章 |
| NFR-9 | 本地化 | 界面文字为简体中文，集中在 `server/src/text.ts`；数字格式统一（千分位、百分比带分子分母、括号零值不写） | `sidebar.test.ts`、`editor.test.ts` |
| NFR-10 | 可诊断性 | 输出频道记录每次工具调用的命令行、退出码与耗时 | 手册 09 章 |

# 6 约束与假设

- 工具行为以 bot-metric 1.2.1 / 1.2.3 实测为准；报告契约字段以 `bot-metric/schema/analysis-report-*.json` 为准。
- 检测读磁盘上的文件：未保存的改动不参与分析（状态栏变淡注明）。
- 用户机器上有 `cargo`（取不到时按目录归组，功能降级不中断）。
- 阈值、质量目标、阻塞策略只写在 `bot-metric.toml`；VS Code 设置只控制交互行为（「配置」与「设置」两个词在这一意义上使用）。

# 7 已知限制

- 带泛型参数的类型（如 `impl<'a> X<'a>`）关联不到 impl 块，悬停写明「未统计」。
- 增长率目标（`max_code_size_growth_ratio`）需要基线，扩展不带基线，该项通常「无法判定」。
- 没有基线的质量目标「不适用」在侧栏不显示（导出报告列出）。
- `duplication_findings = "all"` 的大项目可能超出 128 MiB 输出上限，需改用 `top`。
- 无语言服务器崩溃重启策略（客户端只启停；异常时查输出日志重载窗口）。
- 只分析一个 Cargo 项目（第一个工作区文件夹），多根工作区不逐一分析。

# 8 验收准则

0.1.0 视为可交付，当且仅当：

1. `npm ci && npm test` 通过：版本一致性检查（package.json、README、CHANGELOG、package-lock 四处一致）、TypeScript 构建、全部离线自动测试（11 个测试文件，源码实测 122 个用例，其中端到端 11 项在未设环境变量时跳过）；
2. 设置 `BA_TEST_BINARY`（bot-metric ≥ 1.2.1）与 `BA_TEST_PROJECT`（Rust 项目，如 ripgrep checkout）后，端到端 11 项全部通过；
3. `npm run package` 与 `node scripts/package.mjs --target win32-x64 [--bin <bot-metric>]` 生成 `dist/bot-analyzer-0.1.0.vsix` 与（可选内置二进制的）平台包；
4. 在装有 rust-analyzer 的 VS Code 中按手册逐项人工验收（安装、首次检测、保存链路、代码项检测、导出、故障排查场景）。

前三项已在交付前完成；第 4 项以《使用手册》为准在真实环境执行。
