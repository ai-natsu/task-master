"""カンバンボード（旧 client/src/components/KanbanBoard.tsx の移植）。

CustomTkinter/Tkinter にはドラッグ用のネイティブAPIが無いため、
ButtonPress-1でドラッグ開始位置を記録し、B1-Motionでカーソルに追従する
フローティングウィンドウ(擬似ドラッグプレビュー)を表示、ButtonRelease-1で
winfo_containing()により実際にカーソル下にあるウィジェットを特定して
列/カードを判定する方式を採る。
"""

import tkinter as tk

import customtkinter as ctk

from app.db.statuses import list_statuses
from app.db.tasks import list_tasks, reorder_tasks, update_task
from app.i18n import format_date, t
from app.logic.dnd import plan_kanban_drag
from app.logic.due import is_overdue
from app.ui import theme
from app.ui.widgets.badges import color_pill, priority_badge
from app.ui.widgets.ellipsis import EllipsisLabel
from app.ui.widgets.task_edit import create_task_via_form, edit_task

_DRAG_THRESHOLD_PX = 4  # これ未満の移動は単なるクリックとみなしドラッグ扱いしない
_MAX_VISIBLE_TAGS = 2
_MAX_TAG_NAME_LEN = 4
# meta_row(期限+タグ)の実質的な幅。列幅272px(固定)から、cards_areaの余白・
# スクロールバー・カード自身の余白を差し引いた概算値。カード構築は
# refresh()中に同期的に行われ、winfo_width()がまだ正しい値を返さない
# ("要アイドル処理"問題)ため、実測ではなくこの概算値を基準に折り返しを
# 判定する(列幅自体がwidth=272で固定されているため、概算値も安定する)。
_META_ROW_WIDTH = 205
_ELLIPSIS_RESERVE = 36


def _truncate(text: str, max_len: int) -> str:
    return text if len(text) <= max_len else text[:max_len] + "..."


