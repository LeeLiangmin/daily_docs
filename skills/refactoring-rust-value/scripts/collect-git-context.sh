#!/usr/bin/env bash
set -euo pipefail

# Lightweight helper for migration discovery.
# Usage:
#   collect_git_context.sh <repo> <old_rev> <new_rev> [output_dir]

repo=${1:?repo path required}
old_rev=${2:?old revision required}
new_rev=${3:?new revision required}
out=${4:-migration-context}

mkdir -p "$out"

git -C "$repo" status --short > "$out/status.txt"
git -C "$repo" diff --stat "$old_rev" "$new_rev" > "$out/diff-stat.txt"
git -C "$repo" diff --name-status -M -C "$old_rev" "$new_rev" > "$out/name-status.txt"
git -C "$repo" log --oneline --decorate "$old_rev..$new_rev" > "$out/commits.txt"
git -C "$repo" diff --numstat "$old_rev" "$new_rev" > "$out/numstat.txt"

cat > "$out/README.txt" <<TXT
Generated migration context.

Files:
- diff-stat.txt: high-level change size
- name-status.txt: additions/deletions/renames/copies
- commits.txt: migration commit history
- numstat.txt: per-file line change counts

These are candidate-discovery inputs only. Final value claims must be verified against source code and related evidence.
TXT

echo "Wrote $out"
