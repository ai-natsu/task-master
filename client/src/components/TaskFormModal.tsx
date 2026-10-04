import { useEffect, useState } from "react";
import type { Priority, Tag, Task } from "../types";
import { PRIORITIES, PRIORITY_LABELS } from "../types";
import { useCreateTag, useTags } from "../api/tags";
import { useStatuses } from "../api/statuses";
import { TagPill } from "./Badges";
import { useT } from "../i18n";
import { errorMessage } from "../utils/errorMessage";

export interface TaskFormValue {
  title: string;
  description: string;
  status: string;
  priority: Priority;
  startDate: string;
  dueDate: string;
  tagIds: string[];
  parentId: string | null;
}

interface Props {
  open: boolean;
  mode: "create" | "edit";
  initial?: Partial<TaskFormValue>;
  parentOptions: { id: string; title: string; depth: number }[];
  onSubmit: (value: TaskFormValue) => void | Promise<void>;
  onClose: () => void;
  /** 保存に失敗したときのメッセージ（モーダルを閉じず、ボタンの上に赤字で表示する） */
  error?: string;
}

const empty: TaskFormValue = {
  title: "",
  description: "",
  status: "",
  priority: "MEDIUM",
  startDate: "",
  dueDate: "",
  tagIds: [],
  parentId: null,
};

export function TaskFormModal({ open, mode, initial, parentOptions, onSubmit, onClose, error }: Props) {
  const t = useT();
  const [value, setValue] = useState<TaskFormValue>({ ...empty, ...initial });
  const [newTagName, setNewTagName] = useState("");
  const { data: tags = [] } = useTags();
  const { data: statuses = [] } = useStatuses();
  const createTag = useCreateTag({ inline: true });
  const [tagError, setTagError] = useState("");
  // 必須項目（タイトル）が未入力のまま保存しようとしたときの、項目の下に出す赤字
  const [titleError, setTitleError] = useState("");

  useEffect(() => {
    if (open) {
      setValue({ ...empty, ...initial });
      setTitleError("");
    }
  }, [open, initial]);

  if (!open) return null;

  const toggleTag = (tag: Tag) => {
    setValue((v) => ({
      ...v,
      tagIds: v.tagIds.includes(tag.id) ? v.tagIds.filter((id) => id !== tag.id) : [...v.tagIds, tag.id],
    }));
  };

  const handleCreateTag = async () => {
    if (!newTagName.trim()) {
      setTagError(t("{field}を入力してください", { field: t("名前") }));
      return;
    }
    setTagError("");
    try {
      const tag = await createTag.mutateAsync({ name: newTagName.trim() });
      setValue((v) => ({ ...v, tagIds: [...v.tagIds, tag.id] }));
      setNewTagName("");
    } catch (e) {
      setTagError(errorMessage(e, t));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-5 shadow-xl dark:bg-slate-800">
        <h3 className="text-base font-semibold">{mode === "create" ? t("タスクを作成") : t("タスクを編集")}</h3>

        <div className="mt-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500">{t("タイトル")}</label>
            <input
              autoFocus
              value={value.title}
              onChange={(e) => {
                setValue((v) => ({ ...v, title: e.target.value }));
                if (titleError) setTitleError("");
              }}
              className={`mt-1 w-full rounded-lg border px-3 py-2 text-sm dark:bg-slate-900 ${
                titleError ? "border-red-400" : "border-slate-300 dark:border-slate-600"
              }`}
              placeholder={t("タスク名を入力")}
              aria-invalid={!!titleError}
            />
            {titleError && (
              <p role="alert" className="mt-1 text-xs text-red-600">
                {titleError}
              </p>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500">{t("詳細")}</label>
            <textarea
              value={value.description}
              onChange={(e) => setValue((v) => ({ ...v, description: e.target.value }))}
              rows={3}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
              placeholder={t("詳細（任意）")}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500">{t("ステータス")}</label>
              <select
                value={value.status || statuses[0]?.id || ""}
                onChange={(e) => setValue((v) => ({ ...v, status: e.target.value }))}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
              >
                {statuses.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500">{t("優先度")}</label>
              <select
                value={value.priority}
                onChange={(e) => setValue((v) => ({ ...v, priority: e.target.value as Priority }))}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {t(PRIORITY_LABELS[p])}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500">{t("開始日")}</label>
              <input
                type="date"
                value={value.startDate}
                onChange={(e) => setValue((v) => ({ ...v, startDate: e.target.value }))}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500">{t("期限")}</label>
              <input
                type="date"
                value={value.dueDate}
                onChange={(e) => setValue((v) => ({ ...v, dueDate: e.target.value }))}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500">{t("親タスク")}</label>
            <select
              value={value.parentId ?? ""}
              onChange={(e) => setValue((v) => ({ ...v, parentId: e.target.value || null }))}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
            >
              <option value="">{t("なし（最上位）")}</option>
              {parentOptions.map((p) => (
                <option key={p.id} value={p.id}>
                  {"　".repeat(p.depth)}
                  {p.title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-500">{t("タグ")}</label>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {tags.map((tag) => (
                <button
                  key={tag.id}
                  onClick={() => toggleTag(tag)}
                  className={value.tagIds.includes(tag.id) ? "ring-2 ring-offset-1 rounded-full" : "opacity-60"}
                >
                  <TagPill tag={tag} />
                </button>
              ))}
            </div>
            <div className="mt-2 flex gap-1.5">
              <input
                value={newTagName}
                onChange={(e) => {
                  setNewTagName(e.target.value);
                  setTagError("");
                }}
                onKeyDown={(e) => e.key === "Enter" && handleCreateTag()}
                placeholder={t("新しいタグ")}
                className="flex-1 rounded-lg border border-slate-300 px-2 py-1 text-xs dark:border-slate-600 dark:bg-slate-900"
              />
              <button
                onClick={handleCreateTag}
                className="rounded-lg bg-slate-100 px-2 py-1 text-xs font-medium hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600"
              >
                {t("追加")}
              </button>
            </div>
            {tagError && <p className="mt-1 text-xs text-red-600">{tagError}</p>}
          </div>
        </div>

        {error && (
          <p role="alert" className="mt-4 text-sm text-red-600">
            {error}
          </p>
        )}

        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-lg px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            {t("キャンセル")}
          </button>
          <button
            onClick={() => {
              if (!value.title.trim()) {
                setTitleError(t("{field}を入力してください", { field: t("タイトル") }));
                return;
              }
              void onSubmit(value);
            }}
            className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
          >
            {mode === "create" ? t("作成") : t("保存")}
          </button>
        </div>
      </div>
    </div>
  );
}

export function taskToFormValue(task?: Task): Partial<TaskFormValue> | undefined {
  if (!task) return undefined;
  return {
    title: task.title,
    description: task.description ?? "",
    status: task.status,
    priority: task.priority,
    startDate: task.startDate ? task.startDate.slice(0, 10) : "",
    dueDate: task.dueDate ? task.dueDate.slice(0, 10) : "",
    tagIds: task.tags.map((t) => t.id),
    parentId: task.parentId,
  };
}