class KanbanBoardWidget(ctk.CTkFrame):
    def __init__(self, master, app, project_id: str, on_change=None, filters: dict | None = None):
        super().__init__(master, fg_color=theme.PANEL_BG)
        self.app = app
        self.project_id = project_id
        self.on_change = on_change or (lambda: None)
        self.filters = filters or {}

        self._drag_task = None
        self._drag_start_xy: tuple[int, int] | None = None
        self._drag_started = False
        self._drag_ghost: tk.Toplevel | None = None
        self._task_is_done: dict[str, bool] = {}
        self._card_widgets: dict[str, ctk.CTkFrame] = {}
        self._column_containers: dict[int, str] = {}

        self.scroll = ctk.CTkScrollableFrame(
            self, orientation="horizontal", fg_color="transparent"
        )
        self.scroll.pack(fill="both", expand=True)

        self.refresh()

    def set_filters(self, filters: dict) -> None:
        self.filters = filters
        self.refresh()

    def refresh(self) -> None:
        # 列・カードを毎回全部作り直すため、表示されたままだと一瞬空になる
        # 瞬間が見えてちらつく。再構築が終わるまで画面から外しておく。
        self.scroll.pack_forget()
        for child in self.scroll.winfo_children():
            child.destroy()
        self._card_widgets.clear()
        self._task_is_done.clear()
        self._column_containers.clear()

        statuses = list_statuses(self.app.conn)
        tasks = list_tasks(self.app.conn, project_id=self.project_id, **self.filters)
        columns: dict[str, list] = {s.id: [] for s in statuses}
        for task in tasks:
            columns.setdefault(task.status, []).append(task)
        for col in columns.values():
            col.sort(key=lambda task: task.order)

        for status in statuses:
            col_frame = ctk.CTkFrame(
                self.scroll, width=272, fg_color=theme.SUBTLE_BG, corner_radius=14
            )
            col_frame.pack(side="left", fill="y", padx=6, pady=4)
            col_frame.pack_propagate(False)
            self._column_containers[id(col_frame)] = status.id

            header = ctk.CTkFrame(col_frame, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(12, 6))
            ctk.CTkLabel(
                header, text="●", text_color=status.color, width=14, font=ctk.CTkFont(size=14)
            ).pack(side="left")
            ctk.CTkLabel(
                header, text=status.label, font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left")
            ctk.CTkLabel(
                header,
                text=str(len(columns.get(status.id, []))),
                fg_color=("#e2e8f0", "#334155"),
                text_color=theme.TEXT_PRIMARY,
                corner_radius=8,
                width=22,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(side="right")

            cards_area = ctk.CTkScrollableFrame(col_frame, fg_color="transparent")
            cards_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            self._column_containers[id(cards_area)] = status.id

            col_tasks = columns.get(status.id, [])
            if not col_tasks:
                ctk.CTkLabel(
                    cards_area, text=t("ここにドロップ"), text_color=theme.TEXT_MUTED
                ).pack(pady=20)
            for task in col_tasks:
                self._build_card(cards_area, task, status.is_done)

        self.scroll.pack(fill="both", expand=True)

    def _build_card(self, parent, task, is_done: bool) -> None:
        card = ctk.CTkFrame(
            parent, corner_radius=10, border_width=1,
            fg_color=theme.CARD_BG, border_color=theme.CARD_BORDER,
        )
        card.pack(fill="x", pady=4)
        self._card_widgets[task.id] = card
        self._task_is_done[task.id] = is_done

        title_label, meta_row = self._populate_card(card, task, is_done)

        for widget in (card, title_label, meta_row):
            widget.bind("<ButtonPress-1>", lambda e, tk_=task: self._start_drag(e, tk_))
            widget.bind("<B1-Motion>", self._on_drag_motion)
            widget.bind("<ButtonRelease-1>", self._end_drag)
            widget.bind("<Enter>", lambda _e, c=card: self._hover_card(c, True), add="+")
            widget.bind("<Leave>", lambda _e, c=card: self._hover_leave(c), add="+")
        self._set_cursor_recursive(card, "fleur")

    # --- マウスオーバー（枠をアクセント色で強調＋つかむカーソル） -----------------
    def _set_cursor_recursive(self, widget, cursor: str) -> None:
        try:
            widget.configure(cursor=cursor)
        except (tk.TclError, ValueError):
            pass  # カーソル指定に対応しないウィジェットは既定のまま
        for child in widget.winfo_children():
            self._set_cursor_recursive(child, cursor)

    def _hover_card(self, card, on: bool) -> None:
        if self._drag_started:
            return
        card.configure(border_color=theme.ACCENT if on else theme.CARD_BORDER)

    def _hover_leave(self, card) -> None:
        # 子ウィジェットへ移動しただけの Leave では解除しない
        def check() -> None:
            if not card.winfo_exists():
                return
            under = card.winfo_containing(*card.winfo_pointerxy())
            while under is not None and under is not card:
                under = getattr(under, "master", None)
            if under is not card:
                self._hover_card(card, False)

        card.after(15, check)

    def _populate_card(self, card, task, is_done: bool):
        """カード枠の中身（タイトル・優先度・タグ・期限）を組み立てる。

        通常のカードとドラッグ中のゴースト（カード全体の複製）で共用する。
        """
        title_label = EllipsisLabel(
            card,
            text=task.title,
            font=ctk.CTkFont(overstrike=is_done, weight="bold"),
            text_color=theme.TEXT_MUTED if is_done else theme.TEXT_PRIMARY,
            padding=4,
        )
        title_label.pack(fill="x", padx=10, pady=(10, 4))

        meta_row = ctk.CTkFrame(card, fg_color="transparent")
        meta_row.pack(fill="x", padx=10, pady=(0, 10))

        # 1段目＝優先度・タグ、2段目＝期限。日本語の日付表示（2026年10月05日）は幅が広く、
        # 同じ段に置くとタグが入らなくなるため、期限は別の段にする（V1 のカードと同じ）。
        # なお、カード構築はrefresh()中に同期的に行われてwinfo_width()がまだ正しい値を
        # 返さないため、実測ではなく_META_ROW_WIDTH(列幅がwidth=272で固定のため安定する
        # 概算値)を基準に、タグがいくつ収まるか判定する。
        tags_area = ctk.CTkFrame(meta_row, fg_color="transparent")
        tags_area.pack(anchor="w")
        available_width = _META_ROW_WIDTH

        badge = priority_badge(tags_area, task.priority)
        badge.pack(side="left")
        badge.update_idletasks()
        used_width = badge.winfo_reqwidth()

        total_tags = len(task.tags)
        shown = 0
        for index, tag in enumerate(task.tags[:_MAX_VISIBLE_TAGS]):
            label = _truncate(tag.name, _MAX_TAG_NAME_LEN)
            probe = color_pill(tags_area, label, tag.color)
            probe.pack(side="left", padx=(4, 0))
            probe.update_idletasks()
            pill_width = probe.winfo_reqwidth() + 4
            has_more_after = (index + 1) < total_tags
            reserve = _ELLIPSIS_RESERVE if has_more_after else 0
            if used_width + pill_width + reserve > available_width:
                probe.destroy()
                break
            used_width += pill_width
            shown += 1
        if total_tags > shown:
            color_pill(tags_area, "...").pack(side="left", padx=(4, 0))

        if task.due_date:
            overdue = not is_done and is_overdue(task.due_date)
            ctk.CTkLabel(
                meta_row,
                text=t("期限: {date}").format(date=format_date(task.due_date)),
                text_color="#dc2626" if overdue else theme.TEXT_MUTED,
            ).pack(anchor="w", pady=(4, 0))

        return title_label, meta_row

    def _start_drag(self, event, task) -> None:
        # ここではまだゴースト(浮動プレビュー)は出さない。単なるクリックで
        # ドラッグ用のタイトル文字が一瞬表示されてしまっていたため、実際に
        # _DRAG_THRESHOLD_PX以上動いてから初めてドラッグ開始とみなす。
        self._drag_task = task
        self._drag_start_xy = (event.x_root, event.y_root)
        self._drag_started = False

    def _begin_drag_visuals(self, task) -> None:
        card = self._card_widgets.get(task.id)
        if card:
            card.configure(border_color=theme.ACCENT, border_width=2)

        ghost = tk.Toplevel(self)
        ghost.overrideredirect(True)
        try:
            ghost.attributes("-alpha", 0.85)
            ghost.attributes("-topmost", True)
        except tk.TclError:
            pass  # 一部環境では透過/最前面がサポートされないため握りつぶす
        # ドラッグ元と同じ見た目のカード全体を複製して追従させる（V1 と同じ）。
        ghost_card = ctk.CTkFrame(
            ghost, corner_radius=10, border_width=2,
            fg_color=theme.CARD_BG, border_color=theme.ACCENT,
        )
        ghost_card.pack()
        self._populate_card(ghost_card, task, self._task_is_done.get(task.id, False))
        if card:
            # ドラッグ元カードと同じ大きさに揃える（CTkのサイズ指定は拡大率前の値）
            scale = ctk.ScalingTracker.get_widget_scaling(card)
            ghost_card.configure(
                width=card.winfo_width() / scale, height=card.winfo_height() / scale
            )
            ghost_card.pack_propagate(False)
        self._drag_ghost = ghost

    def _on_drag_motion(self, event) -> None:
        if self._drag_task is None:
            return
        if not self._drag_started:
            start_x, start_y = self._drag_start_xy
            if (
                abs(event.x_root - start_x) < _DRAG_THRESHOLD_PX
                and abs(event.y_root - start_y) < _DRAG_THRESHOLD_PX
            ):
                return
            self._drag_started = True
            self._begin_drag_visuals(self._drag_task)
        if self._drag_ghost is not None:
            self._drag_ghost.geometry(f"+{event.x_root + 12}+{event.y_root + 12}")

    def _end_drag(self, event) -> None:
        if self._drag_ghost is not None:
            self._drag_ghost.destroy()
            self._drag_ghost = None
            # 直後にwinfo_containingでドロップ先を判定するため、ゴースト
            # ウィンドウの消去をウィンドウマネージャに確実に反映させる。
            self.update_idletasks()

        task, self._drag_task = self._drag_task, None
        started, self._drag_started = self._drag_started, False
        self._drag_start_xy = None
        if task is None:
            return
        active_id = task.id
        card = self._card_widgets.get(active_id)
        if card:
            card.configure(border_width=1)
        if not started:
            # しきい値未満の移動 = シングルクリック → 編集を開く
            self._edit(task)
            return

        target_widget = self.winfo_containing(event.x_root, event.y_root)
        over = self._resolve_drop_target(target_widget)
        if over is None:
            return

        tasks = list_tasks(self.app.conn, project_id=self.project_id)
        plan = plan_kanban_drag(tasks, active_id, over)
        if plan.get("status_change"):
            update_task(
                self.app.conn,
                plan["status_change"]["id"],
                status=plan["status_change"]["status"],
            )
        if plan.get("reorder"):
            reorder_tasks(self.app.conn, plan["reorder"])
        if plan:
            self.refresh()
            self.on_change()

    def _resolve_drop_target(self, widget) -> dict | None:
        w = widget
        while w is not None:
            for task_id, card in self._card_widgets.items():
                if w is card:
                    return {"id": task_id, "type": "card"}
            status_id = self._column_containers.get(id(w))
            if status_id is not None:
                return {"id": f"column:{status_id}", "type": "column", "status_id": status_id}
            w = getattr(w, "master", None)
        return None

    def _edit(self, task) -> None:
        if edit_task(self.app, self.project_id, task):
            self.refresh()
            self.on_change()

    def add_root_task(self) -> None:
        if create_task_via_form(self.app, self.project_id):
            self.refresh()
            self.on_change()
