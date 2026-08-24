#!/usr/bin/env python3
"""维度 2（变更成本与可维护性）取证：从 git 历史里挖"改漏了"的证据。

三种分析，都是维度 2 的通用取证手段：

  1. 补漏对（patch-pair）：一个"新增/feat"型 commit 之后不久，出现提到同一关键词的
     "漏/遗漏/补上"型 commit。这是"扩展点分散、编译器覆盖不到"的直接证据，
     也是材料里最有说服力的一类——它有复发率。
  2. 变更热点：改动最频繁的文件，深读时优先看，也是"这块反复出问题"的量化依据。
  3. 变更耦合：总是一起被修改的文件对，反映隐式耦合——改 A 必须记得改 B，
     而这件事没有任何机制保证。

输出是线索，必须人工复核后才能写进材料。

用法:
    python find_change_cost.py --repo /path/to/old-repo
    python find_change_cost.py --repo . --since 2019-01-01 --window 10
    python find_change_cost.py --repo . --json out.json
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict

# "新增了一个东西"
FEAT = re.compile(
    r"\bfeat\b|\badd\b|\bnew\b|\bsupport\b|\bintroduce\b|新增|增加|添加|支持|引入",
    re.IGNORECASE,
)
# "刚才那个东西没改全"
MISS = re.compile(
    r"\bmissing\b|\bmissed\b|\bforgot\b|\bomit|\bunhandled\b|\balso (update|handle)\b|"
    r"漏|遗漏|补上|补全|补充处理|没有处理|未处理|忘记",
    re.IGNORECASE,
)
FIXY = re.compile(r"\bfix\b|\bbug\b|修复|修正|解决", re.IGNORECASE)

# 从 commit message 里抽可比对的标识符：大写常量、CamelCase、snake_case、中文引号内的词
TOKEN = re.compile(r"[A-Z][A-Z0-9_]{2,}|[A-Za-z_][A-Za-z0-9_]{3,}")
STOP = {
    "fix", "feat", "add", "new", "support", "missing", "missed", "forgot", "update",
    "handle", "case", "switch", "branch", "code", "test", "tests", "when", "with",
    "from", "into", "that", "this", "also", "make", "used", "using", "type", "value",
}

SEP = "\x1e"
FMT = SEP.join(["%H", "%ad", "%s", "%b"]) + "\x1d"


def run_git(repo, args):
    try:
        r = subprocess.run(["git", "-C", repo] + args,
                           capture_output=True, text=True, errors="replace", check=True)
        return r.stdout
    except FileNotFoundError:
        sys.exit("找不到 git 命令")
    except subprocess.CalledProcessError as e:
        sys.exit(f"git 执行失败: {e.stderr.strip()[:400]}")


def load(repo, since, until, paths):
    args = ["log", "--reverse", f"--pretty=format:{FMT}", "--date=short", "--no-merges"]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    if paths:
        args += ["--"] + paths
    out, commits = run_git(repo, args), []
    for rec in out.split("\x1d"):
        if not rec.strip():
            continue
        p = rec.strip("\n").split(SEP)
        if len(p) < 3:
            continue
        commits.append({"hash": p[0], "date": p[1], "subject": p[2],
                        "body": p[3] if len(p) > 3 else ""})
    return commits


def tokens(text):
    return {t for t in TOKEN.findall(text) if t.lower() not in STOP}


def find_pairs(commits, window):
    """在 feat 之后 window 个 commit 内，找提到同一标识符的 miss 型 commit。"""
    pairs = []
    for i, c in enumerate(commits):
        text = c["subject"] + "\n" + c["body"]
        if not FEAT.search(text):
            continue
        ftok = tokens(text)
        if not ftok:
            continue
        for j in range(i + 1, min(i + 1 + window, len(commits))):
            d = commits[j]
            dtext = d["subject"] + "\n" + d["body"]
            if not (MISS.search(dtext) or (FIXY.search(dtext) and MISS.search(dtext))):
                continue
            shared = ftok & tokens(dtext)
            if shared:
                pairs.append({"feat": c, "miss": d, "shared": sorted(shared),
                              "gap": j - i})
                break
    return pairs


def hotspots(repo, since, until, paths, top):
    args = ["log", "--pretty=format:%H", "--numstat", "--no-merges"]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    if paths:
        args += ["--"] + paths
    out = run_git(repo, args)
    freq, per_commit, cur = Counter(), [], []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r"[0-9a-f]{40}", line):
            if cur:
                per_commit.append(cur)
            cur = []
            continue
        parts = line.split("\t")
        if len(parts) == 3:
            f = parts[2]
            freq[f] += 1
            cur.append(f)
    if cur:
        per_commit.append(cur)

    couple = Counter()
    for files in per_commit:
        u = sorted(set(files))
        if 1 < len(u) <= 12:  # 超大 commit 噪音太多，跳过
            for a in range(len(u)):
                for b in range(a + 1, len(u)):
                    couple[(u[a], u[b])] += 1
    return freq.most_common(top), couple.most_common(top)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="旧 C/C++ 仓库路径")
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--path", nargs="*", default=None)
    ap.add_argument("--window", type=int, default=8,
                    help="feat 之后多少个 commit 内算作补漏，默认 8")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--json")
    args = ap.parse_args()

    commits = load(args.repo, args.since, args.until, args.path)
    if not commits:
        sys.exit("没有取到任何 commit，检查路径 / 时间范围")

    pairs = find_pairs(commits, args.window)
    hot, couple = hotspots(args.repo, args.since, args.until, args.path, args.top)

    feat_total = sum(1 for c in commits
                     if FEAT.search(c["subject"] + "\n" + c["body"]))

    print(f"仓库: {args.repo}   commit 总数: {len(commits)}")
    print()
    print("=" * 70)
    print("一、补漏对（维度 2 的一等素材）")
    print("=" * 70)
    if not pairs:
        print("  未发现。可能是真的没有，也可能是 commit message 不规范；")
        print("  改用 --window 放大窗口，或人工翻 feat 型 commit 后面几条。")
    else:
        rate = len(pairs) / feat_total * 100 if feat_total else 0
        print(f"  新增型 commit {feat_total} 个，其中 {len(pairs)} 个后面跟着补漏"
              f"（{rate:.0f}%）")
        print(f"  —— 这个比例就是材料里的复发率，比任何描述性文字都有力\n")
        for p in pairs:
            print(f"  ● 关键词: {', '.join(p['shared'][:4])}   间隔 {p['gap']} 个 commit")
            print(f"      新增  {p['feat']['hash'][:9]}  {p['feat']['date']}  "
                  f"{p['feat']['subject'][:60]}")
            print(f"      补漏  {p['miss']['hash'][:9]}  {p['miss']['date']}  "
                  f"{p['miss']['subject'][:60]}")
    print()
    print("=" * 70)
    print("二、变更热点（深读优先级 + \"这块反复出问题\"的量化依据）")
    print("=" * 70)
    for f, n in hot:
        print(f"  {n:>4} 次   {f}")
    print()
    print("=" * 70)
    print("三、变更耦合（改 A 必须记得改 B，但没有机制保证）")
    print("=" * 70)
    if not couple:
        print("  未发现明显的成对修改")
    for (a, b), n in couple:
        print(f"  {n:>4} 次   {a}  ⇄  {b}")

    print("""
