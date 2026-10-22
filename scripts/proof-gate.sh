#!/usr/bin/env bash
# Bend 証明ゲートを全法則ディレクトリに実行し、PASS 以外を失敗にする CI 用ラッパー。
#
# run-verification.py proof は結果を JSON で返し終了コードは常に 0 のため、
# ここで status を読んで PASS -> exit 0、それ以外（FAIL / SKIPPED / TOOL_NOT_FOUND）-> exit 1 にする。
# bend 入りの CI で SKIPPED が出るのは承認行の失効か laws: のずれなので、見えるように失敗扱いにする。
# 追加引数はそのまま run-verification.py proof に渡す（例: --laws-dir .sdd/laws/<feature>）。
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v bend >/dev/null 2>&1; then
  echo "proof-gate: 'bend' が PATH にありません。CI の proof ジョブはインストール済みを前提とします。" >&2
  echo "proof-gate: 手元では https://bend-lang.com/install.sh で導入してください。" >&2
  exit 1
fi

out="$(python3 plugins/sdd-workflow/skills/run-checklist/scripts/run-verification.py proof "$@")"
printf '%s\n' "$out"

status="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status", ""))')"
if [ "$status" = "PASS" ]; then
  exit 0
fi

reason="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("reason", ""))')"
echo "proof-gate: status=${status:-unknown} ${reason}" >&2
exit 1
