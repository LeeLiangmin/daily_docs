#!/usr/bin/env python3
"""大规模 C/C++ 代码库里定位"核心"：按扇入排序符号与数据结构。

解决的问题：几十万行代码没法通读，必须先知道读什么。图谱工具（GitNexus 等）能
给出精确结果，本脚本是没有图谱工具时的替代方案——基于头文件声明 + 全库引用计数，
粗糙但足够排序。

三种排序：
  1. 函数扇入：被多少个不同文件引用。高扇入 = 接口契约的核心。
  2. 数据结构扇入：被多少个不同文件读写。**这个通常比函数更能指出系统的核心**——
     在 C 项目里，系统的"血液"是那几个到处传递的 struct。
  3. 核心 × 热点交集：高扇入 且 改动频繁的，是"既核心又难维护"的地方，
     A 级素材的高发区（需要 --repo 提供 git 仓库）。

用法:
    python rank_core_symbols.py --root /path/to/c-src
    python rank_core_symbols.py --root src/ --repo . --top 20
    python rank_core_symbols.py --root src/ --json core.json
"""

import argparse
import json
import os
import re
import subprocess
from collections import Counter, defaultdict

C_SRC = {".c", ".cc", ".cpp", ".cxx"}
C_HDR = {".h", ".hpp", ".hh", ".hxx"}
SKIP_DIRS = {".git", "build", "out", "node_modules", "third_party", "vendor",
             "external", "cmake-build-debug", "target"}

# 头文件里的函数声明：返回类型 名字(
FUNC_DECL = re.compile(
    r"^\s*(?!#|//|/\*)(?:[A-Za-z_][\w\s\*]*?[\s\*])([A-Za-z_]\w{2,})\s*\([^;{]*\)\s*;",
    re.MULTILINE)
STRUCT_DECL = re.compile(
    r"^\s*typedef\s+struct\s*(?:\w+)?\s*\{[^}]*\}\s*(\w+)\s*;|"
    r"^\s*struct\s+(\w+)\s*\{", re.MULTILINE)

KEYWORDS = {"if", "for", "while", "switch", "return", "sizeof", "defined",
            "typedef", "struct", "union", "enum", "static", "const", "void",
            "int", "char", "long", "short", "unsigned", "signed", "float",
            "double", "extern", "inline", "goto", "else", "case", "break"}


def walk(root, exts):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in exts:
                yield os.path.join(dirpath, fn)


