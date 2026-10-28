"""生成「规范评审对照稿」HTML：总览 + 每条的原/现定级、原/现 lint + 原文与修订稿的逐行文本对照。

用法：
    python gen_review.py 原文.md 修订稿.md clauses.toml [-o 规范评审对照稿.html] [--title 规范评审对照稿]

输入约定（详见同目录 README.md）：
- 原文.md / 修订稿.md：每条规范以「### 条款ID 标题」开头，所属分类取上方最近的「## 分类」标题；
  【级别】取自「**【级别】** 建议」一行；修订稿中的「**【检测】**」字段不进入对照。
- clauses.toml：每条一个 [[clause]]，决定输出哪些条款及顺序，写明检测能力和原/现 lint。
只依赖 Python 3.11+ 标准库。
"""
import argparse
import difflib
import html
import re
import sys
import tomllib
from pathlib import Path

SUPPORT = {"完全支持": "full", "部分支持": "part", "不支持": "none"}
EMPTY = "&#8203;"  # 空单元格占位，保持行高
SIMILAR = 0.35     # 同一行改动的相似度阈值，低于它按「删一行 + 加一行」处理

CSS = """<style>
:root {
  --bg: #f4f5f2; --sheet: #ffffff; --ink: #1c2226; --ink-2: #4b555b; --ink-3: #7c868b; --line: #dde1dc;
  --accent: #1f5f6b; --code-bg: #eef0ec;
  --add-bg: #e3f3e6; --add-ink: #1e6b34; --add-strong: #b9e3c3;
  --del-bg: #fbe8e6; --del-ink: #9a2b22; --del-strong: #f2c2bc;
  --full: #2f7d47; --part: #a86b0c; --none: #8a8f93;
  --f-display: "Noto Serif SC", "Songti SC", "SimSun", serif;
  --f-body: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  --f-mono: "JetBrains Mono", "SFMono-Regular", Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #14191c; --sheet: #1b2226; --ink: #e3e7e5; --ink-2: #aab3b6; --ink-3: #7d878b; --line: #2d363b;
    --accent: #7cc3cf; --code-bg: #232c30;
    --add-bg: #17301f; --add-ink: #8fd6a2; --add-strong: #245a35;
    --del-bg: #3a1c1a; --del-ink: #f0a59c; --del-strong: #6b2b25;
    --full: #6cc38a; --part: #e0a548; --none: #8d969a;
    color-scheme: dark;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font-family: var(--f-body); font-size: 15px; line-height: 1.7; }
code { font-family: var(--f-mono); font-size: .86em; background: var(--code-bg); padding: .05em .35em; border-radius: 3px; word-break: break-word; }
a { color: var(--accent); }
.wrap { max-width: 1200px; margin: 0 auto; padding: 28px 16px 64px; }
.masthead { padding-bottom: 18px; border-bottom: 2px solid var(--ink); margin-bottom: 24px; }
.masthead h1 { font-family: var(--f-display); font-size: clamp(26px, 4vw, 36px); line-height: 1.25; margin: 4px 0 0; }
.panel, .rule { background: var(--sheet); border: 1px solid var(--line); border-radius: 8px; padding: 20px 22px; margin-bottom: 28px; min-width: 0; }
.panel h2 { font-family: var(--f-display); font-size: 20px; margin: 0 0 12px; }
.ovwrap, .diffwrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; }
table.ov { min-width: 640px; }
table.ov td, table.ov th { padding: 7px 10px; border-bottom: 1px solid var(--line); text-align: left; font-size: 14px; vertical-align: top; }
table.ov th { font-size: 12px; color: var(--ink-3); font-weight: 500; }
table.ov td:first-child { font-family: var(--f-mono); font-size: 13px; white-space: nowrap; }
.sup { display: inline-block; font-size: 12px; padding: 1px 8px; border-radius: 10px; border: 1px solid currentColor; white-space: nowrap; line-height: 1.6; }
.sup.full { color: var(--full); } .sup.part { color: var(--part); } .sup.none { color: var(--none); }
.rule { scroll-margin-top: 16px; }
.rhead { border-bottom: 1px solid var(--line); padding-bottom: 12px; margin-bottom: 16px; }
.rid { font-family: var(--f-mono); font-size: 14px; color: var(--accent); font-weight: 600; }
.rcat { font-family: var(--f-body); font-weight: 400; color: var(--ink-3); font-size: 12px; margin: 0 8px; }
.rhead h2 { font-family: var(--f-display); font-size: 21px; line-height: 1.4; margin: 4px 0 0; }
.rule h3 { font-size: 14px; font-weight: 700; margin: 22px 0 8px; }
.kv { display: grid; gap: 4px; font-size: 13px; }
.kv > div { display: flex; gap: 4px; align-items: baseline; }
.lk { font-size: 11px; color: var(--ink-3); width: 5em; flex: none; }
.lv { display: flex; flex-direction: column; align-items: flex-start; gap: 3px; }
.muted { color: var(--ink-3); }
table.diff { font-family: var(--f-mono); font-size: 12.5px; line-height: 1.55; table-layout: fixed; min-width: 760px; border: 1px solid var(--line); }
table.diff col.c-ln { width: 3.2em; }
table.diff thead th { font-family: var(--f-body); font-size: 12px; font-weight: 500; color: var(--ink-3); text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line); background: var(--bg); }
table.diff td { padding: 1px 8px; vertical-align: top; white-space: pre-wrap; word-break: break-word; }
table.diff td.ln { color: var(--ink-3); text-align: right; user-select: none; padding-right: 6px; border-right: 1px solid var(--line); }
tr.del td.a, tr.chg td.a { background: var(--del-bg); }
tr.add td.b, tr.chg td.b { background: var(--add-bg); }
tr.del td.b, tr.add td.a { background: repeating-linear-gradient(135deg, transparent 0 6px, var(--line) 6px 7px); }
del { background: var(--del-strong); color: var(--del-ink); text-decoration: none; border-radius: 2px; }
ins { background: var(--add-strong); color: var(--add-ink); text-decoration: none; border-radius: 2px; }
@media (max-width: 860px) { .wrap { padding: 16px 12px 48px; } .panel, .rule { padding: 16px 14px; } }
</style>"""


