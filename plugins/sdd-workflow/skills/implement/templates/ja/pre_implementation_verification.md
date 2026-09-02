# 実装前検証

## ドキュメントの読み込みと検証

```
1. タスク分解を読み込み: ${SDD_TASK_PATH}/{ticket}/tasks.md
2. 技術設計ドラフトを読み込み: ${SDD_TASK_PATH}/{ticket}/design-draft.md
3. 抽象仕様書を読み込み: ${SDD_SPECIFICATION_PATH}/[{path}/]{feature}.md または {feature}_spec.md
4. PRDを読み込み（存在する場合）: ${SDD_REQUIREMENT_PATH}/[{path}/]{feature}.md
```

**命名規則の違いに注意**:

- **requirement 配下**: サフィックスなし（`index.md`, `{feature-name}.md`）
- **specification 配下**: `_spec` サフィックスは任意（`index_spec.md`, `{feature-name}_spec.md`、または
  サフィックスなし）。どちらの形式でも手順 3 を満たす
- **task 配下**: 技術設計ドラフトは `design-draft.md` の固定ファイル名。チケット単位のパスであり、
  抽象仕様書のフラット／階層構造とは独立している
