# テスト設計書 — TaskMaster

本書は TaskMaster のテスト方針とテストケースを定義する。設計に対応するテストは実装済みで、全て green（ユニット/統合 62 件 + E2E 5 件）。

## 目次

- [実行方法](#sec-run)
- [1. テスト方針](#sec-1)
- [2. サーバー API 統合テスト](#sec-2)
- [3. クライアント ユニットテスト（純粋関数）](#sec-3)
- [4. クライアント コンポーネントテスト（API はモック）](#sec-4)
- [5. E2E（Playwright）](#sec-5)
- [6. 優先度と網羅の考え方](#sec-6)
- [7. 前提・留意](#sec-7)
- [8. テスト分担表（ファイル × テスト種別）](#sec-8)

<a id="sec-run"></a>

## 実行方法

```bash
npm test           # = test:unit（Vitest: server 47 + client 15）
npm run test:e2e   # Playwright E2E（server/e2e.db を自動初期化して起動）
```

初回のみ `npx playwright install chromium` が必要。ユニットは `server/test.db`、E2E は `server/e2e.db` を使い、開発用 `dev.db` には触れない。

<a id="sec-1"></a>

## 1. テスト方針

本章ではテスト全体の方針 — レイヤー構成・採用ツール・スクリプトの分離・ファイル配置・原則 — を定める。
**個々のテストケースは §2〜§5 に、どこから優先的に固めるかは §6 に記述する**（下表の「詳細」列から辿れる）。ファイル単位でどのテストを書くべきかの一覧は [§8 テスト分担表](#sec-8) を参照。

### レイヤーと目的

| レイヤー | 対象 | 目的 | 詳細 |
|---|---|---|---|
| ユニット（純粋関数） | `client/src/utils/tree.ts` 等の副作用のないロジック | 変換・計算ロジックの正しさを高速に検証 | [§3](#sec-3) |
| API 統合 | `server/src/routes/*.ts` + Prisma + テスト用 SQLite | エンドポイントの入出力・バリデーション・DB 反映を検証 | [§2](#sec-2) |
| コンポーネント | `client/src/components`・`pages` | API をモックし、描画とユーザー操作を検証 | [§4](#sec-4) |
| E2E | 実サーバー + 実ブラウザ | 主要フローが通しで動くことを検証 | [§5](#sec-5) |

各レイヤーをどの順で固めるか（回帰が致命的な箇所の優先度）は [§6 優先度と網羅の考え方](#sec-6) にまとめる。

### 採用ツール

| テスト種別 | ツール | 実行スクリプト |
|---|---|---|
| ユニット / 統合 / コンポーネント | **Vitest** | `npm test`（＝ `test:unit`） |
| サーバー API の HTTP 検証 | Vitest + **Supertest** | 同上 |
| クライアント コンポーネント | Vitest + React Testing Library + jsdom（API は `vi.mock`） | 同上 |
| E2E（ブラウザ通し） | **Playwright** | `npm run test:e2e` |

**ユニット系（Vitest）と E2E（Playwright）はスクリプトを完全に分離する。**
Vitest はブラウザを起動せず高速にロジックを検証、Playwright は実サーバー＋実ブラウザで主要フローを検証する。CI では「Vitest（速い・常時）」→「Playwright（重い・マージ前）」の順で段階実行する想定。

### スクリプト構成

npm workspaces（`server` / `client`）を活かし、ユニットは各ワークスペースの Vitest、E2E はルートの Playwright に集約する。

**ルート `package.json`**
```jsonc
{
  "scripts": {
    "test": "npm run test:unit",
    "test:unit": "npm run test --workspace=server && npm run test --workspace=client",
    "test:coverage": "npm run test:coverage --workspace=server && npm run test:coverage --workspace=client",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

**`server/package.json` / `client/package.json`**
```jsonc
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

### ファイル配置

```
task-master/
├─ package.json                # test / test:unit / test:coverage / test:e2e
├─ playwright.config.ts        # E2E 設定（webServer で server+client を自動起動）
├─ e2e/                        # Playwright（ユニットとディレクトリごと分離）
│  ├─ global-setup.ts          # e2e.db を作り直して migrate + seed
│  ├─ helpers.ts               # プロジェクト/タスク作成の共通操作
│  ├─ projects.spec.ts         # E-1 階層表示 / E-6 アーカイブ・復元
│  ├─ kanban.spec.ts           # E-2 ドラッグでのステータス変更・永続化
│  └─ statuses.spec.ts         # E-4 ステータス追加 / E-5 削除制約
├─ server/
│  ├─ vitest.config.ts         # env で DATABASE_URL="file:./test.db" を注入
│  └─ src/
│     ├─ app.ts                # createApp()（listen と分離し Supertest から使う）
│     ├─ app.test.ts           # 配線の検証（health / 404 / CORS / json / mount）
│     ├─ test/setup.ts         # test.db を作り直して migrate、各テスト前に全行削除
│     ├─ test/factories.ts     # seedStatuses / makeProject / makeTask
│     └─ routes/*.test.ts      # API 統合テスト（Supertest）
└─ client/
   ├─ vitest.config.ts         # environment: "jsdom"、Vite 設定を継承
   └─ src/
      ├─ test/setup.ts         # RTL matchers 登録 / 各テスト後に cleanup
      ├─ test/factories.ts     # makeTask
      ├─ utils/tree.test.ts    # 純粋関数ユニット
      ├─ utils/dnd.test.ts     # ドラッグ判定ロジック
      └─ components/*.test.tsx # コンポーネント
```

- **切り分けの境界**: `e2e/` 配下＝Playwright、`src/**/*.test.ts(x)`＝Vitest。Vitest 設定の `include` を `src/` 配下に限定し、Playwright の `testDir` は `e2e/` に限定して、互いを拾わないようにする。
- **テスト用 DB**: サーバー Vitest は `vitest.config.ts` の `test.env` で `DATABASE_URL`（`test.db`）を注入する。`db.ts` が PrismaClient を生成する前に値が確定している必要があるため、`.env` 読み込みではなくこの方式を採る。Playwright は `playwright.config.ts` の `webServer.env` で `e2e.db` を指定する。いずれも開発用 `dev.db` に触れない。

### 原則

- API テストは各テスト前に DB を初期化し、テスト間で状態を共有しない（順序非依存）。
- 日付が絡むテスト（期限超過・ガント範囲）は現在時刻を固定（`vi.setSystemTime`）。
- 「完了」判定は `status.isDone` を根拠にする（`"DONE"` 文字列をハードコードしない）ことをテストでも保証する。

---

<a id="sec-2"></a>

## 2. サーバー API 統合テスト

### 2.0 アプリ配線（`app.ts`）

各リソースのテスト（2.1 以降）は、リクエストの通り道にある設定 — ルーターのマウントパス、`express.json()` — を**暗黙的に**検証する。マウントパスを間違えれば 404 になり、各テストが落ちるためである。

一方、**通り道に乗らない設定は暗黙的にすら検証されない**。`cors()` は Supertest がブラウザではないため影響を受けず、`/api/health` は誰も叩かない。実際、`cors()` を削除しても 2.1 以降の 42 件は全て green のままだった（ブラウザからのアクセスは壊れているにもかかわらず）。この穴を塞ぐのが本節である。

| # | ケース | 期待結果 |
|---|---|---|
| A-1 | GET `/api/health` | 200、`{ok:true}` |
| A-2 | GET 未定義パス | 404 |
| A-3 | CORS ヘッダー | `access-control-allow-origin: *`（消すと 2.1 以降は素通りする） |
| A-4 | JSON ボディ解析 | `Content-Type: application/json` の body が届き zod の 400 に到達する |
| A-5 | 全リソースルーターのマウント | `/api/{projects,tasks,tags,statuses,stats}` が 404 にならない |

> カバレッジ 100% は「全行が**実行された**」を意味し、「全設定が**正しいと確認された**」ではない。`cors()` の行は実行されるためカバレッジには計上されるが、A-3 が無ければ検証はされていなかった。

### 2.1 `/api/projects`

| # | ケース | 期待結果 |
|---|---|---|
| P-1 | POST 正常（name のみ） | 201、`order` は末尾+1、`archived=false` |
| P-2 | POST name 空 | 400（zod） |
| P-3 | GET 一覧 | `archived=false` のみ、`order` 昇順、`_count.tasks` 付き |
| P-4 | GET `?includeArchived=true` | アーカイブ済みも含む |
| P-5 | PATCH `{archived:true}` | 200、以降 P-3 の一覧から消える |
| P-6 | PATCH `{archived:false}`（復元） | 200、一覧に再表示 |
| P-7 | PATCH 存在しない id | 404 |
| P-8 | DELETE | 204、配下タスクも Cascade で削除される（別クエリで 0 件確認） |
| P-9 | PATCH `/reorder` | 渡した id 順に `order` が 0..n-1 で再採番 |

### 2.2 `/api/tasks`

| # | ケース | 期待結果 |
|---|---|---|
| T-1 | POST 正常 | 201、`tags` は配列に整形、`order` 末尾+1 |
| T-2 | POST status 省略 | 先頭ステータス（order 最小）が自動採用 |
| T-3 | POST 不正な status（存在しない id） | 400 "Invalid status" |
| T-4 | POST 存在しない parentId | 400 "Parent task not found" |
| T-5 | POST tagIds 指定 | TaskTag が作成され、`tags` に反映 |
| T-6 | GET `?projectId=` なし | アーカイブ済みプロジェクトのタスクを除外 |
| T-7 | GET `?status=&priority=&tagId=&search=` | 各フィルタが AND で効く |
| T-8 | GET `?parentId=null` | 最上位タスクのみ |
| T-9 | GET `?search=` | title / description 部分一致 |
| T-10 | PATCH status 変更 | 200、値が反映 |
| T-11 | PATCH 不正な status | 400 |
| T-12 | PATCH tagIds | 既存 TaskTag を全削除して張り替え |
| T-13 | DELETE 親タスク | 子孫も Cascade 削除 |
| T-14 | PATCH `/reorder` | `{id,order,parentId?,projectId?}` が一括反映（1 トランザクション） |

#### 循環参照の検出（`/api/tasks/:id/move` → `isDescendantOrSelf`）

| # | ケース（A>B>C の階層） | 期待結果 |
|---|---|---|
| M-1 | C を B 配下へ移動（正常な付け替え） | 200 |
| M-2 | A を A 自身の配下へ | 400 "Cannot move a task under itself or its own subtask" |
| M-3 | A を C（自分の孫）の配下へ | 400（多段の子孫でも検出できること） |
| M-4 | A を無関係な別ツリー D 配下へ | 200 |
| M-5 | parentId=null へ（最上位化） | 200 |

> M-3 が `isDescendantOrSelf` の再帰（多段探索）を担保する中心ケース。

### 2.3 `/api/statuses`

| # | ケース | 期待結果 |
|---|---|---|
| S-1 | GET | `order` 昇順 |
| S-2 | POST | 201、`order` 末尾+1 |
| S-3 | PATCH label/color/isDone | 200、反映 |
| S-4 | PATCH `/reorder` | id 順に再採番 |
| S-5 | DELETE 使用中ステータス | 409「N 件のタスクで使用中」、件数が正しい |
| S-6 | DELETE 最後の 1 件 | 409「最後のステータスは削除できません」 |
| S-7 | DELETE 未使用かつ複数あるうちの 1 件 | 204 |

### 2.4 `/api/tags`

| # | ケース | 期待結果 |
|---|---|---|
| G-1 | POST | 201 |
| G-2 | POST 重複 name | 409 "Tag already exists" |
| G-3 | DELETE | 204、タスクからも解除（TaskTag Cascade） |

### 2.5 `/api/stats`（動的ステータス・アーカイブ）

前提データを固定して算出結果を検証する。

| # | ケース | 期待結果 |
|---|---|---|
| ST-1 | `total` | 全タスク数 |
| ST-2 | `byStatus` | 全ステータス id をキーに 0 埋め、件数集計 |
| ST-3 | `byPriority` | LOW/MEDIUM/HIGH/URGENT を 0 埋め集計 |
| ST-4 | `completionRate` | `isDone=true` のステータス合計 / total を小数第一位で丸め |
| ST-5 | 複数の isDone ステータス（完了＋取下げ） | 両方が「完了」として `completionRate` に加算される |
| ST-6 | `overdue` | `isDone=false` かつ dueDate < 現在。isDone なステータスは除外（時刻固定） |
| ST-7 | `dueSoon` | isDone=false かつ 現在〜+3日 |
| ST-8 | `?projectId=` なし | アーカイブ済みプロジェクトのタスクを集計から除外 |
| ST-9 | total=0 | `completionRate=0`（0 除算しない） |

> ST-5/ST-6 が「`isDone` 駆動」の要。`"DONE"` 決め打ちだと落ちる設計になっていることを保証する。

---

<a id="sec-3"></a>

## 3. クライアント ユニットテスト（純粋関数）

### 3.1 `utils/tree.ts`

| # | 関数 | ケース | 期待結果 |
|---|---|---|---|
| U-1 | `buildTaskTree` | フラットな `Task[]`（親子混在） | 正しいネスト構造、各階層 `order` 昇順 |
| U-2 | `buildTaskTree` | parentId が結果セットに存在しない（フィルタで親が欠落） | そのタスクはルート扱い（迷子にしない） |
| U-3 | `buildTaskTree` | 空配列 | `[]` |
| U-4 | `flattenWithDepth` | 3 階層ツリー | 深さ注釈付きで DFS 順に平坦化 |
| U-5 | `flattenNodes` | 同上 | `{node, depth}` 列、親→子の順 |
| U-6 | `countAll` | ネストツリー | 子孫を含む総数 |

---

<a id="sec-4"></a>

## 4. クライアント コンポーネントテスト（API はモック）

### 4.1 ドラッグ&ドロップのロジック（描画より振る舞い重視）

| # | 対象 | ケース | 期待結果 |
|---|---|---|---|
| C-1 | `TaskTree.onDragEnd` | 同一 parent 内で並べ替え | `reorder` が新しい order 配列で呼ばれる |
| C-2 | `TaskTree.onDragEnd` | 異なる parent 間のドラッグ | 何もしない（親跨ぎはフォームで行う仕様） |
| C-3 | `KanbanBoard` handleDragEnd | 同一カラム内 card→card | `reorder` のみ（status 変更なし） |
| C-4 | `KanbanBoard` handleDragEnd | 別カラムへドロップ | `updateTask({status})` ＋挿入位置で `reorder` |
| C-5 | `KanbanBoard` handleDragEnd | カラム空領域へドロップ | 末尾に挿入 |
| C-6 | `KanbanBoard` handleDragEnd | over=null | 何もしない |

> **役割分担**: DnD の実ポインタ操作は E2E（Playwright §5）で検証する。Vitest 側（C-1〜C-6）では `handleDragEnd` 相当の判定ロジックを純関数として切り出し、「どの入力（active/over）で reorder / updateTask がどう呼ばれるか」を高速に検証する。ドラッグの物理挙動＝Playwright、判定分岐＝Vitest、と二層で守る。

### 4.2 ガントチャート `GanttChart`

| # | ケース | 期待結果 |
|---|---|---|
| GA-1 | start/due 両方あり | バー幅 = 日数+1、開始位置が range 起点からの日数 |
| GA-2 | due のみ / start のみ | 1 日分のバー |
| GA-3 | 両方なし | バー非表示 |
| GA-4 | 日付範囲 | 全タスクの min/due と今日を内包し、前後に余白を付与 |
| GA-5 | 今日ライン | today が範囲内なら縦ラインの left 位置が正しい |

### 4.3 表示系・フォーム

| # | 対象 | ケース | 期待結果 |
|---|---|---|---|
| V-1 | `StatusBadge` | status を渡す | ラベル表示、色がスタイルに反映 |
| V-2 | StatsCards 優先度 | 並び順 | 緊急→高→中→低（降順） |
| V-3 | `FilterBar` | ステータス選択 | `onChange` が status 付きで発火 |
| V-4 | `TaskFormModal` | 送信 | title 空なら送信不可、開始日/期限/タグ/親が値に含まれる |
| V-5 | `ProjectsList` | アーカイブ操作 | 「アーカイブ」で `updateProject({archived:true})`、チェックで一覧再取得 |
| V-6 | `Sidebar` | 描画 | 旧「+ 追加」が無い／「📁 プロジェクト一覧」リンクがある |
| V-7 | `Dashboard` | プロジェクト数カード | 非アーカイブ件数を表示 |

---

<a id="sec-5"></a>

## 5. E2E（Playwright）

`npm run test:e2e` で実行。`playwright.config.ts` の `webServer` で API（3001）と Vite（5173）を専用 DB 付きで自動起動し、テスト後に破棄する。DnD は Playwright の実ポインタ操作（`dragTo` / `mouse.down→move→up`）で検証できるため、E2E がドラッグ系の本命の検証手段となる。

| # | シナリオ | 主な検証点 |
|---|---|---|
| E-1 | プロジェクト作成 → タスク作成 → サブタスク作成 | ツリーに階層表示される |
| E-2 | カンバンでカードを別カラムへドラッグ | ステータス変更がリロード後も永続 |
| E-3 | カンバンで同一カラム内を並べ替え | 並び順がリロード後も永続 |
| E-4 | 設定でステータス追加 | タスクフォーム/フィルタ/カンバン列に反映 |
| E-5 | ステータス削除（使用中） | エラー表示され削除されない |
| E-6 | プロジェクトをアーカイブ → 復元 | サイドバー/ダッシュボードから消え、復元で戻る |
| E-7 | ガント表示 | バーが開始日〜期限に描画される |

### 実行環境の注意

- Playwright ブラウザのインストール（`npx playwright install`）が初回に必要。
- 各テストは独立させる（`beforeEach` で API 経由の状態初期化、または専用 DB を毎回リセット）。UI 経由で作ったデータに後続テストが依存しない。
- 現時点の実装は DnD の「別 parent 間ドラッグ」を無効化している（ツリー）等、UI 仕様に沿った期待値にする。

---

<a id="sec-6"></a>

## 6. 優先度と網羅の考え方

- **最優先（回帰が致命的）**: M-1〜M-5（循環参照）、ST-4〜ST-9（統計・isDone）、S-5/S-6（削除制約）、P-3〜P-6・T-6・ST-8（アーカイブ除外）。
- **見落としやすい**: A-1〜A-5（配線）。他テストの通り道に乗らない設定は、壊れても全テストが green のままになるため、専用テストでしか守れない。
- **次点**: DnD ロジック（C-1〜C-6）、tree ユニット（U-1〜U-6）。
- **カバレッジ目安**: サーバー routes は分岐網羅を重視、クライアントは純ロジックと主要コンポーネントのハッピーパス＋境界。

<a id="sec-7"></a>

## 7. 前提・留意

- テストは専用 DB を使い、開発用 `dev.db` を触らない（Vitest→`server/test.db`、Playwright→`server/e2e.db`）。
- 破壊的シード（`npm run seed`）は開発用 `dev.db` を対象にするため、テスト実行とは独立。

<a id="sec-8"></a>

## 8. テスト分担表（ファイル × テスト種別）

各ソースファイルをどのテスト種別で担保するかの一覧。各種別の詳細な定義とツール構成は [§1 テスト方針](#sec-1) を参照。

### 凡例

| テスト種別 | 意味 |
|---|---|
| **UT** | 単体（Vitest）。隔離してロジック/表示を検証 |
| **統合** | API を HTTP ＋ 実 DB で検証（Vitest + Supertest） |
| **E2E** | 実ブラウザで UI→API→DB を通しで検証（Playwright） |
| **(間接)** | 専用テストは持たず、他の経路でカバーされる |
| **—** | テスト対象外 |

**実装状態** — ✅ 実装済 / △ 一部のみ / ⬜ 未実装 / — 対象外

### 判断の指針

```
そのファイルは…
├─ 入力→出力が決まる純粋な処理？          → UT
├─ 表示だけ / フォームの検証ロジック？        → UT（描画確認が要るなら E2E 併用）
├─ DB の制約・集計・トランザクションが本質？   → 統合
└─ 画面をまたぐ操作・遷移・ドラッグ・永続化？  → E2E
```

原則: **ロジックは UT に寄せ、UI の通しフローは E2E**。UI を重厚に UT するより、ロジックを純関数へ切り出して UT ＋ 主要フローを E2E、が費用対効果が高い。

### テスト分担表

#### サーバー `server/src/`

| ファイル | テスト種別 | 実装状態 | 理由 |
|---|---|---|---|
| `routes/projects.ts` | 統合 | ✅ | CRUD・アーカイブ除外・reorder |
| `routes/tasks.ts` | 統合 | ✅ | フィルタ・reorder・循環参照（`isDescendantOrSelf`） |
| `routes/tags.ts` | 統合 | ✅ | 一意制約(409)・カスケード解除 |
| `routes/stats.ts` | 統合 | ✅ | 集計・isDone 駆動 |
| `routes/statuses.ts` | 統合 | ✅ | 削除制約（使用中/最後の1件） |
| `app.ts` | 統合 | ✅ | 配線の検証（§2.0 A-1〜A-5）。cors / health は他テストの通り道に乗らないため専用テストが要る |
| `db.ts` / `constants.ts` | 統合(間接) | ✅ | 統合テスト経由で通過 |
| `index.ts` | — | — | `listen` の起動コード |
| `prisma/seed.ts` | — | — | 開発用データ投入 |

#### クライアント `client/src/` — UT でやるべき

| ファイル | テスト種別 | 実装状態 | 備考 |
|---|---|---|---|
| `utils/tree.ts` | UT | ✅ | 純関数 |
| `utils/dnd.ts` | UT | ✅ | ドラッグ判定を純関数化済 |
| `components/StatsCards.tsx` | UT | ✅ | 優先度並び順など表示ロジック |
| `components/Badges.tsx` | UT | ⬜ | 表示専用（ラベル・色） |
| `components/FilterBar.tsx` | UT | ⬜ | 選択で `onChange` 発火 |
| `components/TaskFormModal.tsx` | UT | ⬜ | 送信可否・値組み立て（ロジック抽出推奨） |
| `components/ProjectFormModal.tsx` | UT | ⬜ | 同上 |
| `components/ConfirmDialog.tsx` | UT | ⬜ | open 制御・確定/取消 |
| `api/client.ts` | UT | ⬜ | `fetch` をモックしエラー整形を検証 |

#### クライアント — UT + E2E の併用

| ファイル | 分担 | 実装状態 |
|---|---|---|
| `components/GanttChart.tsx` | 日付範囲・バー幅の計算=UT（要抽出）／描画=E2E | ⬜UT / △E2E |
| `components/KanbanBoard.tsx` | 判定=UT(`dnd.ts`)／ドラッグ挙動=E2E | ✅ / ✅ |
| `components/TaskTree.tsx`・`TaskNode.tsx` | 判定=UT(`dnd.ts`)／並び替え=E2E | ✅ / ⬜ |

#### クライアント — E2E でやるべき

| ファイル | テスト種別 | 実装状態 | 理由 |
|---|---|---|---|
| `pages/ProjectsList.tsx` | E2E | ✅ | アーカイブ/復元フロー |
| `pages/Settings.tsx` | E2E | ✅ | ステータス追加/削除制約 |
| `pages/ProjectView.tsx` | E2E | △ | ツリー/カンバン/ガント切替・フィルタ |
| `pages/Dashboard.tsx` | E2E | ⬜ | 集計カード・期限一覧の表示 |
| `components/Sidebar.tsx` | E2E | △ | ナビゲーション |
| `api/*.ts`（React Query フック） | E2E(間接) | ✅ | 実サーバー通信で担保。UT化はコスパ低 |
| `components/Layout.tsx` | — | — | Outlet 配置のみ |
