# AI オペレーション

This file provides guidance to coding agents working with code in this repository.

## プロジェクト概要

AI駆動仕様駆動開発（AI-SDD）ワークフローを支援するClaude Codeプラグインのマーケットプレイスリポジトリ。Vibe
Coding問題を防ぎ、仕様書を真実の源として高品質な実装を実現する。`SDD_LANG` 環境変数による多言語対応。

詳細な開発ルール（リポジトリ構成、テストと検証、プラグイン開発ガイド、CLAUDE.md執筆方針、scripts/作業ガイド等）は
`.claude/rules/` 配下のトピック別ファイルを参照してください。`.sdd/` 配下のAI-SDDワークフロー原則そのものは
`.sdd/AI-SDD-PRINCIPLES.md` が正典です。

## AI-SDD Instructions (v4.0.0)

<!-- sdd-workflow version: "4.0.0" -->

このプロジェクトは AI-SDD（AI駆動仕様駆動開発）ワークフローに従います。

### ドキュメント操作

`.sdd/` ディレクトリ配下のファイルを操作する際は、`.sdd/AI-SDD-PRINCIPLES.md` を参照し、AI-SDDワークフローに準拠してください。

**トリガー条件**:

- `.sdd/` 配下のファイルの読み取りまたは変更
- 新しい仕様書、設計書、要求仕様書の作成
- `.sdd/` ドキュメントを参照する機能の実装

詳細なディレクトリ構造・ファイル命名規則・ドキュメントリンク規約は、`.claude/rules/ai-sdd-instructions.md` を参照してください。
