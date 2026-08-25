#!/usr/bin/env python3
"""扫描旧 C/C++ 仓库的 git 历史，按缺陷类别归类修复型 commit。

输出是**线索而非结论**：关键词匹配一定有假阳性、也一定会漏。
使用者必须人工复核采样后，才能把数字写进文档，并注明统计口径。

用法:
    python mine_fix_commits.py --repo /path/to/old-repo
    python mine_fix_commits.py --repo . --since 2018-01-01 --json out.json
    python mine_fix_commits.py --repo . --category memory --show 20
"""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict

# 缺陷类别 -> (匹配模式, 是否属于 Rust 能结构性防止的类别)
# 模式同时匹配 commit message；--deep 模式下也匹配 diff 内容。
CATEGORIES = {
    "memory_uaf": (
        r"use[- ]?after[- ]?free|uaf|dangling|悬垂|野指针|释放后|已释放|脏数据",
        True,
    ),
    "memory_double_free": (r"double[- ]?free|重复释放|二次释放", True),
    "memory_leak": (r"\bleak|泄漏|泄露|memleak|forgot to free|漏.{0,4}释放", True),
    "memory_overflow": (
        r"buffer overflow|overrun|out[- ]of[- ]bounds|\boob\b|越界|溢出|off[- ]by[- ]one|"
        r"\b(strcpy|strcat|sprintf|memcpy|gets)\b|未限长|覆盖栈|畸形包|长度.{0,4}(校验|检查)",
        True,
    ),
    "null_deref": (
        r"null (pointer|deref|ptr)|nullptr|segfault|segv|空指针|null check|检查.{0,4}空",
        True,
    ),
    "uninitialized": (r"uninitialized|uninit|未初始化|garbage value", True),
    "concurrency_race": (
        r"data race|race condition|竞态|竞争|tsan|thread[- ]safe|线程安全",
        True,  # 数据竞争是 True；逻辑竞态需人工区分，复核时注意
    ),
    "concurrency_lock_misuse": (
        r"missing (un)?lock|forgot.{0,10}(un)?lock|忘记.{0,6}(加锁|解锁|unlock)|"
        r"未加锁|漏.{0,6}解锁|unlock[^，。；\n]{0,10}(遗漏|缺失)|锁未释放|忘记[^，。；\\n]{0,20}(加锁|解锁|lock|unlock)|(加锁|解锁)[^，。；\\n]{0,10}遗漏",
        True,  # 忘记加/解锁：Rust 的 MutexGuard 能结构性排除
    ),
    "concurrency_deadlock": (
        r"deadlock|死锁|lock (order|ordering)|加锁顺序|锁顺序|活锁|livelock",
        False,  # 死锁 Rust 不防，单独成类以免污染统计
    ),
    "error_handling": (
        r"unchecked (return|result)|ignore[d]? (the )?(return|error)|error path|"
        r"missing (error )?check|未检查|错误处理|返回值.{0,6}检查|goto (cleanup|err)",
        True,
    ),
    "resource_leak": (
        r"\bfd leak|file descriptor|忘记.{0,4}close|not closed|未关闭|handle leak",
        True,
    ),
    "type_confusion": (
        r"type confusion|wrong cast|bad cast|类型.{0,4}错|signed|unsigned|truncat|窄化|"
        r"传参.{0,4}[写弄反]|参数.{0,4}[写弄反]|传反|用错.{0,6}(参数|字段)|混用|当作[^，。；\\n]{0,10}类型|错误类型|强转|误当成",
        True,
    ),
    "state_machine": (
        r"missing case|unhandled (case|state|enum)|switch.{0,10}(default|case)|"
        r"[漏遗][^，。；\n]{0,24}(分支|case|switch|枚举|状态)|"
        r"(分支|case|switch)[^，。；\n]{0,16}[漏遗]|补[上全][^，。；\n]{0,20}(分支|case)|"
        r"状态[^，。；\n]{0,6}遗漏|缺[少失][^，。；\n]{0,16}(分支|case|处理|状态)|未处理[^，。；\n]{0,10}(状态|分支)",
        True,
    ),
    "logic_business": (
        r"logic (error|bug)|wrong (result|value|order)|逻辑|算错|业务|需求|配置|typo|拼写",
        False,  # Rust 无帮助，用于计算"不可归因"占比
    ),
}