def die(msg):
    sys.exit(f"gen_review: {msg}")


def esc(s):
    return html.escape(s, quote=False) or EMPTY


def parse_md(path):
    """按「### 条款ID 标题」切分条款；跳过代码块内的 # 行。"""
    clauses, cur, category, fence = {}, None, "", False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^(#{1,3})\s+(.*?)\s*$", line)
        if m and len(m.group(1)) < 3:
            cur = None
            if len(m.group(1)) == 2:
                category = m.group(2)
            continue
        if m:
            cid, _, title = m.group(2).partition(" ")
            if cid in clauses:
                die(f"{path.name} 中条款 {cid} 出现两次")
            cur = clauses[cid] = {"title": title.strip(), "category": category, "lines": []}
        if cur is not None:
            cur["lines"].append(line)
    for c in clauses.values():
        while c["lines"] and c["lines"][-1].strip() in ("", "---"):
            c["lines"].pop()
    return clauses


def drop_detect(lines):
    """去掉【检测】字段：从该行到下一个「**【」字段之前。"""
    for i, line in enumerate(lines):
        if line.startswith("**【检测】**"):
            j = next((k for k in range(i + 1, len(lines)) if lines[k].startswith("**【")), len(lines))
            lines = lines[:i] + lines[j:]
            while lines and not lines[-1].strip():
                lines.pop()
            return lines
    return lines


def level_of(lines):
    for line in lines:
        m = re.match(r"^\*\*【级别】\*\*\s*(.+?)\s*$", line)
        if m:
            return m.group(1)
    return None


def inline(x, y):
    """同一行改动：左侧用 <del> 标删掉的片段，右侧用 <ins> 标新增的片段。"""
    a, b = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, x, y, autojunk=False).get_opcodes():
        if op == "equal":
            a.append(html.escape(x[i1:i2], quote=False))
            b.append(html.escape(y[j1:j2], quote=False))
            continue
        if i2 > i1:
            a.append("<del>%s</del>" % html.escape(x[i1:i2], quote=False))
        if j2 > j1:
            b.append("<ins>%s</ins>" % html.escape(y[j1:j2], quote=False))
    return "".join(a) or EMPTY, "".join(b) or EMPTY


def ratio(x, y):
    return difflib.SequenceMatcher(None, x, y, autojunk=False).ratio()


