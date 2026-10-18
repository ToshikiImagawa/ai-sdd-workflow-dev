---
id: "adr-task-implementation-proof-gate"
title: "Bend 証明ゲート 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-10-17"
updated: "2026-10-18"
sdd-version: "5.1.0"
depends-on: ["spec-task-implementation-proof-gate"]
ticket: "149"
tags: ["checklist", "verification", "proof", "bend", "laws"]
category: "task-implementation"
---

# Bend 証明ゲート 決定ログ

## 2026-10-17 hub import を静的 allowlist で禁止する

- **Decision**: 法則ファイルの `import` 文は、Bend 同梱の標準ライブラリ `Base` と、同じ法則ディレクトリ内に実在する `.bend` への相対 `import` だけを許可し、それ以外（未知の形式・未解決の名前・`from` 形式・別名付きを含む）は検査器を起動する前に FAIL とする。
- **Rationale**: 判定のオフライン再現性（NFR-003）、`BEND_NO_TELEMETRY=1` によるテレメトリ停止方針、サプライチェーン面の安全性を揃える。Hub の import 構文を網羅的に deny するより allowlist のほうが構文変更に強く、未知の形式は FAIL 側に倒れる。clarify Q4 として提示し 2026-10-17 にユーザーが承認した。
- **Rejected alternatives**: `.sdd-config.json` で hub import を許可可能にする — 許可した途端に PASS がネットワーク状態に依存するため却下（必要になった時点で別途議論する）。禁止せず bend に任せる — bend が名前解決のためネットワークへ出てしまい PRD NFR_002 に反するため却下。

## 2026-10-17 `laws/` 配下の命名検証を `naming.py` の対象にしない

- **Decision**: `.bend` ファイルの命名は `naming.py` / pre-tool-use の deny 対象に加えず、固定ファイル名（`LAWS.bend` / `PROOF.bend` / `main.bend`）の不備はゲート実行時の SKIPPED / FAIL の理由として報告する。
- **Rationale**: `naming.py` は `requirement/` と `specification/` を名前だけで区別するための書き込み時 deny であり、opt-in 機能のために `.md` 前提（naming.py / doc_walker / sdd_index）を崩す価値がない。`main.bend` が import する補助 `.bend` を置く余地も残せる。不備は front-matter-reviewer の `--cross-ref` と post-tool-use が可視化する。
- **Rejected alternatives**: `naming.py` を `.bend` に拡張し pre-tool-use で deny する — 共有モジュールの `.md` 前提を崩し、補助 `.bend` の配置を阻害するため却下。

## 2026-10-17 `laws-status: proven` は人が立てる

- **Decision**: run-checklist は PASS 時に spec の front matter を書き換えず、レポートで `laws-status: proven` への遷移を推奨するに留める。遷移は人が行う。
- **Rationale**: PASS は実行環境（bend の版、Lean 基盤の有無）に依存し、自動更新は AI の自己昇格を許す経路になる。run-checklist の書き込みは `task/{ticket}/` に閉じており、spec 本文・front matter への書き込み経路を増やさない（PRD DC_002）。`impl-status` のように機械更新する前例はあるが、`proven` は「人が承認した法則が証明された」という承認連鎖の終端なので人の手に置く。前提（承認行・`PROOF.bend`）は front-matter-reviewer が warning で検証する。clarify Q2 として提示し 2026-10-17 にユーザーが承認した。
- **Rejected alternatives**: run-checklist が PASS 時に spec の front matter を書き換える — 環境依存の結果で spec を機械更新し、自己採点の経路を作るため却下。

## 2026-10-17 チェックリスト項目を `CHK-205 [P2]` とし `--category proof` を別名にする

