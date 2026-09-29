#!/usr/bin/env python3
"""检查以 <section> 分页的幻灯片 HTML（v4）：标题长度、密度、可读性，以及内容质量的可机检部分。
只用 Python 标准库，不需要浏览器；渲染层面的检查（溢出、留白、换行）用页面内置自检（按 C 或网址加 ?check）。

用法：
    python3 check_deck.py <目录或文件> [...] [--profile talk|tech|read] [--content-width 1696] [-v]

档位（--profile，默认 tech）：
    talk  演讲型   30–100 词   最小 24px
    tech  技术型  100–260 词   最小 22px
    read  阅读型  150–380 词   最小 20px

逐页检查：标题长度与逗号、副标题、字号（SVG 按缩放折算有效字号）、对比度、偏稀 / 偏满、结构化证据块、
          常量列（整列值都相同的表格列）、结论条与标题重合、SVG 未按 1:1、演讲者备注。
全套检查：字号 / 字体种类、节奏（是否每页都贴着词数上限）、模板单一（表格 + 结论条）、
          结论条使用频率、目录声称的部分数与页眉编号是否一致。
人工核对清单（不计入问题数）：跨页数值（同一单位在多页出现）、目录里“听完你能……”的承诺。

支持每页一个 .html 文件，也支持一个文件含多个 <section>。
封面 / 结尾 / 观点页（id 含 cover、title、thanks、end、wrap、closing）不检查偏稀与结构块。
同时识别 assets/deck-shell.html 的组件类（.title .lede .card .code .flow .step .kpi .callout）与主题令牌。
这是基于标记的估算，不是渲染结果；通过检查不代表内容正确，内容门禁见 references/quality-gates.md。
退出码：有问题返回 1，否则 0。
"""
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

PROFILES = {
    "talk": {"min_font": 24, "min_words": 30, "max_words": 100},
    "tech": {"min_font": 22, "min_words": 100, "max_words": 260},
    "read": {"min_font": 20, "min_words": 150, "max_words": 380},
}
MAX_SIZES = 6
MAX_FAMILIES = 3
EXEMPT = re.compile(r"cover|title|thanks|end|wrap|closing", re.I)
TITLE_LIMIT = {"talk": 12, "tech": 18, "read": 22}   # 汉字等效字数（拉丁字符按 0.55 计）
LEDE_LIMIT = 40
SIM_THRESHOLD = 0.25       # 结论条与标题的二元组重合系数
CEILING_RATIO = 0.85       # 词数 ≥ 上限 × 该值，算“贴近上限”
CEILING_SHARE = 0.60       # 贴近上限的页占比超过它，判节奏单一
TAKE_SHARE = 0.60          # 结论条页占比上限
TEMPLATE_SHARE = 0.60      # 同一模板页占比上限
SVG_TOLERANCE = 0.05       # SVG 缩放偏离 1 超过它就提示

HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
VOID = {"br", "hr", "img", "meta", "link", "input"}
MONO = re.compile(r"mono|courier|consolas|menlo", re.I)
TAKE = re.compile(
    r"<(div|p)\b[^>]*>\s*<b\b[^>]*>\s*(?:所以|结论|小结|注意|Takeaway|So)\s*[：:]\s*</b>(.*?)</\1>", re.S
)
TAKE_CLS = re.compile(r"<(div|p)\b[^>]*class=\"[^\"]*\bcallout\b[^\"]*\"[^>]*>(.*?)</\1>", re.S)
# 外壳默认主题令牌（页面里有 <style> 时以页面为准）
THEMES = {
    "dark": {"bg": "#1b1815", "fg": "#f5f0e8", "muted": "#b8ada0", "accent": "#e0693a", "accent2": "#6cc3b8", "card": "#26221e", "code": "#100e0c"},
    "light": {"bg": "#f5f0e8", "fg": "#1b1815", "muted": "#5f574e", "accent": "#b8481c", "accent2": "#1d6f66", "card": "#fbf8f2", "code": "#26221e"},
    "accent": {"bg": "#b8481c", "fg": "#fff8f0", "muted": "#fff1e8", "accent": "#fff8f0", "accent2": "#fff1e8", "card": "#9c3b15", "code": "#1b1815"},
}
CLS_COLOR = {"lede": "muted", "sub": "muted", "ft": "muted", "eyebrow": "accent", "tag": "accent", "hl": "accent"}
CSS_SKIP = re.compile(r"#hint|#check|\.notes|\.ok|\.bad")
# “5 倍”“5×”都归为“倍”；“0.25 × 1/3”里的乘号不算
NUM = re.compile(r"(\d+(?:\.\d+)?)\s*(ps|ns|ms|μs|GHz|MHz|倍|%|拍)|(\d+(?:\.\d+)?)(×)(?![\s\d.])")
ALWAYS_REVIEW = {"倍"}      # 比值类声明：只出现在一页也列出来核对
CN = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
PROMISE_HDR = re.compile(r"听完|你能|将能|能够|学会|Outcome", re.I)
EYEBROW_NUM = re.compile(r"^\s*(\d{1,2})\s*[·.、．]")
PART_CLAIM = re.compile(r"[分共]\s*([一二三四五六七八九十\d]+)\s*个?\s*部分")


