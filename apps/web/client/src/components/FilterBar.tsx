import type { Priority, Tag } from "../types";
import { PRIORITIES, PRIORITY_LABELS } from "../types";
import { useStatuses } from "../api/statuses";
import { useT } from "../i18n";

export interface FilterState {
  search: string;
  status?: string;
  priority?: Priority;
  tagId?: string;
}

interface Props {
  value: FilterState;
  onChange: (value: FilterState) => void;
  tags: Tag[];
}

export function FilterBar({ value, onChange, tags }: Props) {
  const t = useT();
  const { data: statuses = [] } = useStatuses();

  return (
    <div className="flex flex-wrap items-center gap-2">
      <input
        value={value.search}
        onChange={(e) => onChange({ ...value, search: e.target.value })}
        placeholder={t("タスクを検索...")}
        className="w-56 rounded-lg border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
      />
      <select
        value={value.status ?? ""}
        onChange={(e) => onChange({ ...value, status: e.target.value || undefined })}
        className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
      >
        <option value="">{t("すべてのステータス")}</option>
        {statuses.map((s) => (
          <option key={s.id} value={s.id}>
            {s.label}
          </option>
        ))}
      </select>
      <select
        value={value.priority ?? ""}
        onChange={(e) => onChange({ ...value, priority: (e.target.value || undefined) as Priority | undefined })}
        className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
      >
        <option value="">{t("すべての優先度")}</option>
        {PRIORITIES.map((p) => (
          <option key={p} value={p}>
            {t(PRIORITY_LABELS[p])}
          </option>
        ))}
      </select>
      <select
        value={value.tagId ?? ""}
        onChange={(e) => onChange({ ...value, tagId: e.target.value || undefined })}
        className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
      >
        <option value="">{t("すべてのタグ")}</option>
        {tags.map((t) => (
          <option key={t.id} value={t.id}>
            #{t.name}
          </option>
        ))}
      </select>
      {(value.search || value.status || value.priority || value.tagId) && (
        <button
          onClick={() => onChange({ search: "" })}
          className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
        >
          {t("クリア")}
        </button>
      )}
    </div>
  );
}
