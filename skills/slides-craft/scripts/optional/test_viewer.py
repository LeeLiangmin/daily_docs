#!/usr/bin/env python3
"""【可选工具，非必需】检查 HTML 幻灯片的查看器：在多种窗口尺寸（含非全屏、高度小于 1080）下，
当前页是否完整显示、居中、等比、并充分利用窗口。

用法：
    python3 test_viewer.py <deck.html> [--sizes 1440x700,1280x600,...] [--margin 0.5]

依赖：playwright + chromium（pip install playwright && python3 -m playwright install chromium）。
没有浏览器时脚本会说明并以退出码 3 结束——这是正常情况：改用页面内置自检（C 键）或人工在小窗口下打开检查。

检查项（对当前可见的 <section>，量的是变换后的实际显示矩形）：
    1. 完整落在窗口内（不被裁切）
    2. 上下、左右留白分别对称（居中，误差 ≤ 1px）
    3. 宽高比保持 16:9（误差 ≤ 0.5%）
    4. 充分利用窗口：显示宽占窗口宽，或显示高占窗口高，至少一项 ≥ 0.9
       （非全屏可以留一圈很小的边距，但不能一边大片空白、另一边紧贴）
退出码：全部通过 0；有失败 1；无法运行 3。
"""
import sys
from pathlib import Path

DEFAULT_SIZES = [
    (1920, 1080), (1600, 900), (1440, 700), (1366, 640), (1280, 600),
    (1024, 768), (800, 1000), (2560, 1440),
]
JS_RECT = """
() => {
  const vis = [...document.querySelectorAll('section')].filter(s => {
    const cs = getComputedStyle(s);
    return cs.display !== 'none' && cs.visibility !== 'hidden';
  });
  const el = document.querySelector('section.active') || vis[0];
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return {l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height,
          iw: window.innerWidth, ih: window.innerHeight};
}
"""


JS_OVERFLOW = """
() => [...document.querySelectorAll('section')].map(s => {
  const cs = getComputedStyle(s);
  const wasNone = cs.display === 'none';
  if (wasNone) s.style.display = 'flex';
  const pb = parseFloat(getComputedStyle(s).paddingBottom) || 0;
  let maxBottom = 0, worst = '';
  for (const c of s.children) {
    const ccs = getComputedStyle(c);
    if (ccs.position === 'absolute' || ccs.display === 'none') continue;
    const b = c.offsetTop + c.offsetHeight;
    if (b > maxBottom) { maxBottom = b; worst = (c.tagName.toLowerCase() + (c.className ? '.' + c.className : '')).slice(0, 30); }
  }
  const r = {id: s.id, h: s.clientHeight, pb: pb, maxBottom: maxBottom, worst: worst,
             scrollH: s.scrollHeight, scrollW: s.scrollWidth, clientW: s.clientWidth};
  if (wasNone) s.style.display = '';
  return r;
})
"""


def parse_sizes(s):
    out = []
    for part in s.split(","):
        w, h = part.lower().split("x")
        out.append((int(w), int(h)))
    return out


def main():
    args = sys.argv[1:]
    sizes = DEFAULT_SIZES
    if "--sizes" in args:
        i = args.index("--sizes")
        sizes = parse_sizes(args[i + 1])
        del args[i:i + 2]
    if not args:
        print(__doc__)
        sys.exit(2)
    path = Path(args[0]).resolve()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("未安装 playwright，无法自动检查；请人工在小窗口（高度 < 1080）下打开确认。")
        sys.exit(3)

    fails = 0
    print(f"{'窗口':>10} | {'显示矩形 左,上,右,下':<32} | 上/下留白 | 左/右留白 | 宽高比 | 利用率 | 结果")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for W, H in sizes:
                page = browser.new_page(viewport={"width": W, "height": H})
                # 不等外部字体，避免离线时卡住；布局不依赖字体
                page.route("**/*", lambda route: route.abort()
                           if route.request.url.startswith("http") else route.continue_())
                page.goto(path.as_uri(), wait_until="domcontentloaded")
                page.wait_for_timeout(300)
                r = page.evaluate(JS_RECT)
                page.close()
                if not r:
                    print(f"{W}x{H}: 找不到可见的 <section>")
                    fails += 1
                    continue
                top, bottom = r["t"], H - r["b"]
                left, right = r["l"], W - r["r"]
                problems = []
                if min(top, bottom, left, right) < -0.5:
                    problems.append("被裁切")
                if abs(top - bottom) > 1 or abs(left - right) > 1:
                    problems.append("未居中")
                ratio = r["w"] / r["h"]
                if abs(ratio - 16 / 9) / (16 / 9) > 0.005:
                    problems.append("宽高比变形")
                util = max(r["w"] / W, r["h"] / H)
                if util < 0.9:
                    problems.append("利用率低")
                status = "通过" if not problems else "失败：" + "、".join(problems)
                fails += bool(problems)
                print(f"{W:>5}x{H:<4} | {r['l']:7.1f},{r['t']:7.1f},{r['r']:7.1f},{r['b']:7.1f}   | "
                      f"{top:6.1f}/{bottom:<6.1f} | {left:6.1f}/{right:<6.1f} | {ratio:.3f}  | {util:5.2f}  | {status}")
            browser.close()
    except Exception as e:  # 浏览器不可用
        print("无法启动浏览器：", str(e)[:200])
        sys.exit(3)

    print("\n未通过窗口数：", fails)

    # ---- 内容溢出（在 1920×1080 下逐页量，布局像素，不受缩放影响）----
    ov_fails = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.route("**/*", lambda route: route.abort()
                       if route.request.url.startswith("http") else route.continue_())
            page.goto(path.as_uri(), wait_until="domcontentloaded")
            page.wait_for_timeout(300)
            rows = page.evaluate(JS_OVERFLOW)
            browser.close()
        print("\n内容溢出检查（参考：外部字体被拦截，实际字体下高度可能略有差异）")
        for r in rows:
            problems = []
            limit = r["h"] - r["pb"]
            if r["h"] and abs(r["h"] - 1080) > 1:
                problems.append(f"页面高度 {r['h']:.0f}px ≠ 1080（检查 box-sizing:border-box）")
            if r["maxBottom"] > limit + 1:
                problems.append(f"内容底 {r['maxBottom']:.0f} > 安全区底 {limit:.0f}（{r['worst']}）")
            if r["scrollH"] > r["h"] + 1:
                problems.append(f"内容被裁切：scrollHeight {r['scrollH']} > {r['h']:.0f}")
            if r["scrollW"] > r["clientW"] + 1:
                problems.append(f"内容横向被裁切：scrollWidth {r['scrollW']} > {r['clientW']:.0f}")
            if problems:
                ov_fails += 1
                print(f"  [{r['id'] or '?'}] " + "；".join(problems))
        if not ov_fails:
            print("  各页内容都在安全区内")
    except Exception as e:
        print("内容溢出检查跳过：", str(e)[:120])

    print("\n未通过：窗口", fails, "个；溢出页", ov_fails, "页")
    sys.exit(1 if (fails or ov_fails) else 0)


if __name__ == "__main__":
    main()