# ---------- 颜色与数值工具 ----------
def lum(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def prop(style, name):
    m = re.search(r"(?:^|;)\s*" + re.escape(name) + r"\s*:\s*([^;]+)", style or "")
    return m.group(1).strip() if m else None


def solid_hex(value):
    if not value or "gradient" in value or "url(" in value:
        return None
    m = HEX.search(value)
    return "#" + m.group(1) if m else None


def px_of(value):
    if not value:
        return None
    m = re.match(r"([\d.]+)px", value.strip())
    return float(m.group(1)) if m else None


def bigrams(s):
    s = re.sub(r"[\s，。；：、“”\"'（）()：:,.;!?！？\-—·]", "", s)
    return {s[i:i + 2] for i in range(len(s) - 1)}


def overlap(a, b):
    A, B = bigrams(a), bigrams(b)
    return len(A & B) / min(len(A), len(B)) if A and B else 0.0


def title_len(t):
    t = re.sub(r"\s+", "", t or "")
    return sum(1.0 if ord(ch) > 0x2E80 else 0.55 for ch in t)


def parse_themes(text):
    """从页面 <style> 里读取 .slide.<主题>{--bg:…} 令牌。"""
    out = {}
    for m in re.finditer(r"\.slide\.(\w+)\s*\{([^}]*)\}", text):
        toks = dict(re.findall(r"--(\w+)\s*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})", m.group(2)))
        if "bg" in toks and "fg" in toks:
            out[m.group(1)] = toks
    return out


def theme_issues(themes):
    out = []
    for name, t in themes.items():
        for k in ("fg", "muted", "accent", "accent2"):
            for base in ("bg", "card"):
                if k in t and base in t:
                    r = contrast(t[k], t[base])
                    if r < 4.5:
                        out.append(f"主题 {name}：--{k} 在 --{base} 上对比度 {r:.2f}:1 < 4.5")
    return out


def css_font_issues(text, used, min_font):
    """读取 <style> 里的 font-size，低于最小字号的规则（仅限页面用到的类）。"""
    out = []
    for style in re.findall(r"<style\b[^>]*>(.*?)</style>", text, flags=re.S):
        style = re.sub(r"/\*.*?\*/", "", style, flags=re.S)
        for m in re.finditer(r"([^{}@]+)\{([^{}]*)\}", style):
            sel, body = m.group(1).strip(), m.group(2)
            fs = re.search(r"font-size\s*:\s*([\d.]+)px", body)
            if not fs or CSS_SKIP.search(sel):
                continue
            px = float(fs.group(1))
            names = re.findall(r"\.([A-Za-z_][\w-]*)", sel.split(",")[0].split()[-1])
            if names and not any(n in used for n in names):
                continue
            if px < min_font - 0.5:
                out.append(f"样式 {sel[:40]} 字号 {px:g}px < {min_font}px")
    return out


def cn_or_int(s):
    return int(s) if s.isdigit() else CN.get(s)


def lint_viewer(text):
    """整份 HTML 的静态查看器检查（只对含 <script>/<style> 的完整页面）。
    这些写法在窗口不是恰好 1920×1080 时会错位或裁切；渲染实测用页面内置自检（C 键）。"""
    if not re.search(r"<section\b", text) or not re.search(r"<style\b", text):
        return []
    # 去掉注释（外壳自己的说明里会提到这些错误写法）
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"(?m)^[ \t]*//.*$", "", text)
    out = []
    uses_scale = "scale(" in text
    if re.search(r"width\s*:\s*1920px", text) and not re.search(r"box-sizing\s*:\s*border-box", text):
        out.append("缺 box-sizing:border-box：.slide 写了 1920px 宽又有 padding，实际会被撑大（如 2144×1300），页脚跑出画布")
    if uses_scale and re.search(r"transform-origin\s*:\s*center", text):
        out.append("缩放用了 transform-origin:center：窗口高度小于 1080 时画面被推低，上方留白、下方被裁；改为 0 0 加 translate 居中")
    if uses_scale and re.search(r"place-items\s*:\s*center", text):
        out.append("用 grid 的 place-items:center 居中缩放后的画布：布局盒仍是 1920×1080，非全屏会错位；改为 fixed 舞台 + translate")
    if uses_scale and "translate(" not in text:
        out.append("缩放没有配平移居中（translate）：画面不会落在窗口中央")
    return out


