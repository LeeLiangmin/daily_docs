# HTML 幻灯片查看器

输出单文件 HTML 幻灯片时，**从 `assets/deck-shell.html` 起手，只增删 `<section class="slide">`，不要自己重写外壳**。
外壳保证：固定 1920×1080 画布、等比缩放、上下左右居中、非全屏时留一圈小边距、F 全屏、打印导出 PDF、触摸滑动、`#3` 直达第 3 页、自动页码，以及**页面内置自检**。

## 为什么不能手写：两个真实出现过的错误

在一份按旧版 skill 生成的稿子上实测（窗口 1440×700，非全屏）：

| 现象 | 根因 |
|---|---|
| 上方空出约 190px，下方被裁掉约 330px | `#viewport` 固定 1920×1080，靠 `body{display:grid;place-items:center}` 居中，再用 `transform-origin:center` 缩放。布局盒子仍是 1920×1080，从窗口顶部往下排，缩放只是绕它的中心收缩，画面被整体推低 |
| 页面实际是 2144×1300，页脚跑到画布外，宽高比变成 1.649 | `.slide` 写了 `width:1920px;height:1080px;padding:…` 但没有 `box-sizing:border-box`，padding 被额外加上 |

窗口正好 1920×1080（全屏）时这两个错误看不出来，一进入普通浏览器窗口就暴露。

## 正确做法

1. `*,*::before,*::after{box-sizing:border-box}`：画布 1920×1080 就是 1920×1080。
2. `#stage{position:fixed;inset:0}` 铺满窗口；`#deck{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:0 0;overflow:hidden}`。
3. 用 JS 算缩放和平移，绕左上角缩放，再平移到居中：

   ```js
   var m = isFull() ? 0 : clamp(round(min(vw, vh) * 0.02), 8, 24);   // 非全屏留边距
   var s = Math.min((vw - 2*m) / 1920, (vh - 2*m) / 1080);
   var x = (vw - 1920*s) / 2, y = (vh - 1080*s) / 2;
   deck.style.transform = 'translate(' + x + 'px,' + y + 'px) scale(' + s + ')';
   ```

4. 监听 `resize`、`fullscreenchange`；用 `window.innerWidth/innerHeight`，不要假定窗口大小。
5. 非全屏留边距，避免“一边大片空白、另一边紧贴窗口边缘”；全屏时边距为 0。
6. 操作提示不要常驻：鼠标移动或按键时显示，2.5 秒后淡出，避免压在页面底部。

## 打印 / 导出 PDF

外壳自带 `@media print`：每页一张 1920×1080，取消缩放，隐藏提示。浏览器打印时选择“背景图形”，边距“无”，纸张按页面尺寸。

## 内嵌到预览面板 / iframe

面板尺寸通常小于 1080 高，属于最容易暴露缩放错误的场景。同样使用上面的外壳，它按容器的 `window.innerWidth/innerHeight` 计算，不依赖窗口是否全屏。

## 交付前验证（不需要 Playwright 或任何自动化）

1. **静态脚本**（纯 Python 标准库）：`python3 scripts/check_deck.py deck.html --profile tech`。
2. **页面内置自检**（在任何浏览器里）：打开 `deck.html?check`，或按 **C** 键，或在控制台运行 `slidesCheck()`。逐页报告：页面高度不是 1080、内容越过底部安全区、被裁切、横向溢出、内容只占可用高度不足 60%、标题或副标题折行、卡片空了一半以上、小于 22px 的文字。
3. **人工**：浏览器窗口拉到高度 600–700（非全屏）看一遍；按 `aesthetics.md` §6 自查。

没有浏览器可用的平台：只做 1 和 3，并在交付说明里写明“未做渲染检查”。

可选：有 playwright 时，`scripts/optional/test_viewer.py deck.html` 在 8 种窗口尺寸下实测居中与溢出。它不是必需步骤，缺失时不要为它安装依赖。

`scripts/check_deck.py` 也会对整份 HTML 做静态提示：缺 `box-sizing:border-box`、`transform-origin:center` 与缩放并用、grid 居中与缩放并用、缩放没有平移。

## 检查清单

- [ ] 使用 `assets/deck-shell.html` 的外壳，没有自己改居中逻辑
- [ ] 页面内置自检（C 键）全部通过；或已人工在高度 600–700 的窗口下确认
- [ ] 每页高度就是 1080，页脚在画布内
- [ ] 打印预览每页一张，无空白页
