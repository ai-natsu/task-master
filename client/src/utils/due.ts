// 期限の判定は日付単位。期限日は UTC 0 時の日付として保存されている（フォームの YYYY-MM-DD → ISO）。
export const DUE_SOON_DAYS = 3;

function localDayKey(d: Date): string {
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

/** 期限日が今日より前（今日が期限のものは含まない）。 */
export function isOverdue(dueDate: string, now = new Date()): boolean {
  return dueDate.slice(0, 10) < localDayKey(now);
}

/** 期限日が本日〜3日後（4日間）。 */
export function isDueSoon(dueDate: string, now = new Date()): boolean {
  const key = dueDate.slice(0, 10);
  const last = new Date(now.getFullYear(), now.getMonth(), now.getDate() + DUE_SOON_DAYS);
  return key >= localDayKey(now) && key <= localDayKey(last);
}
