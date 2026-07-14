# Issue #16 — .sdd インデックス検証 RUNBOOK

`.sdd/` ドキュメントの読み込みを「生 Glob/Grep/Read」から「hook が構築した圧縮 index（SQLite → index.md）の 1 回 Read」に置き換え、トークン消費を削減する機能の検証手順書。

## ステータス

| フェーズ | 結果 | 備考 |
|:---------|:-----|:-----|
| **Step1: A/B 実測ゲート** | ✅ pass（89.38% 削減） | 2026-07-13 完了。詳細は #16 Issue 本文 |
| **Step2: 本実装** | ✅ 完了 | PR #38。スキーマ v2、テーブル形式 index.md |

## アーキテクチャ（Step2 本実装）

```
SessionStart hook
  └─ session-start.py → sdd_index.rebuild_all()
       .sdd/**/*.md を走査 → SHA-256 で変更検出 → 変更ファイルのみ再抽出
       → SQLite (.sdd/.cache/index.sqlite, スキーマ v2)
       → 派生: .sdd/.cache/index.json + index.md（テーブル形式）

PostToolUse hook (Write|Edit|MultiEdit)
  └─ post-tool-use.py → sdd_index.update_one()（増分更新、DB 既存時のみ）

消費者 (agent/skill)
  └─ SDD_INDEX=on 時: .sdd/.cache/index.md を 1 回 Read → 本文 Read 不要
     SDD_INDEX=off / 未設定 時: 現行の Glob/Grep/Read フロー（変更なし）
```

### index.md フォーマット（v2: テーブル形式）

```
## Metadata       — 全ドキュメントのメタデータ（doc_id, type, path, status, depends-on, category）
## Requirement IDs — 要求 ID の def/ref 一覧（横断検索向け）
## SysML Relationships — Mermaid requirementDiagram の関係型
## API Signatures  — REST endpoint (GET/POST/PUT/DELETE/PATCH)
## Data Models     — フェンスブロック内のデータ定義（ドキュメント別）
```

### 抽出対象（信頼性基準で選定）

| 抽出 | 言語依存 | 信頼性 |
|------|----------|--------|
| フロントマター (YAML) | なし | 高（フォーマット規約で統制） |
| Requirement IDs (`UR-001` 等) | なし | 高（AI-SDD 命名規約） |
| SysML Relationships | なし | 高（Mermaid 構文） |
| Data Models (フェンスブロック) | なし | 高（```lang で明示） |
| REST endpoints (`GET /api/...`) | なし | 高（HTTP メソッドは普遍） |

意図的に除外: Literals（数値制約）、関数シグネチャ（`def/function`）— 言語依存で不完全な抽出は誤解を生むため。

## 前提

- `claude` CLI v2.x / `python3` / `jq`
- **tokenizer バックエンド**（集計フェーズのみ必要）: 次のいずれか。
  - **Vertex AI**（本プロジェクトの既定手段）: ADC 認証 + `pip install 'anthropic[vertex]'`。
  - **API キー**: `ANTHROPIC_API_KEY` を export + `pip install anthropic`。

## A/B 実測手順（Step1 で使用、再検証時にも利用可能）

### 実験デザイン

off と on を**別プロジェクト**（別 `cwd` = 別 transcript project-key）として、**同一 `.sdd` 本文・同一コマンド・同一 config** で起動する。独立変数は **プラグインバージョン** のみ（`--plugin-dir` で切り替え）。

| 群 | fixture | プラグイン | 挙動 |
|:--|:--|:--|:--|
| off（ベースライン） | `sdd-{scale}-off` | マーケットプレイス版（index 未対応） | 生 Glob/Grep/Read |
| on | `sdd-{scale}-on` | 本実装版（index 対応） | session-start が index 構築 → 消費者が 1 回 Read |

両 fixture とも `.sdd-config.json` に `index: true` を設定。マーケットプレイス版はこの設定を無視する。

### 計測パラメータ

| 項目 | 値 |
|:--|:--|
| 主指標 | `.sdd/` を指す tool_result content トークンの群内**中央値** |
| 合格閾値 | 主指標中央値 **≥30% 削減** かつ 副指標（非キャッシュ入力）非悪化 かつ 品質等価 |
| N / キャッシュ | N=5、warm 主軸 |

### 手順

```bash
cd <repo>

# 1. off/on fixture ペアを生成（同一 .sdd 本文 + 同一 config）
python3 .claude/tests/harness/synthesize_sdd.py --scale small