# ---------- 单页解析 ----------
class SectionChecker(HTMLParser):
    def __init__(self, min_font, content_w, themes=None):
        super().__init__(convert_charrefs=True)
        self.themes = themes or THEMES
        self.theme = None
        self.lede = None
        self._in_lede = False
        self._lede_buf = []
        self.cls_count = defaultdict(int)
        self.min_font = min_font
        self.content_w = content_w
        self.stack = []          # (tag, bg, color, size, svg_scale)
        self.issues = []
        self.sizes = set()
        self.families = set()
        self.words = 0
        self.blocks = 0
        self.has_notes = False
        self.in_aside = 0
        self._mono_seen = False
        self.title = None
        self.eyebrow = None
        self.tables = []
        self._in_title = None
        self._title_buf = []
        self._in_eyebrow = False
        self._eb_buf = []
        self._tbl = None
        self._row = None
        self._row_th = False
        self._cell = None

    # SVG 的有效缩放 = 渲染宽度 / viewBox 宽度
    def _svg_scale(self, a):
        vb = a.get("viewbox")
        if not vb:
            return None
        try:
            _, _, vw, vh = [float(x) for x in vb.replace(",", " ").split()]
        except ValueError:
            return None
        st = a.get("style", "")
        w, h = prop(st, "width"), prop(st, "height")
        if w and w.endswith("%"):
            try:
                return self.content_w * float(w[:-1]) / 100 / vw
            except ValueError:
                return None
        if px_of(w):
            return px_of(w) / vw
        if px_of(h) and (not w or w == "auto"):
            return px_of(h) / vh
        return None

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        a = dict(attrs)
        st = a.get("style", "")
        parent = self.stack[-1] if self.stack else (None, None, None, None, None)
        cls = (a.get("class") or "").split()
        for k in cls:
            self.cls_count[k] += 1
        if tag == "li":
            self.cls_count["li"] += 1
        tk = self.themes.get(self.theme, {}) if self.theme else {}
        if tag == "section":
            for k in cls:
                if k in self.themes:
                    self.theme = k
                    tk = self.themes[k]
        bg = solid_hex(prop(st, "background")) or parent[1]
        color = solid_hex(prop(st, "color")) or parent[2]
        if tk:
            if tag == "section" and self.theme:
                bg, color = tk["bg"], tk["fg"]
            if "card" in cls or "callout" in cls:
                bg, color = tk["card"], tk["fg"]
            if "code" in cls:
                bg, color = tk["code"], "#f5f0e8"
            for k in cls:
                if k in CLS_COLOR and CLS_COLOR[k] in tk and not solid_hex(prop(st, "color")):
                    color = tk[CLS_COLOR[k]]
            if tag == "th" and "accent" in tk:
                color = tk["accent"]
        if "lede" in cls and self.lede is None:
            self._in_lede, self._lede_buf = True, []
        size = px_of(prop(st, "font-size")) or parent[3]
        scale = parent[4]
        if tag == "section" and not solid_hex(prop(st, "background")) and not self.theme:
            self.issues.append("章节没有纯色 background（需要显式底色）")
        if tag == "svg":
            scale = self._svg_scale(a)
            self.blocks += 1
            if scale and abs(scale - 1) > SVG_TOLERANCE:
                self.issues.append(
                    f"SVG 缩放 {scale:.2f}：viewBox 宽度应等于显示宽度（按 1:1 绘制），否则内部字号失真"
                )
        if tag == "table":
            self.blocks += 1
            self._tbl = {"header": [], "rows": []}
        if tag == "tr":
            self._row, self._row_th = [], False
        if tag in ("th", "td"):
            self._cell = []
            if tag == "th":
                self._row_th = True
        if (tag in ("h1", "h2") or "title" in cls) and self.title is None:
            self._in_title, self._title_buf = tag, []
        if tag == "p" and self.title is None and self.eyebrow is None and not self._in_title and "lede" not in cls:
            self._in_eyebrow, self._eb_buf = True, []
        if tag == "aside":
            self.has_notes = True
            self.in_aside += 1
        own = px_of(prop(st, "font-size"))
        if own:
            self.sizes.add(int(own))
            eff = own * (scale if scale else 1)
            if eff < self.min_font - 0.5:
                extra = f"×缩放 {scale:.2f}＝有效 {eff:.1f}px" if scale and abs(scale - 1) > 0.02 else ""
                self.issues.append(f"字号 {own:g}px{extra} < {self.min_font}px（<{tag}>）")
        ff = prop(st, "font-family")
        if ff:
            self.families.add(ff.split(",")[0].strip().strip("'\""))
            if MONO.search(ff) and not self._mono_seen and tag in ("p", "div"):
                self.blocks += 1
                self._mono_seen = True
        self.stack.append((tag, bg, color, size, scale))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag == "aside" and self.in_aside:
            self.in_aside -= 1
        if self._in_lede and tag in ("p", "div", "span"):
            self.lede = "".join(self._lede_buf).strip()
            self._in_lede = False
        if self._in_title == tag:
            self.title = "".join(self._title_buf).strip()
            self._in_title = None
        if tag == "p" and self._in_eyebrow:
            self.eyebrow = "".join(self._eb_buf).strip()
            self._in_eyebrow = False
        if tag in ("th", "td") and self._cell is not None and self._row is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        if tag == "tr" and self._row is not None and self._tbl is not None:
            if self._row_th and not self._tbl["header"]:
                self._tbl["header"] = self._row
            else:
                self._tbl["rows"].append(self._row)
            self._row = None
        if tag == "table" and self._tbl is not None:
            self.tables.append(self._tbl)
            self._tbl = None
        while self.stack:
            if self.stack.pop()[0] == tag:
                break

    def handle_data(self, data):
        if self._in_title:
            self._title_buf.append(data)
        if self._in_eyebrow:
            self._eb_buf.append(data)
        if self._in_lede:
            self._lede_buf.append(data)
        if self._cell is not None:
            self._cell.append(data)
        if self.in_aside or not self.stack or not data.strip():
            return
        tag, bg, color, size, _ = self.stack[-1]
        self.words += len(re.findall(r"[一-鿿]|[A-Za-z0-9_]+", data))
        if bg and color:
            need = 3.0 if (size or 0) >= 44 else 4.5
            r = contrast(color, bg)
            if r < need:
                self.issues.append(
                    f"对比度 {r:.1f}:1 < {need}（{color} 在 {bg} 上）：“{data.strip()[:16]}”"
                )


