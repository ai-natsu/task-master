// 日本語の原文 → 英語。キーは画面に出す日本語そのもの（`{name}` はプレースホルダ）。
export const en: Record<string, string> = {
  // 共通
  "キャンセル": "Cancel",
  "削除する": "Delete",
  "削除": "Delete",
  "編集": "Edit",
  "追加": "Add",
  "作成": "Create",
  "保存": "Save",
  "クリア": "Clear",
  "名前": "Name",
  "説明": "Description",
  "カラー": "Color",
  "上へ": "Move up",
  "下へ": "Move down",

  // サイドバー
  "📊 ダッシュボード": "📊 Dashboard",
  "📁 プロジェクト一覧": "📁 Projects",
  "プロジェクト一覧": "Projects",
  "⚙️ 設定": "⚙️ Settings",
  "プロジェクトを削除": "Delete project",
  "「{name}」を削除すると、含まれるすべてのタスクも削除されます。よろしいですか？":
    'Deleting "{name}" will also delete all of its tasks. Are you sure?',

  // ダッシュボード
  "ダッシュボード": "Dashboard",
  "プロジェクト数": "Projects",
  "直近7日の完了": "Completed in last 7 days",
  "期限超過のタスク": "Overdue Tasks",
  "期限超過のタスクはありません": "No overdue tasks",
  "期限が近いタスク": "Upcoming Tasks",
  "予定されているタスクはありません": "No upcoming tasks",
  "{count} 件のタスク": "{count} tasks",
  "まだプロジェクトがありません。サイドバーから作成してください。":
    "No projects yet. Create one from the sidebar.",

  // 統計
  "タスク総数": "Total tasks",
  "完了率": "Completion rate",
  "期限超過": "Overdue",
  "期限が近い（3日後まで）": "Due soon (today to +3 days)",
  "ステータス別": "By status",
  "優先度別": "By priority",

  // 優先度
  "低": "Low",
  "中": "Medium",
  "高": "High",
  "緊急": "Urgent",

  // プロジェクト一覧
  "+ 新しいプロジェクト": "+ New project",
  "アーカイブ済みも表示": "Show archived",
  "アーカイブ済み": "Archived",
  "アーカイブ": "Archive",
  "復元": "Restore",
  "プロジェクトがありません。「+ 新しいプロジェクト」から作成してください。":
    'No projects. Create one with "+ New project".',

  // プロジェクトフォーム
  "新しいプロジェクト": "New project",
  "プロジェクトを編集": "Edit project",
  "プロジェクト名": "Project name",
  "説明（任意）": "Description (optional)",

  // プロジェクト詳細
  "プロジェクトを読み込み中...": "Loading project...",
  "ツリー": "Tree",
  "カンバン": "Kanban",
  "ガント": "Gantt",
  "統計を表示": "Show stats",
  "統計を隠す": "Hide stats",
  "+ 新しいタスク": "+ New task",
  "タスクを削除": "Delete task",
  "「{name}」を削除すると、サブタスクも削除されます。よろしいですか？":
    'Deleting "{name}" will also delete its subtasks. Are you sure?',

  // フィルタ
  "タスクを検索...": "Search tasks...",
  "すべてのステータス": "All statuses",
  "すべての優先度": "All priorities",
  "すべてのタグ": "All tags",

  // タスクフォーム
  "タスクを作成": "Create task",
  "タスクを編集": "Edit task",
  "タイトル": "Title",
  "タスク名を入力": "Enter task name",
  "詳細": "Details",
  "詳細（任意）": "Details (optional)",
  "ステータス": "Status",
  "優先度": "Priority",
  "開始日": "Start date",
  "期限": "Due date",
  "親タスク": "Parent task",
  "なし（最上位）": "None (top level)",
  "タグ": "Tags",
  "新しいタグ": "New tag",

  // ツリー・カンバン・ガント
  "ドラッグして並び替え": "Drag to reorder",
  "サブタスクを追加": "Add subtask",
  "+サブ": "+Sub",
  "タスクがありません。「新しいタスク」から追加してください。": 'No tasks. Add one with "New task".',
  "ここにドロップ": "Drop here",
  "タスクがありません。": "No tasks.",
  "タスク": "Task",
  "ダブルクリックで編集": "Double-click to edit",
  "バーは開始日〜期限の期間を表します（片方のみ設定の場合は1日分）。開始日・期限が未設定のタスクはバー非表示。バーを左右にドラッグして日程を移動、両端のドラッグで期間を変更できます。バーまたはタスク名のダブルクリックで編集できます。":
    "Each bar spans the start date to the due date (one day if only one is set). Tasks with neither date have no bar. Drag a bar sideways to move it, or drag either end to change the span. Double-click a bar or task name to edit.",
  "yyyy年M月": "MMM yyyy",

  // 設定
  "設定": "Settings",
  "ステータス設定": "Status settings",
  "タスクのステータスを追加・変更できます。「完了として扱う」を付けたステータスは、完了率の計算や期限超過の判定で完了済みとして扱われます。タスクで使用中のステータスは削除できません。":
    'Add or change task statuses. Statuses marked "Treat as done" count as completed in the completion rate and overdue checks. Statuses in use by tasks cannot be deleted.',
  "完了として扱う": "Treat as done",
  "新しいステータス名（例: レビュー中）": "New status name (e.g. In review)",
  "祝日": "Holidays",
  "祝日を登録します。ガントチャート等での休日表示に使われます。日付が同じ行はCSV取り込み時に更新されます。":
    "Register holidays. They are used to mark days off in the Gantt chart, etc. Rows with a matching date are updated on CSV import.",
  "日付": "Date",
  "名称": "Name",
  "新しい祝日名": "New holiday name",
  "CSVから読み込む": "Import from CSV",
  "{count} 件を登録・更新しました": "Registered/updated {count} item(s)",
  "CSVの文字コードを判定できませんでした": "Could not determine the CSV file's character encoding.",
  "エラー": "Error",
  "OK": "OK",
  "プロジェクトが見つかりません": "Project not found",
  "タスクが見つかりません": "Task not found",
  "ステータスが見つかりません": "Status not found",
  "タグが見つかりません": "Tag not found",
  "祝日が見つかりません": "Holiday not found",
  "親タスクが見つかりません": "Parent task not found",
  "指定のステータスが存在しません": "Invalid status",
  "ステータスが1件もありません": "No statuses defined",
  "入力内容を確認してください": "Please check your input",
  "入力内容を確認してください（{field}）": "Please check your input ({field})",
  "タグが既に存在します": "Tag already exists",
  "このステータスは {count} 件のタスクで使用中のため削除できません":
    "This status is used by {count} tasks and cannot be deleted",
  "最後のステータスは削除できません": "The last status cannot be deleted",
  "タスクを自分自身またはその配下には移動できません": "A task cannot be moved under itself or its own subtasks",
  "予期しないエラーが発生しました。もう一度お試しください": "An unexpected error occurred. Please try again.",
  "タグを管理します。プロジェクトを問わず全体で共有されます。新しいタグの作成もここから行えます。":
    "Manage tags. They are shared across all projects. You can also create new tags here.",
  "新しいタグ名": "New tag name",
  "タグを削除": "Delete tag",
  "「{name}」タグを削除しますか？{count}件のタスクからこのタグが外れます。":
    'Delete the tag "{name}"? It will be removed from {count} task(s).',
  "言語 / Language": "言語 / Language",
  "表示言語を切り替えます。この設定はこのブラウザに保存されます。":
    "Choose the display language. This setting is saved in this browser.",
};
