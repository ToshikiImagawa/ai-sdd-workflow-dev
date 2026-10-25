#!/bin/bash
set -eu

# sdd-workflow プラグインの配布用 zip を作るスクリプト
# release.yml とローカルで同じものを使う
#
# 使い方: bash scripts/build-plugin-archive.sh <version> <out-dir>
#
# - カレントディレクトリが属する git リポジトリの plugins/sdd-workflow/ を固める
#   （PLUGIN_SRC_DIR で上書き可。過去タグを固めるときは、そのタグを checkout した
#   worktree の中からこのスクリプトを実行する）
# - zip のトップディレクトリは sdd-workflow/
# - evals/・__pycache__/・*.pyc・.DS_Store は含めない
# - シンボリックリンクは実体化する（Claude Code の zip 展開がリンクを保持する保証がないため）
# - 同じ入力からは同じ zip になるよう、ファイル順序（LC_ALL=C sort）・更新時刻（固定）・
#   タイムゾーン（UTC）を揃え、extra attributes を除去（zip -X）する
# - <out-dir>/sdd-workflow-<version>.zip と .zip.sha256 を出力し、sha256 を stdout に出す
#   （進捗・エラーは stderr）

PLUGIN_NAME=sdd-workflow

if [ $# -ne 2 ]; then
    echo "usage: $0 <version> <out-dir>" >&2
    exit 2
fi
VERSION=$1
OUT_DIR=$2

for cmd in zip unzip jq; do
    command -v "$cmd" > /dev/null || { echo "error: $cmd is required" >&2; exit 1; }
done

sha256_of() {
    if command -v sha256sum > /dev/null; then
        sha256sum "$1" | cut -d' ' -f1
    else
        shasum -a 256 "$1" | cut -d' ' -f1
    fi
}

if [ -n "${PLUGIN_SRC_DIR:-}" ]; then
    SRC_DIR=$PLUGIN_SRC_DIR
else
    SRC_DIR="$(git rev-parse --show-toplevel)/plugins/$PLUGIN_NAME"
fi
[ -f "$SRC_DIR/.claude-plugin/plugin.json" ] || {
    echo "error: plugin not found: $SRC_DIR/.claude-plugin/plugin.json" >&2
    exit 1
}

SRC_VERSION=$(jq -r '.version' "$SRC_DIR/.claude-plugin/plugin.json")
if [ "$SRC_VERSION" != "$VERSION" ]; then
    echo "error: plugin.json version is $SRC_VERSION, expected $VERSION" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"
OUT_DIR=$(cd "$OUT_DIR" && pwd)
ZIP="$OUT_DIR/$PLUGIN_NAME-$VERSION.zip"
rm -f "$ZIP" "$ZIP.sha256"

STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

# 1. 除外対象を除いたファイル一覧を作り、リンクを実体化しながらステージングへコピーする
#    （cp -L はリンク先の内容をコピーする。BSD / GNU 共通）
(
    cd "$SRC_DIR"
    find . \( -path ./evals -o -name __pycache__ \) -prune \
        -o \( -type f -o -type l \) ! -name '*.pyc' ! -name .DS_Store -print \
        | LC_ALL=C sort
) > "$STAGE/files.txt"
[ -s "$STAGE/files.txt" ] || { echo "error: no files found under $SRC_DIR" >&2; exit 1; }

mkdir -p "$STAGE/$PLUGIN_NAME"
while IFS= read -r rel; do
    rel=${rel#./}
    dest="$STAGE/$PLUGIN_NAME/$rel"
    mkdir -p "$(dirname "$dest")"
    if ! cp -L "$SRC_DIR/$rel" "$dest"; then
        echo "error: failed to copy $rel (broken symlink?)" >&2
        exit 1
    fi
done < "$STAGE/files.txt"

# 2. 更新時刻を固定する（zip が扱える最小の 1980-01-01 より後の固定値）
find "$STAGE/$PLUGIN_NAME" -exec touch -h -t 198001020000 {} +

# 3. ソート済みの一覧を順に zip へ入れる（ディレクトリエントリは入れない）
(
    cd "$STAGE"
    sed "s|^\./|$PLUGIN_NAME/|" files.txt | TZ=UTC zip -q -X -D "$ZIP" -@
)

# 4. 検証: plugin.json の version・除外対象・リンクが残っていないこと
ZIP_VERSION=$(unzip -p "$ZIP" "$PLUGIN_NAME/.claude-plugin/plugin.json" | jq -r '.version')
if [ "$ZIP_VERSION" != "$VERSION" ]; then
    echo "error: $PLUGIN_NAME/.claude-plugin/plugin.json in zip has version $ZIP_VERSION, expected $VERSION" >&2
    exit 1
fi
if unzip -Z1 "$ZIP" | grep -E "^$PLUGIN_NAME/evals/|/__pycache__/|\.pyc$|(^|/)\.DS_Store$" >&2; then
    echo "error: excluded files found in zip (listed above)" >&2
    exit 1
fi
# unzip -Z の属性欄が l で始まるエントリはシンボリックリンク
if unzip -Z "$ZIP" | grep -E '^l' >&2; then
    echo "error: symlinks found in zip (listed above)" >&2
    exit 1
fi

SHA256=$(sha256_of "$ZIP")
echo "$SHA256  $(basename "$ZIP")" > "$ZIP.sha256"
echo "built $ZIP ($(unzip -Z1 "$ZIP" | wc -l | tr -d ' ') files)" >&2
echo "$SHA256"