class Slide:
    pass


def analyze(sec, label, name, cfg, content_w, themes=None):
    c = SectionChecker(cfg["min_font"], content_w, themes)
    c.feed(sec)
    cc = c.cls_count
    if cc["code"]:
        c.blocks += 1
    if cc["flow"]:
        c.blocks += 1
    if cc["step"] >= 3:
        c.blocks += 1
    if cc["kpi"]:
        c.blocks += 1
    if cc["card"] >= 2:
        c.blocks += 1
    if cc["note"] >= 3:
        c.blocks += 1      # 编号批注列
    if cc["li"] >= 3:
        c.blocks += 1      # 有序 / 无序列表（3 条以上）
    if cc["card"] >= 4:
        c.blocks += 1      # 网格 / 多列卡片算两个块
    s = Slide()
    s.label, s.name, s.c = label, name, c
    s.exempt = bool(EXEMPT.search(name))
    body = re.sub(r"<aside.*?</aside>", "", sec, flags=re.S)
    takes = {re.sub(r"<[^>]+>", "", m.group(2)).strip() for m in list(TAKE.finditer(body)) + list(TAKE_CLS.finditer(body))}
    s.takes = sorted(t for t in takes if t)
    s.text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))
    s.numbers = []
    for m in NUM.finditer(s.text):
        v, u = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), "倍")
        s.numbers.append((v, u))
    s.issues = list(dict.fromkeys(c.issues))
    s.sim = max((overlap(c.title or "", t) for t in s.takes), default=0.0)
    s.sim_lede = max((overlap(c.lede or "", t) for t in s.takes), default=0.0) if c.lede else 0.0
    s.class_shell = cc["title"] > 0 or cc["lede"] > 0
    s.has_table = bool(c.tables)
    return s