def read(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


MACRO_PARAM = re.compile(r"^\s*#\s*define\s+\w+\s*\(([^)]*)\)", re.MULTILINE)


def macro_params(text):
    """宏参数名会被误认成结构体/函数名，先收集起来排除。"""
    names = set()
    for m in MACRO_PARAM.finditer(text):
        for part in m.group(1).split(","):
            part = part.strip()
            if re.fullmatch(r"\w+", part):
                names.add(part)
    return names


def collect_symbols(root):
    funcs, structs, decl_file = set(), set(), {}
    for h in walk(root, C_HDR):
        text = read(h)
        skip = macro_params(text)
        for m in FUNC_DECL.finditer(text):
            name = m.group(1)
            if name and name not in KEYWORDS and name not in skip:
                funcs.add(name)
                decl_file.setdefault(name, os.path.relpath(h, root))
        for m in STRUCT_DECL.finditer(text):
            name = m.group(1) or m.group(2)
            if name and name not in KEYWORDS and name not in skip:
                structs.add(name)
                decl_file.setdefault(name, os.path.relpath(h, root))
    return funcs, structs, decl_file


def count_refs(root, names):
    """统计每个符号被多少个不同文件引用，以及总引用次数。"""
    files_using = defaultdict(set)
    total = Counter()
    if not names:
        return files_using, total
    pattern = re.compile(r"\b(" + "|".join(re.escape(n) for n in names) + r")\b")
    for src in list(walk(root, C_SRC)) + list(walk(root, C_HDR)):
        rel = os.path.relpath(src, root)
        text = read(src)
        # 粗略去掉注释，减少假阳性
        text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
        text = re.sub(r"//[^\n]*", " ", text)
        for m in pattern.finditer(text):
            n = m.group(1)
            files_using[n].add(rel)
            total[n] += 1
    return files_using, total


def git_hotspots(repo, since):
    args = ["git", "-C", repo, "log", "--pretty=format:", "--name-only", "--no-merges"]
    if since:
        args.append(f"--since={since}")
    try:
        out = subprocess.run(args, capture_output=True, text=True,
                             errors="replace", check=True).stdout
    except Exception:
        return Counter()
    return Counter(l.strip() for l in out.splitlines() if l.strip())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", "--root", dest="old", required=True,
                    help="C/C++ 旧实现源码根目录")
    ap.add_argument("--repo", help="git 仓库路径（给出则计算核心×热点交集）")
    ap.add_argument("--since", help="git 统计起始日期")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--json")
    args = ap.parse_args()

    funcs, structs, decl_file = collect_symbols(args.old)
    if not funcs and not structs:
        raise SystemExit("没有在头文件里找到任何声明，检查 --root 是否指向源码目录")

    f_files, f_total = count_refs(args.old, funcs)
    s_files, s_total = count_refs(args.old, structs)

    def rank(names, files_using, total):
        rows = [(n, len(files_using.get(n, ())), total.get(n, 0),
                 decl_file.get(n, "?")) for n in names]
        return sorted(rows, key=lambda r: (-r[1], -r[2]))

    f_rank = rank(funcs, f_files, f_total)
    s_rank = rank(structs, s_files, s_total)

    print(f"旧实现源码根目录: {args.old}")
    print(f"头文件声明: 函数 {len(funcs)} 个, 结构体 {len(structs)} 个\n")

    print("=" * 72)
    print("一、数据结构扇入排序 —— 先看这个")
    print("   系统的核心通常是那几个到处传递的 struct，而不是某个函数")
    print("=" * 72)
    print(f"{'结构体':<28}{'涉及文件数':>10}{'引用次数':>10}  声明于")
    for n, nf, tot, d in s_rank[:args.top]:
        print(f"{n:<28}{nf:>10}{tot:>10}  {d}")

    print()
    print("=" * 72)
    print("二、函数扇入排序 —— 接口契约的核心")
    print("=" * 72)
    print(f"{'函数':<28}{'涉及文件数':>10}{'引用次数':>10}  声明于")
    for n, nf, tot, d in f_rank[:args.top]:
        print(f"{n:<28}{nf:>10}{tot:>10}  {d}")

    inter = []
    if args.repo:
        hot = git_hotspots(args.repo, args.since)
        if hot:
            print()
            print("=" * 72)
            print("三、核心 × 热点交集 —— A 级素材的高发区")
            print("   既是核心（高扇入）又难维护（改动频繁），说明这里的复杂度")
            print("   一直没被结构化解决。优先深读。")
            print("=" * 72)
            for n, nf, tot, d in (s_rank + f_rank):
                # 用"声明所在头文件"和"同名 .c"近似定位该符号的实现文件
                cands = [p for p in hot
                         if os.path.basename(p).split(".")[0] == os.path.basename(d).split(".")[0]]
                churn = sum(hot[p] for p in cands)
                if nf >= 2 and churn > 0:
                    inter.append((n, nf, churn, d))
            inter.sort(key=lambda r: -(r[1] * r[2]))
            print(f"{'符号':<28}{'扇入文件':>10}{'改动次数':>10}  声明于")
            for n, nf, churn, d in inter[:args.top]:
                print(f"{n:<28}{nf:>10}{churn:>10}  {d}")

    print("""
怎么用这份结果（配合 references/at-scale.md）：
  1. 数据结构扇入前 3-5 名，就是主干数据流上的核心载体。**先追它们**：
     谁构造、谁修改、谁消费、生命周期由谁负责——这条链在新实现里变成什么了？
  2. 函数扇入前几名是接口契约的核心，看它们的签名如何表达所有权与错误。
  3. "核心 × 热点"里的符号优先深读，这里最可能出 A 级素材。
  4. 本脚本靠标识符匹配，同名局部变量、宏、字符串都会造成假阳性；有 GitNexus 等
     图谱工具时以图谱结果为准，本脚本仅作退路。
  5. 排完序后，在材料的"分析局限"里写明抽样口径：读了哪些、覆盖了多大比例。
""")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fp:
            json.dump({
                "old": args.old,
                "structs": [{"name": n, "files": nf, "refs": t, "decl": d}
                            for n, nf, t, d in s_rank],
                "functions": [{"name": n, "files": nf, "refs": t, "decl": d}
                              for n, nf, t, d in f_rank],
                "core_x_hot": [{"name": n, "files": nf, "churn": c, "decl": d}
                               for n, nf, c, d in inter],
                "caveat": "标识符匹配，存在假阳性；有图谱工具时以图谱为准。",
            }, fp, ensure_ascii=False, indent=2)
        print(f"完整结果已写入 {args.json}")


if __name__ == "__main__":
    main()
