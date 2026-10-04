# システム設計書 — TaskMaster（V2 デスクトップ版）

本書は TaskMaster V2 のシステム方式（アーキテクチャ・ディレクトリ構成・ビルドと配布・運用）を定義する。外部から見える仕様（画面・インターフェース・データ・エラー）は `docs/BASIC_DESIGN.md` を参照。

## 目次

- [1. アーキテクチャ](#1-アーキテクチャ)
- [2. ディレクトリ構成](#2-ディレクトリ構成)
- [3. データの保存場所と初期化](#3-データの保存場所と初期化)
- [4. ビルドと配布](#4-ビルドと配布)
- [5. テストと静的解析](#5-テストと静的解析)
- [6. セキュリティ・性能・運用](#6-セキュリティ性能運用)

---

## 1. アーキテクチャ

### 1.1 レイヤー構成

| レイヤー | 場所 | 責務 |
|---|---|---|
| エントリポイント | `app/main.py` | 起動（外観・フォントの初期設定、DB 接続、初期ステータス投入、保存済み言語の読込、メインウィンドウ表示） |
| 画面 | `app/ui/` | CustomTkinter による画面・ウィジェット。画面遷移（`AppWindow.navigate()`）、ユーザー操作の受付、データ層の呼び出し |
| 純粋関数 | `app/logic/` | ツリー構築（`tree.py`）、D&D の決定（`dnd.py`）、ガントの座標計算（`gantt.py`）、期限判定（`due.py`）。UI・DB に依存しない |
| データ層 | `app/db/` | SQLite の直接操作。業務ルールの検証と業務例外の送出（`errors.py`） |
| 国際化 | `app/i18n.py`, `app/locales/` | 日本語原文をキーにした翻訳（`t()`）、言語の保持 |
| 定義 | `app/constants.py`, `app/models.py` | 区分値、データクラス |

依存の向きは「画面 → 純粋関数 / データ層」で、データ層・純粋関数は画面に依存しない。これにより、データ層と純粋関数は GUI なしで自動テストできる。

### 1.2 方式決定の理由
- **直接 `sqlite3`（ORM なし）**：単一プロセス・単一ユーザーで、テーブルが少なく、依存を増やさずに単一 exe にまとめるため。
- **日本語原文をキーにした翻訳辞書**：未翻訳の文言があっても原文のまま表示され画面が壊れない。辞書は Python モジュールにして、Nuitka でデータファイルを追加同梱する手間を避ける。
- **純粋関数の切り出し**：D&D・ガントのように GUI でしか確認しづらい処理を、判定ロジックだけ単体テスト可能にする。

---

## 2. ディレクトリ構成

```
app/
  main.py            # エントリポイント
  constants.py       # 区分値（優先度）、入力欄の文字数の上限（LIMITS）
  models.py          # データクラス
  i18n.py            # t()・言語の保持
  locales/en.py      # 英語辞書
  db/                # SQLite 直接操作のデータ層（schema.sql 含む）
  logic/             # ツリー構築・D&D 計画・ガント計算・期限判定・カレンダーの格子（純粋関数）
  ui/                # CustomTkinter 画面・ウィジェット
  assets/            # アイコン
tests/
  unit/              # 単体：app/logic・app/i18n などの純粋関数
  integration/       # 結合：app/db（一時 SQLite ファイル）
  gui/               # UI 部品：Tk ウィジェットの表示・入力チェック（マーカー gui）
  e2e/               # E2E：画面遷移・モーダル・確認ダイアログ（マーカー e2e）
packaging/
  build_exe.py       # Nuitka ビルドスクリプト
  build_zip.py       # 配布用 zip の作成（ビルド＋同梱物の整理）
  release.py         # zip に入れるファイルの作成（ライセンス表記の生成など）
  dist_files/        # zip に同梱する文書・サンプル（README.txt、holidays_sample.csv）
docs/                # 設計書
seed.py              # サンプルデータ投入（破壊的）
```

---

## 3. データの保存場所と初期化

### 3.1 保存場所
- データは `taskmaster.db`（SQLite ファイル）1 つ。配布 exe を使う場合は **exe と同じフォルダ**、開発時（`python -m app.main`）は **リポジトリ直下**。
- exe の場所は、Nuitka の onefile が設定する環境変数 `NUITKA_ONEFILE_PARENT`（ブートストラッププロセスの PID）から元の exe パスを解決する（Windows 専用。`app/db/connection.py` の `get_app_dir`）。

### 3.2 初期化
- 起動時に `connect()` が DB ファイルを開き、`PRAGMA user_version` を見てスキーマ（`schema.sql`）を一度だけ適用し、`PRAGMA foreign_keys` を有効にする。
- ステータスが 1 件も無い場合のみ、未着手／進行中／完了／取下げの 4 件を投入する（`ensure_default_statuses`。既存データがある場合は投入しない）。テストや `seed.py` は素のスキーマを前提にするため、この処理は起動時（`main.py`）からのみ呼ぶ。

### 3.3 バックアップ・移行
- `taskmaster.db` をコピーするだけでバックアップ・別 PC への移行ができる（アプリ終了後にコピーする）。
- データファイルは配布物に含めない。

---

## 4. ビルドと配布

### 4.1 ビルド
- `python packaging/build_exe.py` で `packaging/dist/TaskMaster.exe`（単一 exe、Windows）を生成する。初回は C コンパイラバックエンド `zig` のダウンロードで数分かかる。
- exe には Python 実行環境、CustomTkinter/Tk の資産、`app/db/schema.sql`、アイコンが含まれる（`--include-data-files` で明示的に同梱）。

### 4.2 配布
- 配布形態は **zip**。`python packaging/build_zip.py` で `packaging/dist/TaskMaster-<版>-win64.zip` を作る（exe のビルドを含む。ビルド済みなら `--skip-build` で zip だけ作れる）。
- 解凍すると `TaskMaster/` フォルダができ、その中の `TaskMaster.exe` をそのまま起動できる。データ（`taskmaster.db`）は初回起動時に同じフォルダへ作られるため、zip には含めない。
- 同梱物：

| ファイル | 内容 |
|---|---|
| `TaskMaster.exe` | アプリ本体 |
| `README.txt` | 利用者向けの案内（起動方法・データの保存場所・バックアップ・バージョンアップ・SmartScreen の警告について）。メモ帳で読めるよう UTF-8（BOM つき）・CRLF |
| `LICENSE.txt` | TaskMaster 自体のライセンス（AGPL-3.0）の全文。リポジトリの `LICENSE` から作る。メモ帳で読めるよう CRLF |
| `THIRD_PARTY_NOTICES.txt` | 利用ライブラリ（customtkinter・Pillow・charset-normalizer・darkdetect・packaging）の名前・版・ライセンス文書。ビルド時にインストール済みのパッケージから生成する。Python と Tcl/Tk は出典のみ |
| `holidays_sample.csv` | 祝日の取り込み例（2026 年分）。設定画面の「CSV から読み込む」で使える |

- TaskMaster 自体のライセンスは、AGPL-3.0 と商用ライセンスのデュアルライセンス（リポジトリ直下の `LICENSE` に AGPL-3.0 の全文、README の「ライセンス」に商用ライセンスの案内）。
- 対応 OS は Windows。Mac 版は近日対応予定（Mac 用のビルドは Mac 上でしかできないため、GitHub Actions の macOS 環境での生成を想定。データ保存場所は「アプリと同じフォルダ」が使えないため別の場所に変更が必要）。

---

## 5. テストと静的解析

- **tests/unit**：`app/logic` の純粋関数（tree / dnd / gantt / due）、`app/i18n`、エラー文言、省略表示を検証する。
- **tests/integration**：`app/db/*.py` を一時ディレクトリの専用 SQLite ファイルに対して検証する。循環参照検出・統計（isDone 駆動・期限判定）・アーカイブ除外・ステータス削除制約・祝日 CSV・設定の CRUD・文字数の上限を重点的にカバーする。開発用 `taskmaster.db` には触れない。
- **tests/gui**：入力欄の文字数の上限、フォームの必須の赤字、確認ダイアログを、実際の Tk ウィジェットで検証する。
- **tests/e2e**：アプリ全体（`AppWindow`）を実際に動かし、画面遷移表に対応する遷移・モーダル・確認ダイアログを検証する。
- 画面を開けない環境では、`tests/gui` と `tests/e2e` は自動でスキップされる。方針・ファイル配置・実行方法は [テスト設計書](TEST_DESIGN.md) を参照。
- 静的解析は ruff（`python -m ruff check .`）。

---

## 6. セキュリティ・性能・運用

| 区分 | 方針 |
|---|---|
| セキュリティ | ローカル単一ユーザー前提。ネットワーク通信は行わない。認証は対象外。SQL の値はプレースホルダ（`?`）でバインドする |
| 性能 | 集計・絞り込み対象カラムにインデックス。個人〜小規模データ量で即応。一覧は毎回全件を再構築する単純な方式 |
| 運用 | 監視・ログ運用は無し。障害時は `taskmaster.db` のバックアップから復旧する |
| 可用性 | ローカル実行のみ。複数人の同時利用・サーバー公開は対象外 |
