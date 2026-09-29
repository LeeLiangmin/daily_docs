#!/usr/bin/env bash
# 迁移复盘：本地数据统计脚本
#
# 只做机械统计，不上传任何数据。在迁移项目的 git 仓库根目录运行。
#
# 配置（环境变量）：
#   TOOL_AUTHOR   工具提交的作者名正则（git log --author 用），如 'migrate-bot'
#                 留空则所有提交都算作人工提交
#   SRC_DIR       原始 C/C++ 代码目录（相对仓库根），如 'c_src'
#   DST_DIR       迁移后 Rust 代码目录（相对仓库根），如 'src'
#   TOOL_REV      工具原始输出所在的提交（用于量化人工改动），留空则跳过
#   FINAL_REV     最终版本，默认 HEAD
#   OUT_DIR       输出目录，默认 ./retro-stats
#
# 用法示例：
#   TOOL_AUTHOR='migrate-bot' SRC_DIR=c_src DST_DIR=src TOOL_REV=abc123 \
#     bash collect-stats.sh
#
# 输出：
#   timeline.csv      日期, 工具提交数, 工具增行, 工具删行, 人工提交数, 人工增行, 人工删行
#   src_modules.csv   模块, 文件数, 行数        （SRC_DIR 下一级目录为模块）
#   dst_modules.csv   模块, 文件数, 行数, unsafe 次数, 工具输出后人工改动行数
#   unsafe.txt        各文件 unsafe 出现次数排行
#   summary.txt       汇总

set -euo pipefail

TOOL_AUTHOR="${TOOL_AUTHOR:-}"
SRC_DIR="${SRC_DIR:-}"
DST_DIR="${DST_DIR:-src}"
TOOL_REV="${TOOL_REV:-}"
FINAL_REV="${FINAL_REV:-HEAD}"
OUT_DIR="${OUT_DIR:-retro-stats}"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "请在 git 仓库内运行" >&2; exit 1; }
mkdir -p "$OUT_DIR"

# ---------- 1. 时间线 ----------
tool_hashes="$OUT_DIR/.tool_hashes"
: > "$tool_hashes"
if [ -n "$TOOL_AUTHOR" ]; then
  git log --author="$TOOL_AUTHOR" --pretty=tformat:'%H' "$FINAL_REV" > "$tool_hashes" || true
fi

git log --date=short --pretty=format:'@%H %ad' --numstat "$FINAL_REV" \
| awk -v hf="$tool_hashes" '
  BEGIN { while ((getline h < hf) > 0) tool[h]=1 }
  /^@/ { split(substr($0,2), p, " "); h=p[1]; d=p[2]; t=(h in tool);
         if (t) tc[d]++; else hc[d]++; days[d]=1; next }
  NF==3 && $1 ~ /^[0-9]+$/ {
         if (t) { ta[d]+=$1; tr[d]+=$2 } else { ha[d]+=$1; hr[d]+=$2 } }
  END {
    print "date,tool_commits,tool_added,tool_deleted,human_commits,human_added,human_deleted"
    for (d in days) printf "%s,%d,%d,%d,%d,%d,%d\n", d, tc[d], ta[d], tr[d], hc[d], ha[d], hr[d]
  }' \
| { IFS= read -r header; echo "$header"; sort; } > "$OUT_DIR/timeline.csv"

# ---------- 2. 模块统计 ----------
count_modules() {  # $1=目录 $2=find 的 name 条件
  local dir="$1"; shift
  [ -d "$dir" ] || return 0
  find "$dir" -type f \( "$@" \) -print0 \
  | xargs -0 -r wc -l 2>/dev/null \
  | awk -v root="$dir/" '
      $2 != "total" {
        p=$2; sub("^" root, "", p)
        n=split(p, a, "/"); m=(n>1)?a[1]:"(root)"
        f[m]++; l[m]+=$1 }
      END { for (m in f) printf "%s,%d,%d\n", m, f[m], l[m] }' | sort
}

