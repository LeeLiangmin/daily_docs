#!/usr/bin/env python3
"""扫描 Rust 新实现，找出**设计亮点候选**。

为什么需要它：其余脚本全部指向旧仓库（历史缺陷、变更成本、危险模式），
工具的方向决定了挖掘的方向——只有考古工具，写出来的就是缺陷起诉书。
本脚本反过来，从新实现里找"团队做了设计判断"的痕迹，供文档的主体章节使用。

它找的不是"用了 Rust 特性"（那是教科书条目），而是**只有做过设计取舍才会出现的结构**：
newtype 区分语义、typestate 表达状态、私有字段 + 校验构造器、sealed trait、
Mutex<T> 把数据关进锁里、零拷贝签名、封装比例，等等。

输出是候选，需要人工判断哪些真有设计含量。

用法:
    python find_design_signals.py --root /path/to/rust/src
    python find_design_signals.py --root src/ --json signals.json
"""

import argparse
import json
import os
import re
from collections import defaultdict

SKIP_DIRS = {".git", "target", "node_modules", ".cache"}

# 每条信号：(名称, 正则, 设计含量说明, 该问的问题)
SIGNALS = [
    ("newtype（元组结构体包装单一类型）",
     r"^[ \t]*(?:pub(?:\([\w:]+\))?\s+)?struct\s+(\w+)\s*\(\s*(?:pub\s+)?[^,)]+\)\s*;",
     "把语义相同的底层类型区分开——旧实现里通常都是 int/char*，靠命名约定",
     "这个 newtype 区分的是什么？旧实现里这两个概念混用过吗？"),

    ("typestate（类型参数表示状态）",
     r"PhantomData\s*<|^[ \t]*(?:pub(?:\([\w:]+\))?\s+)?struct\s+\w+\s*<\s*S(?:tate)?\s*(?::|>)",
     "把操作顺序/状态提升到类型层面，非法调用编译不过",
     "它表达的是什么顺序约束？旧实现里这条约束写在哪（注释？运行时挡？）"),

    ("可失败构造器（构造即合法）",
     r"fn\s+(?:new|try_new|with_\w+|from_\w+)\s*\([^)]*\)\s*->\s*(?:Result|Option)\s*<",
     "一经构造即合法：非法值无法存在，而不是构造后再逐个校验",
     "构造时校验了什么不变量？旧实现在哪里校验、漏过吗？"),

    ("消费式 builder（链式配置）",
     r"fn\s+\w+\s*\(\s*mut\s+self\s*,[^)]*\)\s*->\s*Self\b|fn\s+build\s*\(\s*self\b|struct\s+\w+Builder\b",
     "配置在构造期一次定完，取代加载后仍可调用的 setter",
     "旧实现是一堆运行时 setter 吗？加载后再调用会怎样（静默忽略？未定义？）"),

    ("sealed trait / 封闭抽象",
     r"mod\s+(?:private|sealed)\b|:\s*sealed::|trait\s+\w+\s*:\s*\w*[Ss]ealed",
     "抽象对外封闭，外部无法错误扩展",
     "为什么要封闭？旧实现的扩展点是怎么防误用的？"),

    ("Mutex/RwLock 直接包住数据",
     r"\b(?:Mutex|RwLock)\s*<\s*(?!\(\s*\)\s*>)[A-Z]\w*",
     "数据关在锁里——拿不到锁就拿不到数据，'忘记加锁'这个动作不存在",
     "旧实现里锁和数据是分开的吗？绑定关系写在哪？"),

    ("trait 定义（扩展点）",
     r"^[ \t]*(?:pub(?:\([\w:]+\))?\s+)?trait\s+(\w+)",
     "扩展点的契约由编译器强制，取代 void* + 函数指针",
     "旧实现对应的扩展点是什么形态？新增一个实现要改几处？"),

    ("泛型 sink / 依赖注入（对目的地抽象）",
     r"fn\s+\w+\s*<\s*\w+\s*:\s*(?:std::io::)?(?:Write|Read)\b|"
     r"&\s*mut\s+dyn\s+(?:std::io::)?(?:Write|Read)\b",
     "输出目的地由标准 trait 抽象，取代自定义回调基类；错误可沿签名上报",
     "旧实现为此定义了几个类？回调返回 void 吗（写失败能上报吗）？"),

    ("枚举定义（封闭状态空间）",
     r"^[ \t]*(?:pub(?:\([\w:]+\))?\s+)?enum\s+(\w+)",
     "状态集合封闭，新增变体时编译器列出所有待改点",
     "旧实现里这组状态是 #define + switch 吗？新增时漏改过吗？"),

    ("match 分发点（是否穷尽需人工确认）",
     r"^[ \t]*match\s+[^\n{]+\{",
     "对枚举的 match 若无 _ 兜底则是穷尽的，新增变体会编译失败；对非枚举的 match 无此性质",
     "先确认它匹配的是不是枚举、有没有 _ 通配；再问旧实现同样的分发有几处、漏改过吗"),

    ("NonZero / NonNull（值域约束）",
     r"\bNonZero\w+|\bNonNull\s*<",
     "值域约束进类型，取代 0/NULL 哨兵值",
     "旧实现用什么当哨兵？哨兵被当作合法值用过吗？"),

    ("借用式返回 / 迭代器（零拷贝出口）",
     r"->\s*(?:impl\s+Iterator\s*<\s*Item\s*=\s*&|&\s*(?:'\w+\s+)?(?:str|\[)|Cow\s*<)",
     "返回借用而非拷贝，且生命周期由编译器绑定——旧实现返回内部指针要靠文档警告",
     "旧实现对应的返回值是内部指针吗？文档里写了几次'不得在对象销毁后使用'？"),

    ("Bytes / 引用计数缓冲（共享而不拷贝）",
     r"\bBytes\b|\bArc\s*<|\bRc\s*<",
     "共享点显式化：出现的地方就是系统真正需要共享的地方",
     "旧实现靠什么共享？手工引用计数还是裸指针 + 生命周期约定？"),

    ("自定义错误枚举",
     r"#\[derive\([^)]*\bError\b[^)]*\)\]|impl\s+std::error::Error\s+for",
     "错误分类由类型承载，可穷尽匹配，根因链可追溯",
     "旧实现的错误是几个 int 常量吗？信息在传播中丢失过吗？"),

    ("#[from] 错误转换（保留根因）",
     r"#\[\s*from\s*\]|impl\s+From\s*<[^>]+>\s+for\s+\w*Error",
     "底层错误原样进入本层错误类型，source() 链完整",
     "旧实现的错误细节靠什么捎带（errno？全局变量？）转发时丢过吗？"),

    ("#[must_use] 显式标注",
     r"#\[\s*must_use",
     "作者主动要求返回值不可被丢弃——超出默认保证的设计动作",
     "为什么这里需要额外强调？旧实现在这里被忽略过吗？"),

    ("Drop 实现（资源收尾）",
     r"impl\s+(?:<[^>]*>\s*)?Drop\s+for\s+(\w+)",
     "收尾逻辑与类型绑定，覆盖所有退出路径",
     "旧实现对应的清理在哪？goto cleanup 有几条分支？"),

    ("自由函数 + 显式输入输出（纯函数模块）",
     r"^[ \t]*(?:pub(?:\([\w:]+\))?\s+)?fn\s+(?!new\b|default\b|from\b|clone\b)\w+\s*"
     r"\(\s*(?!&?\s*(?:mut\s+)?self\b)[^)]*\)\s*->\s*(?!Self\b)",
     "不依赖对象内部状态，可独立理解与独立测试",
     "旧实现同一逻辑依赖几个成员字段？能脱离对象单独测试吗？"),

    ("有序容器（顺序是被刻意保留的）",
     r"\bIndexMap\s*<|\bBTreeMap\s*<|\bVecDeque\s*<",
     "容器选型本身是设计决策：顺序语义被显式表达，而非依赖实现细节",
     "旧实现靠什么维持顺序？额外的 order 字段 + 排序，还是碰巧？"),

    ("Option 字段（可选性显式化）",
     r"^[ \t]*(?:pub(?:\([\w:]+\))?\s+)?\w+\s*:\s*Option\s*<",
     "'可能没有'进入类型，取代 NULL/空串/-1 哨兵",
     "旧实现这个字段用什么表示'没有'？哨兵值和合法值混淆过吗？"),
]

