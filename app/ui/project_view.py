"""プロジェクト詳細画面（旧 client/src/pages/ProjectView.tsx の移植）。"""

import customtkinter as ctk

from app.db.projects import get_project
from app.ui import theme
from app.ui.widgets.filter_bar import FilterBar
from app.ui.widgets.gantt_chart_widget import GanttChartWidget
from app.ui.widgets.kanban_board_widget import KanbanBoardWidget
from app.ui.widgets.stats_cards import StatsCardsPanel
from app.ui.widgets.task_tree_widget import TaskTreeWidget

_VIEW_MODES = [("tree", "ツリー"), ("kanban", "カンバン"), ("gantt", "ガント")]


class ProjectView(ctk.CTkFrame):
    def __init__(self, master, app, project_id: str, **_kwargs):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.project_id = project_id
        self.view_mode = "tree"
        self._body: ctk.CTkBaseClass | None = None
        self._stats_panel: StatsCardsPanel | None = None
        self._stats_visible = False
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self) -> None:
        project = get_project(self.app.conn, self.project_id)
        if project is None:
            label = ctk.CTkLabel(self, text="プロジェクトが見つかりません")
            label.grid(row=0, column=0, sticky="w")
            return

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", anchor="w")
        ctk.CTkLabel(
            title_box,
            text=project.name,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=theme.TEXT_PRIMARY,
        ).pack(anchor="w")
        if project.description:
            ctk.CTkLabel(
                title_box, text=project.description, text_color=theme.TEXT_MUTED
            ).pack(anchor="w")

        ctk.CTkButton(
            header,
            text="+ 新しいタスク",
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            command=self._add_root_task,
        ).pack(side="right")

        self.view_switch = ctk.CTkSegmentedButton(
            header,
            values=[label for _, label in _VIEW_MODES],
            command=self._on_view_switch,
        )
        self.view_switch.set(dict(_VIEW_MODES)[self.view_mode])
        self.view_switch.pack(side="right", padx=12)

        self.stats_toggle_btn = ctk.CTkButton(
            header,
            text="統計を表示",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            command=self._toggle_stats,
        )
        self.stats_toggle_btn.pack(side="right", padx=(0, 12))

        self.filter_bar = FilterBar(self, app=self.app, on_change=self._on_filters_changed)
        self.filter_bar.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        self.stats_row = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_row.grid(row=2, column=0, sticky="ew")

        self._show_view(self.view_mode)

    def _toggle_stats(self) -> None:
        self._stats_visible = not self._stats_visible
        if self._stats_visible:
            self.stats_toggle_btn.configure(text="統計を隠す")
            self._stats_panel = StatsCardsPanel(
                self.stats_row, app=self.app, project_id=self.project_id
            )
            self._stats_panel.pack(fill="x", pady=(0, 12))
        else:
            self.stats_toggle_btn.configure(text="統計を表示")
            if self._stats_panel is not None:
                self._stats_panel.destroy()
                self._stats_panel = None

    def _on_filters_changed(self, filters: dict) -> None:
        if self._body is not None:
            self._body.set_filters(filters)

    def _on_view_switch(self, label: str) -> None:
        mode = next(m for m, lbl in _VIEW_MODES if lbl == label)
        self._show_view(mode)

    def _show_view(self, mode: str) -> None:
        if self._body is not None:
            self._body.destroy()
        self.view_mode = mode

        on_change = self.app.sidebar.refresh_projects
        widget_cls = {
            "tree": TaskTreeWidget,
            "kanban": KanbanBoardWidget,
            "gantt": GanttChartWidget,
        }[mode]
        self._body = widget_cls(
            self,
            app=self.app,
            project_id=self.project_id,
            on_change=on_change,
            filters=self.filter_bar.get_filters(),
        )
        self._body.grid(row=3, column=0, sticky="nsew")

    def _add_root_task(self) -> None:
        self._body.add_root_task()