if [ -n "$SRC_DIR" ]; then
  { echo "module,files,loc"
    count_modules "$SRC_DIR" -name '*.c' -o -name '*.h' -o -name '*.cc' -o -name '*.cpp' -o -name '*.cxx' -o -name '*.hpp' -o -name '*.hh'
  } > "$OUT_DIR/src_modules.csv"
fi

# unsafe 次数（按模块）
unsafe_by_module="$OUT_DIR/.unsafe_by_module"
: > "$unsafe_by_module"
if [ -d "$DST_DIR" ]; then
  grep -rnw 'unsafe' --include='*.rs' "$DST_DIR" 2>/dev/null \
    | cut -d: -f1 | sort | uniq -c | sort -rn > "$OUT_DIR/unsafe.txt" || true
  awk -v root="$DST_DIR/" '{
      p=$2; sub("^" root, "", p); n=split(p, a, "/"); m=(n>1)?a[1]:"(root)"; u[m]+=$1 }
      END { for (m in u) print m, u[m] }' "$OUT_DIR/unsafe.txt" > "$unsafe_by_module"
fi

# 工具输出之后的人工改动行数（按模块）
changed_by_module="$OUT_DIR/.changed_by_module"
: > "$changed_by_module"
if [ -n "$TOOL_REV" ]; then
  git diff --numstat "$TOOL_REV" "$FINAL_REV" -- "$DST_DIR" \
  | awk -v root="$DST_DIR/" '$1 ~ /^[0-9]+$/ {
      p=$3; sub("^" root, "", p); n=split(p, a, "/"); m=(n>1)?a[1]:"(root)"; c[m]+=$1+$2 }
      END { for (m in c) print m, c[m] }' > "$changed_by_module"
fi

{ echo "module,files,loc,unsafe_count,changed_since_tool"
  count_modules "$DST_DIR" -name '*.rs' \
  | awk -F, -v uf="$unsafe_by_module" -v cf="$changed_by_module" '
      BEGIN { while ((getline l < uf) > 0) { split(l,a," "); u[a[1]]=a[2] }
              while ((getline l < cf) > 0) { split(l,a," "); c[a[1]]=a[2] } }
      { printf "%s,%s,%s,%d,%d\n", $1, $2, $3, u[$1], c[$1] }'
} > "$OUT_DIR/dst_modules.csv"

# ---------- 3. 汇总 ----------
{
  echo "生成时间: $(date '+%Y-%m-%d %H:%M')"
  echo "统计范围: $FINAL_REV"
  echo "总提交数: $(git rev-list --count "$FINAL_REV")"
  echo "工具提交数: $(wc -l < "$tool_hashes" | tr -d ' ')$( [ -s "$tool_hashes" ] || echo ' (未设置 TOOL_AUTHOR 或无匹配)')"
  echo "首次提交: $(git log --reverse --date=short --pretty=format:'%ad' "$FINAL_REV" | head -1)"
  echo "最后提交: $(git log -1 --date=short --pretty=format:'%ad' "$FINAL_REV")"
  if [ -n "$SRC_DIR" ] && [ -f "$OUT_DIR/src_modules.csv" ]; then
    echo "源代码行数 ($SRC_DIR): $(awk -F, 'NR>1{s+=$3} END{print s+0}' "$OUT_DIR/src_modules.csv")"
  fi
  echo "目标代码行数 ($DST_DIR): $(awk -F, 'NR>1{s+=$3} END{print s+0}' "$OUT_DIR/dst_modules.csv")"
  echo "unsafe 总次数: $(awk -F, 'NR>1{s+=$4} END{print s+0}' "$OUT_DIR/dst_modules.csv")"
  if [ -n "$TOOL_REV" ]; then
    echo "工具输出后人工改动行数: $(awk -F, 'NR>1{s+=$5} END{print s+0}' "$OUT_DIR/dst_modules.csv") (增+删, 相对 $TOOL_REV)"
  fi
} > "$OUT_DIR/summary.txt"

rm -f "$tool_hashes" "$unsafe_by_module" "$changed_by_module"
cat "$OUT_DIR/summary.txt"
echo
echo "明细已写入 $OUT_DIR/"