FIX_HINT = re.compile(
    r"\bfix|\bbug\b|\bcrash|patch|repair|resolve|修复|修正|解决|问题|缺陷|异常",
    re.IGNORECASE,
)

SEP = "\x1e"  # record separator
FMT = SEP.join(["%H", "%an", "%ad", "%s", "%b"]) + "\x1d"


def run_git(repo, args):
    try:
        out = subprocess.run(
            ["git", "-C", repo] + args,
            capture_output=True, text=True, errors="replace", check=True,
        )
        return out.stdout
    except FileNotFoundError:
        sys.exit("找不到 git 命令")
    except subprocess.CalledProcessError as e:
        sys.exit(f"git 执行失败: {e.stderr.strip()[:400]}")


def load_commits(repo, since, until, path_filter):
    args = ["log", f"--pretty=format:{FMT}", "--date=short", "--no-merges"]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    if path_filter:
        args += ["--"] + path_filter
    raw = run_git(repo, args)
    commits = []
    for rec in raw.split("\x1d"):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        parts = rec.split(SEP)
        if len(parts) < 4:
            continue
        h, author, date, subject = parts[:4]
        body = parts[4] if len(parts) > 4 else ""
        commits.append(
            {"hash": h, "author": author, "date": date,
             "subject": subject, "body": body}
        )
    return commits


def classify(text):
    hits = []
    for name, (pattern, rust_relevant) in CATEGORIES.items():
        if re.search(pattern, text, re.IGNORECASE):
            hits.append((name, rust_relevant))
    return hits


