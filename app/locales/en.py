"""英語翻訳テーブル。キーは日本語の原文（画面の文言そのまま、またはPythonの
str.format()プレースホルダを含むテンプレート）。"""

TRANSLATIONS: dict[str, str] = {
    # --- 共通 -----------------------------------------------------------
    "ダッシュボード": "Dashboard",
    "プロジェクト一覧": "Projects",
    "プロジェクト": "Projects",
    "設定": "Settings",
    "編集": "Edit",
    "削除": "Delete",
    "削除する": "Delete",
    "追加": "Add",
    "作成": "Create",
    "保存": "Save",
    "キャンセル": "Cancel",
    "クリア": "Clear",
    "名前": "Name",
    "名称": "Name",
    "説明": "Description",
    "色": "Color",
    "日付": "Date",
    "タグ": "Tags",
    "タスク": "Task",
    "ダブルクリックで編集": "Double-click to edit",
    "ステータス": "Status",
    "優先度": "Priority",
    "開始日": "Start Date",
    "期限": "Due Date",
    # --- 優先度（app/ui/widgets/badges.py） -------------------------------
    "低": "Low",
    "中": "Medium",
    "高": "High",
    "緊急": "Urgent",
    # --- ダッシュボード ---------------------------------------------------
    "プロジェクト数": "Projects",
    "直近7日の完了数": "Completed (last 7 days)",
    "タスク総数": "Total Tasks",
    "完了率": "Completion Rate",
    "期限超過": "Overdue",
    "期限が近い（3日後まで）": "Due soon (today to +3 days)",
    "期限超過のタスク": "Overdue Tasks",
    "期限が近いタスク": "Upcoming Tasks",
    "プロジェクトがありません": "No projects yet",
    "●  {name}    {count} 件": "●  {name}    {count} tasks",
    "該当するタスクはありません": "No matching tasks",
    # --- プロジェクト一覧 ---------------------------------------------------
    "+ 新しいプロジェクト": "+ New Project",
    "アーカイブ済みも表示": "Show archived too",
    "アーカイブ済み": "Archived",
    "復元": "Restore",
    "アーカイブ": "Archive",
    "タスク {count} 件": "{count} tasks",
    "「{name}」を削除しますか？配下の{count}件のタスクも削除されます。": (
        'Delete "{name}"? Its {count} subtasks will also be deleted.'
    ),
    "プロジェクトを削除": "Delete Project",
    # --- プロジェクト詳細 ---------------------------------------------------
    "ツリー": "Tree",
    "カンバン": "Kanban",
    "ガント": "Gantt",
    "プロジェクトが見つかりません": "Project not found",
    "+ 新しいタスク": "+ New Task",
    "統計を表示": "Show Stats",
    "統計を隠す": "Hide Stats",
    "ここにドロップ": "Drop here",
    "期限: {date}": "Due: {date}",
    # --- 統計内訳 -----------------------------------------------------------
    "ステータス別": "By Status",
    "優先度別": "By Priority",
    # --- プロジェクト作成/編集モーダル ---------------------------------------
    "プロジェクトを編集": "Edit Project",
    "新しいプロジェクト": "New Project",
    # --- タスク作成/編集モーダル ---------------------------------------------
    "タスクを編集": "Edit Task",
    "新しいタスク": "New Task",
    "タイトル": "Title",
    "(ステータス未設定)": "(No status)",
    "親タスク": "Parent Task",
    "(なし・最上位)": "(None / top level)",
    "新しいタグ": "New tag",
    "有効": "Enable",
    "続けて作成": "Keep creating",
    # --- タスクツリー ---------------------------------------------------------
    "タスクがありません。「+ 新しいタスク」から追加してください。": (
        'No tasks yet. Add one with "+ New Task".'
    ),
    "+ サブタスクを追加": "+ Add Subtask",
    "ステータス変更": "Change Status",
    "エラー": "Error",
    "タスクを自分自身またはその配下には移動できません": (
        "A task cannot be moved under itself or its own subtasks"
    ),
    # --- 共通のエラーメッセージ（V1 と同じ。docs/BASIC_DESIGN.md §7.2） -----------
    "タスクが見つかりません": "Task not found",
    "ステータスが見つかりません": "Status not found",
    "タグが見つかりません": "Tag not found",
    "祝日が見つかりません": "Holiday not found",
    "親タスクが見つかりません": "Parent task not found",
    "指定のステータスが存在しません": "Invalid status",
    "ステータスが1件もありません": "No statuses defined",
    "このステータスは {count} 件のタスクで使用中のため削除できません": (
        "This status is used by {count} tasks and cannot be deleted"
    ),
    "予期しないエラーが発生しました。もう一度お試しください": (
        "An unexpected error occurred. Please try again."
    ),
    "「{title}」を削除しますか？配下のサブタスクも削除されます。": (
        'Delete "{title}"? Its subtasks will also be deleted.'
    ),
    "タスクを削除": "Delete Task",
    # --- ガントチャート ---------------------------------------------------------
    "タスクがありません。": "No tasks.",
    # --- フィルタバー ---------------------------------------------------------
    "すべてのステータス": "All Statuses",
    "すべての優先度": "All Priorities",
    "すべてのタグ": "All Tags",
    "タスクを検索...": "Search tasks...",
    # --- 設定画面：ステータス遷移 -------------------------------------------
    "ステータス遷移": "Status Workflow",
    "ステータス遷移を設定します。新しいステータスを追加できます。"
    "既存ステータスの削除や順番の入れ替えもできます。": (
        "Configure the status workflow. You can add new statuses, "
        "delete existing ones, and reorder them."
    ),
    "新しいステータス名": "New status name",
    "完了として扱う": "Treat as done",
    "最後のステータスは削除できません": "The last status cannot be deleted",
    # --- 設定画面：祝日 -----------------------------------------------------
    "祝日": "Holidays",
    "祝日を登録します。ガントチャート等での休日表示に使われます。"
    "日付が同じ行はCSV取り込み時に更新されます。": (
        "Register holidays here. They are used for holiday highlighting in "
        "the Gantt chart, etc. Rows with a matching date are updated on CSV import."
    ),
    "新しい祝日名": "New holiday name",
    "CSVから読み込む": "Import from CSV",
    "祝日CSVを選択": "Select a holiday CSV file",
    "CSVファイル": "CSV files",
    "すべてのファイル": "All files",
    "{count} 件を登録・更新しました": "Registered/updated {count} item(s)",
    "CSVの文字コードを判定できませんでした": (
        "Could not determine the CSV file's character encoding."
    ),
    # --- 設定画面：タグ -------------------------------------------------------
    "タグを管理します。プロジェクトを問わず全体で共有されます。"
    "新しいタグの作成もここから行えます。": (
        "Manage tags here. They are shared across all projects. "
        "You can also create new tags from here."
    ),
    "新しいタグ名": "New tag name",
    "タグを削除": "Delete Tag",
    "「{name}」タグを削除しますか？{count}件のタスクからこのタグが外れます。": (
        'Delete the tag "{name}"? It will be removed from {count} task(s).'
    ),
    "タグが既に存在します": "Tag already exists",
}
