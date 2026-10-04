import { useT } from "../i18n";

interface Props {
  open: boolean;
  title: string;
  message: string;
  /** 確定ボタンの文言（省略時は「削除する」） */
  confirmLabel?: string;
  /** 危険な操作（削除など）は赤、通常の操作（アーカイブ・復元など）は藍色のボタンにする（省略時は赤） */
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({ open, title, message, confirmLabel, danger = true, onConfirm, onCancel }: Props) {
  const t = useT();
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl dark:bg-slate-800">
        <h3 className="text-base font-semibold">{title}</h3>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{message}</p>
        <div className="mt-4 flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="rounded-lg px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:hover:bg-slate-700"
          >
            {t("キャンセル")}
          </button>
          <button
            onClick={onConfirm}
            className={
              danger
                ? "rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
                : "rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
            }
          >
            {confirmLabel ?? t("削除する")}
          </button>
        </div>
      </div>
    </div>
  );
}
