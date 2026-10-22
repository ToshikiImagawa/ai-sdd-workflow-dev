#!/usr/bin/env bash
# 差分テスト（tests/laws/test_*.py）の '# source:' 行を spec の節ハッシュと照合する CI 用ラッパー。
#
# 各テストファイル先頭の '# spec: <id>' から spec を特定し、
# draft_laws.py check --tests <file> --spec <spec> を実行する（laws-drafting_spec 3.1.3-9）。
# draft_laws.py check は結果を JSON で返し終了コードは常に 0 のため、ここで errors を読んで
# 1 件でもあれば exit 1 にする（test_source_missing / test_source_drift など）。
# spec を変えて節ハッシュがずれたら、該当テストの '# source:' を hash サブコマンドの値で更新する。
# bend は不要。
set -euo pipefail

cd "$(dirname "$0")/.."

tests_dir="${1:-tests/laws}"
checker="plugins/sdd-workflow/skills/draft-laws/scripts/draft_laws.py"

if [ ! -d "$tests_dir" ]; then
  echo "check-laws-tests: ${tests_dir} がありません" >&2
  exit 1
fi

failed=0
checked=0
for t in "$tests_dir"/test_*.py; do
  [ -f "$t" ] || continue
  spec_id="$(grep -m1 -E '^# spec:' "$t" | sed -E 's/^# spec:[[:space:]]*//; s/[[:space:]]*$//')"
  if [ -z "$spec_id" ]; then
    echo "check-laws-tests: ${t}: 先頭に '# spec: <id>' がありません" >&2
    failed=1
    continue
  fi
  spec="$(grep -rl -E "^id:[[:space:]]*\"${spec_id}\"" .sdd/specification --include='*.md' | head -1)"
  if [ -z "$spec" ]; then
    echo "check-laws-tests: ${t}: id '${spec_id}' の spec が .sdd/specification に見つかりません" >&2
    failed=1
    continue
  fi
  out="$(python3 "$checker" check --tests "$t" --spec "$spec")"
  errors="$(printf '%s' "$out" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("errors", 0))')"
  checked=$((checked + 1))
  if [ "$errors" != "0" ]; then
    echo "check-laws-tests: ${t} (spec: ${spec}): errors=${errors}" >&2
    printf '%s' "$out" | python3 -c 'import json,sys; [print("  -", f["code"], f["message"]) for f in json.load(sys.stdin)["findings"] if f["severity"] == "error"]' >&2
    failed=1
  else
    echo "check-laws-tests: ok ${t} (spec: ${spec})"
  fi
done

if [ "$checked" -eq 0 ] && [ "$failed" -eq 0 ]; then
  echo "check-laws-tests: ${tests_dir} に test_*.py がありません" >&2
  exit 1
fi
exit "$failed"
