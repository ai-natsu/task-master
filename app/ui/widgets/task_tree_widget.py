"""タスクツリー表示（旧 client/src/components/TaskTree.tsx + TaskNode.tsx の移植）。

ttk.Treeview はネイティブに展開/折りたたみを持つため採用し、ドラッグ&ドロップは
マウスイベントで検出して純粋関数 plan_row_drop に委ねる（並べ替え・親の付け替え）。
"""

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from app.db.statuses import list_statuses
from app.db.tasks import create_task, delete_task, list_tasks, reorder_tasks, update_task
from app.i18n import format_date, t
from app.logic.dnd import plan_row_drop
from app.logic.due import is_overdue
from app.logic.tree import build_task_tree, flatten_nodes
from app.ui import theme
from app.ui.widgets.badges import PRIORITY_COLORS, priority_label
from app.ui.widgets.confirm_dialog import ask_confirm
from app.ui.widgets.task_edit import edit_task
from app.ui.widgets.task_form_dialog import ask_task_form

_EMPTY_IID = "__empty__"
_DRAG_THRESHOLD_PX = 5  # これ以下の動きはドラッグでなくクリック（編集）として扱う
_DROP_EDGE = 0.25  # 行の上下この割合 = 兄弟として挿入、中央 = 子にする
_TAGS_MAX_LEN = 14  # タグ列(幅160px)に収まる目安の文字数。超過分は"..."で省略する


def _format_tags(tags) -> str:
    joined = ", ".join(tag.name for tag in tags)
    if len(joined) <= _TAGS_MAX_LEN:
        return joined
    return joined[:_TAGS_MAX_LEN] + "..."


