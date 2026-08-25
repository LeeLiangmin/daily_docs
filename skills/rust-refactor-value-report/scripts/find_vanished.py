#!/usr/bin/env python3
"""找出**旧实现有、新实现没有对应物**的机制。

为什么需要它：重写的最大价值往往不是"新增了什么巧妙的类型"，而是"旧实现里
一整套机制失去了存在的必要"——手工引用计数、回滚代码、转换层、对象池、
清理纪律。这类证据在 design-patterns.md 里被列为最有分量的设计决策，
但此前没有任何工具能发现它：其余脚本要么挖旧仓库的历史缺陷，要么扫新实现
里出现了什么，**没有一个做"消失"这件事**。

做法：抽取旧实现的公共符号（函数、结构体、宏），逐个到新实现里找近似对应物
（跨语言命名归一化：CopyString→copy_string / copy_str / copy…），
找不到的列为"疑似消失"，并按扇入排序——扇入越高的机制，消失的分量越重。

跨语言名字匹配必然粗糙，输出是**候选**，必须人工判断：
  · 真的消失了（价值点）
  · 换了个名字（不是消失，去掉）
  · 功能被砍了（属于范围决策，写进"对比基准"而不是价值点）

用法:
    python find_vanished.py --old <cpp-src> --new <rust-src>
    python find_vanished.py --old simpleini --new simpleini_rs/src --top 30
"""

import argparse
import json
import os
import re
from collections import Counter

C_SRC = {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hh", ".hxx", ".inl"}
SKIP_DIRS = {".git", "build", "out", "target", "node_modules", "third_party",
             "vendor", "external", "cmake-build-debug", "tests", "test"}

FUNC = re.compile(
    r"^[ \t]*(?!#|//)(?:[A-Za-z_][\w:<>,\s\*&]*?[\s\*&])([A-Za-z_]\w{3,})\s*\([^;{]*\)\s*[;{]",
    re.MULTILINE)
STRUCT = re.compile(
    r"^[ \t]*(?:typedef\s+)?(?:struct|class|union)\s+(\w{3,})\b", re.MULTILINE)
MACRO = re.compile(r"^[ \t]*#\s*define\s+([A-Z_][A-Z0-9_]{3,})\b", re.MULTILINE)
MEMBER = re.compile(r"^[ \t]*(?:[A-Za-z_][\w:<>,\s\*&]*?[\s\*&])(m_\w{2,})\s*[;=\[]",
                    re.MULTILINE)

KEYWORDS = {
    "if", "for", "while", "switch", "return", "sizeof", "defined", "typedef",
    "struct", "union", "enum", "static", "const", "void", "int", "char", "long",
    "short", "unsigned", "signed", "float", "double", "extern", "inline", "goto",
    "else", "case", "break", "class", "public", "private", "protected", "template",
    "typename", "namespace", "using", "operator", "virtual", "friend", "explicit",
    "true", "false", "null", "nullptr", "this", "new", "delete",
}

# 这些前缀/后缀在跨语言比对时不携带信息，归一化时剥掉
NOISE_TOKENS = {"get", "set", "is", "has", "do", "impl", "internal", "helper",
                "temp", "tmp", "the", "a", "an"}


def walk(root, exts=None):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS and not d.startswith(".")]
        for f in fn:
            if exts is None or os.path.splitext(f)[1].lower() in exts:
                yield os.path.join(dp, f)


def read(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def split_identifier(name):
    """CopyString / copy_string / m_pData / SI_MAX_SIZE → 小写词元集合。"""
    n = re.sub(r"^(m_|g_|s_|SI_|si_)", "", name)
    n = re.sub(r"^(p|a|b|n|u|sz)(?=[A-Z])", "", n)  # 匈牙利前缀
    parts = re.split(r"[_\s]+", n)
    out = []
    for part in parts:
        out += re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z0-9]+|\d+", part)
    toks = {t.lower() for t in out if t}
    toks -= NOISE_TOKENS
    return {t for t in toks if len(t) >= 3}


