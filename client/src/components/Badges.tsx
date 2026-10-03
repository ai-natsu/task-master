import clsx from "clsx";
import type { Priority, StatusDef, Tag } from "../types";
import { PRIORITY_COLORS, PRIORITY_LABELS } from "../types";
import { useT } from "../i18n";

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

export function TagPill({ tag, onRemove }: { tag: Tag; onRemove?: () => void }) {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ backgroundColor: `${tag.color}22`, color: tag.color }}
    >
      #{tag.name}
      {onRemove && (
        <button onClick={onRemove} className="hover:opacity-70">
          ×
        </button>
      )}
    </span>
  );
}
