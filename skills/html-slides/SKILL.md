---
name: html-slides
description: 用单个自包含 HTML 文件制作演示幻灯片（HTML PPT）：先写叙事大纲，再套用内置模板的版式，支持键盘翻页、逐步显示、演讲者备注、总览、导出 PDF，并做溢出检查和截图核对。用户要做 PPT、幻灯片、演示文稿、汇报 deck、分享材料时使用。
---

# HTML 幻灯片

产出一个**单文件、零依赖、可离线打开**的 HTML 演示文稿。模板在 `assets/template.html`，检查脚本在 `scripts/check.mjs`。

## 工作流程

按顺序做，不要跳步：

1. **问清三件事**（信息不足时问一轮，已有就跳过）：听众是谁、时长多少、听完要他们记住或做什么。
2. **写大纲，先给用户确认**：每页一行，写成"页码. 版式 — 标题（结论句）"。时长估算：每页约 1–2 分钟。
3. **复制模板**：把 `assets/template.html` 复制到用户指定位置（默认 `slides/index.html`），改 `<title>`。模板里的示例幻灯片每页演示一种版式，写法照抄对应的那页，然后删掉全部示例。
4. **逐页填充**：按下面的版式清单选版式，遵守内容规则。
5. **检查**：跑 `scripts/check.mjs`，或让用户用浏览器打开看左上角有没有红色溢出提示。有溢出就拆页或删内容，不要缩小字号。
6. **交付**：告诉用户文件位置和快捷键（见文末）。

## 内容规则

- **标题写结论，不写话题。** 写"新方案把响应时间降低了 40%"，不写"性能对比"。
- **一页一个观点。** 两个观点就拆两页。
- **要点 ≤ 5 条，每条 ≤ 2 行。** 超出就拆页或改用表格。
- **数字要有口径。** 大数字下面用 `.desc` 写数据来源或计算方式。
- **每一章以章节页开头**，最后一页之前放一页结论（`layout-quote`）。
- **不编造数据。** 用户没给的数字用"〈待填〉"占位，交付时列出所有占位。
- **不改字号来塞内容。** 模板字号是按投影可读性定的。

## 版式清单

每页是 `<main class="deck">` 下的一个 `<section class="slide ...">`。

| 版式 | 写法 | 用途 |
|---|---|---|
| 封面 | `section.slide.layout-cover`，含 `.eyebrow`、`h1`、`.lead`、`.meta` | 第一页 |
| 章节页 | `section.slide.layout-section`，含 `.num`、`h1`、`.lead` | 每章开头 |
| 标准页 | `section.slide`，`h2` + `.body` 包内容 | 要点列表，最常用 |
| 多栏 | `h2` + `.cols`（可加 `.w-6-4` / `.w-4-6` / `.three`），栏内可用 `.card` / `.card.accent` | 两项对比、三项并列 |
| 流程 | `.flow` 下多个 `.st`，含 `.n` 序号、`h3`、`p` | 3–5 个有先后顺序的步骤 |
| 图文 | `h2` + `.media`：左边文字，右边 `.pic` 包 `img` 或 `svg`；加 `.flip` 左右互换 | 讲解配截图、照片、示意图 |
| 大数字 | `.stats` 下多个 `.stat`，含 `.value`（单位放 `<small>`）、`.label`、`.desc` | 2–4 个关键指标 |
| 表格 | `table.tbl`，数字列加 `.num`，重点行加 `tr.hl` | ≤ 7 行 × 6 列 |
| 代码 | `pre.code`，上方可加 `.code-label`；着色用 `span.k` 关键字 / `.s` 字符串 / `.c` 注释 / `.f` 函数 / `.n` 数字；`span.hl` 高亮一行 | ≤ 14 行；前后对比放两栏 |
| 时间线 | `.timeline` 下多个 `.ev`（完成的加 `.done`），含 `.date`、`.what`、`.desc` | 3–6 个节点 |
| 条形图 | `.bars` 下多个 `.bar`：名称、`.track > .fill[style="--v:0–100"]`、`.val`；`.fill.alt` 换次强调色 | 简单对比，≤ 8 条 |
| 引用 / 结论 | `section.slide.layout-quote`，`blockquote` + `cite` | 全场结论、金句 |
| 整页图片 | `.figure` 包 `img` 或内联 `svg`，下方 `.caption` | 大图、架构图 |
| 结尾 | `section.slide.layout-end` | 最后一页 |

**辅助元素：**
- `.callout`：页内重点提示框
- `.tag` / `.tag.ok` / `.tag.warn` / `.tag.bad`：状态标签
- `.foot`：页底注释（数据来源等）
- `.lead`、`.small`：大号灰字、小号灰字
- `<strong>`：强调色加粗，每页最多 2 处
- `.body.center`：内容少时垂直居中（大数字、时间线常用）
- `.cols.stretch`：两栏卡片拉伸到页底等高（默认按内容高度）

**行为：**
- 元素加 `class="step"`：按 → 逐个出现
- 页内加 `<aside class="notes">…</aside>`：演讲者备注，放映时按 N 显示
- `section` 加 `data-no-number`：不显示页码（封面、章节页、结尾）

## 图表与图片

- 复杂图表用**内联 SVG** 手写，颜色用 `var(--accent)`、`var(--text)` 等变量，这样切换明暗主题也正常。
- 需要真正的数据图表时，可以按用户同意引入 CDN 库（如 ECharts），但要提醒用户这样就不能离线打开了。
- 图片优先用相对路径，放在 HTML 同目录的 `assets/` 下；需要单文件分发时转成 base64 内嵌。

## 换主题

只改模板顶部 `:root` 里的变量：`--accent`（主色）、`--accent-2`（次色）、`--bg`、`--text`、`--font`。`[data-theme="dark"]` 是暗色版本，同步修改。不要在单页上写零散的颜色。

## 检查

有 Node 和 Playwright 时：

```bash
node scripts/check.mjs slides/index.html          # 检查溢出
node scripts/check.mjs slides/index.html --shots  # 同时把每页截图到 slides/shots/
```

没有 Playwright 时先 `npm i -D playwright && npx playwright install chromium`；装不了就让用户在浏览器里打开，看左上角是否出现"内容溢出：第 N 页"，以及按 O 进入总览，红框的就是溢出页。

交付前逐项确认：
- [ ] 溢出检查通过
- [ ] 截图逐页看过：没有文字挤压、重叠、空白过多
- [ ] 每页标题是结论句
- [ ] 所有"〈待填〉"已列给用户
- [ ] 按 P 打印预览，每页一张、逐步元素全部显示

## 放映快捷键（交付时告诉用户）

| 键 | 作用 |
|---|---|
| → / 空格 / Enter | 下一步 |
| ← | 上一步 |
| Home / End | 首页 / 末页 |
| F | 全屏 |
| O | 总览（点击缩略图跳转） |
| N | 演讲者备注 |
| T | 明暗主题切换 |
| P | 打印 / 导出 PDF（打印对话框里选"另存为 PDF"，边距选"无"，勾选"背景图形"） |
| ? | 帮助 |

网址后加 `#5` 可直接打开第 5 页。
