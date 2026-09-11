#!/usr/bin/env bash
# skill-creator プラグインのインストールパス（skills/skill-creator ディレクトリ）を検索して1行で標準出力する。
# キャッシュディレクトリ名にバージョンハッシュが含まれ更新のたびに変わるため、固定パスに依存せず毎回検索する。
set -uo pipefail

CANDIDATES=$(find "$HOME/.claude/plugins/cache" -maxdepth 5 -type d -path "*/skill-creator/*/skills/skill-creator" 2>/dev/null)
# find がキャッシュディレクトリ自体の不在で非ゼロ終了しても($HOME/.claude/plugins/cache が
# 一度もプラグインをインストールしていない環境等)、pipefail によりここで異常終了させず
# 空文字列として下の友好的なエラーメッセージへ進む(set -e は使わない)。

if [ -z "$CANDIDATES" ]; then
  echo "ERROR: skill-creator プラグインが見つかりません。'/plugin install skill-creator' でインストールしてください。" >&2
  exit 1
fi

# 複数バージョンが残っている場合は最新を使う。ディレクトリ名はバージョン番号ではなく
# インストール時に振られるハッシュなので、文字列ソート(lexical)には順序として意味がない
# (例: ハッシュの先頭文字によっては新しい方が辞書順で前に来る)。mtime が最も新しいものを
# 使う(ls -t は macOS/Linux 双方の ls で対応、xargs で候補パス全体を一度に渡す)。
echo "$CANDIDATES" | xargs ls -dt | head -1
