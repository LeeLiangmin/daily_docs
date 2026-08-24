#!/usr/bin/env python3
"""对比 C/C++ 旧实现与 Rust 新实现的客观计数指标。

产出的是**可复现的计数**，用来支撑材料里的定量说法。
每个指标都要在材料里写明统计口径；计数本身不构成结论。

用法:
    python code_metrics.py --old /path/to/c-repo --new /path/to/rust-repo
    python code_metrics.py --old src/ --new rust/src/ --json metrics.json
"""

import argparse
import json
import os
import re
from collections import Counter

C_EXT = {".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx", ".inl"}
RUST_EXT = {".rs"}
SKIP_DIRS = {".git", "target", "build", "out", "node_modules", "third_party",
             "vendor", "external", ".cache", "cmake-build-debug"}

# 旧实现里的"危险模式/人工约定"计数
C_PATTERNS = {
    "手动内存分配 malloc/calloc/realloc": r"\b(malloc|calloc|realloc)\s*\(",
    "手动释放 free/delete": r"\b(free|delete)\s*[\(\[]",
    "裸 new": r"\bnew\s+[A-Za-z_]",
    "goto 清理路径": r"\bgoto\s+\w*(cleanup|err|fail|out|done)\w*",
    "goto（全部）": r"\bgoto\s+\w+",
    "空指针检查": r"(if\s*\(\s*!?\s*\w+\s*(==|!=)\s*(NULL|nullptr|0)\s*\))|(if\s*\(\s*!\s*\w+\s*\))",
    "void* 使用": r"\bvoid\s*\*",
    "C 风格强制转换": r"\(\s*(struct\s+)?\w+\s*\*+\s*\)\s*\w",
    "reinterpret_cast": r"\breinterpret_cast\s*<",
    "不安全字符串函数": r"\b(strcpy|strcat|sprintf|gets|memcpy|strncpy|alloca)\s*\(",
    "互斥锁操作": r"\b(pthread_mutex_(lock|unlock)|EnterCriticalSection|std::lock_guard)",
    "宏定义": r"^\s*#\s*define\s+\w+",
    "宏泛型展开（DEFINE_/DECLARE_ 调用）": r"^\s*(DEFINE|DECLARE|IMPL)_[A-Z_]+\s*\(",
    "TODO/FIXME/HACK/XXX": r"\b(TODO|FIXME|HACK|XXX)\b",
    "约定型注释（必须/不要/仅限）": r"(//|/\*|\*)\s*.*(must |should |do not |don't |caller |注意|必须|不要|仅|只能|需先|调用方)",
    "errno 使用": r"\berrno\b",
    "疑似丢弃返回值的调用语句": r"^\s*(?!(if|for|while|switch|return|else|do)\b)"
                              r"[A-Za-z_][\w:]*\s*\([^;]*\)\s*;",
    "返回 -1 风格错误": r"return\s+-1\s*;",
}

RUST_PATTERNS = {
    "unsafe 块/函数": r"\bunsafe\b",
    "unwrap()": r"\.unwrap\s*\(\s*\)",
    "expect()": r"\.expect\s*\(",
    "panic!": r"\bpanic!\s*\(",
    "clone()": r"\.clone\s*\(\s*\)",
    "Result 出现": r"\bResult\s*<",
    "Option 出现": r"\bOption\s*<",
    "? 运算符（近似）": r"[\w\)\]]\?\s*[;,\)\.\n]",
    "自定义错误类型 thiserror/anyhow": r"\b(thiserror|anyhow)\b",
    "match 表达式": r"\bmatch\s+.*\{",
    "trait 定义": r"^\s*(pub\s+)?trait\s+\w+",
    "Mutex/RwLock": r"\b(Mutex|RwLock)\s*<",
    "Arc/Rc": r"\b(Arc|Rc)\s*<",
    "#[test]": r"#\[\s*(test|tokio::test)\s*\]",
    "文档注释 ///": r"^\s*///",
    "TODO/FIXME/HACK/XXX": r"\b(TODO|FIXME|HACK|XXX)\b",
    "裸指针": r"\*\s*(const|mut)\s+\w",
    "extern \"C\" / FFI": r"extern\s+\"C\"",
    "枚举定义": r"^\s*(pub\s+)?enum\s+\w+",
    "newtype 模式（元组结构体）": r"^\s*(pub\s+)?struct\s+\w+\s*\([^)]*\)\s*;",
    "matches! 宏": r"\bmatches!\s*\(",
    "#[must_use]": r"#\[\s*must_use",
    "#[deny(...)] / #![deny(...)]": r"#!?\[\s*deny",
}


def walk(root, exts):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                       and not d.startswith(".")]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in exts:
                yield os.path.join(dirpath, fn)


def count_lines(path):
    """返回 (总行数, 非空非纯注释行数)。粗略口径，够用即可。"""
    total = code = 0
    in_block = False
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                total += 1
                s = line.strip()
                if in_block:
                    if "*/" in s:
                        in_block = False
                    continue
                if not s:
                    continue
                if s.startswith("//"):
                    continue
                if s.startswith("/*"):
                    if "*/" not in s:
                        in_block = True
                    continue
                code += 1
    except OSError:
        pass
    return total, code


def scan(root, exts, patterns, label):
    compiled = {k: re.compile(v, re.MULTILINE) for k, v in patterns.items()}
    counts = Counter()
    files = 0
    total_lines = code_lines = 0
    test_files = 0
    for path in walk(root, exts):
        files += 1
        t, c = count_lines(path)
        total_lines += t
        code_lines += c
        low = os.path.basename(path).lower()
        if "test" in low or f"{os.sep}test" in path.lower():
            test_files += 1
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            continue
        for name, rx in compiled.items():
            n = len(rx.findall(content))
            if n:
                counts[name] += n
    return {
        "label": label,
        "root": root,
        "files": files,
        "test_files": test_files,
        "total_lines": total_lines,
        "code_lines": code_lines,
        "patterns": dict(counts),
    }


