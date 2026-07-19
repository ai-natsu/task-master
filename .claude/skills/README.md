# プロジェクトスキル構成

このディレクトリには、本プロジェクト専用の Claude Code スキル
（`.claude/skills/<名前>/SKILL.md`）を置く。git 管理され、チーム全員が共有する。

## スキルとは

特定の作業の「手順書」。`/<名前>` で明示的に呼び出すか、`description` に
合致するタスクで Claude が自動的に参照する。サブエージェント（別コンテキストで
動く実行者）と違い、スキルは現在の会話に手順を読み込んで Claude 自身が実行する。

## スキル一覧

| スキル | 呼び出し | 役割 |
|---|---|---|
| code-style | `/code-style [check] [パス]` | ESLint の検査・修正（Prettier は今回見送り） |

（スキルを追加したらここに 1 行足す）

## code-style の詳細

### 引数
| 形式 | 動作 |
|---|---|
| `/code-style` | 検査 → 自動修正 → 手動修正 → 再検証（既定） |
| `/code-style check` | 検査のみ・コード変更なし（CI と同一判定） |
| `/code-style <パス>` | 範囲を限定して修正（例: `/code-style server`） |

### 品質3層でのスキルの位置づけ

```
フック（編集直後の1ファイル自動整形）
  → スキル /code-style（リポジトリ全体の一括仕上げ）
    → CI（npm run check がマージゲート）
```

3層とも同じコマンド（`npm run check` = `eslint .`）を共有するため、
「手元で通れば CI も通る」が成立する。整形（Prettier）は今回見送り
（経緯は [../../docs/STATIC_ANALYSIS.md](../../docs/STATIC_ANALYSIS.md)）。

### 禁止事項
`eslint-disable` の無断追加 / ルール緩和 / 無関係リファクタの混入（詳細は SKILL.md）

## スキルとサブエージェント・フックの使い分け

| 仕組み | 実行者 | 用途 |
|---|---|---|
| スキル | 現在の Claude | 手順の標準化（lint、リリース手順など） |
| サブエージェント | 別コンテキストの Claude | 委譲したい大きめの作業（レビュー、調査） |
| フック | シェルコマンド（機械） | 決定的な自動処理（編集後の整形） |

関連: サブエージェントは [../agents/README.md](../agents/README.md)、
権限・フック設定は [../PERMISSIONS.md](../PERMISSIONS.md) を参照。

## スキルを追加するには

1. `.claude/skills/<name>/SKILL.md` を作成する
   ```markdown
   ---
   name: <name>
   description: いつ使うか（自動参照の判断材料になる）
   ---

   （手順・引数の解釈・禁止事項・報告フォーマット）
   ```
2. この README の一覧表に行を追加する
3. PR でレビューを受ける
