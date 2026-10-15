
## claude design 
https://claude.ai/artifact/XgEW2cA8T1xBgSsaviv7vU#7ddea9f4-e9d6

## claude docs 
https://claude.ai/artifact/7TWb4orXv4FwZyeo2fw1iN#page-dcb81aee8d83

## 目录

- `bot-analyzer/`：Bot Analyzer 插件（VS Code 扩展）的源码工作区，内容是 0.11.0 源码的副本（与 `v0.11/bot-analyzer-0.11.0-src/` 逐文件一致），后续开发改这里。首次构建先 `npm ci`（仓库里没有 `node_modules/`），再 `npm run build` → `npm test`（端到端要 `BA_TEST_BINARY`、`BA_TEST_PROJECT`）→ `npm run package`，产物在 `dist/`。
- `design/`：当前设计资料，已更新到 0.11.0——`Bot Analyzer 设计文档.md`（0.11.0）、`Bot Analyzer 0.11.0 交付记录.md`、`画布导出（第 41 版）.html`。画布是 0.10.0 的导出件（0.11.0 按在线画布第 43 版实现，没有导出离线 HTML，本地画布落后两版）；截图在 `界面实拍/`（2 张，0.9.0 交付的）和 `离线核对/`（2 张，0.9.0 窄宽度核对），0.11.0 交付的 13 张实拍不在这个工作区。
- `bot-metric/`：度量工具 bot-metric 的源码（Rust）。
- `v0.11/`：0.11.0 交付快照——设计文档、交付记录、两份 vsix，以及 0.11.0 源码目录 `bot-analyzer-0.11.0-src/`（与 `bot-analyzer/` 逐文件一致）；这一版没有导出画布 HTML。
- `v0.10/`：0.10.0 交付快照——设计文档、画布 HTML（第 41 版）、交付记录、两份 vsix，以及 0.10.0 源码目录 `bot-analyzer-0.10.0-src/`（旧版源码，开发已不再使用）。
- `v0.7/`、`v0.8/`、`v0.9/`：更早版本的交付快照，都保留当时的设计文档、画布 HTML、源码 zip 和 vsix；`v0.9/` 另有 2 张截图和改动前的备份 `_old-0.9.0/`。
- 根目录其余 `*.md` / `*.html` / `*.xlsx`：度量、问题、BM、质量目标与门禁的对照材料。
