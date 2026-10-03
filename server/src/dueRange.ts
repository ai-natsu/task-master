// 期限が近い = 本日〜3日後の4日間（日付単位）。期限日は UTC 0 時の日付として保存されている。
export const DUE_SOON_DAYS = 3;
const DAY_MS = 24 * 60 * 60 * 1000;

export function dueRange(now = new Date()) {
  // 「今日」はサーバー（=利用者）のローカル日付で決め、保存形式に合わせて UTC 0 時に変換する
  const todayStart = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
  const soonEnd = new Date(todayStart.getTime() + (DUE_SOON_DAYS + 1) * DAY_MS); // 排他的
  return { todayStart, soonEnd };
}
