import { useEffect, useState } from "react";
import type { Project } from "../types";

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
  onSubmit: (value: ProjectFormValue) => void;
  onClose: () => void;
}

export function ProjectFormModal({ open, mode, initial, onSubmit, onClose }: Props) {
  const [value, setValue] = useState<ProjectFormValue>({
    name: initial?.name ?? "",
    description: initial?.description ?? "",
    color: initial?.color ?? COLORS[0],
  });

  useEffect(() => {
    if (open) {
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
          {mode === "create" ? "新しいプロジェクト" : "プロジェクトを編集"}
        </h3>

        <div className="mt-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-500">名前</label>
            <input
              autoFocus
              value={value.name}
              onChange={(e) => setValue((v) => ({ ...v, name: e.target.value }))}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
              placeholder="プロジェクト名"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500">説明</label>
            <textarea
              value={value.description}
              onChange={(e) => setValue((v) => ({ ...v, description: e.target.value }))}
              rows={2}
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-900"
              placeholder="説明（任意）"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-500">カラー</label>
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

        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-lg px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            キャンセル
          </button>
          <button
            onClick={() => value.name.trim() && onSubmit(value)}
            className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
          >
            {mode === "create" ? "作成" : "保存"}
          </button>
        </div>
      </div>
    </div>
  );
}
