# 開発 TIPS — TaskMaster

開発時によく使う「dev サーバーの起動・停止・確認」と「MCP サーバー」の手順をまとめる。

## 1. dev サーバーの起動 / 再起動 / 停止 / 起動確認

TaskMaster は 2 プロセス構成。**両方**を起動しないとアプリは正しく動かない。

| プロセス | 役割 | ポート | 起動スクリプト |
|---|---|---|---|
| server | Express + Prisma（API・DB `server/dev.db`） | 3001 | `npm run dev:server` |
| client | Vite（フロント。`/api` を 3001 へプロキシ） | 5173 | `npm run dev:client` |

> ⚠️ **client（Vite）だけ起動しても、タスク追加などの保存は通りません。** Vite は `/api` を 3001 のサーバーへ中継するだけなので、**server も必ず起動**すること（保存先は `server/dev.db`）。

### 1-1. 手元のターミナルで操作

```powershell
# 必ずリポジトリのルートで実行（下記「よくあるエラー」参照）
cd C:\work\claude001

# 別々のターミナルで1つずつ
npm run dev:server   # → http://localhost:3001
npm run dev:client   # → http://localhost:5173
```

- **停止**: そのターミナルで `Ctrl + C`
- **再起動**: `Ctrl + C` で停止してから、同じコマンドを再実行

### 1-2. Claude Code に任せる（推奨・簡単）

Claude Code の Browser/preview 機能（`.claude/launch.json` の `server`/`client`）で起動・停止できる。会話で頼むだけ。

| やりたいこと | 頼み方の例 |
|---|---|
| 起動 | 「dev サーバー起動して」 |
| 状態確認 | 「dev 動いてる?」 |
| ログ確認 | 「サーバーのログ見せて」 |
| 再起動 | 「dev サーバー再起動して」 |
| 停止 | 「dev サーバー止めて」 |

### 1-3. 起動しているかの確認方法

いずれか。応答があれば起動、接続拒否なら未起動。

```powershell
# PowerShell
Test-NetConnection localhost -Port 3001
Test-NetConnection localhost -Port 5173
# もしくは
Get-NetTCPConnection -LocalPort 3001,5173 -State Listen
```

```bash
# どのシェルでも（curl）
curl http://localhost:3001/api/health   # server: ok 系が返る
curl http://localhost:5173/             # client: HTML が返る
netstat -ano | findstr ":3001 :5173"    # LISTENING があれば起動中
```

- **ブラウザ**: `http://localhost:5173`（画面が出る）と `http://localhost:3001/api/health`（ヘルスチェック）を開く。

### 1-4. よくあるエラー

- **`enoent Could not read package.json`**: npm を **package.json の無い場所**で実行している。`cd C:\work\claude001`（ルート）へ移動してから実行する。`dev:server`/`dev:client` はルートの `package.json` に定義されたスクリプト。
- **タスク追加などが保存されない / 作成ボタンが無反応**: `server`（3001）が起動していない可能性が高い。まず両プロセスの起動を確認（§1-3）。
- Windows で `node`/`npm` が見つからない: `C:\Program Files\nodejs\` を PATH に追加、または `.claude/launch.json` は `server/dev.cmd`/`client/dev.cmd` 経由で起動している（CLAUDE.md の Windows note 参照）。

## 2. MCP サーバー

MCP（Model Context Protocol）サーバーを登録すると、Claude Code から外部ツール（Figma など）を利用できる。

### 2-1. このリポジトリの MCP 一覧

プロジェクト直下の [`.mcp.json`](../.mcp.json) に定義。

| 名前 | 用途 | コマンド | 認証 |
|---|---|---|---|
| figma | Figma のデザイン読み取り（Framelink `figma-developer-mcp`） | `npx -y figma-developer-mcp --stdio` | `FIGMA_API_KEY`（環境変数） |

現在の接続状況を見るには、会話で「今つながっている MCP を見せて」と頼む（Claude が接続済みコネクタを一覧表示する）。

### 2-2. Figma MCP の使い方

1. **トークン発行**: Figma → Settings → Security → *Personal access tokens*。スコープに *File content*（read）を含める（`figd_...`）。
2. **環境変数を設定**（値は各自。秘密情報なので Claude には渡さない）:
   ```powershell
   setx FIGMA_API_KEY "figd_..."
   ```
   `setx` は**新しいプロセスから有効**。設定後は **Claude Code を再起動**する。
3. **承認**: 再起動時、プロジェクトの `.mcp.json` を検出して承認を求められる（プロジェクト MCP は初回に許可が必要）。承認するとツールが有効化。
4. **初回実行**で `npx` が `figma-developer-mcp` を取得（ネット接続要）。
5. **使う**: Figma の共有 URL（ファイル or フレームのリンク）を Claude に渡すと、デザインを読んで HTML/React やデザイントークンに起こせる。用途は主に「**Figma → 実装**」の読み取り。

### 2-3. MCP サーバーの追加

- **プロジェクト限定**（このリポジトリだけ）: ルートの `.mcp.json` に定義（上記 figma の形式）。チームで共有したい設定向き。
- **全プロジェクト共通**: `claude mcp add -s user <名前> <コマンド...>`（user スコープ）。
- 秘密情報は必ず**環境変数参照**（`${VAR}`）にし、値はコミットしない。`.gitignore` は `.env` 系を除外済み。

### 2-4. 確認・トラブル

- 認証エラー時は、トークン（`FIGMA_API_KEY`）の設定と Claude Code の再起動・再承認を確認。
- 反映されない時は Claude Code の再起動（`.mcp.json` は起動時に読み込まれる）。
