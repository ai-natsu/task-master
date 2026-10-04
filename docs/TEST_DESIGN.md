# テスト設計書 — TaskMaster（V2 デスクトップ版）

本書は V2（Python + CustomTkinter）のテスト方針と、テストの種類・置き場所・実行方法を定義する。
V1（Node / TypeScript の Web 版）の同名の文書と、テストの 4 層（単体・結合・UI 部品・E2E）を対応させている。

## 目次

- [実行方法](#実行方法)
- [1. テスト方針](#1-テスト方針)
- [2. ファイル配置](#2-ファイル配置)
- [3. 各層の内容](#3-各層の内容)
- [4. 入力値のチェック（文字数の上限）](#4-入力値のチェック文字数の上限)
- [5. 実行環境の注意](#5-実行環境の注意)
- [6. V1 との対応](#6-v1-との対応)

## 実行方法

リポジトリのルートで実行する。

```bash
python -m pytest                       # 全部（単体・結合・UI 部品・E2E）
python -m pytest -m "not gui and not e2e"   # 速い層だけ（単体・結合。画面を開かない）
python -m pytest tests/gui             # UI 部品のテスト
python -m pytest tests/e2e             # 画面遷移・操作の E2E
python -m ruff check .                 # 静的解析（CI のゲートと同じ）
```

- 単体・結合のテストは、一時ディレクトリの SQLite ファイルを使い、開発用の `taskmaster.db` には触れない。
- UI 部品と E2E は、画面（Tk のウィンドウ）を実際に開く。画面を開けない環境（ディスプレイが無い CI など）では、自動でスキップされる。

## 1. テスト方針

| 層 | 目的 | 置き場所 | マーカー |
|---|---|---|---|
| 単体（UT） | 純粋関数・文字列処理を、画面もデータベースも使わずに検証する | `tests/unit/` | なし |
| 結合 | データ層（`app/db`）を、実際の SQLite ファイルに対して検証する | `tests/integration/` | なし |
| UI 部品 | 部品の表示・入力・エラー表示を、実際の Tk ウィジェットで検証する（V1 の Playwright CT に相当） | `tests/gui/` | `gui` |
| E2E | アプリ全体を実際に動かし、画面遷移・モーダル・確認ダイアログを検証する（V1 の Playwright E2E に相当） | `tests/e2e/` | `e2e` |

- 画面に依存しない判断ロジック（ドラッグ判定・ガントの日付計算・期限判定など）は、純粋関数に切り出して単体テストで守る（`app/logic/`）。
- 画面（`app/ui/`）は、UI 部品と E2E のテストで守る。ピクセル単位の見た目やドラッグ操作の手触りは、自動テストの対象外とし、`python -m app.main` で手動確認する。
- 本番の配布物（`TaskMaster.exe`）には、テストを含めない。Nuitka は読み込まれるモジュールだけを同梱し、`tests/` は読み込まれない。

## 2. ファイル配置

```
tests/
├─ conftest.py             # conn（一時 DB）、statuses、app_window（実画面。GUI テスト共通）
├─ factories.py            # テストデータの作成（make_task など）
├─ gui_support.py          # GUI テストの補助（ウィジェット検索、タブのクリック、モーダルの取得）
├─ unit/                   # 単体テスト
│  ├─ test_tree / test_dnd / test_gantt / test_due     # app/logic の純粋関数
│  ├─ test_i18n / test_errors / test_ellipsis          # 辞書・エラー文言・省略表示
│  └─ test_release                                     # 配布 zip の組み立て
├─ integration/            # 結合テスト（データ層 + SQLite）
│  ├─ test_projects_db / test_tasks_db / test_statuses_db / test_tags_db
│  ├─ test_holidays_db / test_stats_db / test_app_settings_db
│  └─ test_validation_db                               # 文字数の上限・必須（§4）
├─ gui/                    # UI 部品のテスト（マーカー gui）
│  ├─ test_limits.py       # 入力欄の文字数の上限（上限ちょうど・超過・貼り付け）
│  └─ test_forms.py        # フォームの必須の赤字・上限、確認ダイアログ
└─ e2e/                    # 画面遷移・操作のテスト（マーカー e2e）
   └─ test_navigation.py   # 画面遷移表 No.1〜12、設定画面のエラー表示
```

## 3. 各層の内容

### 3.1 結合テスト（データ層）

循環参照の検出、統計（`isDone` 駆動・期限判定）、アーカイブ除外、ステータス削除制約（使用中・最後の 1 件）、祝日の CSV 取り込み、アプリ設定の保存を、一時 SQLite ファイルに対して検証する。

### 3.2 UI 部品のテスト（`tests/gui/`）

- 入力欄の文字数の上限：上限ちょうどまで入力できる、上限を超える入力はできない、貼り付けは上限で切り詰められる。
- フォーム：必須項目（タイトル・名前）が空・空白のみで保存すると、入力欄の下に赤字を出して赤枠にし、保存しない。入力し直すと消える。新しいタグ名が空のときの赤字。
- 確認ダイアログ：確定・キャンセル、確定ボタンの文言の差し替え。

### 3.3 E2E（`tests/e2e/`）

設計書（`docs/BASIC_DESIGN.md`）の画面遷移表に対応する。

| 画面遷移表 | テスト |
|---|---|
| No.1〜3 | サイドバーから、ダッシュボード・プロジェクト一覧・設定へ遷移する |
| No.4 | サイドバーのプロジェクト名から、プロジェクト詳細へ遷移する |
| No.6 | プロジェクト一覧の名前から、プロジェクト詳細へ遷移する |
| （表示切替） | プロジェクト詳細で、ツリー・カンバン・ガントを切り替える |
| No.7 | 「+ 新しいプロジェクト」でモーダルが開く／作成するとプロジェクト一覧に追加される |
| No.8 | 編集でモーダルが開き、既存の名前が入っている |
| No.9 | 「+ 新しいタスク」でモーダルが開く |
| No.12 | アーカイブ・復元・削除は確認ダイアログを経由し、キャンセルすると変わらない |
| （入力チェック） | 設定画面で、名前・名称が空のまま追加すると赤字が出る |

V1 にある、ブラウザの戻る/進む・URL の直接入力・再読み込みのテストは、V2 には該当する操作が無いため、対象外。

## 4. 入力値のチェック（文字数の上限）

仕様（`docs/BASIC_DESIGN.md` の入力項目）の上限を、定数 `LIMITS`（`app/constants.py`）にまとめ、次の 2 か所で守る。V1 の値と同じ。

| 項目 | 上限 | 画面（入力欄） | データ層（`app/db/validation.py`） |
|---|---|---|---|
| プロジェクト名 | 1〜200 文字 | 201 文字目は入力できない | `ValidationError` |
| プロジェクトの説明 | 2000 文字以内 | 同上 | 同上 |
| タスクのタイトル | 1〜300 文字 | 同上 | 同上 |
| タスクの詳細 | 5000 文字以内 | 同上 | 同上 |
| ステータス名・タグ名 | 1〜50 文字 | 同上 | 同上 |
| 祝日名（CSV 取り込みを含む） | 1〜100 文字 | 同上 | 同上 |

- 画面側：`app/ui/widgets/limits.py`（入力欄・複数行欄の上限、貼り付けの切り詰め）。
- データ層：画面を通らない経路（CSV の取り込みなど）でも仕様を守るために検査する。メッセージは「入力内容を確認してください（○○は1〜N文字）」（英語は「Please check your input (…)」）。
- テスト：`tests/gui/test_limits.py`、`tests/gui/test_forms.py`、`tests/integration/test_validation_db.py`。

## 5. 実行環境の注意

- UI 部品と E2E は、実際のウィンドウを開くため、実行中に画面が一瞬表示される。実行中は、キーボード・マウスの操作を控える。
- 同じ Python プロセスで 1 つの `AppWindow` を共有する（`tests/conftest.py` の `app_window`）。テストごとに、一意な名前のプロジェクトを作って、互いに影響しないようにしている。
- ディスプレイが無い環境では、`app_window` が画面を開けず、該当のテストをスキップする。

## 6. V1 との対応

| 層 | V1（Node / TypeScript） | V2（Python） |
|---|---|---|
| 単体 | Vitest（`*.test.ts`、ソースの隣） | pytest（`tests/unit/`） |
| 結合 | Vitest + Supertest（`server/tests/integration/`） | pytest + SQLite（`tests/integration/`） |
| UI 部品 | Playwright CT（`*.test.tsx`、ソースの隣） | pytest + Tk（`tests/gui/`） |
| E2E | Playwright（`e2e/`） | pytest + Tk（`tests/e2e/`） |
| 入力値の上限 | `client/src/constants/limits.ts`、サーバーの zod スキーマ | `app/constants.py` の `LIMITS`、`app/db/validation.py` |
| 実行コマンド | `npm test` / `npm run test:ct` / `npm run test:e2e` | `python -m pytest`（マーカーで層を選べる） |
