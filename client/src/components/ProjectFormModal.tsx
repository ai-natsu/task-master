import { useEffect, useState } from "react";
import type { Project } from "../types";
import { useT } from "../i18n";

const COLORS = ["#6366f1", "#22c55e", "#ef4444", "#f59e0b", "#0ea5e9", "#a855f7", "#ec4899"];

export interface ProjectFormValue {
  name: string;
  description: string;
  color: string;
}

interface Props {
  open: boolean;
  mode: "create" | "edit";
  initial?: Project;
  onSubmit: (value: ProjectFormValue) => void | Promise<void>;
  onClose: () => void;
  /** 保存に失敗したときのメッセージ（モーダルを閉じず、ボタンの上に赤字で表示する） */
  error?: string;
}

export function ProjectFormModal({ open, mode, initial, onSubmit, onClose, error }: Props) {
  const t = useT();
  const [value, setValue] = useState<ProjectFormValue>({
    name: initial?.name ?? "",
    description: initial?.description ?? "",
    color: initial?.color ?? COLORS[0],
  });

  // 必須項目（名前）が未入力のまま保存しようとしたときの、項目の下に出す赤字
  const [nameError, setNameError] = useState("");

  useEffect(() => {
    if (open) {
      setNameError("");
      setValue({
        name: initial?.name ?? "",
        description: initial?.description ?? "",
        color: initial?.color ?? COLORS[0],
      });
    }
  }, [open, initial]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl dark:bg-slate-800">
        <h3 className="text-base font-semibold">
          {mode === "create" ? t("新しいプロジェクト") : t("プロジェクトを編集")}
        </h3>

        <div className="mt-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500">{t("名前")}</label>
            <input
              autoFocus
              value={value.name}
              onChange={(e) => {
                setValue((v) => ({ ...v, name: e.target.value }));
                if (nameError) setNameError("");
              }}
              className={`mt-1 w-full rounded-lg border px-3 py-2 text-sm dark:bg-slate-900 ${
                nameError ? "border-red-400" : "border-slate-300 dark:border-slate-600"
              }`}
              placeholder={t("プロジェクト名")}
              aria-invalid={!!nameError}
            />
            {nameError && (
              <p role="alert" className="mt-1 text-xs text-red-600">
                {nameError}
              </p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500">{t("説明")}</label>
            <textarea
              value={value.description}
              onChange={(e) => setValue((v) => ({ ...v, description: e.target.value }))}
              rows={2}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
              placeholder={t("説明（任意）")}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500">{t("カラー")}</label>
            <div className="mt-1 flex gap-2">
              {COLORS.map((c) => (
                <button
                  key={c}
                  onClick={() => setValue((v) => ({ ...v, color: c }))}
                  className="h-6 w-6 rounded-full"
                  style={{ backgroundColor: c, outline: value.color === c ? `2px solid ${c}` : "none", outlineOffset: 2 }}
                />
              ))}
            </div>
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
              if (!value.name.trim()) {
                setNameError(t("{field}を入力してください", { field: t("名前") }));
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
