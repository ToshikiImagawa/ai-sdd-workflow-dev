#!/usr/bin/env bash
# `claude plugin eval` のラッパー。plugins/sdd-workflow/evals/ のケース（prose 実装 spec の決定表 1 行 = 1 ケース）を
# 実行し、結果 JSON を要約する。モデル呼び出しに課金が発生するため CI では実行せず、手元で任意に実行する。
#
# 使い方: bash scripts/skill-evals.sh [--case <glob>] [--tag <tag>] [その他 claude plugin eval の引数]
# 環境変数:
#   SKILL_EVALS_RUNS          ケースあたりの実行回数（既定 1。既定の 3 回はコストが 3 倍になる）
#   SKILL_EVALS_MAX_COST_USD  コスト上限 USD（既定 5。超過で claude が exit 2）
#   SKILL_EVALS_CONCURRENCY   同時実行数 1-8（既定 4）
#   SKILL_EVALS_OUT           結果 JSON の出力先（既定 plugins/sdd-workflow/evals/results/skill-evals.json。results/ は .gitignore 済み）
#
# 終了コード は claude plugin eval のまま: 0 全ケースが閾値（既定 1.0）以上 / 1 閾値未満・読込エラー / 2 コスト上限。
# scaffold_script（各ケースの fixture）は本リポジトリが作成したものなので --scaffold で有効化する。
# Bash / Write / Edit はスキルが使う（check-spec のヘルパー、generate-prd --amend の編集）ため操作者権限で許可する。
# 認証は実行者の claude ログイン（または API キー）を claude が読む。
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v claude >/dev/null 2>&1; then
  echo "skill-evals: claude CLI が見つかりません（https://claude.ai/install.sh）" >&2
  exit 1
fi

runs="${SKILL_EVALS_RUNS:-1}"
max_cost="${SKILL_EVALS_MAX_COST_USD:-5}"
concurrency="${SKILL_EVALS_CONCURRENCY:-4}"
out="${SKILL_EVALS_OUT:-plugins/sdd-workflow/evals/results/skill-evals.json}"
mkdir -p "$(dirname "$out")"

status=0
claude plugin eval ./plugins/sdd-workflow \
  --trust-plugin --scaffold \
  --allow-tools Bash Write Edit \
  --runs "$runs" --concurrency "$concurrency" \
  --ablation none --no-publish \
  --max-cost-usd "$max_cost" \
  --json "$out" \
  "$@" || status=$?

if [ -f "$out" ]; then
  python3 - "$out" <<'EOF' >&2
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
agg = d.get("aggregates", {})
print(f"skill-evals: passed {agg.get('casesPassed', '?')}/{agg.get('casesTotal', '?')} cases, "
      f"cost ${float(d.get('costUsd', 0)):.2f}, {d.get('durationSeconds', '?')}s, partial={d.get('partial')}")
for c in d.get("cases", []):
    for r in c.get("arms", {}).get("with", []):
        if r.get("passed"):
            continue
        failed = [g["name"] for g in r.get("graders", []) if not g.get("passed")]
        print(f"  FAIL {c['name']}: {', '.join(failed) or r.get('error') or 'no grader result'}")
EOF
else
  echo "skill-evals: 結果 JSON が書かれませんでした（${out}）" >&2
fi

exit "$status"