- **Decision**: 仕様レビューカテゴリの固定項目 `CHK-205 [P2]`「法則証明（proof ゲート）」を、front matter に `laws:` を持つ spec に対してのみ生成する。`/run-checklist --category proof` は「CHK-205 のみ」を指す別名として受理する。
- **Rationale**: Bend は必須依存ではないため P1（マージ前必須）にするとマージが環境依存になる（PRD DC_001）。カテゴリ 1〜9 は親 PRD IR_002 で固定されており、`CHK-204`（制約の実装）の隣が意味的にも自然。`laws:` の無い spec に項目を出すと常に SKIPPED のノイズになる。既存の `--category` は CHK カテゴリ名を取るため `proof` は別名として定義する。clarify Q5 として提示し 2026-10-17 にユーザーが承認した。
- **Rejected alternatives**: `CHK-205 [P1]` — マージ可否が bend の有無に依存するため却下。新カテゴリ 10（`CHK-10xx`）— 親 PRD で固定されたカテゴリ体系を崩すため却下。

## 2026-10-17 `# spec:` の値は spec の `id` とする

- **Decision**: `LAWS.bend` の先頭コメント `# spec:` には spec の front matter `id` を書く。
- **Rationale**: ファイル移動・リネームに強く、front-matter-reviewer の `--cross-ref` が持つ id レジストリで spec `laws:` ↔ LAWS `# spec:` の双方向整合を検証できる。id → path の解決は spec の直接走査（または `.cache/index.md`）で可能。clarify Q1 として提示し 2026-10-17 にユーザーが承認した。
- **Rejected alternatives**: `${SDD_ROOT}` 相対パス — インデックス無しでも直接検証できる利点はあるが、移動・リネームに弱いため却下。

## 2026-10-17 `--verdict` で Lean 基盤が無い場合は通常検査にフォールバックする

- **Decision**: `--verdict` 指定時に Lean 基盤が無ければ通常検査にフォールバックして判定を返し、`verdict: "unavailable"` を併記する。TOOL_NOT_FOUND は「`bend` 自体が無い」場合だけに限定する。
- **Rationale**: ゲートの主判定（法則が満たされるか）を Lean の有無で失わない。失敗ケースの出力・終了コードは `--verdict` の有無で同一と実測されているため、フォールバックで判定が揺れない。`verdict` の 3 値（`checked` / `unavailable` / `not-requested`）で再検査の有無を機械可読に残す。clarify Q3 として提示し 2026-10-17 にユーザーが承認した。
- **Rejected alternatives**: Lean 基盤が無ければ TOOL_NOT_FOUND で終える — 主判定まで失われ、bend 不在と区別できなくなるため却下。

## 2026-10-17 法則ディレクトリはスキルが `laws:` を読み `--laws-dir` で渡す

- **Decision**: spec の `laws:` を読み `${SDD_ROOT}/` を前置して `--laws-dir` に渡すのはスキル（LLM）の仕事とし、スクリプトは渡されたディレクトリを検査する。`--laws-dir` 省略時は `SDD_LAWS_PATH` 配下を再帰走査する。
- **Rationale**: CONSTITUTION A-002（spec の解釈は LLM、ディレクトリ検査は決定的なスクリプト）。スクリプトに spec の解釈責務を持ち込まず、`--laws-dir` 無しでも全走査できるため手動実行にも使える。`laws:` は PRD FR_003 どおり `${SDD_ROOT}` 相対に保ち、前置はスキルの定型作業にする。
- **Rejected alternatives**: スクリプトが spec の front matter を読んで対象を決める — スクリプトに spec 解釈の責務が混入し A-002 に反するため却下。

## 2026-10-17 複数法則ディレクトリの集約はスクリプトが行う

- **Decision**: スクリプトが全ディレクトリの判定を FAIL > TIMEOUT > TOOL_NOT_FOUND > SKIPPED > PASS の順で最悪判定に集約し、`results` に個別判定を併記する。スキルは 1 回だけ呼ぶ。
- **Rationale**: run-checklist は 1 項目（CHK-205）に 1 判定を記録する。集約を haiku のスキルに任せると不安定なので、決定的なスクリプト側に置き「見逃し」を作らない。
- **Rejected alternatives**: スキルがディレクトリごとに呼び、スキル側で集約する — 集約が非決定的になるため却下。