下一步（不要跳过）：
  1. 逐个打开补漏对的 diff（git show），确认它确实是"新增东西时漏改了别处"，
     而不是碰巧共用了一个词。假阳性在这里很常见。
  2. 复核通过的补漏对，去新实现里找对应位置：同样的扩展现在靠什么保证改全？
     枚举穷尽匹配、trait 的必填方法、还是仍然靠人？——这决定归因等级。
  3. 变更耦合排前几的文件对，去新实现里看这层耦合还在不在。若已被类型或模块
     边界消化掉，是维度 2 的好素材。
  4. 补漏率（第一节那个百分比）写进材料时，说明统计口径与窗口大小。
""")
    print("=" * 68)
    print("  ⚠ 以上为启发式匹配的未复核结果，禁止直接写入材料。")
    print("=" * 68)

    if args.json:
        payload = {
            "repo": args.repo,
            "commits": len(commits),
            "feat_commits": feat_total,
            "patch_pairs": [
                {"shared": p["shared"], "gap": p["gap"],
                 "feat": {k: p["feat"][k] for k in ("hash", "date", "subject")},
                 "miss": {k: p["miss"][k] for k in ("hash", "date", "subject")}}
                for p in pairs
            ],
            "hotspots": hot,
            "coupling": [{"a": a, "b": b, "count": n} for (a, b), n in couple],
            "caveat": "启发式匹配，存在假阳性与漏检，必须人工复核后使用。",
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"完整结果已写入 {args.json}")


if __name__ == "__main__":
    main()