def diff_stat(repo, h):
    out = run_git(repo, ["show", "--stat", "--oneline", "--no-color", h])
    lines = [l for l in out.splitlines() if l.strip()]
    return lines[-1] if lines else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="旧 C/C++ 仓库路径")
    ap.add_argument("--since", help="起始日期，如 2018-01-01")
    ap.add_argument("--until", help="截止日期")
    ap.add_argument("--path", nargs="*", default=None,
                    help="只统计这些路径，如 src/ lib/")
    ap.add_argument("--category", help="只显示某一类别的候选 commit")
    ap.add_argument("--top", "--show", dest="top", type=int, default=8,
                    help="每个类别展示的候选 commit 数量，默认 8")
    ap.add_argument("--all-commits", action="store_true",
                    help="不限于修复型 commit，扫描全部（噪音更大）")
    ap.add_argument("--json", help="把完整结果写到 JSON 文件")
    args = ap.parse_args()

    commits = load_commits(args.repo, args.since, args.until, args.path)
    if not commits:
        sys.exit("没有取到任何 commit，检查路径 / 时间范围 / 仓库是否有历史")

    buckets = defaultdict(list)
    fix_total = 0
    multi_hit = 0
    unclassified = []
    # 去重集合：一个 commit 只算一次，避免多类别命中导致的重复计数
    dedup_all, dedup_rust, dedup_not_rust = set(), set(), set()

    for c in commits:
        text = f"{c['subject']}\n{c['body']}"
        if not args.all_commits and not FIX_HINT.search(text):
            continue
        fix_total += 1
        hits = classify(text)
        if not hits:
            unclassified.append(c)
            continue
        if len(hits) > 1:
            multi_hit += 1
        dedup_all.add(c["hash"])
        # 只要命中任一 Rust 可防类别，该 commit 记为"可防"；否则记为"不可防"
        if any(rel for _, rel in hits):
            dedup_rust.add(c["hash"])
        else:
            dedup_not_rust.add(c["hash"])
        for name, _ in hits:
            buckets[name].append(c)

    rust_relevant_n = sum(
        len(v) for k, v in buckets.items() if CATEGORIES[k][1]
    )
    not_relevant_n = sum(
        len(v) for k, v in buckets.items() if not CATEGORIES[k][1]
    )

    print(f"仓库: {args.repo}")
    rng = f"{args.since or '起始'} ~ {args.until or '至今'}"
    print(f"时间范围: {rng}   路径过滤: {args.path or '全部'}")
    print(f"扫描 commit 总数: {len(commits)}")
    print(f"其中判定为修复型: {fix_total}")
    print(f"命中缺陷类别: {sum(len(v) for v in buckets.values())} 次"
          f"（{multi_hit} 个 commit 命中多个类别，存在重复计数）")
    unc_rate = len(unclassified) / fix_total * 100 if fix_total else 0
    print(f"未能归类的修复型 commit: {len(unclassified)}（{unc_rate:.0f}%）")
    print()
    print(f"{'类别':<24}{'数量':>6}  Rust 可结构性防止")
    print("-" * 72)
    for name, items in sorted(buckets.items(), key=lambda x: -len(x[1])):
        mark = "是" if CATEGORIES[name][1] else "否/需人工区分"
        print(f"{name:<24}{len(items):>6}  {mark}")
    print("-" * 72)
    print(f"含重复计数：Rust 相关类别命中 {rust_relevant_n} 次，不相关 {not_relevant_n} 次")
    print()
    total_d = len(dedup_all)
    pct = (len(dedup_rust) / total_d * 100) if total_d else 0
    print("【去重口径 —— 材料里应引用这一组数字】")
    print(f"  已归类的修复型 commit（去重）: {total_d}")
    print(f"  其中 Rust 可结构性排除: {len(dedup_rust)}  ({pct:.0f}%)")
    print(f"  Rust 无帮助（死锁/逻辑/配置等）: {len(dedup_not_rust)}")
    print()

    if unclassified and not args.category:
        print(f"\n### 未能归类（{len(unclassified)} 条，需人工过一遍）")
        print("  关键词法在 commit message 不规范时退化明显；这批里往往藏着真素材，")
        print("  尤其是变更成本类的证据（用 find_change_cost.py 专门挖）。")
        for c in unclassified[: args.top if args.top else 10]:
            print(f"  {c['hash'][:10]}  {c['date']}  {c['subject'][:80]}")

    show_cats = [args.category] if args.category else list(buckets.keys())
    for name in show_cats:
        items = buckets.get(name)
        if not items:
            continue
        print(f"\n### {name}  （候选，需人工复核）")
        for c in items[: args.top]:
            print(f"  {c['hash'][:10]}  {c['date']}  {c['subject'][:80]}")

    print("=" * 72)
    print("  ⚠ 以上为关键词匹配的未复核结果，禁止直接写入文档。")
    print("  ⚠ 必须先完成下面第 1-4 步的人工复核，并在材料中注明复核比例。")
    print("=" * 72)
    print("""
下一步（不要跳过）：
  1. 人工复核采样：对每个类别抽 5-10 条，用 `git show <hash>` 看 diff 实际改了什么，
     确认它真的属于这个类别。关键词匹配的假阳性率通常不低。
  2. concurrency_race 需人工区分：数据竞争属于 Rust 能防的，逻辑竞态（check-then-act）
     不属于。concurrency_deadlock 已单独成类且默认不计入"可防"，不要再手动加回去。
  2b. 注意跨类别误捕：形如"重试次数 off-by-one"会被 memory_overflow 的关键词捕获，
     但它是逻辑错误；复核时以 diff 实际改了什么为准，不看 commit message 措辞。
  3. 从 memory_* / concurrency_race / error_handling 里挑 2-3 条影响大、故事完整的，
     作为材料里的真实案例深挖。
  4. 去 Rust 实现里找到对应代码，确认它确实靠类型系统排除了该问题（而不是用了
     unsafe 或 unwrap），再定归因等级。
  5. 在材料里写明统计口径与人工复核比例。
""")

    if args.json:
        payload = {
            "repo": args.repo,
            "range": {"since": args.since, "until": args.until},
            "path_filter": args.path,
            "total_commits": len(commits),
            "fix_commits": fix_total,
            "multi_category_commits": multi_hit,
            "unclassified": [c["hash"] for c in unclassified],
            "categories": {
                name: {
                    "rust_preventable": CATEGORIES[name][1],
                    "count": len(items),
                    "commits": [
                        {k: c[k] for k in ("hash", "date", "subject")}
                        for c in items
                    ],
                }
                for name, items in buckets.items()
            },
            "caveat": "关键词匹配结果，存在假阳性与漏检，且单个 commit 可能命中多个类别；"
                      "必须人工复核后使用。",
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"完整结果已写入 {args.json}")


if __name__ == "__main__":
    main()