def diff_rows(a, b):
    rows = []

    def row(cls, i, ta, j, tb):
        rows.append(f'<tr class="{cls}"><td class="ln">{i}</td><td class="tx a">{ta}</td>'
                    f'<td class="ln">{j}</td><td class="tx b">{tb}</td></tr>')

    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                row("eq", i1 + k + 1, esc(a[i1 + k]), j1 + k + 1, esc(b[j1 + k]))
            continue
        # 改动块：每个原文行按顺序找最相似的修订行配成一对，其余为整行删除/新增。
        j = j1
        for i in range(i1, i2):
            best = max(range(j, j2), key=lambda x: ratio(a[i], b[x]), default=None)
            if best is not None and ratio(a[i], b[best]) >= SIMILAR:
                for k in range(j, best):
                    row("add", "", EMPTY, k + 1, esc(b[k]))
                ta, tb = inline(a[i], b[best])
                row("chg", i + 1, ta, best + 1, tb)
                j = best + 1
            else:
                row("del", i + 1, esc(a[i]), "", EMPTY)
        for k in range(j, j2):
            row("add", "", EMPTY, k + 1, esc(b[k]))
    return "".join(rows)


def lints(items):
    return "".join(f"<code>{html.escape(x, quote=False)}</code>" for x in items) or "<span class=muted>（无）</span>"


def kv(rows):
    return '<div class="kv">%s</div>' % "".join(
        f'<div><span class="lk">{k}</span><span class="lv">{v}</span></div>' for k, v in rows)


def build(orig, rev, meta, title):
    overview, sections = [], []
    for c in meta.get("clause", []):
        cid = c.get("id") or die("clauses.toml 中有条款缺少 id")
        if cid not in orig:
            die(f"原文中找不到 {cid}")
        if cid not in rev:
            die(f"修订稿中找不到 {cid}")
        if c.get("support") not in SUPPORT:
            die(f"{cid} 的 support 必须是 {' / '.join(SUPPORT)} 之一")
        o, r = orig[cid], rev[cid]
        a, b = o["lines"], drop_detect(r["lines"])
        old = level_of(a) or c.get("level") or die(f"{cid} 原文没有【级别】行，需在 clauses.toml 中写 level")
        new = level_of(b) or c.get("level") or die(f"{cid} 修订稿没有【级别】行，需在 clauses.toml 中写 level")
        sup = f'<span class="sup {SUPPORT[c["support"]]}">{c["support"]}</span>'
        anchor = cid.replace(".", "-")
        name = html.escape(o["title"], quote=False)
        category = html.escape(c.get("category", o["category"]), quote=False)
        level = new if old == new else f"{old} → <b>{new}</b>"

        overview.append(f'<tr><td><a href="#{anchor}">{cid}</a></td><td>{name}</td><td>{level}</td><td>{sup}</td></tr>')
        sections.append(f"""<section class="rule" id="{anchor}">
  <header class="rhead">
    <div class="rid">{cid}<span class="rcat">{category}</span>{sup}</div>
    <h2>{name}</h2>
  </header>
  <h3>定级</h3>
  {kv([("原定级", old), ("现定级", new)])}
  <h3>lint</h3>
  {kv([("原 lint", lints(c.get("lint_old", []))), ("现 lint", lints(c.get("lint_new", [])))])}
  <h3>文本对照</h3>
  <div class="diffwrap"><table class="diff"><colgroup><col class="c-ln"><col><col class="c-ln"><col></colgroup><thead><tr><th></th><th>原文</th><th></th><th>修订稿</th></tr></thead><tbody>{diff_rows(a, b)}</tbody></table></div>
</section>""")
    if not sections:
        die("clauses.toml 中没有任何 [[clause]]")

    return f"""<!doctype html>
<!-- 由 gen_review.py 生成。生成方法与填写约定见 README.md。 -->
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{CSS}
</head>
<body>
<div class="wrap">
  <header class="masthead"><h1>{title}</h1></header>

  <section class="panel">
    <h2>总览</h2>
    <div class="ovwrap"><table class="ov">
      <thead><tr><th>条款</th><th>标题</th><th>定级</th><th>检测能力</th></tr></thead>
      <tbody>{"".join(overview)}</tbody>
    </table></div>
  </section>

{chr(10).join(sections)}
</div>
</body>
</html>
""", len(sections)


def main():
    ap = argparse.ArgumentParser(description="生成规范评审对照稿 HTML")
    ap.add_argument("original", type=Path, help="原文 markdown")
    ap.add_argument("revised", type=Path, help="修订稿 markdown")
    ap.add_argument("meta", type=Path, help="clauses.toml")
    ap.add_argument("-o", "--output", type=Path, default=Path("规范评审对照稿.html"))
    ap.add_argument("--title", default="规范评审对照稿")
    args = ap.parse_args()

    meta = tomllib.loads(args.meta.read_text(encoding="utf-8"))
    out, n = build(parse_md(args.original), parse_md(args.revised), meta, args.title)
    args.output.write_text(out, encoding="utf-8", newline="\n")
    print(f"{args.output}: {n} 条")


if __name__ == "__main__":
    main()