## 2026-10-17 `main.bend` は任意とする

- **Decision**: 参照モデル `main.bend` は任意とし、法則がモデル関数を参照しない自己完結の場合は省略できる。
- **Rationale**: `# model-of:` は `main.bend` にのみ置くため、無ければ見直し促し（FR-009）の対象が無いだけで判定には影響しない。
- **Rejected alternatives**: `main.bend` を必須にする — 自己完結の法則にも空のモデルを強いることになるため却下。

## 2026-10-17 階層 spec の法則ディレクトリは `laws/{parent}/{child}/` とする

- **Decision**: 階層 spec に対応する法則ディレクトリの既定を `laws/{parent}/{child}/` とし、省略時の探索は `LAWS.bend` / `PROOF.bend` を直接含むディレクトリだけを対象にして中間ディレクトリを SKIPPED に数えない。
- **Rationale**: spec / requirement / adr と同じ階層規則（AI-SDD の階層構造）に揃え、識別子をディレクトリ名に置く方針と整合する。`laws:` はパスのリストなので別形式でも動作するが、既定を揃えておく。clarify Q6 として提示し 2026-10-17 にユーザーが承認した。
- **Rejected alternatives**: `laws/{parent}-{child}/` — 動作はするが他ディレクトリの階層規則と不一致になるため却下。

## 2026-10-17 承認行に法則本文の内容ハッシュを含めて束縛する

- **Decision**: `# approved:` 行に承認日・承認者に加えて法則本文（先頭コメント部を除く）の内容ハッシュ（sha256 先頭 12 桁）を含め、不一致なら承認失効として SKIPPED とする。ハッシュは `--print-laws-hash` で人が得る。
- **Rationale**: 承認行の有無だけでは「承認後に法則を弱めて PASS を得る」抜け道が残る（prd-reviewer / spec-reviewer 指摘）。`LAWS.bend` 単体で検証でき、先頭コメント部を除外することで承認行の追記自体では失効しない。
- **Rejected alternatives**: 承認行の有無だけを見る — 承認後の改変を検出できないため却下。git の履歴で承認日以降の変更を検出する — フックは git 無しでも動くという方針と相容れず、日付粒度で曖昧なため却下。

## 2026-10-17 孤児 laws はゲートの FAIL と reviewer の error の両方で静的に検出する

- **Decision**: `LAWS.bend` の `# spec:` が実在する spec に解決でき、かつその spec の `laws:` が当該ディレクトリを指すこと（双方向）を法則ディレクトリの成立条件とし、満たさなければゲートは FAIL（判定表 #4）、front-matter-reviewer `--cross-ref` は error とする。明示指定・再帰走査とも同条件で、承認判定（#5）より前に評価する。
- **Rationale**: spec が正典であり（D-001）、spec に結びつかない法則は派生物として成立しないので「失敗ではない」では済まない。両方に置くことで bend の有無によらず静的に検出でき、既存 #2（spec → laws）と対になって双方向の整合が閉じる。`# spec:` による laws → spec の参照は検証のための照合で、`depends-on` の依存方向は変えない。PR #152 レビュー中のユーザー指示で追加した。
- **Rejected alternatives**: warning / SKIPPED に留める — `laws:` の書き忘れや spec 削除後の取り残しがノイズに埋もれ、承認済み法則が spec 無しで PASS を出しうるため却下。ゲート側のみで検出 — bend 未導入環境では TOOL_NOT_FOUND で #4 に到達せず検出経路が無くなるため却下。reviewer 側のみで検出 — `--cross-ref` を実行しない限り見つからず、ゲート単体で判定の完全性を保てないため却下。

## 2026-10-17 `SDD_LAWS_DIR` / `SDD_LAWS_PATH` は常時エクスポートする

