---
id: "adr-workflow-foundation-task-type-determination"
title: "タスク種別判定と破壊的変更・PRD起草ポリシー 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-09-02"
updated: "2026-09-02"
depends-on: ["spec-workflow-foundation-task-type-determination", "spec-spec-design-plan-refactor", "spec-quality-guardrails-vibe-detection"]
tags: ["task-type", "breaking-change", "prd-policy"]
category: "workflow-foundation"
---

# タスク種別判定と破壊的変更・PRD起草ポリシー 決定ログ

**関連 Spec:** [task-type-determination_spec.md](../../specification/workflow-foundation/task-type-determination_spec.md)
（ポリシー本体）、[plan-refactor_spec.md](../../specification/spec-design/plan-refactor_spec.md) FR-008・
[vibe-detection_spec.md](../../specification/quality-guardrails/vibe-detection_spec.md) FR-006
（このポリシーを利用する下流の振る舞い）

このファイルは append-only の決定ログである。過去のエントリは書き換えず、決定を覆す場合は新しい
エントリを追記し、`supersedes` / `superseded-by` で相互参照する。

---

## 2026-09-02: PRD の「Never Automated」は書き換えを禁じるが新規起草は禁じない

**決定**: `AI-SDD-PRINCIPLES.md` の「Updating `requirement/` (PRD) — Never Automated」は、既存 PRD の
内容を下流（spec/design/実装）から逆算して**書き換える**操作を禁止するものであり、PRD が存在しない場合に
**ゼロから起草する**操作には適用されない、と明文化した。起草した PRD は `status: "draft"` かつ `tags` に
`"reverse-engineered"` を含め、人間が承認するまで承認済み PRD として扱わない。

**理由**: 「PRD が存在しないが spec と実装がある」ケースが、禁止・許可のいずれとも読めるグレーゾーンで
放置されていた（issue #96 背景）。既存の逆生成 spec（`plan-refactor` Case B）と同じ承認ゲート付きの扱いに
揃えることで、原則内の一貫性を保ちつつ、実務上の空白を埋められる。

**却下した代替案**:

- **PRD 起草を一切禁止する**: 「PRD が無ければ人間が必ず先に書く」という運用を維持できるが、既存の
  逆生成 spec 運用（承認ゲート付きで許可）と非対称になり、「なぜ spec は逆生成できて PRD はできないのか」
  という一貫性の欠如を残すため却下
- **AI が起草した PRD を暫定的に承認済みとして扱う**: 実装速度は上がるが、PRD は人間のビジネス判断を
  記録する文書であるという原則（Never Automated の趣旨）に反するため却下

---

## 2026-09-02: 破壊的変更の移行手順は一時ドラフトでなく `adr/` に記録する

**決定**: 破壊的変更の影響分析・後方互換性の方針決定・移行手順は、`task/{ticket-number}/design-draft.md`
のような一時ドラフトに留めず、`adr/{feature}-decisions.md` に永続的な決定として記録する。既存の決定を
覆す場合は `supersedes` / `superseded-by` で無効化し、過去のエントリは書き換えない。

**理由**: 移行手順は実装完了後も参照される情報であり、実装完了後に削除される一時ドラフトに置くと
消失する。`adr/` は前提 issue #92 で新設された永続的な決定記録であり、この用途に最も適合する
（D-003: ドキュメント永続性ルールの遵守）。

**却下した代替案**:

- **`*_spec.md` に移行手順を直接書く**: spec は抽象的な構造・振る舞いの定義であり、個別の移行手順
  （具体的な手順・日付・却下した代替案）を書く場所として抽象度が合わないため却下

---

## 2026-09-02: `plan-refactor` は PRD 起草を提案するが実行しない

**決定**: `plan-refactor` の Case B が PRD 不在を検知した場合、起草を**提案**する一文を計画出力に含めるが、
`requirement/**` への書き込みは行わない。実際の起草は人間が別途判断する。

**理由**: `plan-refactor` は既存の設計判断として `requirement/**` への Edit 権限を持たない
（PRD is read-only context）。この制約を変更せずに「PRD 不在を検知したのに何も提案しない」という
issue #96 の指摘（元の空白）を解消するには、提案と実行を分離するのが最小の変更である。

**却下した代替案**:

- **`plan-refactor` に `requirement/**` への Edit 権限を追加し、直接起草させる**: 提案の一手間を
  省けるが、「PRD は人間の承認を経てから書く」という上記決定の承認ゲートの趣旨と衝突し、
  `plan-refactor` の既存の権限境界（設計判断）を変更するスコープ拡大になるため却下

---

## 2026-09-02: `vibe-detector` の推奨開始フェーズは既存のリスク評価と別軸で出力する

**決定**: `vibe-detector` は、既存の「曖昧さ×仕様書有無」によるリスクレベル評価（High/Medium/Low）を
変更せず、それとは独立した軸として、依頼内容を Task Type Determination 表に照らした推奨開始フェーズ
（Specify/Plan/Tasks/Implement）をリスクレポートに追加する。

**理由**: リスクレベルは「曖昧さの解消が必要か」を判定する軸であり、推奨開始フェーズは「どこから着手
すべきか」を判定する軸であって、両者は独立した問いである。1つの軸に混ぜると、例えば「明確だが破壊的変更」
（曖昧さは低いが Specify から始めるべき）のようなケースを表現できなくなる。

**却下した代替案**:

- **推奨開始フェーズをリスクレベルの一部として統合する**: 出力項目を減らせるが、上記の理由により
  「明確だが PRD が無い依頼は素通りする」という issue #96 の指摘そのものを再現してしまうため却下