def collect(paths):
    files = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files += sorted(p.rglob("*.html"))
        elif p.exists():
            files.append(p)
    return files


def main():
    args = sys.argv[1:]
    profile, content_w, verbose = "tech", 1696.0, False
    if "-v" in args:
        verbose = True
        args.remove("-v")
    if "--profile" in args:
        i = args.index("--profile")
        if i + 1 >= len(args) or args[i + 1] not in PROFILES:
            print("--profile 需要是 talk / tech / read")
            sys.exit(2)
        profile = args[i + 1]
        del args[i:i + 2]
    if "--content-width" in args:
        i = args.index("--content-width")
        content_w = float(args[i + 1])
        del args[i:i + 2]
    if not args:
        print(__doc__)
        sys.exit(2)
    cfg = PROFILES[profile]

    slides = []
    viewer = []
    page_issues = []
    for f in collect(args):
        text = f.read_text(encoding="utf-8", errors="ignore")
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)   # 注释里的标签不算内容
        viewer += [(f.name, m) for m in lint_viewer(text)]
        themes = parse_themes(text) or THEMES
        used = set(re.findall(r"class=\"([^\"]+)\"", text))
        used = {k for v in used for k in v.split()}
        page_issues += [(f.name, m) for m in theme_issues(themes) + css_font_issues(text, used, cfg["min_font"])]
        for i, sec in enumerate(re.findall(r"<section\b.*?</section>", text, flags=re.S)):
            sid = re.search(r'id="([^"]+)"', sec[:200])
            name = sid.group(1) if sid else str(i + 1)
            slides.append(analyze(sec, f"{f.name}#{name}", name, cfg, content_w, themes))
    if not slides:
        print("没有找到 <section>。")
        sys.exit(1)

    # ---- 逐页 ----
    for s in slides:
        c = s.c
        if not c.has_notes:
            s.issues.append("缺少演讲者备注 <aside>")
        if c.words > cfg["max_words"]:
            s.issues.append(f"偏满：{c.words} 词 > {cfg['max_words']}，拆论点（不是删证据）")
        if not s.exempt and c.words < cfg["min_words"]:
            s.issues.append(f"偏稀：{c.words} 词 < {cfg['min_words']}，补具体信息（命令、数字、机制、取舍、例子）")
        if not s.exempt and profile != "talk" and c.blocks < 2:
            s.issues.append(f"结构化证据块 {c.blocks} 个 < 2（表格 / 代码 / 图 / 对比栏）")
        for t in c.tables:
            rows = [r for r in t["rows"] if r]
            if len(rows) >= 3:
                ncol = max(len(r) for r in rows)
                for j in range(ncol):
                    vals = [r[j] for r in rows if len(r) == ncol]
                    if len(vals) >= 3 and len(set(vals)) == 1 and vals[0]:
                        hdr = t["header"][j] if j < len(t["header"]) else f"第{j + 1}列"
                        s.issues.append(f"常量列“{hdr}”：{len(vals)} 行都是“{vals[0][:12]}”，没有信息，删掉或改成有区分度的内容")
        if not s.exempt:
            if c.title:
                tl = title_len(c.title)
                if tl > TITLE_LIMIT[profile]:
                    s.issues.append(f"标题过长：“{c.title[:24]}”约 {tl:.0f} 字 > {TITLE_LIMIT[profile]}：改成短标题，把结论放进副标题 .lede")
                if re.search(r"[，,；;。]", c.title):
                    s.issues.append(f"标题含逗号 / 句号：“{c.title[:24]}”是完整句子，拆成短标题 + 副标题")
            if s.class_shell and not c.lede:
                s.issues.append("缺少 .lede 结论副标题")
            if c.lede and title_len(c.lede) > LEDE_LIMIT:
                s.issues.append(f"副标题约 {title_len(c.lede):.0f} 字 > {LEDE_LIMIT}：压缩到一行")
            if s.takes and s.sim_lede >= SIM_THRESHOLD:
                s.issues.append(f"结论条与副标题重合度 {s.sim_lede:.2f} ≥ {SIM_THRESHOLD}：二者说了同一件事，删一个")
        if s.takes and s.sim >= SIM_THRESHOLD:
            s.issues.append(f"结论条与标题重合度 {s.sim:.2f} ≥ {SIM_THRESHOLD}：结论条要给新信息（含义、反例、阈值、行动），不复述标题")
        if verbose and s.takes:
            print(f"  (sim {s.label}: {s.sim:.2f})")

    content = [s for s in slides if not s.exempt]
    deck = []

    # ---- 全套：节奏 ----
    if len(content) >= 6:
        near = [s for s in content if s.c.words >= cfg["max_words"] * CEILING_RATIO]
        if len(near) / len(content) > CEILING_SHARE:
            deck.append(
                f"节奏单一：{len(near)}/{len(content)} 页词数贴近上限（≥ {int(cfg['max_words'] * CEILING_RATIO)}）。"
                "留出低密度锚点页（一张大图、一个大数字），最高密度页不超过六成"
            )
        with_take = [s for s in content if s.takes]
        if len(with_take) / len(content) > TAKE_SHARE:
            deck.append(
                f"结论条出现在 {len(with_take)}/{len(content)} 页（> {int(TAKE_SHARE * 100)}%）："
                "只在有新信息时使用，其余页让证据自己说话"
            )
        sig = defaultdict(list)
        for s in content:
            sig[(s.has_table, bool(s.takes))].append(s.name)
        (k, names), = [max(sig.items(), key=lambda kv: len(kv[1]))]
        if len(names) / len(content) > TEMPLATE_SHARE and k == (True, True):
            deck.append(
                f"模板单一：{len(names)}/{len(content)} 页都是“表格 + 结论条”。"
                "至少混用 3 种版式（大图、批注代码、对比栏、步骤序列、大数字）"
            )

    # ---- 全套：目录声称的部分数 vs 页眉编号 ----
    nums = [int(m.group(1)) for s in slides if s.c.eyebrow for m in [EYEBROW_NUM.match(s.c.eyebrow)] if m]
    claims = []
    for s in slides:
        for m in PART_CLAIM.finditer(s.text):
            v = cn_or_int(m.group(1))
            if v:
                claims.append((s.name, v))
    if nums and claims:
        mx = max(nums)
        for name, v in claims:
            if v != mx:
                deck.append(f"章节数不一致：{name} 声称 {v} 个部分，但页眉编号最大到 {mx:02d}")
                break

    # ---- 全套：字号 / 字体 ----
    all_sizes = set().union(*[s.c.sizes for s in slides])
    all_fams = set().union(*[s.c.families for s in slides])
    if len(all_sizes) > MAX_SIZES:
        deck.append(f"字号种类 {len(all_sizes)} > {MAX_SIZES}，合并成 5–6 级字阶")
    if len(all_fams) > MAX_FAMILIES:
        deck.append(f"字体种类 {len(all_fams)} > {MAX_FAMILIES}")

    # ---- 输出 ----
    total = 0
    for s in slides:
        if s.issues:
            total += len(s.issues)
            print(f"[{s.label}]")
            for it in s.issues:
                print("  -", it)
    if deck:
        print("\n[全套]")
        for it in deck:
            total += 1
            print("  -", it)
    if page_issues:
        print("\n[样式与主题]")
        for fname, it in page_issues:
            total += 1
            print(f"  - {fname}: {it}")
    if viewer:
        print("\n[查看器]")
        for fname, it in viewer:
            total += 1
            print(f"  - {fname}: {it}")

    print()
    print(f"档位 {profile}；共 {len(slides)} 页；字号 {sorted(all_sizes)}；字体 {sorted(all_fams)}")
    print("每页词数 / 结构块：" + "，".join(f"{s.name}={s.c.words}/{s.c.blocks}" for s in slides))

    # ---- 人工核对清单（不计入问题数）----
    by_unit = defaultdict(lambda: defaultdict(list))
    for s in slides:
        for v, u in s.numbers:
            if v not in by_unit[u][s.name]:
                by_unit[u][s.name].append(v)
    lines = []
    for u, per_slide in by_unit.items():
        if len(per_slide) >= 2 or u in ALWAYS_REVIEW:
            lines.append(f"  {u}：" + "；".join(f"{n}[{','.join(vs)}]" for n, vs in per_slide.items()))
    promises = []
    for s in slides:
        for t in s.c.tables:
            for j, h in enumerate(t["header"]):
                if PROMISE_HDR.search(h):
                    promises += [(s.name, r[j]) for r in t["rows"] if j < len(r) and r[j]]
    if lines or promises:
        print("\n[人工核对（不计入问题数）]")
        if lines:
            print("跨页数值，确认同一量在各页一致、且比值可由页上数字推出：")
            print("\n".join(lines))
        if promises:
            print("目录里的“听完你能……”，逐条确认有对应页面：")
            for n, p in promises:
                print(f"  {n}: {p}")

    print("\n发现问题：", total)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