- **Decision**: session-start は `laws:` を持つ spec の有無にかかわらず `SDD_LAWS_DIR`（既定 `laws`）/ `SDD_LAWS_PATH`（既定 `${SDD_ROOT}/laws`）を常時エクスポートする。`init-structure.py` の既定 config には `laws` を含めず、ディレクトリ自体は opt-in 時に初めて作る。
- **Rationale**: spec FR-003 / §4.1「他ディレクトリと同様に」エクスポートする定義と整合する。変数が常に存在してもディレクトリが無ければ副作用はない。統括セッションが 2026-10-17 に承認した。
- **Rejected alternatives**: `laws:` を持つ spec があるときだけエクスポートする — セッション開始時に全 spec の front matter を走査する必要があり、フックの軽量性と A-002（スクリプトは決定的・単純）に反するため却下。

## 2026-10-17 承認行の真正性は運用と生成スキルの指示で守り pre-tool-use では deny しない

- **Decision**: AI が `# approved:` 行を書いてしまう事故は、PR レビューで承認行の追加を確認する運用と、法則案生成スキルの指示での禁止で防ぐ。pre-tool-use での deny は入れない。
- **Rationale**: 内容ハッシュによる束縛は「承認後の改変」を塞ぐが「AI が承認行を書く」ことは塞がない。pre-tool-use は `.bend` への書き込み主体（人か AI か）を判別できないため、deny では人の承認作業まで阻害する。
- **Rejected alternatives**: pre-tool-use で `# approved:` を含む `.bend` の書き込みを deny する — 書き込み主体を判別できず人の承認も止めてしまうため却下。

## 2026-10-17 `AI-SDD-PRINCIPLES.source.md` と spec テンプレートの変更を本チケットの範囲外とする

- **Decision**: 原則文書（`AI-SDD-PRINCIPLES.source.md`）の構成図への `laws/` 追記、spec テンプレート（en/ja）への任意「Laws」節の追加、`sdd_index.py` への `laws` / `laws_status` 列の追加は本チケットでは行わない。利用者向けの説明は README / CHANGELOG に限る。本リポジトリ自身の dogfooding 用 `.sdd/laws/`（候補: proof-gate_spec 3.1.1 判定表の法則化）も本チケットでは作らない。
- **Rationale**: 法則への参照は front matter `laws:` で表現でき本文節は重複になる。`sdd_index.py` の列追加はスキーマ bump を伴い、「`drafted` のまま放置された spec」を列挙したくなった時点で別チケットで判断すればよい。原則文書は opt-in 機能のために改版する必要がなく、設計ドラフト（削除済み）§7.1 のモデル作成ガイドは README に反映した。
- **Rejected alternatives**: 本チケットで原則文書・テンプレート・インデックスまで拡張する — opt-in 機能に対して変更範囲が広く、スキーマ bump と原則文書の改版を伴うため却下。

## 2026-10-18 Bend 側の観察の実機再確認は未実施とし自前の静的検査で代替する

- **Decision**: spec §4.1 が実装時に求める Bend 側の観察（先頭コメント部の読み飛ばし、`LAWS.bend` 未 import の拒否、Hub import の構文、`bend --version` の出力形式）の実機再確認は本チケットでは実施していない。ゲートはこれらの観察に依存せず、`laws_header.py` の静的検査（先頭コメント解析・内容ハッシュ・`law` 宣言・LAWS import・import allowlist）で同じ条件を自前で課す。実機再確認は別 issue で扱う。
- **Rationale**: CI に本物の `bend` を入れない方針（NFR-001 / DC_001）のため、実装 PR の検証はダミー `bend` による subprocess テストに限られた。観察に依存しない設計なので、再確認の結果が変わってもゲートの判定表は影響を受けない。未実施を事実どおり記録し、spec の要求に対する受け皿を残す。
- **Rejected alternatives**: 実機再確認が済むまで `impl-status: implemented` を保留する — ゲートの判定が観察に依存しないため、保留する実益がなく却下。再確認を省略して記録も残さない — spec §4.1 の「結果を決定ログに記録する」との不整合が残るため却下。
