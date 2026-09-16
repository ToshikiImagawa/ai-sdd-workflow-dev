---
id: "adr-spec-design-generate-spec"
title: "仕様書・設計書生成 決定ログ"
type: "adr"
status: "approved"
sdd-phase: "implement"
created: "2026-07-08"
updated: "2026-07-28"
sdd-version: "5.0.0"
depends-on: ["spec-spec-design-generate-spec"]
tags: ["specification", "design-doc", "generation"]
category: "spec-design"
---

# 仕様書・設計書生成 決定ログ

## 2026-07-08 生成をスクリプト + Claude の 2 フェーズ実行にする

- **Decision**: テンプレート・参照のコピーを Python スクリプトで行い、その後 Claude が生成を行う 2 フェーズ構成とする。
- **Rationale**: テンプレート / 参照のコピーは決定的操作であり、スクリプト化することでトークンを節約できる（A-002 フックとスクリプトの責務分離）。
- **Rejected alternatives**: 単一プロンプトで全て行う — 決定的操作にトークンを消費するため却下。

## 2026-07-08 テンプレートはプロジェクト優先で解決する

- **Decision**: プロジェクトの `{root}/*_TEMPLATE.md` を優先し、存在しない場合のみ言語別のスキルテンプレートにフォールバックする。
- **Rationale**: プロジェクト固有のテンプレート差異を尊重する必要があるため。
- **Rejected alternatives**: スキル同梱テンプレートに固定する — プロジェクト固有の差異を無視するため却下。

## 2026-07-08 spec と design を 2 層に分離する

- **Decision**: 生成物を単一ドキュメントにせず、抽象仕様（spec）と技術設計（design）の 2 層に分離する。
- **Rationale**: spec は「何を」、design は「どのように」に責務を分けることで、仕様がガードレールとして機能する（DC_001）。
- **Rejected alternatives**: 単一ドキュメントにまとめる — 抽象度が混在し、仕様がガードレールとして機能しないため却下。

## 2026-07-08 品質レビューと front matter 検証を外部エージェントへ委譲する

- **Decision**: 生成後の品質レビューを spec-reviewer、front matter 検証を front-matter-reviewer に委譲する。
- **Rationale**: 品質レビューと front matter 検証はそれぞれ独立した責務であり、専用エージェントへ委譲することで実装の重複を避けられる。
- **Rejected alternatives**: スキル内でレビューまで完結させる — レビュー本体のロジックが専用エージェントと重複するため却下。

## 2026-07-08 CI モードではリスク評価・レビューを省略し design を常時生成する

- **Decision**: `--ci` 指定時はリスク評価とレビューを省略し、上書きを自動承認したうえで Design Doc を常に生成する。
- **Rationale**: 非対話パイプラインでの自動生成を成立させるため。生成省略の確認を挟めない環境では design まで必ず生成する方が安全であり、対話モードでは品質ゲートを維持する（FR-009）。
- **Rejected alternatives**: 常に対話モードで動作させる — 非対話パイプラインで停止してしまうため却下。

## 2026-07-08 出力エンコーディングを UTF-8 に維持する

- **Decision**: 生成物を ASCII エスケープせず UTF-8 で出力する。
- **Rationale**: 日本語生成物の文字化けを防止する必要がある（T-003）。
- **Rejected alternatives**: ASCII エスケープして出力する — 日本語生成物が可読でなくなるため却下。
