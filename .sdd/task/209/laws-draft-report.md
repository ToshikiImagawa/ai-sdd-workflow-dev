# 法則案 抽出レポート: prd-generation

- spec: .sdd/specification/prd-generation_spec.md（`spec-prd-generation`）
- 出力: .sdd/laws/prd-generation/LAWS.bend
- 生成日: 2026-10-21
- `laws.max_laws`: 10（front matter 未指定のため既定値）

## 法則化できた理由

FR-010（PRD FR_001_05 / UR_005 / DC_004）の「新規 ID は既存の最大値（プレフィックス別）の続きから
採番する」は計算可能な決定規則だった。元の spec には番号付きの決定表・不変条件の節が無かったため、
3.3.2 節として ID 採番規則の決定表を、3.3.1 節として不変条件を追記した（新しい要件は発明していない。
PRD UR_005 / DC_004 に既に書かれている規則の構造化のみ）。

## 採用した法則

| 法則 | 出典 | 命題 |
|:--|:--|:--|
| next_id_empty | §3.3.2 | 既存要求 ID 群が空集合のとき、新規 ID の採番結果は 1（`P_001`）である |
| next_id_singleton | §3.3.2 | 既存要求 ID 群の最大値が `a` のとき、新規 ID の採番結果は `a + 1` である |

## モデル API

参照モデルが実装すべき関数（`LAWS.bend` の `# model-api:` 行の写し。`model` 段階はこれに従う）。

固定元: `unfixed`（spec に `model-api:` 行が無く、`main.bend` も未作成のため。承認時に人が API を確認する）。

| 関数 | 引数 | 戻り値 | 符号化の注記 |
|:--|:--|:--|:--|
| Model.next_id | ids: List<&2, Nat> | Nat | プレフィックスは法則の対象外（1 プレフィックス分の既存 ID 群を `Nat` のリストとして渡す想定）。戻り値は採番結果の連番部分のみ（プレフィックス文字列の合成はモデル外） |

## 未採用の候補

なし（候補 2 件とも priority 1 で採用、上限 10 件に収まった）。

## 法則化しない理由

| 節 | 理由（IO 依存 / 性能 / 散文のみ / 節番号なし） |
|:--|:--|
| §3.1 機能要件 (FR-001〜FR-010) | FR 表の散文のみ。番号付きの決定表・不変条件ではないため draft-laws の抽出ルール上、出典にできない |
| §3.2 非機能要件 (NFR-001〜NFR-003) | 定性的な目標値の記述のみで、数値目標・決定ロジックが無い |
| §3.3.1 不変条件（既存 ID・ノードの不変性） | 「変更しない」という不変性は等式一本では表現しづらく、法則化すると参照モデルの定義の単なる書き写し（自明法則）になるため見送った。`main.bend` 実装時に amend 処理が既存要素を変更しない構造（新規差分のみを追記する関数設計）で満たす |
| §4.1 入出力定義 | 保存先パス・環境変数名の列挙で、ファイルシステム・IO が中心のため対象外 |
| §7 振る舞い図 | シーケンス図（制御フローの時系列表現）であり、決定表・集約規則・不変条件の節ではないため対象外 |
| §8 制約事項 | 基盤モデルの能力依存・入力情報量依存という運用上の制約で、計算可能なロジックではない |
| §DC_002（テンプレート優先とフォールバック、概要節で言及） | プロジェクトテンプレートの存在有無というファイルシステム判定が起点であり、IO 依存のため対象外 |

## 静的チェック

`draft_laws.py check` の結果: error 0 件、warning 0 件（`--require-model` なし。モデル API が `unfixed` のため
固定 API 名チェックは未実行）。

| コード | 重大度 | 法則 | メッセージ |
|:--|:--|:--|:--|
| （findings なし） | - | - | - |

## 次の手順（人が行う）

1. 法則をレビューし、法則ファイルの先頭コメント部の末尾（最初の `import` より上）に承認行を追記する:
   `# approved: YYYY-MM-DD <承認者> sha256:270c60c406c1`
   （現在の内容ハッシュ: `270c60c406c1`。再取得は `run-verification.py proof --print-laws-hash --laws-dir .sdd/laws/prd-generation`）
2. spec の front matter への追加案（未適用。人が追加する）。`laws:` を追加するまでは、proof ゲートは未承認判定（SKIPPED・判定表 #5）より先に孤児 laws（FAIL・判定表 #4）を報告する:
   ```yaml
   laws: ["laws/prd-generation"]
   laws-status: drafted
   ```
3. 承認後に `laws-status: approved` へ更新し、`/draft-laws model prd-generation` を実行する。
4. `/run-checklist prd-generation <ticket> --category proof` で検査する。PASS 後に人が `laws-status: proven` へ更新する。
