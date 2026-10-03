import { useState } from "react";
import {
  useCreateStatus,
  useDeleteStatus,
  useReorderStatuses,
  useStatuses,
  useUpdateStatus,
} from "../api/statuses";
import type { StatusDef } from "../types";
import { LANGUAGES, useLanguage, useT, type Language } from "../i18n";
import { HolidaySettings } from "../components/HolidaySettings";

function StatusRow({
  status,
  isFirst,
  isLast,
  onMoveUp,
  onMoveDown,
}: {
  status: StatusDef;
  isFirst: boolean;
  isLast: boolean;
  onMoveUp: () => void;
  onMoveDown: () => void;
}) {
  const t = useT();
  const updateStatus = useUpdateStatus();
  const deleteStatus = useDeleteStatus();
  const [label, setLabel] = useState(status.label);
  const [error, setError] = useState("");

  const saveLabel = () => {
    const trimmed = label.trim();
    if (!trimmed || trimmed === status.label) {
      setLabel(status.label);
      return;
    }
    updateStatus.mutate({ id: status.id, label: trimmed });
  };

  const handleDelete = () => {
    setError("");
    deleteStatus.mutate(status.id, {
      onError: (e) => setError(e.message),
    });
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-800">
      <div className="flex items-center gap-3">
        <div className="flex flex-col">
          <button
            onClick={onMoveUp}
            disabled={isFirst}
            className="px-1 text-xs text-slate-400 hover:text-slate-600 disabled:opacity-30 dark:hover:text-slate-200"
            title={t("上へ")}
          >
            ▲
          </button>
          <button
            onClick={onMoveDown}
            disabled={isLast}
            className="px-1 text-xs text-slate-400 hover:text-slate-600 disabled:opacity-30 dark:hover:text-slate-200"
            title={t("下へ")}
          >
            ▼
          </button>
        </div>

        <input
          type="color"
          value={status.color}
          onChange={(e) => updateStatus.mutate({ id: status.id, color: e.target.value })}
          className="h-8 w-8 cursor-pointer rounded border border-slate-300 dark:border-slate-600"
          title={t("カラー")}
        />

        <input
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          onBlur={saveLabel}
          onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
        />

        <label className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
          <input
            type="checkbox"
            checked={status.isDone}
            onChange={(e) => updateStatus.mutate({ id: status.id, isDone: e.target.checked })}
            className="rounded"
          />
          {t("完了として扱う")}
        </label>

        <button
          onClick={handleDelete}
          className="rounded-lg px-2 py-1 text-xs font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30"
        >
          {t("削除")}
        </button>
      </div>
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </div>
  );
}

export function Settings() {
  const t = useT();
  const { language, setLanguage } = useLanguage();
  const { data: statuses = [] } = useStatuses();
  const createStatus = useCreateStatus();
  const reorderStatuses = useReorderStatuses();
  const [newLabel, setNewLabel] = useState("");
  const [newColor, setNewColor] = useState("#f59e0b");

  const handleCreate = () => {
    const label = newLabel.trim();
    if (!label) return;
    createStatus.mutate({ label, color: newColor });
    setNewLabel("");
  };

  const move = (index: number, delta: number) => {
    const ids = statuses.map((s) => s.id);
    const target = index + delta;
    if (target < 0 || target >= ids.length) return;
    [ids[index], ids[target]] = [ids[target], ids[index]];
    reorderStatuses.mutate(ids);
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-bold">{t("設定")}</h1>

      <section className="mt-6">
        <h2 className="text-sm font-semibold">{t("ステータス設定")}</h2>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          {t("タスクのステータスを追加・変更できます。「完了として扱う」を付けたステータスは、完了率の計算や期限超過の判定で完了済みとして扱われます。タスクで使用中のステータスは削除できません。")}
        </p>

        <div className="mt-4 space-y-2">
          {statuses.map((s, i) => (
            <StatusRow
              key={s.id}
              status={s}
              isFirst={i === 0}
              isLast={i === statuses.length - 1}
              onMoveUp={() => move(i, -1)}
              onMoveDown={() => move(i, 1)}
            />
          ))}
        </div>

        <div className="mt-4 flex items-center gap-2 rounded-lg border border-dashed border-slate-300 p-3 dark:border-slate-700">
          <input
            type="color"
            value={newColor}
            onChange={(e) => setNewColor(e.target.value)}
            className="h-8 w-8 cursor-pointer rounded border border-slate-300 dark:border-slate-600"
            title={t("カラー")}
          />
          <input
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            placeholder={t("新しいステータス名（例: レビュー中）")}
            className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
          />
          <button
            onClick={handleCreate}
            className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
          >
            {t("追加")}
          </button>
        </div>
      </section>

      <HolidaySettings />

      <section className="mt-8">
        <h2 className="text-sm font-semibold">{t("言語 / Language")}</h2>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          {t("表示言語を切り替えます。この設定はこのブラウザに保存されます。")}
        </p>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value as Language)}
          aria-label={t("言語 / Language")}
          className="mt-3 rounded-lg border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
        >
          {LANGUAGES.map((l) => (
            <option key={l.code} value={l.code}>
              {l.label}
            </option>
          ))}
        </select>
      </section>
    </div>
  );
}