class TaskTreeWidget(ctk.CTkFrame):
    def __init__(self, master, app, project_id: str, on_change=None, filters: dict | None = None):
        super().__init__(master, fg_color=theme.PANEL_BG)
        self.app = app
        self.project_id = project_id
        self.on_change = on_change or (lambda: None)
        self.filters = filters or {}
        self._tasks_by_id: dict = {}
        self._statuses_by_id: dict = {}
        self._status_labels: dict[str, str] = {}
        self._drag_id: str | None = None
        self._press_on_indicator = False
        self._drag_moved = False
        self._drag_start_y = 0
        self._hover_id: str | None = None
        self._grid_lines: list[tk.Frame] = []
        self._column_lines: list[tk.Frame] = []
        self._priority_overlays: list[tk.Label] = []
        self._status_overlays: list[tk.Label] = []

        style = ttk.Style()
        style.configure(
            "TaskTree.Treeview",
            rowheight=34,
            background=theme.CARD_BG[0],
            fieldbackground=theme.CARD_BG[0],
            foreground=theme.TEXT_PRIMARY[0],
            borderwidth=0,
            font=(theme.FONT_FAMILY, 11),
        )
        style.configure(
            "TaskTree.Treeview.Heading",
            background=("#f1f5f9"),
            foreground=theme.TEXT_MUTED[0],
            relief="flat",
            font=(theme.FONT_FAMILY, 10, "bold"),
        )
        style.map(
            "TaskTree.Treeview",
            background=[("selected", theme.ACCENT)],
            foreground=[("selected", "#ffffff")],
        )

        self.tree = ttk.Treeview(
            self,
            style="TaskTree.Treeview",
            columns=("status", "priority", "start", "due", "tags"),
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", text=t("タスク"))
        self.tree.heading("status", text=t("ステータス"))
        self.tree.heading("priority", text=t("優先度"))
        self.tree.heading("start", text=t("開始日"))
        self.tree.heading("due", text=t("期限"))
        self.tree.heading("tags", text=t("タグ"))
        self.tree.column("#0", width=320, stretch=True)
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("priority", width=70, anchor="center")
        self.tree.column("start", width=90, anchor="center")
        self.tree.column("due", width=90, anchor="center")
        self.tree.column("tags", width=160)

        self.tree.tag_configure("overdue", foreground="#dc2626")
        self.tree.tag_configure("done", foreground="#94a3b8")
        self.tree.tag_configure("hover", background="#eef2ff")
        self.tree.tag_configure("dropchild", background="#c7d2fe")
        self._drop_line = tk.Frame(self.tree, bg=theme.ACCENT, height=3)
        self._drop_child_id: str | None = None

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hscrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(
            yscrollcommand=self._on_tree_yscroll(scrollbar),
            xscrollcommand=self._on_tree_xscroll(hscrollbar),
        )
        hscrollbar.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<ButtonPress-1>", self._on_press)
        self.tree.bind("<B1-Motion>", self._on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self._on_release)
        # ダブルクリックでは何もしない（既定の「展開/折りたたみの切替」も止める）。編集は
        # シングルクリック。Tk は最も具体的なバインドだけを実行するため、連続クリックの2回目
        # でも通常の押下処理（_on_press）は実行しつつ、既定の切替だけを "break" で止める。
        self.tree.bind("<Double-1>", self._on_repeat_press)
        self.tree.bind("<Triple-1>", self._on_repeat_press)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind("<Leave>", lambda _e: self._set_hover(None))
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<Configure>", lambda _e: self._redraw_overlays())
        self.tree.bind("<<TreeviewOpen>>", lambda _e: self.after_idle(self._redraw_overlays))
        self.tree.bind("<<TreeviewClose>>", lambda _e: self.after_idle(self._redraw_overlays))

        self.refresh()

    def _on_tree_yscroll(self, scrollbar: ttk.Scrollbar):
        """ttk.Treeviewは複数カラムの行に罫線・セル単位の色付けを描く標準機能を
        持たないため、行の下端に重なる薄いFrame(罫線)や、特定セルに重なる
        Label(優先度の文字色・ステータスの背景色)を敷き詰めて表現している。
        スクロール位置が変わるたびに画面上の位置がずれるため、
        yscrollcommand(スクロールバー操作・マウスホイール・キー操作など、
        表示範囲が変わるあらゆる経路で呼ばれる)に相乗りして引き直す。
        """

        def _handler(*args) -> None:
            scrollbar.set(*args)
            self._redraw_overlays()

        return _handler

    def _on_tree_xscroll(self, scrollbar: ttk.Scrollbar):
        """縦の列境界線(_draw_column_lines)は横スクロール位置に応じて左右に
        動くため、yscrollと同様にxscrollcommandに相乗りして引き直す。
        """

        def _handler(*args) -> None:
            scrollbar.set(*args)
            self._redraw_overlays()

        return _handler

    def _all_item_ids(self) -> list[str]:
        item_ids: list[str] = []

        def _collect(parent: str = "") -> None:
            for iid in self.tree.get_children(parent):
                item_ids.append(iid)
                _collect(iid)

        _collect()
        return item_ids

    def _redraw_overlays(self) -> None:
        self._draw_grid_lines()
        self._draw_cell_overlays()
        self._draw_column_lines()

    def _draw_grid_lines(self) -> None:
        item_ids = self._all_item_ids()

        while len(self._grid_lines) < len(item_ids):
            self._grid_lines.append(
                tk.Frame(self, height=1, bg=theme.CARD_BORDER[0], bd=0, highlightthickness=0)
            )

        tree_width = self.tree.winfo_width()
        for line, iid in zip(self._grid_lines, item_ids):
            bbox = self.tree.bbox(iid)
            if not bbox:
                line.place_forget()
                continue
            _x, y, _w, h = bbox
            line.place(in_=self.tree, x=0, y=y + h - 1, width=tree_width, height=1)
        for line in self._grid_lines[len(item_ids):]:
            line.place_forget()

    def _draw_column_lines(self) -> None:
        """列の境界線を、タスクが0件の時も含めて本体の下端まで表示する。

        ネイティブの列境界線は実際に存在する行の高さ分しか描かれない
        (タスクがない場合の案内行1行分で途切れる)ため、罫線のFrameと
        同じ手法で、ヘッダー下端から本体下端まで届く縦線を別途重ねる。
        """
        item_ids = self._all_item_ids()
        if not item_ids:
            for line in self._column_lines:
                line.place_forget()
            return

        first_bbox = self.tree.bbox(item_ids[0])
        if not first_bbox:
            for line in self._column_lines:
                line.place_forget()
            return
        header_bottom = first_bbox[1]
        tree_height = self.tree.winfo_height()

        boundaries = []
        # 最後の列(タグ)の右端には境界線を引かない(その先に列がないため)。
        for col in ("#0", "status", "priority", "start", "due"):
            bbox = self.tree.bbox(item_ids[0], col)
            if bbox:
                x, _y, w, _h = bbox
                boundaries.append(x + w)

        while len(self._column_lines) < len(boundaries):
            self._column_lines.append(
                tk.Frame(self, width=1, bg=theme.CARD_BORDER[0], bd=0, highlightthickness=0)
            )

        for line, x in zip(self._column_lines, boundaries):
            line.place(
                in_=self.tree, x=x, y=header_bottom, width=1, height=tree_height - header_bottom
            )
        for line in self._column_lines[len(boundaries):]:
            line.place_forget()

    def _draw_cell_overlays(self) -> None:
        """優先度・ステータスのセル文字色を、カンバン/ダッシュボードと揃える。

        ttk.Treeviewはセル単位の色指定に対応しないため、該当セルにぴったり
        重なるtk.Labelを被せて表現する(罫線のFrameと同じ手法)。
        """
        item_ids = self._all_item_ids()
        font = (theme.FONT_FAMILY, 11)

        while len(self._priority_overlays) < len(item_ids):
            self._priority_overlays.append(
                tk.Label(self, bd=0, highlightthickness=0, font=font, anchor="center")
            )
        while len(self._status_overlays) < len(item_ids):
            self._status_overlays.append(
                tk.Label(self, bd=0, highlightthickness=0, font=font, anchor="center")
            )

        for index, iid in enumerate(item_ids):
            priority_overlay = self._priority_overlays[index]
            status_overlay = self._status_overlays[index]
            task = self._tasks_by_id.get(iid)
            if task is None:
                priority_overlay.place_forget()
                status_overlay.place_forget()
                continue

            priority_bbox = self.tree.bbox(iid, "priority")
            if priority_bbox:
                x, y, w, h = priority_bbox
                _, fg = PRIORITY_COLORS.get(task.priority, PRIORITY_COLORS["MEDIUM"])
                priority_overlay.configure(
                    text=priority_label(task.priority), fg=fg, bg=theme.CARD_BG[0]
                )
                # 行下端の罫線(_draw_grid_linesがy+h-1に描く1px線)を覆って
                # 隠してしまわないよう、オーバーレイの高さを1px短くする。
                priority_overlay.place(in_=self.tree, x=x, y=y, width=w, height=h - 1)
            else:
                priority_overlay.place_forget()

            status = self._statuses_by_id.get(task.status)
            status_bbox = self.tree.bbox(iid, "status")
            if status_bbox and status is not None:
                x, y, w, h = status_bbox
                status_overlay.configure(
                    text=status.label, fg=status.color, bg=theme.CARD_BG[0]
                )
                status_overlay.place(in_=self.tree, x=x, y=y, width=w, height=h - 1)
            else:
                status_overlay.place_forget()

        for extra in self._priority_overlays[len(item_ids):]:
            extra.place_forget()
        for extra in self._status_overlays[len(item_ids):]:
            extra.place_forget()

    def set_filters(self, filters: dict) -> None:
        self.filters = filters
        self.refresh()

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())

        tasks = list_tasks(self.app.conn, project_id=self.project_id, **self.filters)
        self._tasks_by_id = {task.id: task for task in tasks}
        statuses = {s.id: s for s in list_statuses(self.app.conn)}
        self._statuses_by_id = statuses
        self._status_labels = {sid: s.label for sid, s in statuses.items()}

        tree_nodes = build_task_tree(tasks)
        if not tree_nodes:
            self.tree.insert(
                "", "end", iid=_EMPTY_IID,
                text=t("タスクがありません。「+ 新しいタスク」から追加してください。"),
            )
            self.after_idle(self._redraw_overlays)
            return

        for flat in flatten_nodes(tree_nodes):
            task = flat.node.task
            status = statuses.get(task.status)
            is_done = status.is_done if status else False
            overdue = not is_done and is_overdue(task.due_date)

            tags = []
            if overdue:
                tags.append("overdue")
            elif is_done:
                tags.append("done")

            parent_iid = task.parent_id or ""
            self.tree.insert(
                parent_iid, "end", iid=task.id, text=task.title, open=True,
                values=(
                    status.label if status else task.status,
                    priority_label(task.priority),
                    format_date(task.start_date),
                    format_date(task.due_date),
                    _format_tags(task.tags),
                ),
                tags=tuple(tags),
            )

        self.after_idle(self._redraw_overlays)

    # --- ドラッグ&ドロップ（並べ替え・親の付け替え） ---------------------------
    # クリック（編集）とドラッグは、しきい値（_DRAG_THRESHOLD_PX）で分ける：
    # しきい値を超えて動いたらドラッグで、離しても編集は開かない。
    def _on_press(self, event) -> None:
        row_id = self.tree.identify_row(event.y)
        self._drag_id = row_id if row_id != _EMPTY_IID else None
        self._drag_moved = False
        self._drag_start_y = event.y
        # 展開/折りたたみの矢印を押したときは、編集を開かない
        self._press_on_indicator = "indicator" in self.tree.identify_element(event.x, event.y)

    def _on_repeat_press(self, event) -> str:
        self._on_press(event)
        return "break"

    def _drop_target(self, event) -> tuple[str, str] | None:
        """ポインタ位置から (ドロップ先の行, 位置) を求める。位置は before / after / child。"""
        row_id = self.tree.identify_row(event.y)
        if not row_id or row_id == _EMPTY_IID or row_id == self._drag_id:
            return None
        bbox = self.tree.bbox(row_id)
        if not bbox:
            return None
        _x, y, _w, h = bbox
        frac = (event.y - y) / h
        zone = "before" if frac < _DROP_EDGE else "after" if frac > 1 - _DROP_EDGE else "child"
        return row_id, zone

    def _on_drag_motion(self, event) -> None:
        if not self._drag_id:
            return
        if not self._drag_moved:
            if abs(event.y - self._drag_start_y) <= _DRAG_THRESHOLD_PX:
                return
            self._drag_moved = True
        self._draw_drop_indicator(self._drop_target(event))

    def _clear_drop_indicator(self) -> None:
        self._drop_line.place_forget()
        if self._drop_child_id is not None and self.tree.exists(self._drop_child_id):
            tags = [x for x in self.tree.item(self._drop_child_id, "tags") if x != "dropchild"]
            self.tree.item(self._drop_child_id, tags=tuple(tags))
        self._drop_child_id = None

    def _draw_drop_indicator(self, target: tuple[str, str] | None) -> None:
        self._clear_drop_indicator()
        if target is None:
            return
        row_id, zone = target
        if zone == "child":
            self._drop_child_id = row_id
            self.tree.item(row_id, tags=(*self.tree.item(row_id, "tags"), "dropchild"))
            return
        _x, y, _w, h = self.tree.bbox(row_id)
        line_y = y if zone == "before" else y + h
        self._drop_line.place(x=0, y=line_y - 1, relwidth=1)

    # --- マウスオーバー（行を薄く強調） -----------------------------------------
    def _on_motion(self, event) -> None:
        row_id = self.tree.identify_row(event.y)
        self._set_hover(row_id if row_id and row_id != _EMPTY_IID else None)

    def _set_hover(self, row_id: str | None) -> None:
        if row_id == self._hover_id:
            return
        if self._hover_id is not None and self.tree.exists(self._hover_id):
            tags = [x for x in self.tree.item(self._hover_id, "tags") if x != "hover"]
            self.tree.item(self._hover_id, tags=tuple(tags))
        self._hover_id = row_id
        if row_id is not None and self.tree.exists(row_id):
            tags = [*self.tree.item(row_id, "tags"), "hover"]
            self.tree.item(row_id, tags=tuple(tags))

    def _on_release(self, event) -> None:
        if not self._drag_id:
            return
        active_id, self._drag_id = self._drag_id, None
        moved, self._drag_moved = self._drag_moved, False
        target = self._drop_target_for(event, active_id) if moved else None
        self._clear_drop_indicator()

        if not moved:
            # しきい値内＝シングルクリック → 編集を開く
            task = self._tasks_by_id.get(active_id)
            if task and not self._press_on_indicator:
                self._edit(task)
            return
        if target is None:
            return

        drop_id, zone = target
        tasks = list_tasks(self.app.conn, project_id=self.project_id)
        plan = plan_row_drop(tasks, active_id, drop_id, zone)
        if plan.get("reorder"):
            reorder_tasks(self.app.conn, plan["reorder"])
            self.refresh()
            self.on_change()

    def _drop_target_for(self, event, active_id: str) -> tuple[str, str] | None:
        self._drag_id = active_id  # _drop_target は自分自身を除外するために参照する
        try:
            return self._drop_target(event)
        finally:
            self._drag_id = None

    # --- 右クリックメニュー -------------------------------------------------
    def _on_right_click(self, event) -> None:
        row_id = self.tree.identify_row(event.y)
        task = self._tasks_by_id.get(row_id)
        if task is None:
            return
        self.tree.selection_set(row_id)

        menu_font = (theme.FONT_FAMILY, 12)
        menu = tk.Menu(self, tearoff=0, font=menu_font)
        menu.add_command(label=t("+ サブタスクを追加"), command=lambda: self._add_subtask(row_id))
        menu.add_command(label=t("編集"), command=lambda: self._edit(task))
        if self._status_labels:
            status_menu = tk.Menu(menu, tearoff=0, font=menu_font)
            for sid, label in self._status_labels.items():
                status_menu.add_command(
                    label=label, command=lambda s=sid, tk_=task: self._change_status(tk_.id, s)
                )
            menu.add_cascade(label=t("ステータス変更"), menu=status_menu)
        menu.add_separator()
        menu.add_command(label=t("削除"), command=lambda: self._delete(task))
        menu.tk_popup(event.x_root, event.y_root)

    # --- CRUD操作 -------------------------------------------------------------
    def _change_status(self, task_id: str, status_id: str) -> None:
        update_task(self.app.conn, task_id, status=status_id)
        self.refresh()
        self.on_change()

    def add_root_task(self) -> None:
        self._add_subtask(None)

    def _add_subtask(self, parent_id: str | None) -> None:
        result = ask_task_form(self.app, self.app.conn, self.project_id, parent_id=parent_id)
        if result:
            result.pop("parent_id", None)
            create_task(self.app.conn, project_id=self.project_id, parent_id=parent_id, **result)
            self.refresh()
            self.on_change()

    def _edit(self, task) -> None:
        if edit_task(self, self.app, self.project_id, task):
            self.refresh()
            self.on_change()

    def _delete(self, task) -> None:
        message = t("「{title}」を削除しますか？配下のサブタスクも削除されます。").format(
            title=task.title
        )
        if ask_confirm(self.app, t("タスクを削除"), message):
            delete_task(self.app.conn, task.id)
            self.refresh()
            self.on_change()
