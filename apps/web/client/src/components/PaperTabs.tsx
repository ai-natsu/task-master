import clsx from "clsx";

interface Tab<T extends string> {
  key: T;
  label: string;
}

/**
 * 紙のタブ風の切替（V2 の PaperTabs と同じ見た目）。上角だけ丸く、選択中のタブは
 * 本体の背景色で下端の線を消し、非選択のタブは濃いグレーで下端を線で閉じる。
 */
export function PaperTabs<T extends string>({
  value,
  onChange,
  tabs,
}: {
  value: T;
  onChange: (key: T) => void;
  tabs: Tab<T>[];
}) {
  return (
    <div className="flex items-end gap-0.5">
      {tabs.map((tab) => {
        const active = tab.key === value;
        return (
          <button
            key={tab.key}
            onClick={() => onChange(tab.key)}
            aria-pressed={active}
            className={clsx(
              "h-9 rounded-t-[10px] border px-[18px] text-sm",
              active
                ? "border-slate-400 border-b-transparent bg-slate-50 text-slate-900 dark:border-slate-500 dark:border-b-transparent dark:bg-slate-800 dark:text-slate-100"
                : "border-slate-400 bg-slate-300 text-slate-600 hover:bg-slate-200 dark:border-slate-500 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
            )}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