VIS = {
    "pub": re.compile(r"^\s*pub\s+(?:fn|struct|enum|trait|mod|const|type)\s", re.M),
    "pub(crate)": re.compile(r"^\s*pub\(crate\)\s+(?:fn|struct|enum|trait|mod|const|type)\s", re.M),
    "private": re.compile(r"^\s*(?:fn|struct|enum|trait|mod|const|type)\s", re.M),
}

HEALTH = {
    "unsafe": r"\bunsafe\b",
    "unwrap()": r"\.unwrap\s*\(\s*\)",
    "expect()": r"\.expect\s*\(",
    "panic!": r"\bpanic!\s*\(",
    "clone()": r"\.clone\s*\(\s*\)",
}


def walk(root):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS and not d.startswith(".")]
        for f in fn:
            if f.endswith(".rs"):
                yield os.path.join(dp, f)


def strip_comments(text):
    """去掉行注释与文档注释，避免注释里的关键词被当成代码信号。
    保留行数不变（用空行替换），以免行号错位。"""
    out = []
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("//"):
            out.append("\n" if line.endswith("\n") else "")
        else:
            out.append(line)
    return "".join(out)


def strip_tests(text):
    """去掉 #[cfg(test)] 模块，避免测试代码污染信号统计。
    用空行替换而非删除，保持行号与原文一致。"""
    out, depth, skipping = [], 0, False
    blank = lambda line: "\n" if line.endswith("\n") else ""
    for line in text.splitlines(keepends=True):
        if not skipping and re.search(r"#\[\s*cfg\s*\(\s*test\s*\)", line):
            skipping, depth = True, 0
            out.append(blank(line))
            continue
        if skipping:
            depth += line.count("{") - line.count("}")
            if depth <= 0 and "}" in line:
                skipping = False
            out.append(blank(line))
            continue
        out.append(line)
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--new", "--root", dest="new", required=True,
                    help="Rust 新实现源码目录，如 src/")
    ap.add_argument("--include-tests", action="store_true",
                    help="不剔除 #[cfg(test)] 模块")
    ap.add_argument("--json")
    args = ap.parse_args()

    hits = defaultdict(list)
    vis_count, health = defaultdict(int), defaultdict(int)
    files = 0

    for path in walk(args.new):
        files += 1
        raw = open(path, encoding="utf-8", errors="replace").read()
        text = raw if args.include_tests else strip_tests(raw)
        text = strip_comments(text)
        rel = os.path.relpath(path, args.new)
        lines = raw.splitlines()   # 展示用原文，保留注释便于阅读上下文

        for name, pat, _why, _q in SIGNALS:
            for m in re.finditer(pat, text, re.MULTILINE):
                # 锚定到匹配文本里第一个非空行，避免 ^\s* 吞掉前导换行导致行号偏移
                offset = m.start() + (len(m.group(0)) - len(m.group(0).lstrip("\n \t")))
                ln = text[:offset].count("\n") + 1
                snippet = lines[ln - 1].strip() if ln - 1 < len(lines) else ""
                hits[name].append((rel, ln, snippet[:90]))
        for k, rx in VIS.items():
            vis_count[k] += len(rx.findall(text))
        for k, pat in HEALTH.items():
            health[k] += len(re.findall(pat, text))

    if not files:
        raise SystemExit("没有找到 .rs 文件，检查 --new")

    print(f"扫描 {files} 个 .rs 文件"
          f"（{'含' if args.include_tests else '已剔除'} #[cfg(test)] 模块）\n")

    print("=" * 72)
    print("设计亮点候选 —— 按信号分组，每条附该追问的问题")
    print("=" * 72)
    order = sorted(SIGNALS, key=lambda s: -len(hits[s[0]]))
    for name, _pat, why, question in order:
        rows = hits[name]
        if not rows:
            continue
        print(f"\n● {name}  （{len(rows)} 处）")
        print(f"  设计含量：{why}")
        print(f"  该问：{question}")
        seen = set()
        for rel, ln, snip in rows:
            key = (rel, ln)
            if key in seen:
                continue
            seen.add(key)
            if len(seen) > 6:
                print(f"    …… 另有 {len(rows) - 6} 处")
                break
            print(f"    {rel}:{ln}  {snip}")

    missing = [n for n, _p, _w, _q in SIGNALS if not hits[n]]
    if missing:
        print("\n" + "=" * 72)
        print("未出现的信号 —— 不是缺陷，但值得想一下为什么没用")
        print("=" * 72)
        for n in missing:
            print(f"  · {n}")
        print("  如果旧实现里存在对应的约定（比如'必须先 init'却没有 typestate），")
        print("  说明这条不变量可能仍是注释约定——那是'代价与局限'一节的内容。")

    print("\n" + "=" * 72)
    print("封装与体检")
    print("=" * 72)
    tot = sum(vis_count.values()) or 1
    print(f"  可见性：pub {vis_count['pub']} / pub(crate) {vis_count['pub(crate)']} / "
          f"私有 {vis_count['private']}"
          f"（对外暴露占比 {vis_count['pub'] / tot * 100:.0f}%）")
    print("  体检（写进'代价与局限'，主动披露）：")
    for k in ("unsafe", "unwrap()", "expect()", "panic!", "clone()"):
        print(f"    {k}: {health[k]}")

    print("""
怎么用这份结果：
  1. 每条信号后面的"该问"，就是 design-patterns.md 里"设计意图五问"的入口。
     带着它去读对应代码，再去旧实现找对照物。
  2. 出现次数少的信号往往比出现次数多的更有价值——一个 typestate 比二十个
     Result 更能说明团队做过设计判断。
  3. 信号只是候选。判断标准仍是：把它讲给另一个 Rust 工程师听，他学到的是
     "Rust 的特性"还是"你们的设计"？后者才值得写进主体章节。
  4. 体检数字主动写进文档，比被评审问出来强得多。
""")
    print("=" * 72)
    print("  ⚠ 以上为启发式匹配的未复核结果，禁止直接写入文档。")
    print("  ⚠ 引用任何数字或结论前，先打开对应代码确认，并在文档中注明口径。")
    print("=" * 72)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({
                "root": args.new, "files": files,
                "signals": {n: [{"file": r, "line": l, "text": s}
                                for r, l, s in hits[n]] for n in hits},
                "missing_signals": missing,
                "visibility": dict(vis_count),
                "health": dict(health),
                "caveat": "正则匹配，存在假阳性与漏检；信号是候选，需人工判断设计含量。",
            }, f, ensure_ascii=False, indent=2)
        print(f"完整结果已写入 {args.json}")


if __name__ == "__main__":
    main()