def build_new_index(new_root):
    """新实现的标识符索引。

    关键：按**单个标识符**保存词元集合，而不是把全库词元揉成一个大集合。
    否则 `DeleteString` 会因为 `delete_key` 和 `String` 各自存在而被误判成"保留"——
    真正的对应物要求这些词元出现在同一个名字里。
    """
    raw_ids, ident_tokens, all_tokens = set(), [], set()
    for p in walk(new_root, {".rs"}):
        text = read(p)
        text = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
        seen = set()
        for ident in re.findall(r"\b[A-Za-z_]\w{2,}\b", text):
            raw_ids.add(ident.lower())
            if ident in seen:
                continue
            seen.add(ident)
            toks = split_identifier(ident)
            if toks:
                ident_tokens.append(toks)
                all_tokens |= toks
    return raw_ids, ident_tokens, all_tokens


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", required=True, help="C/C++ 旧实现源码目录")
    ap.add_argument("--new", required=True, help="Rust 新实现源码目录")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--json")
    args = ap.parse_args()

    # 1. 抽取旧实现符号，并统计扇入（被多少个文件提及）
    kinds, fanin = {}, Counter()
    old_files = list(walk(args.old, C_SRC))
    if not old_files:
        raise SystemExit("没有在 --old 下找到 C/C++ 源文件")
    texts = {p: read(p) for p in old_files}
    for p, text in texts.items():
        clean = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
        clean = re.sub(r"//[^\n]*", " ", clean)
        for rx, kind in ((FUNC, "函数"), (STRUCT, "类型"),
                         (MACRO, "宏"), (MEMBER, "成员状态")):
            for m in rx.finditer(clean):
                name = m.group(1)
                if name.lower() in KEYWORDS or not split_identifier(name):
                    continue
                kinds.setdefault(name, kind)
    all_text = "\n".join(texts.values())
    for name in kinds:
        fanin[name] = len(re.findall(r"\b" + re.escape(name) + r"\b", all_text))

    # 2. 新实现索引
    raw_ids, ident_tokens, all_tokens = build_new_index(args.new)
    if not raw_ids:
        raise SystemExit("没有在 --new 下找到 .rs 文件")

    # 3. 逐个判断有无对应物
    vanished, kept = [], []
    for name, kind in kinds.items():
        toks = split_identifier(name)
        if name.lower() in raw_ids:
            kept.append(name)
            continue
        # 只有当某个新标识符**同时**覆盖全部词元时，才认为是改名而非消失
        covered = any(toks <= t for t in ident_tokens)
        if covered:
            kept.append(name)
            continue
        best = max((len(toks & t) for t in ident_tokens), default=0)
        scattered = len(toks & all_tokens)
        if best == 0 and scattered == 0:
            why = "无任何词元对应"
        elif best == 0:
            why = f"词元散见于不同名字（{scattered}/{len(toks)}），无单一对应物"
        else:
            why = f"最佳单名覆盖 {best}/{len(toks)} 词元"
        vanished.append((name, kind, fanin[name], why))

    vanished.sort(key=lambda r: -r[2])

    print(f"旧实现: {args.old}（{len(old_files)} 个源文件，抽出 {len(kinds)} 个符号）")
    print(f"新实现: {args.new}")
    print(f"疑似消失: {len(vanished)}   疑似保留/改名: {len(kept)}\n")

    print("=" * 72)
    print("疑似消失的机制 —— 按扇入排序，扇入越高分量越重")
    print("=" * 72)
    print(f"{'符号':<32}{'类别':<10}{'旧实现引用':>10}  判定依据")
    for name, kind, fi, why in vanished[:args.top]:
        print(f"{name:<32}{kind:<10}{fi:>10}  {why}")
    if len(vanished) > args.top:
        print(f"…… 另有 {len(vanished) - args.top} 个，用 --top 调整或看 --json")

    print("""
怎么用这份结果：
  1. 逐个分类，只有第一类是价值点：
       · 真的消失了 —— 旧实现需要这套机制，新实现的结构让它没有存在的必要
       · 只是改了名 —— 去掉，不是消失
       · 功能被砍了 —— 属于范围决策，写进"对比基准"而不是价值点
  2. 对确认消失的，按 design-patterns.md 的反推法第 4 条追问：
       这个机制当初解决什么问题 → 那个问题在新结构下还存在吗
       → 是什么结构变化让它消失的
     这条链就是文档主体章节的一节。
  3. 扇入高的优先——一个被引用 40 次的机制消失，比一个被引用 2 次的有分量得多。
  4. 成组出现的消失（同一批机制一起没了）说明背后是同一个设计决策，
     那正是"一个决策消除一整类问题"，值得单独成节。
""")
    print("=" * 72)
    print("  ⚠ 跨语言名字匹配必然粗糙，以上为未复核候选，禁止直接写入文档。")
    print("  ⚠ 每一条都要人工确认属于哪一类，再决定是否进文档。")
    print("=" * 72)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({
                "old": args.old, "new": args.new,
                "vanished": [{"name": n, "kind": k, "fanin": fi, "why": w}
                             for n, k, fi, w in vanished],
                "kept_sample": sorted(kept)[:200],
                "caveat": "跨语言标识符匹配，假阳性与漏检均常见；候选需人工分类。",
            }, f, ensure_ascii=False, indent=2)
        print(f"完整结果已写入 {args.json}")


if __name__ == "__main__":
    main()
