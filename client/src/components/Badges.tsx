import clsx from "clsx";
import type { Priority, StatusDef, Tag } from "../types";
import { PRIORITY_COLORS, PRIORITY_LABELS } from "../types";
import { useT } from "../i18n";
import { visibleTags } from "../utils/tags";

export function PriorityBadge({ priority }: { priority: Priority }) {
  const t = useT();
  return (
    <span className={clsx("rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap", PRIORITY_COLORS[priority])}>
      {t(PRIORITY_LABELS[priority])}
    </span>
  );
}

export function StatusBadge({ status }: { status: StatusDef }) {
  return (
    <span
      className="rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap"
      style={{ backgroundColor: `${status.color}22`, color: status.color }}
    >
      {status.label}
    </span>
  );
}

export function TagPill({
  tag,
  label,
  onRemove,
}: {
  tag: Tag;
  /** 表示する名前（省略時はタグ名そのまま。一覧では短くした名前を渡す） */
  label?: string;
  onRemove?: () => void;
}) {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ backgroundColor: `${tag.color}22`, color: tag.color }}
      title={tag.name}
    >
      {label ?? tag.name}
      {onRemove && (
        <button onClick={onRemove} className="hover:opacity-70">
          ×
        </button>
      )}
    </span>
  );
}

/**
 * 一覧・カード用のタグ表示。最大2件、名前は4文字までで、収まらない分は「...」にする
 * （隠れたタグ名はマウスオーバーで確認できる）。V2 のカンバンと同じ表示制御。
 */
export function TagList({ tags }: { tags: Tag[] }) {
  const { shown, hidden } = visibleTags(tags);
  return (
    <>
      {shown.map(({ tag, label }) => (
        <TagPill key={tag.id} tag={tag} label={label} />
      ))}
      {hidden.length > 0 && (
        <span
          title={hidden.map((t) => t.name).join(", ")}
          className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500 dark:bg-slate-700 dark:text-slate-300"
        >
          ...
        </span>
      )}
    </>
  );
}
