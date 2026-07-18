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

## 配布とメンバーによる改変防止（承認者のみ変更可）

`managed-settings.json` は「所定パスにあるファイルを Claude Code が最優先で読む」だけの仕組みで、**誰がそのファイルを書けるかは OS の権限管理で担保する**。強い順に 3 段階。

### 1. NTFS ACL で読み取り専用にする（基本・必須）

`C:\ProgramData` 配下は既定で一般ユーザーがファイルを作成できるため、明示的にロックする。管理者 PowerShell で実行:

```powershell
New-Item -ItemType Directory -Force "C:\ProgramData\ClaudeCode" | Out-Null
icacls "C:\ProgramData\ClaudeCode" /inheritance:r
icacls "C:\ProgramData\ClaudeCode" /grant:r "SYSTEM:(OI)(CI)F" "Administrators:(OI)(CI)F" "Users:(OI)(CI)RX"
# ファイル配置後
icacls "C:\ProgramData\ClaudeCode\managed-settings.json" /grant:r "SYSTEM:F" "Administrators:F" "Users:R"
```

これでローカル管理者権限を持たないメンバーは書き換え不可になり、承認者（管理者）だけが変更できる。

### 2. MDM / 構成管理で再適用する（ドリフト防止・推奨）

ACL だけでは、管理者権限を持つ者が一時的に変えた場合に検知できない。Intune / Jamf / グループポリシー(GPO) でファイルと ACL を定期再配布すれば、勝手な変更が上書きで戻る。MDM は SYSTEM 権限で動くためユーザーは停止できない。「承認者のみ変更」を運用面で担保する現実解。

### 3. サーバー管理設定（Enterprise・ローカルファイル不要）

Claude for Enterprise の server-managed settings は設定を組織サーバーから配信する。ローカルの編集可能ファイルに依存せず、認証済みの組織メンバーに適用され、キャッシュされたサーバー設定はローカルの managed ファイルを置換する。開発者が自 PC の管理者でも触れる実ファイルが無いのが利点。最も「承認者のみ・ローカル改変不可」に近い。

### 併せて効く Claude Code 側の対策（本テンプレに設定済み）

managed に置くことでメンバーの下位設定では無効化できない:

- `disableBypassPermissionsMode: true` — 確認プロンプトのバイパス禁止
- `disableSideloadFlags: true` — `--mcp-config` / `--agents` 等の抜け道禁止
- `requiredMinimumVersion` — 古い版でキーが無視されるのを防止

### 限界

- 開発者に自 PC のローカル管理者権限を与えている場合、ACL は管理者本人には効かない。真の強制には 2.（MDM 再適用）または 3.（サーバー管理設定）が必要。
- managed 系の設定ソースはマージされない。MDM の device 管理ファイルと Enterprise のサーバー管理設定を併用する場合、`forceLoginOrgUUID` 等は両方に記載する（サーバー設定がキャッシュされると device ファイルを置換するため）。
