import type { Language } from "../i18n";

/**
 * 期限・開始日・祝日の表示形式（V2 と同じ）。日本語は「2026年10月05日」、英語は「2026-10-05」。
 * 保存されている日付部分（先頭10文字）をそのまま使うので、タイムゾーンで表示がずれない。
 */
export function formatDate(iso: string, language: Language): string {
  const day = iso.slice(0, 10);
  if (language !== "ja") return day;
  const [year, month, date] = day.split("-");
  return `${year}年${month}月${date}日`;
}
