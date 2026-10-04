# テスト設計書 — TaskMaster

本書は TaskMaster のテスト方針とテストケースを定義する。設計に対応するテストは実装済みで、全て green（ユニット/統合 133 件 + E2E 5 件）。

## 目次

- [実行方法](#sec-run)
- [1. テスト方針](#sec-1)
- [2. サーバー API 統合テスト](#sec-2)
- [3. ユニットテスト（純粋関数）](#sec-3)
- [4. クライアント コンポーネントテスト（API はモック）](#sec-4)
- [5. E2E（Playwright）](#sec-5)
- [6. 優先度と網羅の考え方](#sec-6)
- [7. 前提・留意](#sec-7)
- [8. テスト分担表（ファイル × テスト種別）](#sec-8)

<a id="sec-run"></a>

## 実行方法

```bash
npm test           # = test:unit（Vitest: server 78 + client 55）
npm run test:e2e   # Playwright E2E（server/e2e.db を自動初期化して起動）
```

初回のみ `npx playwright install chromium` が必要。ユニットは `server/test.db`、E2E は `server/e2e.db` を使い、開発用 `dev.db` には触れない。

<a id="sec-1"></a>

## 1. テスト方針

本章ではテスト全体の方針 — レイヤー構成・採用ツール・スクリプトの分離・ファイル配置・原則 — を定める。
**個々のテストケースは §2〜§5 に、どこから優先的に固めるかは §6 に記述する**（下表の「詳細」列から辿れる）。ファイル単位でどのテストを書くかの一覧は [§8 テスト分担表](#sec-8) を参照。

### レイヤーと目的

| レイヤー | 対象 | 目的 | 詳細 |
|---|---|---|---|
| ユニット（純粋関数） | `client/src/utils/{tree,dnd,gantt}.ts`、`server/src/schemas.ts` — 副作用のないロジック | 変換・計算・検証規則の正しさを高速に検証 | [§3](#sec-3) |
| API 統合 | `server/src/routes/*.ts` + Prisma + テスト用 SQLite（`server/tests/integration/`） | DB の挙動込みでしか守れないもの（制約・カスケード・集計・配線）を検証 | [§2](#sec-2) |
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
│  ├─ vitest.config.ts         # env で DATABASE_URL="file:./test.db" を注入。include は tests/ 配下
│  ├─ tsconfig.json            # 型チェック・ESLint 用（src と tests）
│  ├─ tsconfig.build.json      # 本番ビルド用（src のみ。テストは dist/ に出さない）
│  ├─ src/                     # 本番コードのみ（テストは置かない）
│  │  ├─ app.ts                # createApp()（listen と分離し Supertest から使う）
│  │  └─ schemas.ts            # 全ルーターの zod スキーマ（export して単体テスト可能に）
│  └─ tests/
│     ├─ unit/
│     │  └─ schemas.test.ts    # zod スキーマの境界値（§3.2・DB 不要 = 高速）
│     ├─ integration/          # API 統合テスト（Supertest + test.db）
│     │  ├─ app.test.ts        # 配線の検証（health / 404 / CORS / json / mount）
│     │  ├─ errors.test.ts     # エラー応答の形式・メッセージ
│     │  └─ projects / tasks / statuses / tags / holidays / stats .test.ts
│     └─ helpers/
│        ├─ setup.ts           # test.db を作り直して migrate、各テスト前に全行削除
│        └─ factories.ts       # seedStatuses / makeProject / makeTask
└─ client/
   ├─ vitest.config.ts         # environment: "jsdom"、Vite 設定を継承
   └─ src/
      ├─ test/setup.ts         # RTL matchers 登録 / 各テスト後に cleanup
      ├─ test/factories.ts     # makeTask
      ├─ utils/tree.test.ts    # 純粋関数ユニット
      ├─ utils/dnd.test.ts     # ドラッグ判定ロジック
      ├─ utils/gantt.test.ts   # ガントの日付グリッド計算
      └─ components/*.test.tsx # コンポーネント
```

- **切り分けの境界**: `e2e/` 配下＝Playwright、それ以外＝Vitest。Vitest の `include` は、server は `tests/` 配下、client は `src/` 配下に限定し、Playwright の `testDir` は `e2e/` に限定して、互いを拾わないようにする。
- **置き場所の規則**: server のテストは `server/tests/`（`src/` には本番コードだけを置く）。client の単体テストは、対象のソースの隣に `*.test.ts(x)` で置く（Vite は読み込まれないファイルを出力に含めない）。本番ビルドにテストが混ざらないよう、server の本番ビルドは `tsconfig.build.json`（`src` のみ）を使う。
- **テスト用 DB**: サーバー Vitest は `vitest.config.ts` の `test.env` で `DATABASE_URL`（`test.db`）を注入する。`db.ts` が PrismaClient を生成する前に値が確定している必要があるため、`.env` 読み込みではなくこの方式を採る。Playwright は `playwright.config.ts` の `webServer.env` で `e2e.db` を指定する。いずれも開発用 `dev.db` に触れない。

### 原則

- API テストは各テスト前に DB を初期化し、テスト間で状態を共有しない（順序非依存）。
- 日付が絡むテスト（期限超過・ガント範囲）は現在時刻を固定（`vi.setSystemTime`）。
- 「完了」判定は `status.isDone` を根拠にする（`"DONE"` 文字列をハードコードしない）ことをテストでも保証する。

---

<a id="sec-2"></a>

## 2. サーバー API 統合テスト

### 本章で何を検証するか

Supertest で `createApp()` にリクエストを送り、**Express → zod → Prisma → SQLite → レスポンス**の全経路を本物のまま通す。モックは使わない。

```
テスト → Supertest → Express（ルーティング / json / cors）
                        → zod（型・必須・上限の検証）
                          → Prisma → SQLite（test.db）
テスト ← status / body ←─────────────────────┘
        ＋ Prisma で DB の実際の状態も直接確認
```

**統合テストでしか守れないもの**を主眼に置く。いずれも DB の挙動が本質で、モックに置き換えると「モックが期待通り呼ばれたか」を確認するだけになり、検証の意味が失われる。

| 検証対象 | 例 | 該当 |
|---|---|---|
| カスケード削除 | プロジェクトを消すと配下タスクも消える | P-8 / T-13 / G-3 |
| 外部キー制約 | 使用中のステータスは削除できない | S-5 |
| トランザクション | 並び替えの一括更新が 1 単位で反映される | P-9 / T-14 |
| 集計クエリ | 完了率・期限超過の算出（`isDone` 駆動） | ST-1〜ST-9 |
| 再帰的な DB 探索 | 循環参照の検出（子孫を辿る） | M-1〜M-5 |
| ルーティング・配線 | パス、`express.json()`、`cors()` | A-1〜A-5 |

逆に、**DB を必要としない検証は本章に置かない**。zod スキーマの網羅（境界値）は純粋関数として単体テストへ寄せている（2.6 および [§3.2](#sec-3) を参照）。

### 2.0 アプリ配線（`app.ts`）

各リソースのテスト（2.1 以降）は、リクエストの通り道にある設定 — ルーターのマウントパス、`express.json()` — を**暗黙的に**検証する。マウントパスを間違えれば 404 になり、各テストが落ちるためである。

一方、**通り道に乗らない設定は暗黙的にすら検証されない**。`cors()` は Supertest がブラウザではないため影響を受けず、`/api/health` は誰も叩かない。実際、`cors()` を削除しても 2.1 以降のテストは全て green のままだった（ブラウザからのアクセスは壊れているにもかかわらず）。この穴を塞ぐのが本節である。

なお `/api/health` は Playwright の `webServer.url` が起動待ちに使うため、削除すると E2E も起動しない。

| # | ケース | 期待結果 |
|---|---|---|
| A-1 | GET `/api/health` | 200、`{ok:true}` |
| A-2 | GET 未定義パス | 404 |
| A-3 | CORS ヘッダー | `access-control-allow-origin: *`（消すと 2.1 以降は素通りする） |
| A-4 | JSON ボディ解析 | `Content-Type: application/json` の body が届き zod の 400 に到達する |
| A-5 | 全リソースルーターのマウント | `/api/{projects,tasks,tags,statuses,stats}` が 404 にならない |

> カバレッジ 100% は「全行が**実行された**」を意味し、「全設定が**正しいと確認された**」ではない。`cors()` の行は実行されるためカバレッジには計上されるが、A-3 が無ければ検証はされていなかった。

### 2.1 `/api/projects`

各行の「リクエスト」は HTTP メソッド + パス + パラメータの所在（リクエストボディ / クエリ文字列 / パスパラメータ）を示す。

| # | リクエスト | 条件 | 期待結果 |
|---|---|---|---|
| P-1 | POST `/api/projects` | リクエストボディに `name` のみ指定 | 201。レスポンスの `order` は既存の最大 +1、`archived` は既定値 false |
| P-2 | POST `/api/projects` | リクエストボディの `name` が空文字 | 400（zod のバリデーションエラー）。境界値の網羅は §3.2（単体テスト） |
| P-3 | GET `/api/projects` | クエリ文字列なし | 200。`archived=false` のプロジェクトのみを `order` 昇順で返し、各要素に `_count.tasks` を含む |
| P-4 | GET `/api/projects` | クエリ文字列 `includeArchived=true` | 200。アーカイブ済みのプロジェクトも含めて返す |
| P-5 | PATCH `/api/projects/:id` | パスパラメータに既存 id、リクエストボディに `archived: true` | 200。以降 P-3（クエリなしの GET）の結果から除外される |
| P-6 | PATCH `/api/projects/:id` | 同上、リクエストボディに `archived: false`（復元） | 200。P-3 の結果に再び現れる |
| P-7 | PATCH `/api/projects/:id` | パスパラメータが存在しない id | 404 |
| P-8 | DELETE `/api/projects/:id` | パスパラメータに、タスクを持つプロジェクトの id | 204。配下のタスクも Cascade 削除される（Prisma で件数 0 を確認） |
| P-9 | PATCH `/api/projects/reorder` | リクエストボディの `ids` に並べ替え後の id 配列 | 200。渡した順に `order` が 0..n-1 で再採番される |

### 2.2 `/api/tasks`

| # | リクエスト | 条件 | 期待結果 |
|---|---|---|---|
| T-1 | POST `/api/tasks` | リクエストボディに `title` と `projectId` | 201。レスポンスの `tags` は配列に整形され、`order` は同一階層の最大 +1 |
| T-2 | POST `/api/tasks` | リクエストボディの `status` を省略 | 201。`order` が最小のステータスが自動採用される |
| T-3 | POST `/api/tasks` | リクエストボディの `status` が Status テーブルに存在しない id | 400 "Invalid status"（zod ではなくルート内の存在チェック） |
| T-4 | POST `/api/tasks` | リクエストボディの `parentId` が存在しないタスク id | 400 "Parent task not found" |
| T-5 | POST `/api/tasks` | リクエストボディの `tagIds` に既存タグ id | 201。TaskTag が作成され、レスポンスの `tags` に反映 |
| T-6 | GET `/api/tasks` | クエリ文字列に `projectId` を指定しない | 200。アーカイブ済みプロジェクトに属するタスクを除外 |
| T-7 | GET `/api/tasks` | クエリ文字列に `status` と `priority` を同時指定 | 200。各フィルタが AND 条件で効く |
| T-8 | GET `/api/tasks` | クエリ文字列 `parentId=null` | 200。最上位タスク（`parentId` が null）のみ |
| T-9 | GET `/api/tasks` | クエリ文字列 `search` に部分文字列 | 200。`title` / `description` の部分一致で絞り込む |
| T-10 | PATCH `/api/tasks/:id` | リクエストボディの `status` に既存ステータス id | 200。値が反映される |
| T-11 | PATCH `/api/tasks/:id` | リクエストボディの `status` が存在しない id | 400 |
| T-12 | PATCH `/api/tasks/:id` | リクエストボディの `tagIds` を別のタグに差し替え | 200。既存の TaskTag を全削除して張り替える |
| T-13 | DELETE `/api/tasks/:id` | パスパラメータに、子を持つ親タスクの id | 204。子孫タスクも Cascade 削除される |
| T-14 | PATCH `/api/tasks/reorder` | リクエストボディの `items` に `{id, order}` の配列 | 200。1 トランザクションで一括反映される |

#### 循環参照の検出（`/api/tasks/:id/move` → `isDescendantOrSelf`）

前提の階層: A > B > C（A の子が B、B の子が C）と、無関係な最上位タスク D。いずれも PATCH `/api/tasks/:id/move`。

| # | リクエスト | 条件 | 期待結果 |
|---|---|---|---|
| M-1 | PATCH `/api/tasks/C/move` | リクエストボディの `parentId` に B の id（正常な付け替え） | 200 |
| M-2 | PATCH `/api/tasks/A/move` | リクエストボディの `parentId` に A 自身の id | 400 "Cannot move a task under itself or its own subtask" |
| M-3 | PATCH `/api/tasks/A/move` | リクエストボディの `parentId` に C（A の孫）の id | 400。多段の子孫でも検出できること |
| M-4 | PATCH `/api/tasks/A/move` | リクエストボディの `parentId` に無関係な D の id | 200 |
| M-5 | PATCH `/api/tasks/C/move` | リクエストボディの `parentId` が null（最上位化） | 200。`parentId` が null になる |

> M-3 が `isDescendantOrSelf` の再帰（多段探索）を担保する中心ケース。

### 2.3 `/api/statuses`

| # | リクエスト | 条件 | 期待結果 |
|---|---|---|---|
| S-1 | GET `/api/statuses` | — | 200。`order` 昇順で返す |
| S-2 | POST `/api/statuses` | リクエストボディに `label` | 201。`order` は既存の最大 +1 |
| S-3 | PATCH `/api/statuses/:id` | リクエストボディに `label` と `isDone` | 200。値が反映される |
| S-4 | PATCH `/api/statuses/reorder` | リクエストボディの `ids` に並べ替え後の id 配列 | 200。渡した順に再採番される |
| S-5 | DELETE `/api/statuses/:id` | パスパラメータに、2 件のタスクが使用中のステータス id | 409。エラーメッセージに使用中の件数（2）を含む |
| S-6 | DELETE `/api/statuses/:id` | 他を全て削除し、残り 1 件になった状態でその id | 409「最後のステータスは削除できません」 |
| S-7 | DELETE `/api/statuses/:id` | 未使用かつ他にもステータスが存在する id | 204 |

### 2.4 `/api/tags`

| # | リクエスト | 条件 | 期待結果 |
|---|---|---|---|
| G-1 | POST `/api/tags` | リクエストボディに `name` | 201 |
| G-2 | POST `/api/tags` | リクエストボディの `name` が既存タグと重複（unique 制約違反） | 409 "Tag already exists" |
| G-3 | DELETE `/api/tags/:id` | パスパラメータに、タスクへ付与済みのタグ id | 204。TaskTag も Cascade 削除され、タスクから解除される |

### 2.5 `/api/stats`（動的ステータス・アーカイブ）

前提データを固定して算出結果を検証する。

いずれも GET `/api/stats`。日付が絡むケースは `vi.setSystemTime` で現在時刻を固定する。

| # | 条件 | 期待結果（レスポンスボディ） |
|---|---|---|
| ST-1 | タスク 4 件を投入 | `total` が 4 |
| ST-2 | 同上 | `byStatus` が全ステータス id をキーに 0 埋めされ、件数が集計される |
| ST-3 | 同上 | `byPriority` が LOW/MEDIUM/HIGH/URGENT を 0 埋めして集計される |
| ST-4 | 4 件中 2 件が `isDone=true` のステータス | `completionRate` が 50（小数第一位で丸め） |
| ST-5 | `isDone=true` のステータスが 2 種（完了・取下げ）、3 件中 2 件がそれら | `completionRate` が 66.7。両方が「完了」として加算される |
| ST-6 | 前日期限 1 件（未完了）、当日期限 1 件、前日期限 1 件（完了扱い）、未来 1 件 | `overdue` が 1（日付単位。当日期限は超過ではない）。`isDone=true` のステータスは除外される |
| ST-7 | 当日・3 日後・4 日後・前日の期限各 1 件（未完了）、1 日後 1 件（完了扱い） | `dueSoon` が 2（未完了かつ本日〜3 日後の 4 日間のみ） |
| ST-8 | クエリ文字列に `projectId` を指定せず、アーカイブ済みプロジェクトにもタスクが存在 | `total` が非アーカイブ分のみ（アーカイブ済みを除外） |
| ST-9 | タスクが 0 件 | `total` が 0、`completionRate` が 0（0 除算しない） |

> ST-5/ST-6 が「`isDone` 駆動」の要。`"DONE"` 決め打ちだと落ちる設計になっていることを保証する。

### 2.6 バリデーション（zod スキーマの境界値）

zod スキーマ自体の網羅的な検証は**単体テストに寄せている**（[§3.2](#sec-3)）。スキーマは純粋関数であり、DB も HTTP も不要なためである。実測で 28 件が 8.7 秒（統合）から 31 件が 15 ミリ秒（単体）になった。

統合テスト側に残すのは、**「zod が HTTP 経路に実際に組み込まれているか」**を示す代表ケースのみ。

| # | 検証内容 | 場所 |
|---|---|---|
| P-2 | 不正なボディが 400 として返る（zod がルーターに繋がっている） | 2.1 |
| A-4 | `express.json()` が body を解析し、zod の 400 に到達する | 2.0 |

この 2 件が「配線」を、§3.2 の 31 件が「規則そのもの」を担保する二層構造とする。全ての境界値を HTTP 経由で確認するのは、同じ検証に約 580 倍の時間を払うことになるため行わない。

> T-3 / T-11（不正な `status`）は zod ではなく**ルート内の存在チェック**による 400 のため、単体テストではなく 2.2 に置く。`status` は `z.string()` で型だけを検証し、実在するかは Status テーブルへの問い合わせで確認している — DB が要るので統合テストの領分である。

---

<a id="sec-3"></a>

## 3. ユニットテスト（純粋関数）

対象は DB もネットワークも要らない純粋なロジックのみ。ミリ秒で終わり、結果が実行環境に左右されない。

サーバー側は**ロジックがルートハンドラ内に書かれ Prisma と密結合している**ため、単体テストできる対象がほぼ無い（純粋関数はごく一部）。唯一切り出せた zod スキーマを 3.2 で扱う。クライアント側は `tree.ts` / `dnd.ts` を意図的に純関数として抽出してあり、3.1 / §4.1 が対象。

### 3.1 `client/src/utils/tree.ts`

| # | 関数 | ケース | 期待結果 |
|---|---|---|---|
| U-1 | `buildTaskTree` | フラットな `Task[]`（親子混在） | 正しいネスト構造、各階層 `order` 昇順 |
| U-2 | `buildTaskTree` | parentId が結果セットに存在しない（フィルタで親が欠落） | そのタスクはルート扱い（迷子にしない） |
| U-3 | `buildTaskTree` | 空配列 | `[]` |
| U-4 | `flattenWithDepth` | 3 階層ツリー | 深さ注釈付きで DFS 順に平坦化 |
| U-5 | `flattenNodes` | 同上 | `{node, depth}` 列、親→子の順 |
| U-6 | `countAll` | ネストツリー | 子孫を含む総数 |

### 3.2 `server/src/schemas.ts`（zod スキーマ）

全ルーターのリクエストボディ用スキーマを `schemas.ts` に集約して export し、**スキーマを直接呼んで**検証する（HTTP も DB も介さない）。ルーター側は同じスキーマを import して使うため、テストと本番で同一の定義を共有する。

**方針**: 上限がある項目は**上限ちょうど（合格）と上限超過（不合格）を対で**置く。片方だけでは境界がずれていても気づけないが、対にすることで境界の位置が特定できる。下限がある項目は下限未満・下限ちょうども確認する。

| エンドポイントの用途 | 項目 | 制約 |
|---|---|---|
| プロジェクト作成 | `name` | string、1〜200 文字、必須 |
| プロジェクト作成 | `description` | string、最大 2000 文字、任意 |
| プロジェクト更新 | `archived` | boolean、任意 |
| タスク作成 | `title` | string、1〜300 文字、必須 |
| タスク作成 | `description` | string、最大 5000 文字、任意 |
| タスク作成 | `projectId` | string、必須 |
| タスク作成 | `priority` | enum（LOW / MEDIUM / HIGH / URGENT）、任意 |
| タスク作成 | `startDate` / `dueDate` | ISO8601 datetime または null、任意 |
| タスク作成 | `tagIds` | string の配列、任意 |
| タスク並び替え | `items[].order` | 整数、必須 |
| タグ作成 | `name` | string、1〜50 文字、必須 |
| ステータス作成 | `label` | string、1〜50 文字、必須 |
| ステータス作成 | `isDone` | boolean、任意 |

| # | 対象スキーマ | 条件 | 期待結果 |
|---|---|---|---|
| Z-1 | `projectCreateSchema` | `name` を含めない（必須項目の欠落） | 不合格 |
| Z-2 | `projectCreateSchema` | `name` が空文字（0 文字＝下限 1 未満） | 不合格 |
| Z-3 | `projectCreateSchema` | `name` が 1 文字（下限ちょうど） | 合格 |
| Z-4 | `projectCreateSchema` | `name` が 200 文字（上限ちょうど） | 合格 |
| Z-5 | `projectCreateSchema` | `name` が 201 文字（上限超過） | 不合格 |
| Z-6 | `projectCreateSchema` | `name` が文字列でない（数値 123） | 不合格 |
| Z-7 | `projectCreateSchema` | `description` が 2000 文字（上限ちょうど） | 合格 |
| Z-8 | `projectCreateSchema` | `description` が 2001 文字（上限超過） | 不合格 |
| Z-9 | `projectUpdateSchema` | `archived` が真偽値でない（文字列 "yes"） | 不合格 |
| Z-9b | `projectUpdateSchema` | 空オブジェクト（全項目が任意） | 合格 |
| Z-10 | `taskCreateSchema` | `title` が空文字（下限 1 未満） | 不合格 |
| Z-11 | `taskCreateSchema` | `title` が 300 文字（上限ちょうど） | 合格 |
| Z-12 | `taskCreateSchema` | `title` が 301 文字（上限超過） | 不合格 |
| Z-13 | `taskCreateSchema` | `description` が 5000 文字（上限ちょうど） | 合格 |
| Z-14 | `taskCreateSchema` | `description` が 5001 文字（上限超過） | 不合格 |
| Z-15 | `taskCreateSchema` | `projectId` を含めない（必須項目の欠落） | 不合格 |
| Z-16 | `taskCreateSchema` | `priority` が enum 外の値（"SUPER"） | 不合格 |
| Z-17 | `taskCreateSchema` | `priority` が enum の 4 値それぞれ | いずれも合格 |
| Z-18 | `taskCreateSchema` | `dueDate` が ISO8601 でない（"2026-07-14" — 日付のみ） | 不合格 |
| Z-19 | `taskCreateSchema` | `dueDate` が null（nullable として許容） | 合格 |
| Z-19b | `taskCreateSchema` | `dueDate` が ISO8601 datetime | 合格 |
| Z-20 | `taskCreateSchema` | `tagIds` が配列でない（文字列） | 不合格 |
| Z-21 | `taskReorderSchema` | `items[].order` が整数でない（1.5） | 不合格 |
| Z-21b | `taskReorderSchema` | `items[].order` が整数（0） | 合格 |
| Z-22 | `tagCreateSchema` | `name` が空文字（下限 1 未満） | 不合格 |
| Z-23 | `tagCreateSchema` | `name` が 50 文字（上限ちょうど） | 合格 |
| Z-24 | `tagCreateSchema` | `name` が 51 文字（上限超過） | 不合格 |
| Z-25 | `statusCreateSchema` | `label` が空文字（下限 1 未満） | 不合格 |
| Z-26 | `statusCreateSchema` | `label` が 50 文字（上限ちょうど） | 合格 |
| Z-27 | `statusCreateSchema` | `label` が 51 文字（上限超過） | 不合格 |
| Z-28 | `statusCreateSchema` | `isDone` が真偽値でない（文字列 "true"） | 不合格 |

> **なぜ統合ではなく単体か**: 同じ 28 ケースを HTTP 経由で確認していた時期は 8.7 秒（1 件あたり約 310ms — DB リセット + リクエスト + ルーティング + Prisma 接続を毎回払う）かかっていた。スキーマを直接呼ぶ形にして 31 件が 15ms になった（約 580 倍）。検証内容は同じで、コストだけが減っている。
>
> なお、サーバーの Vitest 設定は `setupFiles` を持たない。DB 初期化は各統合テストが `import "../test/setup.js"` で明示的に取り込む方式とし、DB を使わない本節がその代償を払わないようにしている。

### 3.3 `client/src/utils/gantt.ts`（日付グリッド計算）

ガントチャートの日付計算をコンポーネントから純関数として切り出したもの。`today` は引数で受け取る設計とし、時計を読まないためフェイクタイマー無しで決定的に検証できる。描画そのものは E2E（E-7）が担保する。

| # | 関数 | ケース | 期待結果 |
|---|---|---|---|
| GA-1 | `computeBar` | 開始日と期限の両方あり | `spanDays` は両端を含む日数、`offsetDays` は range 起点からの日数 |
| GA-1b | `computeBar` | 開始日と期限が同日 | 1 日分 |
| GA-2a | `computeBar` | 期限のみ | 1 日分 |
| GA-2b | `computeBar` | 開始日のみ | 1 日分 |
| GA-3 | `computeBar` | 両方なし | `null`（バーを描かない） |
| GA-3b | `computeBar` | range 起点より前の日付 | `offsetDays` が負値 |
| GA-4a | `computeRange` | 日付を持つタスク複数 | 最小〜最大を内包し、前 3 日・後 7 日の余白が付く |
| GA-4b | `computeRange` | today が全タスクより前 | today を含むまで範囲が広がる |
| GA-4c | `computeRange` | today が全タスクより後 | 同上 |
| GA-4d | `computeRange` | 日付を持つタスクが無い | today 起点の 2 週間 + 余白 |
| GA-4e | `computeRange` | タスクが空配列 | 破綻せず範囲を返す |
| GA-4f | `computeRange` | `days` の連続性 | 起点から 1 日刻みで並ぶ |
| GA-6 | `computeMonths` | 月をまたぐ日付列 | 月ごとのラベルと列数にまとめる |
| GA-6b | `computeMonths` | 空配列 | 空 |

> **タイムゾーンに注意**: `startOfDay` はローカル時刻で動くため、テストの入力は `"2026-07-10T00:00:00"`（`Z` 無し＝ローカル）で組み立て、検証も date-fns の `format` で行う。UTC の `toISOString()` で比較すると、実行環境のタイムゾーン次第で 1 日ずれる（実際に最初の実装で発生した）。

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

> ガントチャートの日付計算は `utils/gantt.ts` の純関数として切り出したため、コンポーネントテストではなく [§3.3](#sec-3) のユニットテストで扱う。描画自体は E2E（E-7）が担保する。

### 4.2 表示系・フォーム

いずれも API を `vi.mock` で差し替え、描画とユーザー操作を検証する。

| # | 対象 | ケース | 期待結果 |
|---|---|---|---|
| V-1 | `Badges`（`PriorityBadge` / `StatusBadge` / `TagPill`） | 各バッジを描画 | 優先度は日本語ラベル（低/中/高/緊急）、ステータス・タグは色がインラインスタイルに反映。`TagPill` は `onRemove` 指定時のみ削除ボタンを出し、クリックで呼ばれる |
| V-2 | `StatsCards` | 優先度の並び順 | 緊急→高→中→低（降順） |
| V-3 | `FilterBar` | ステータス / 優先度 / タグ / 検索の各操作 | `onChange` が該当キー付きで発火。「すべて」を選ぶと `undefined`。フィルタ未指定なら「クリア」非表示、押すと全条件リセット |
| V-4 | `TaskFormModal` | 送信・入力・変換 | `open=false` なら非描画。title が空/空白のみなら `onSubmit` を呼ばない。開始日/期限/優先度/親/タグが送信値に含まれる。`taskToFormValue` は日付を `YYYY-MM-DD` に切り出す |
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
- **境界値**: Z-1〜Z-28（zod）。上限ちょうどと上限超過を対で置き、境界が仕様どおりの位置にあることを特定する。片方だけでは境界のずれに気づけない。
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

| テスト種別 | 目的（何を担保するか） | 使用ツール |
|---|---|---|
| **UT** | 隔離してロジック/表示を検証する | Vitest（＋ React Testing Library / jsdom） |
| **統合** | API を HTTP ＋ 実 DB で通して検証する | Vitest + Supertest |
| **E2E** | 実ブラウザで UI→API→DB を通しで検証する | Playwright |
| **(間接)** | 専用テストは持たず、他の経路でカバーする | （上記のいずれかに相乗り） |
| **—** | テスト対象外 | — |

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
| `schemas.ts` | **UT** | ✅ | zod スキーマ（純粋関数）。境界値を §3.2 で網羅。DB も HTTP も不要 |
| `app.ts` | 統合 | ✅ | 配線の検証（§2.0 A-1〜A-5）。cors / health は他テストの通り道に乗らないため専用テストが要る |
| `db.ts` / `constants.ts` | 統合(間接) | ✅ | 統合テスト経由で通過 |
| `index.ts` | — | — | `listen` の起動コード |
| `prisma/seed.ts` | — | — | 開発用データ投入 |

#### クライアント `client/src/` — UT で実施する

| ファイル | テスト種別 | 実装状態 | 備考 |
|---|---|---|---|
| `utils/tree.ts` | UT | ✅ | 純関数（§3.1） |
| `utils/dnd.ts` | UT | ✅ | ドラッグ判定を純関数化済（§4.1） |
| `utils/gantt.ts` | UT | ✅ | 日付グリッド計算を純関数化済（§3.3） |
| `components/StatsCards.tsx` | UT | ✅ | 優先度並び順など表示ロジック（V-2） |
| `components/Badges.tsx` | UT | ✅ | ラベル・色・削除ボタン（V-1） |
| `components/FilterBar.tsx` | UT | ✅ | 各操作で `onChange` 発火・クリア（V-3） |
| `components/TaskFormModal.tsx` | UT | ✅ | 送信可否・値組み立て・`taskToFormValue`（V-4） |
| `components/ProjectFormModal.tsx` | UT | ⬜ | 送信可否・値組み立て |
| `components/ConfirmDialog.tsx` | UT | ⬜ | open 制御・確定/取消 |
| `api/client.ts` | UT | ⬜ | `fetch` をモックしエラー整形を検証 |

#### クライアント — UT + E2E を併用する

| ファイル | 分担 | 実装状態 |
|---|---|---|
| `components/GanttChart.tsx` | 日付範囲・バー幅の計算=UT(`gantt.ts`)／描画=E2E | ✅ / △ |
| `components/KanbanBoard.tsx` | 判定=UT(`dnd.ts`)／ドラッグ挙動=E2E | ✅ / ✅ |
| `components/TaskTree.tsx`・`TaskNode.tsx` | 判定=UT(`dnd.ts`)／並び替え=E2E | ✅ / ⬜ |

#### クライアント — E2E で実施する

| ファイル | テスト種別 | 実装状態 | 理由 |
|---|---|---|---|
| `pages/ProjectsList.tsx` | E2E | ✅ | アーカイブ/復元フロー |
| `pages/Settings.tsx` | E2E | ✅ | ステータス追加/削除制約 |
| `pages/ProjectView.tsx` | E2E | △ | ツリー/カンバン/ガント切替・フィルタ |
| `pages/Dashboard.tsx` | E2E | ⬜ | 集計カード・期限一覧の表示 |
| `components/Sidebar.tsx` | E2E | △ | ナビゲーション |
| `api/*.ts`（React Query フック） | E2E(間接) | ✅ | 実サーバー通信で担保。UT化はコスパ低 |
| `components/Layout.tsx` | — | — | Outlet 配置のみ |