def per_kloc(n, code_lines):
    return round(n / code_lines * 1000, 2) if code_lines else 0.0


def report(res):
    print(f"\n=== {res['label']} ===")
    print(f"路径: {res['root']}")
    print(f"文件数: {res['files']}（其中疑似测试文件 {res['test_files']}）")
    print(f"总行数: {res['total_lines']}   非空非注释行: {res['code_lines']}")
    if not res["patterns"]:
        print("未匹配到任何模式")
        return
    print(f"\n{'模式':<40}{'次数':>8}{'每千行':>10}")
    print("-" * 60)
    for name, n in sorted(res["patterns"].items(), key=lambda x: -x[1]):
        print(f"{name:<40}{n:>8}{per_kloc(n, res['code_lines']):>10}")


BUILD_FILES = {"Makefile", "makefile", "GNUmakefile", "CMakeLists.txt",
               "configure.ac", "Makefile.am", "meson.build"}
BUILD_PATTERNS = {
    "平台/条件分支": r"^\s*(ifeq|ifneq|ifdef|ifndef|if\s*\(|elseif|else\s+if)\b",
    "平台判断关键字": r"\b(WIN32|_WIN32|MSVC|APPLE|Darwin|Linux|UNIX|MINGW|ANDROID)\b",
    "手写编译/链接选项": r"^\s*(CFLAGS|LDFLAGS|CXXFLAGS|LIBS)\s*[+:]?=",
}


def scan_build(root, label):
    """维度 5：构建系统的复杂度计数。"""
    compiled = {k: re.compile(v, re.MULTILINE) for k, v in BUILD_PATTERNS.items()}
    counts, files, lines = Counter(), [], 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if fn in BUILD_FILES or fn.endswith(".cmake") or fn in ("Cargo.toml", "build.rs"):
                path = os.path.join(dirpath, fn)
                files.append(os.path.relpath(path, root))
                try:
                    content = open(path, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                lines += content.count("\n") + 1
                for name, rx in compiled.items():
                    n = len(rx.findall(content))
                    if n:
                        counts[name] += n
    return {"label": label, "files": files, "lines": lines, "counts": dict(counts)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", required=True, help="C/C++ 实现路径")
    ap.add_argument("--new", required=True, help="Rust 实现路径")
    ap.add_argument("--json", help="把结果写到 JSON 文件")
    args = ap.parse_args()

    old = scan(args.old, C_EXT, C_PATTERNS, "旧实现 (C/C++)")
    new = scan(args.new, RUST_EXT, RUST_PATTERNS, "新实现 (Rust)")
    old_b = scan_build(args.old, "旧实现构建")
    new_b = scan_build(args.new, "新实现构建")

    report(old)
    report(new)

    print("\n=== 维度 5：构建系统对比 ===")
    for b in (old_b, new_b):
        print(f"\n{b['label']}: {len(b['files'])} 个文件, {b['lines']} 行")
        print(f"  文件: {', '.join(b['files'][:6]) or '（无）'}")
        for k, v in sorted(b["counts"].items(), key=lambda x: -x[1]):
            print(f"  {k}: {v}")

    print("\n=== 值得关注的几个比值 ===")
    unsafe_n = new["patterns"].get("unsafe 块/函数", 0)
    print(f"新实现 unsafe 出现次数: {unsafe_n}"
          f"（每千行 {per_kloc(unsafe_n, new['code_lines'])}）")
    unwrap_n = (new["patterns"].get("unwrap()", 0)
                + new["patterns"].get("expect()", 0))
    print(f"新实现 unwrap/expect: {unwrap_n}"
          f"（每千行 {per_kloc(unwrap_n, new['code_lines'])}）")
    goto_n = old["patterns"].get("goto 清理路径", 0)
    print(f"旧实现 goto 清理路径: {goto_n}")
    print(f"规模: 旧 {old['code_lines']} 行 vs 新 {new['code_lines']} 行")

    print("""
解读提示（不要跳过）：
  * 行数变化本身不是价值，要能说清少掉的是哪一类代码（错误处理样板？内存管理？
    宏展开？）。说不清就不要把行数写进材料。
  * unsafe 和 unwrap/expect 的密度是**对自己的检查**：密度高说明部分编译期保证
    被绕过或换成了运行时 panic，相关的价值主张要相应降级。主动披露这两个数字会
    显著提升材料的可信度。
  * "约定型注释"的计数是找 references/comparison-patterns.md 模式 6 的入口——
    每一条这类注释都是一个靠人记住的不变量，逐条去新实现里看有没有被类型编码。
  * "疑似丢弃返回值的调用语句"是粗略启发式：匹配独立成句、返回值未被接收或判断的
    函数调用。void 函数会被误计入，必须抽样复核后再引用。
  * 正则匹配有假阳性（比如注释和字符串里的内容也会被计入），数字用于量级比较，
    引用时说明口径。

""" + "=" * 68 + """
  ⚠ 以上为正则计数的未复核结果，禁止直接写入材料。
  ⚠ 引用任何数字前，先抽样打开对应代码确认，并在材料中注明统计口径与复核比例。
""" + "=" * 68)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"old": old, "new": new, "old_build": old_b, "new_build": new_b,
                       "caveat": "正则计数，存在假阳性；用于量级比较，非精确统计。"},
                      f, ensure_ascii=False, indent=2)
        print(f"结果已写入 {args.json}")


if __name__ == "__main__":
    main()
