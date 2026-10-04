# TaskMaster

プロジェクト・タスク・サブタスク（無制限階層）・タグ・優先度・期限を管理できるタスク管理Webアプリ。Node.jsでサーバー起動するため、別途サーバーは不要。カンバンビュー、ガントチャートビュー、タスクツリーでブラウザから進捗管理できる。検索/フィルタ、ドラッグ&ドロップによる並び替え、統計ダッシュボードを備える。

## 目次

- [画面要件](#画面要件)
- [技術要件](#技術要件)
- [データベース定義](#データベース定義)
- [API仕様](#api仕様)
- [起動方法](#起動方法)
- [使い方](#使い方)
- [テスト](#テスト)
- [ディレクトリ構成](#ディレクトリ構成)

## 画面要件

### 共通レイアウト

| 要素 | 内容 |
|---|---|
| サイドバー | ダッシュボード／プロジェクト一覧画面／設定へのリンク、プロジェクトのナビゲーション（アーカイブ済みは非表示） |
| メインエリア | 選択中の画面を表示 |

### ① ダッシュボード（`/`）

全プロジェクト横断の概要画面。

- 統計カード：プロジェクト数（アーカイブ除く）、直近7日の完了数、タスク総数、完了率、期限超過件数、本日〜3日後（4日間）に期限を迎える件数
- ステータス別・優先度別の内訳（棒グラフ、優先度は高い順＝緊急が一番上）
- 期限超過タスク一覧（最大8件、期限が近い順）
- 期限が近いタスク一覧（最大8件）
- プロジェクト一覧カード（プロジェクト名・色・タスク件数、クリックで詳細へ）

### ② プロジェクト一覧（`/projects`）

- 「+ 新しいプロジェクト」ボタンからプロジェクトを作成
- プロジェクトごとに 編集／アーカイブ・復元／削除
- アーカイブしたプロジェクトはサイドバー・ダッシュボード・各一覧から非表示になる（「アーカイブ済みも表示」チェックで表示し、復元できる）

### ③ プロジェクト詳細（`/projects/:projectId`）

- ヘッダー：プロジェクト名・説明・「ツリー / カンバン / ガント」表示切替・「統計を表示」トグル・「+ 新しいタスク」ボタン
- 統計表示（トグルで開閉、このプロジェクトに絞った集計）
- フィルタバー：キーワード検索、ステータス、優先度、タグで絞り込み（複合可）
- カンバンビュー：
  - ステータスごとの列にタスクカードを表示（列は設定画面で自由に増減可）
  - カードを別の列へドラッグ&ドロップするとステータス変更、同じ列内でドラッグすると並び順（優先順）を変更
  - カードのクリックで編集モーダルが開く（ドラッグ中はカード全体が追従する）
- ガントチャートビュー：
  - タスクを行、日付を列として、開始日〜期限の期間をステータス色のバーで表示
  - 月・日ヘッダー（土日は色分け）、今日のハイライトと縦ライン
  - 開始日のみ／期限のみの場合は1日分のバー、両方未設定はバー非表示
  - バー中央のドラッグで開始日・期限を平行移動、バー両端のドラッグで期間を伸縮、行名のドラッグで並べ替え・親の付け替え
  - 土日に加えて祝日も日付ヘッダーを色分け
  - タスク名・バーのダブルクリックで編集モーダルが開く（シングルクリックでは何も起きない）
- タスクツリー：
  - 親子関係を持つタスクを無制限の深さでネスト表示
  - 各行でステータス変更（未着手／進行中／完了）、優先度バッジ、タグ、期限（超過時は赤字）を表示
  - 行のクリックで編集モーダルが開く。行アクション：サブタスク追加・編集・削除（行末のボタン）
  - ドラッグハンドルで並び替え・親の付け替え（行の上端/下端=兄弟として挿入、中央=子にする）
  - 展開／折りたたみ（▾/▸）
- タスク作成・編集モーダル：タイトル・詳細・ステータス・優先度・開始日・期限・親タスク（階層変更）・タグ（複数選択＋その場で新規作成）
- プロジェクト作成・編集モーダル：名前・説明・カラー選択
- 削除確認ダイアログ（プロジェクト／タスク共通）

### ④ 設定（`/settings`）

サイドバー下部の「⚙️ 設定」から開く。

- ステータス設定：ステータスの追加・名称変更・カラー変更・並び替え（▲▼）・削除
- 「完了として扱う」フラグ：付けたステータスは完了率の計算や期限超過の判定で完了済みとして扱われる
- タスクで使用中のステータス、および最後の1件は削除不可（エラーメッセージ表示）
- 祝日：日付（カレンダー／直接入力）・名称を登録。一覧は日付昇順で、名称のインライン編集・削除ができる。CSV（列順「日付,名称」、UTF-8/Shift_JIS）の一括登録にも対応し、日付が一致する行は名称を上書きする
- タグ：プロジェクトを横断して共有される名前・色の一覧。追加・インライン改名・色変更・削除ができる（削除確認ダイアログに付与タスク件数を表示）。名前の重複はエラーで拒否
- 言語 / Language：表示言語を日本語／Englishから選択（即時反映、このブラウザの localStorage に保存）。ステータス名・タグ名・プロジェクト名などユーザーが入力したデータは翻訳されない

## 技術要件

### サーバー（`server/`）

| 項目 | 採用技術 |
|---|---|
| 言語 | TypeScript |
| フレームワーク | Express 4 |
| ORM | Prisma 5 |
| データベース | SQLite（`server/dev.db`） |
| バリデーション | zod（各ルートファイルにインラインでスキーマ定義） |
| 実行 | tsx watch（開発時のホットリロード） |
| ポート | 3001 |

### クライアント（`client/`）

| 項目 | 採用技術 |
|---|---|
| 言語 | TypeScript |
| フレームワーク | React 18 |
| ビルドツール | Vite 5 |
| スタイリング | Tailwind CSS 3 |
| サーバー状態管理 | TanStack React Query 5（キャッシュ・楽観的更新） |
| ルーティング | react-router-dom 6 |
| ドラッグ&ドロップ | @dnd-kit（core / sortable / utilities） |
| 日付処理 | date-fns |
| ポート | 5173（`/api/*` を Vite の proxy で 3001 番へ転送） |

### 動作要件

- Node.js（LTS推奨）
- npm workspaces 構成（ルート / `server` / `client`）

## データベース定義

Prisma schema: [server/prisma/schema.prisma](server/prisma/schema.prisma)

### ER概要

```
Project 1───N Task ───N┐
                 │      ├──N TaskTag N──┐
                 ├─self (parentId)      │
                 └──N─1 Status         Tag
```

### Project

| カラム | 型 | 説明 |
|---|---|---|
| id | String (cuid) | 主キー |
| name | String | プロジェクト名 |
| description | String? | 説明（任意） |
| color | String | 表示色（デフォルト `#6366f1`） |
| archived | Boolean | アーカイブフラグ。trueのプロジェクトは各一覧・集計から除外される（デフォルト false） |
| order | Int | サイドバーでの表示順 |
| createdAt / updatedAt | DateTime | 自動管理 |

### Task

| カラム | 型 | 説明 |
|---|---|---|
| id | String (cuid) | 主キー |
| title | String | タスク名 |
| description | String? | 詳細（任意） |
| status | String | `Status.id` への外部キー（`onDelete: Restrict` — 使用中ステータスは削除不可）。デフォルトの3件は `TODO` / `IN_PROGRESS` / `DONE`、追加分はcuid |
| priority | String | `LOW` \| `MEDIUM` \| `HIGH` \| `URGENT` |
| startDate | DateTime? | 開始日（任意、ガントチャートのバー始点） |
| dueDate | DateTime? | 期限（任意） |
| order | Int | 同一階層内での並び順 |
| projectId | String | 所属プロジェクト（`onDelete: Cascade`） |
| parentId | String? | 親タスクへの自己参照。`null` なら最上位タスク（`onDelete: Cascade`で親削除時に子孫も削除） |
| createdAt / updatedAt | DateTime | 自動管理 |

インデックス：`projectId` / `parentId` / `status` / `priority` / `dueDate`

### Status

ユーザーが設定画面で自由に追加・変更できるタスクのステータス。マイグレーションで `TODO`（未着手）/ `IN_PROGRESS`（進行中）/ `DONE`（完了、isDone=true）の3件が投入される。

| カラム | 型 | 説明 |
|---|---|---|
| id | String (cuid) | 主キー（デフォルト3件のみ固定文字列） |
| label | String | 表示名（例: 未着手、レビュー中） |
| color | String | 表示色（デフォルト `#64748b`） |
| order | Int | 表示順（カンバンの列順・プルダウンの並び順） |
| isDone | Boolean | 完了扱いフラグ。完了率・期限超過・「完了した数」の集計に使われる |

### Tag

| カラム | 型 | 説明 |
|---|---|---|
| id | String (cuid) | 主キー |
| name | String | タグ名（ユニーク） |
| color | String | 表示色（デフォルト `#94a3b8`） |

### Holiday

| カラム | 型 | 説明 |
|---|---|---|
| id | String (cuid) | 主キー |
| date | String | `YYYY-MM-DD`。ユニーク（CSV一括登録で一致する日付の行を上書き） |
| name | String | 祝日名 |

### TaskTag（中間テーブル）

Task と Tag の多対多を表す join モデル。`taskId` + `tagId` の複合主キー。

## API仕様

すべて `/api` 配下。ベースURLは開発時 `http://localhost:3001`。

| メソッド | パス | 概要 |
|---|---|---|
| GET | `/api/projects` | プロジェクト一覧（タスク件数付き）。デフォルトはアーカイブ除外、`?includeArchived=true` で全件 |
| POST | `/api/projects` | プロジェクト作成 |
| PATCH | `/api/projects/reorder` | 並び順の一括更新 |
| GET/PATCH/DELETE | `/api/projects/:id` | 取得・更新・削除 |
| GET | `/api/tasks` | タスク一覧（`projectId`/`status`/`priority`/`tagId`/`search`/`parentId` でフィルタ。`projectId`省略時はアーカイブ済みプロジェクトのタスクを除外） |
| POST | `/api/tasks` | タスク作成 |
| PATCH | `/api/tasks/reorder` | 並び順・親・所属プロジェクトの一括更新 |
| GET/PATCH/DELETE | `/api/tasks/:id` | 取得・更新・削除 |
| PATCH | `/api/tasks/:id/move` | 親タスク／プロジェクトの変更（循環参照を検知して拒否） |
| GET/POST | `/api/tags` | タグ一覧・作成 |
| DELETE | `/api/tags/:id` | タグ削除 |
| GET/POST | `/api/statuses` | ステータス一覧・作成 |
| PATCH | `/api/statuses/reorder` | ステータスの並び順一括更新 |
| PATCH/DELETE | `/api/statuses/:id` | ステータス更新・削除（使用中/最後の1件は409） |
| GET | `/api/stats` | 集計（`projectId`省略で全体集計） |

## 起動方法

### 前提

- Node.js（LTS 推奨）と npm
- Windows / Mac / Linux（Windows では PowerShell または Git Bash）

### 初回だけ行う準備

リポジトリのルートで実行する。

```bash
npm install                                  # server / client 両方の依存関係をインストール
cp server/.env.example server/.env           # 環境設定を作る（Windows の PowerShell は Copy-Item）
cd server
npx prisma migrate deploy                    # データベース（server/prisma/dev.db）を作る
npm run seed                                 # 任意：サンプルデータを入れる（既存データは全削除される）
cd ..
```

`server/.env` の内容（初期値のままでよい）:

| 項目 | 初期値 | 意味 |
|---|---|---|
| `DATABASE_URL` | `file:./dev.db` | データベースのファイル（SQLite。`server/prisma/` からの相対パス） |
| `PORT` | `3001` | API サーバーのポート |

### 起動する（開発用）

ターミナルを 2 つ開き、それぞれで実行する。

| ターミナル | コマンド | 起動するもの |
|---|---|---|
| ① | `npm run dev:server` | API サーバー（http://localhost:3001） |
| ② | `npm run dev:client` | 画面（http://localhost:5173） |

ブラウザで **http://localhost:5173** を開く。画面からの `/api` へのアクセスは、自動で 3001 番に転送される。

起動の確認:

- `http://localhost:3001/api/health` を開いて `{"ok":true}` と表示されれば、API サーバーは動いている。
- ターミナルの表示が `Server listening on http://localhost:3001` なら、サーバーの起動は成功している。

### 停止する

それぞれのターミナルで `Ctrl + C`。

### 本番用にビルドして動かす

```bash
npm run build                                # server/dist/ と client/dist/ を作る
cd server && npm start                       # API サーバーを起動（node dist/index.js、3001 番）
```

- `client/dist/` は静的ファイル（HTML・JS・CSS）。配信用の Web サーバー（nginx など）で公開し、`/api/*` を API サーバーへ転送する。
- 本番ビルドに、テストコードは含まれない（`server/tsconfig.build.json` は `src/` だけを出力する）。

### うまくいかないとき

| 症状 | 対処 |
|---|---|
| `EADDRINUSE`（ポートが使用中） | 3001 または 5173 を使っているプログラムを止める。`server/.env` の `PORT` を変える場合は、`client/vite.config.ts` の proxy の転送先も合わせる |
| 画面は出るが一覧が空 / API エラー | API サーバー（①）が起動しているか確認する。`npx prisma migrate deploy` を実行したか確認する |
| `Environment variable not found: DATABASE_URL` | `server/.env` が無い。`server/.env.example` をコピーして作る |
| サンプルデータを入れ直したい | `cd server && npm run seed`（既存データは全削除される） |

## 使い方

起動後、`http://localhost:5173` をブラウザで開く。`npm run seed` を実行済みなら、サンプルのプロジェクト・タスクが入った状態で確認できる。

### 1. プロジェクトを作る・アーカイブする

1. サイドバーの「📁 プロジェクト一覧」を開き、「+ 新しいプロジェクト」をクリック
2. 名前・説明（任意）・カラーを選んで「作成」
3. サイドバーに追加されたプロジェクト名をクリックするとプロジェクト詳細画面に移動する

プロジェクト一覧画面では編集・削除のほか「アーカイブ」ができる。アーカイブするとサイドバーやダッシュボードに表示されなくなる（データは残る）。「アーカイブ済みも表示」にチェックを入れると表示され、「復元」で元に戻せる。

### 2. タスクを作る

1. プロジェクト詳細画面右上の「+ 新しいタスク」をクリック
2. タイトル（必須）、詳細、ステータス、優先度、期限、タグを入力して「作成」
3. タグは既存のものをクリックして選択するか、下の入力欄に新しいタグ名を入れて「追加」するとその場で新規作成される

### 3. サブタスクを作る（無制限階層）

各タスク行にカーソルを合わせると出る「+サブ」をクリックすると、そのタスクの子タスクとして新規作成モーダルが開く。サブタスクにさらにサブタスクを追加でき、階層に制限はない。

既存タスクの親を変更したい場合は、そのタスクを「編集」し、フォーム内の「親タスク」欄で移動先を選び直す（自分自身やその子孫は選択肢から除外される）。

### 4. ステータスを更新する

各タスク行のステータス（未着手／進行中／完了）は、行内のプルダウンから直接変更できる。編集モーダルを開かずにその場で更新される。

### 5. 並び替える

タスク行にカーソルを合わせると左端に現れる「⠿」をドラッグすると、同じ階層（同じ親を持つタスク同士）の中で並び順を変更できる。異なる親の間へ移動したい場合はドラッグではなく、編集モーダルの「親タスク」で行う。

### 5-2. カンバンで管理する

プロジェクト画面右上の「カンバン」を押すとステータスごとの列表示に切り替わる。

- カードを**別の列へドラッグ** → ステータスがその列のものに変わる
- カードを**同じ列内で上下にドラッグ** → 並び順（優先順）が変わる
- カードをクリック → 編集モーダルが開く

### 5-3. ガントチャートで見る

プロジェクト画面右上の「ガント」を押すと、開始日〜期限をバーで表すガントチャートに切り替わる。開始日はタスクの作成・編集モーダルの「開始日」で設定する。今日の位置には縦ラインが表示される。

### 5-4. ステータスを自分用に変える

サイドバー下部の「⚙️ 設定」→「ステータス設定」で、ステータスの追加（例: レビュー中）・名称/色の変更・並び替え・削除ができる。「完了として扱う」を付けたステータスが完了率などの集計で「完了」と見なされる。

### 5-5. 表示言語を切り替える

サイドバー下部の「⚙️ 設定」→「言語 / Language」で日本語／Englishを選ぶ。選んだ言語はこのブラウザに保存される。

### 6. 検索・絞り込み

プロジェクト詳細画面のフィルタバーで、キーワード検索・ステータス・優先度・タグを組み合わせて絞り込める。「クリア」ですべてリセット。

### 7. 統計を見る

- プロジェクト詳細画面右上の「統計を表示」で、そのプロジェクトに絞った完了率・期限超過件数などを表示
- サイドバーの「ダッシュボード」では、全プロジェクト横断の統計と、期限超過／期限が近いタスクの一覧を確認できる

## テスト

単体・結合は **Vitest**、UI 部品は **Playwright CT**（Component Testing）、E2E は **Playwright**。3 つのスクリプトは分離している。詳細な方針とケース一覧は [docs/TEST_DESIGN.md](docs/TEST_DESIGN.md)。

```bash
npm test           # Vitest（server の単体・結合 + client の関数・ロジックの単体）
npm run test:ct    # Playwright CT（UI 部品を実際のブラウザで描画して検証）
npm run test:e2e   # Playwright E2E（専用 DB で、サーバーと画面を自動で起動する）
```

| 種類 | 場所 | 内容 |
|---|---|---|
| 単体テスト（client） | `client/src/` 内、対象のソースの隣（`*.test.ts`） | `utils/`（ツリー・ドラッグ判定・期限・ガントなど）、`i18n`、フォーム値の変換 |
| UI 部品テスト（client） | `client/src/components/` 内、対象のソースの隣（`*.test.tsx`） | Playwright CT。バッジ・フィルタ・統計・フォーム・確認ダイアログの表示と操作、入力値のチェック（必須・文字数の上限）（API は `page.route` で固定値に差し替える） |
| 単体テスト（server） | `server/tests/unit/` | zod スキーマの境界値 |
| 結合テスト（server） | `server/tests/integration/` | Supertest で API を検証（専用 DB `server/test.db` を各テスト前にリセット）。循環参照・統計（isDone 駆動）・アーカイブ除外・ステータス削除制約・エラー応答・配線（`app.test.ts`） |
| E2E | `e2e/`（ルート直下） | Playwright。専用 DB `server/e2e.db` で、プロジェクト作成→サブタスク、カンバンのドラッグ、ステータス追加/削除制約、アーカイブ/復元（確認ダイアログ） |

- E2E と UI 部品テストは、初回のみ `npx playwright install chromium` が必要。
- 拡張子で振り分ける：`*.test.ts` は Vitest、`*.test.tsx` は Playwright CT、`*.spec.ts`（`e2e/`）は E2E。
- いずれのテストも開発用 `dev.db` には触れない。
- テスト用の共通部品：server は `server/tests/helpers/`（DB の初期化・テストデータ作成）、client は `client/src/test/`（`factories.ts`、CT 用の `ct.ts`）。

## ディレクトリ構成

```
/（リポジトリのルート。npm workspaces）
├─ package.json / eslint.config.mjs / playwright.config.ts   # 全体の設定
├─ server/                 # API（Express + Prisma + SQLite）
│  ├─ src/                 # 本番コードのみ
│  │  ├─ index.ts / app.ts # 起動 / アプリ本体（createApp）
│  │  ├─ db.ts / constants.ts / schemas.ts / errors.ts / dueRange.ts
│  │  └─ routes/           # projects / tasks / statuses / tags / holidays / stats
│  ├─ prisma/              # schema.prisma / migrations/ / seed.ts
│  ├─ tests/
│  │  ├─ unit/             # 単体テスト
│  │  ├─ integration/      # 結合テスト（Supertest）
│  │  └─ helpers/          # setup.ts / factories.ts
│  └─ tsconfig.json / tsconfig.build.json / vitest.config.ts
├─ client/                 # 画面（Vite + React + Tailwind）
│  ├─ index.html / public/ # 起動の入口 / 静的ファイル（アイコン）
│  ├─ playwright/          # Playwright CT のブラウザ側の入口（index.html / index.tsx）
│  ├─ src/                 # 本番コード ＋ テスト（*.test.ts は Vitest、*.test.tsx は Playwright CT。対象の隣）
│  │  ├─ api/ components/ pages/ i18n/ utils/ types/
│  │  ├─ main.tsx / App.tsx / index.css
│  │  └─ test/             # テスト用の共通部品
│  └─ vite.config.ts / vitest.config.ts / playwright-ct.config.ts / tailwind.config.js
├─ e2e/                    # E2E（Playwright）
├─ docs/                   # 設計書（要件・基本設計・画面設計・テスト設計など）
└─ scripts/                # 補助スクリプト（画面キャプチャなど）
```

本番ビルドの出力先（`server/dist/`、`client/dist/`）と、データベース（`server/*.db`）は Git に含めない。
