# Claude Code 権限設定（2レイヤー構成）

このリポジトリでは Claude Code の権限を「組織強制」と「プロジェクト共有」の 2 レイヤーで管理する。

## レイヤーと役割

| ファイル | 配置 | git | 役割 |
| --- | --- | --- | --- |
| `managed-settings.sample.json` | 見本のみ（適用は各端末の OS 別パス） | 追跡 | **組織強制**。絶対に緩められないセキュリティ（秘密ファイルの読取禁止・破壊的操作の禁止・ログイン組織固定・モデル制限・MCP 統制） |
| `settings.json` | `.claude/settings.json` | 追跡 | **プロジェクト共有**。`defaultMode: "ask"` を土台に、頻出で安全なコマンドだけを `allow` で緩和 |
| `settings.local.json` | `.claude/settings.local.json` | 除外 | **個人**。各自の環境で育った許可（自動追記）。コミットしない |

優先順位（強い順）: managed > settings.local.json > settings.json > ユーザー全体設定。
`deny` は同一・下位すべての `allow` に優先する。

## 設計方針

- **ホワイトリスト運用**: `defaultMode: "ask"` により、`allow` に無いコマンドは実行前に必ず確認される。禁止ではなく「都度承認」なので業務は止まらない。
- **`deny` は最小限**: `deny` は `settings.json` 側で緩められないため、「絶対に不要」なもの（秘密ファイル読取・`rm -rf`・force push）だけに絞る。`Invoke-RestMethod` など業務で使うものは `deny` せず `ask` に委ねる。
- **危険度で 3 段階に振り分け**:
  - 強制禁止 → managed の `deny`
  - 都度確認 → どこにも `allow` しない（`git push` / `npm install` / `npm run seed` など）
  - 自動許可 → `settings.json` の `allow`（テスト・ビルド・型チェック・git 参照系など）

## managed-settings.json の配置手順（管理者権限が必要）

1. `managed-settings.sample.json` をコピーし、`REPLACE_WITH_ORG_UUID` を自組織の ID に置換する。
   組織 ID は claude.ai の管理設定、または platform.claude.com の Organization 設定で確認できる。
2. 各 OS の所定パスに `managed-settings.json` として配置する。
   - Windows: `C:\ProgramData\ClaudeCode\managed-settings.json`
   - macOS: `/Library/Application Support/ClaudeCode/managed-settings.json`
   - Linux: `/etc/claude-code/managed-settings.json`
3. 端末管理ツール（MDM 等）での一括配布を推奨。

> 注意: managed に `allowManagedPermissionRulesOnly: true` を入れると `settings.json` の `allow` が無効化され、全操作が確認対象になる。本構成では意図的に有効化していない。
