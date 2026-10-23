import { useEffect, useState, type ReactNode } from "react";
import { errorMessage } from "../utils/errorMessage";
import { useT } from "../i18n";

// 画面のどこからでもエラーダイアログを出せるようにするための橋渡し（QueryClient は React の外で作られる）
let reporter: ((error: unknown) => void) | null = null;

/** 共通のエラーダイアログに表示する（一覧・ビュー上の操作失敗や、想定外のエラー）。 */
export function reportError(error: unknown) {
  reporter?.(error);
}

export function ErrorProvider({ children }: { children: ReactNode }) {
  const t = useT();
  const [error, setError] = useState<{ error: unknown } | null>(null);

  useEffect(() => {
    reporter = (e) => setError({ error: e });
    return () => {
      reporter = null;
    };
  }, []);

  return (
    <>
      {children}
      {error && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 p-4" role="alertdialog">
          <div className="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl dark:bg-slate-800">
            <h3 className="text-base font-semibold">{t("エラー")}</h3>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{errorMessage(error.error, t)}</p>
            <div className="mt-4 flex justify-end">
              <button
                autoFocus
                onClick={() => setError(null)}
                className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
              >
                {t("OK")}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
