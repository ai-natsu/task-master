import { useRef, useState } from "react";
import { LIMITS } from "../constants/limits";
import { format } from "date-fns";
import {
  useBulkHolidays,
  useDeleteHoliday,
  useHolidays,
  useRenameHoliday,
  useUpsertHoliday,
} from "../api/holidays";
import { useFormatDate, useT } from "../i18n";
import { parseHolidayCsv } from "../utils/holidayCsv";
import { errorMessage } from "../utils/errorMessage";
import type { Holiday } from "../types";

function HolidayRow({
  holiday,
  onSuccess,
  onError,
}: {
  holiday: Holiday;
  onSuccess: () => void;
  onError: (message: string) => void;
}) {
  const t = useT();
  const formatDate = useFormatDate();
  const rename = useRenameHoliday({ inline: true });
  const remove = useDeleteHoliday({ inline: true });
  const handlers = { onSuccess, onError: (e: unknown) => onError(errorMessage(e, t)) };
  const [name, setName] = useState(holiday.name);

  const commit = () => {
    const next = name.trim();
    if (!next || next === holiday.name) {
      setName(holiday.name); // 空や未変更は元に戻す
      return;
    }
    rename.mutate({ id: holiday.id, name: next }, handlers);
  };

  return (
    <div className="flex items-center gap-2">
      <span className="w-28 shrink-0 text-sm tabular-nums">{formatDate(holiday.date)}</span>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
        aria-label={t("名称")}
        maxLength={LIMITS.holidayName}
        className="flex-1 rounded-lg border border-slate-300 px-3 py-1 text-sm dark:border-slate-600 dark:bg-slate-900"
      />
      <button
        onClick={() => remove.mutate(holiday.id, handlers)}
        className="rounded px-2 py-1 text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30"
      >
        {t("削除")}
      </button>
    </div>
  );
}

/** 設定画面の「祝日」セクション（V2 と同じ仕様：一覧・追加・名称編集・削除・CSV 一括登録）。 */
export function HolidaySettings() {
  const t = useT();
  const { data: holidays = [] } = useHolidays();
  const upsert = useUpsertHoliday({ inline: true });
  const bulk = useBulkHolidays({ inline: true });
  // 追加・名称変更・削除の失敗は、祝日の節の下に赤字で表示する
  const [error, setError] = useState("");
  const clearError = () => setError("");
  const fileRef = useRef<HTMLInputElement>(null);
  const [date, setDate] = useState(() => format(new Date(), "yyyy-MM-dd"));
  const [name, setName] = useState("");
  const [csvResult, setCsvResult] = useState<{ text: string; error: boolean } | null>(null);

  const handleAdd = () => {
    const trimmed = name.trim();
    if (!date) {
      setError(t("{field}を入力してください", { field: t("日付") }));
      return;
    }
    if (!trimmed) {
      setError(t("{field}を入力してください", { field: t("名称") }));
      return;
    }
    upsert.mutate(
      { date, name: trimmed },
      { onSuccess: clearError, onError: (e) => setError(errorMessage(e, t)) }
    );
    setName("");
  };

  const handleCsv = async (file: File) => {
    const rows = parseHolidayCsv(await file.arrayBuffer());
    if (rows === null) {
      setCsvResult({ text: t("CSVの文字コードを判定できませんでした"), error: true });
      return;
    }
    try {
      const { count } = await bulk.mutateAsync(rows);
      setCsvResult({ text: t("{count} 件を登録・更新しました", { count }), error: false });
    } catch (e) {
      setCsvResult({ text: errorMessage(e, t), error: true });
    }
  };

  return (
    <section className="mt-8">
      <h2 className="text-sm font-semibold">{t("祝日")}</h2>
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
        {t("祝日を登録します。ガントチャート等での休日表示に使われます。日付が同じ行はCSV取り込み時に更新されます。")}
      </p>

      <div className="mt-4 space-y-2">
        {holidays.length > 0 && (
          <div className="flex gap-2 text-xs text-slate-400">
            <span className="w-28 shrink-0">{t("日付")}</span>
            <span>{t("名称")}</span>
          </div>
        )}
        {holidays.map((h) => (
          <HolidayRow key={h.id} holiday={h} onSuccess={clearError} onError={setError} />
        ))}
      </div>

      {error && (
        <p role="alert" className="mt-2 text-xs text-red-600">
          {error}
        </p>
      )}

      <div className="mt-4 flex items-center gap-2 rounded-lg border border-dashed border-slate-300 p-3 dark:border-slate-700">
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          aria-label={t("日付")}
          className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
        />
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          placeholder={t("新しい祝日名")}
          maxLength={LIMITS.holidayName}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
        />
        <button
          onClick={handleAdd}
          className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          {t("追加")}
        </button>
      </div>

      <div className="mt-3 flex items-center gap-3">
        <button
          onClick={() => fileRef.current?.click()}
          className="rounded-lg bg-indigo-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-600"
        >
          {t("CSVから読み込む")}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            e.target.value = ""; // 同じファイルを続けて選べるようにする
            if (file) void handleCsv(file);
          }}
        />
        {csvResult && (
          <span className={csvResult.error ? "text-xs text-red-600" : "text-xs text-slate-500 dark:text-slate-400"}>
            {csvResult.text}
          </span>
        )}
      </div>
    </section>
  );
}
