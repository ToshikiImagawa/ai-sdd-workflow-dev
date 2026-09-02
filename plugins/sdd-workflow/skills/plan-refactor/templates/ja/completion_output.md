# 完了出力テンプレート

## Phase 5: 次のステップの要約

```
✅ リファクタリング計画が完了しました

**生成/更新されたファイル:**
- {spec_path} (Case B のみ — 実装から逆生成した永続仕様書)
- {design_draft_path} (一時ドラフト。実装完了後に削除される)

**リファクタリング計画の場所:**
{design_draft_path} - "Refactoring Plan" セクション

**次のステップ:**
1. リファクタリング計画をレビュー: {design_draft_path}
2. `/task-breakdown {feature-name} {ticket-number}` を実行してリファクタリングを実行可能なタスクに分解
3. TDDアプローチで `/implement {feature-name}` を実行
4. 実装完了後に `/task-cleanup {feature-name}` を実行し、確定した決定を
   ${SDD_ADR_PATH}/{feature-name}.md へ追記する。この時点でドラフト（本計画を含む）は削除されるため、
   決定ログが唯一の恒久的な記録になる
```

## 出力フォーマット

```
File: {file_path}
Persistence: {永続 (specification/) | 一時ドラフト (task/{ticket-number}/)}
Status: {Created/Updated}
Sections Added: Refactoring Plan
```
