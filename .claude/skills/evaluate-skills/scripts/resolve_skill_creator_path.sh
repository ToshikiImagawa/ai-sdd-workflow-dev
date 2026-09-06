#!/usr/bin/env bash
# skill-creator プラグインのインストールパス（skills/skill-creator ディレクトリ）を検索して1行で標準出力する。
# キャッシュディレクトリ名にバージョンハッシュが含まれ更新のたびに変わるため、固定パスに依存せず毎回検索する。
set -euo pipefail

CANDIDATES=$(find "$HOME/.claude/plugins/cache" -maxdepth 5 -type d -path "*/skill-creator/*/skills/skill-creator" 2>/dev/null | sort)

if [ -z "$CANDIDATES" ]; then
  echo "ERROR: skill-creator プラグインが見つかりません。'/plugin install skill-creator' でインストールしてください。" >&2
  exit 1
fi

# 複数バージョンが残っている場合は最新（ソート後の末尾）を使う
echo "$CANDIDATES" | tail -1
