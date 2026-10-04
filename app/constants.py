PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"]

# 入力欄の文字数の上限（仕様：docs/BASIC_DESIGN.md の入力項目・データ定義。V1 と同じ値）
LIMITS = {
    "project_name": 200,
    "project_description": 2000,
    "task_title": 300,
    "task_description": 5000,
    "status_label": 50,
    "tag_name": 50,
    "holiday_name": 100,
}