# 2. 本文ビット一致を照合
bash .claude/tests/harness/verify_parity.sh pair \
  .claude/tests/fixtures/sdd-small-off .claude/tests/fixtures/sdd-small-on

# 3. baseline を記録
bash .claude/tests/harness/verify_parity.sh snapshot .claude/tests/fixtures/sdd-small-off
bash .claude/tests/harness/verify_parity.sh snapshot .claude/tests/fixtures/sdd-small-on

# 4. A/B 起動（マーケットプレイス版 vs 本実装版、N=5 × 2 群）
SDD_AB_MODEL=claude-sonnet-5 \
SDD_AB_PLUGIN_OFF="$HOME/.claude/plugins/marketplaces/ai-sdd-workflow/plugins/sdd-workflow" \
SDD_AB_PLUGIN_ON="$(pwd)/plugins/sdd-workflow" \
  bash .claude/tests/harness/run_ab.sh small 5 doc_consistency

# 5. 本文非変更を確認
bash .claude/tests/harness/verify_parity.sh verify .claude/tests/fixtures/sdd-small-off
bash .claude/tests/harness/verify_parity.sh verify .claude/tests/fixtures/sdd-small-on

# 6. 集計（tokenizer 環境で）
python3 -m venv .claude/tests/.venv
.claude/tests/.venv/bin/pip install 'anthropic[vertex]'
.claude/tests/.venv/bin/python .claude/tests/harness/aggregate_tokens.py \
  --manifest .claude/tests/runs/<RUN_ID>/manifest.json \
  --out-dir  .claude/tests/runs/<RUN_ID>

# 7. 結果確認
cat .claude/tests/runs/<RUN_ID>/summary.md
```

## ローカル E2E 検証手順（Step2 本実装）

### index 構築の検証

```bash
# .sdd-config.json に "index": true を設定した状態で:

# 1. キャッシュを削除してフル構築
rm -f .sdd/.cache/index.sqlite .sdd/.cache/index.md .sdd/.cache/index.json

# 2. session-start 経由で構築
CLAUDE_PLUGIN_ROOT="$(pwd)/plugins/sdd-workflow" \
CLAUDE_PROJECT_DIR="$(pwd)" \
CLAUDE_ENV_FILE="/tmp/test-sdd-env" \
  python3 plugins/sdd-workflow/scripts/session-start.py --default-lang ja

# 3. 検証
ls -la .sdd/.cache/index.{sqlite,md,json}  # 3 ファイル生成を確認
head -5 .sdd/.cache/index.md               # "# .sdd Index (v2, N docs)" を確認
grep SDD_INDEX /tmp/test-sdd-env            # export SDD_INDEX="on" を確認
grep '^## ' .sdd/.cache/index.md            # Metadata, Requirement IDs 等のセクション確認
```

### 増分更新の検証

```bash
# ファイルを変更 → update_one
echo "---" >> .sdd/requirement/some-file.md
CLAUDE_PROJECT_DIR="$(pwd)" python3 plugins/sdd-workflow/scripts/sdd_index.py \
  --update .sdd/requirement/some-file.md
# → index.md が再生成されること

# ファイルを元に戻す
git checkout -- .sdd/requirement/some-file.md

# 同じファイルで再度 update → hash skip で index.md の mtime が変わらないこと
```

### プラグインとしてのロード検証

```bash
claude --plugin-dir ./plugins/sdd-workflow
# session-start 出力に "[AI-SDD] AI-SDD-PRINCIPLES.md updated to v..." が表示されること
# .sdd/.cache/index.md が生成されること（index: true 設定時）
```

## 交絡対策（A/B 実測時に守ること）

- **同一 commit + 同一本文**: off/on は同一プラグインを同一 `.sdd` 本文で起動
- **env 固定**: `run_ab.sh` が `SDD_LANG=en` を export
- **群独立**: off/on は別 `cwd` = 別 project-key。prompt cache 系列が分離
- **cache_read 除外**: 主指標に含めない
- **決定性**: `--print` で 1 ターン実行、固定プロンプト、system pin

## Step1 A/B 実測結果（参考）

| 群 | .sdd tool_result トークン中央値 | 削減率 |
|:--|:--|:--|
| off（生 Read） | 91,812 | — |
| on（index 1 回 Read） | 9,747 | **89.38%** |

実測環境: `feature/test_#16`、claude CLI 2.1.197、claude-sonnet-5、Vertex AI tokenizer。
