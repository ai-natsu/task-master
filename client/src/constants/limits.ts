/**
 * 入力欄の文字数の上限（仕様：docs/BASIC_DESIGN.md の入力項目・データ定義）。
 * server/src/schemas.ts の zod スキーマの上限と同じ値にそろえる。
 */
export const LIMITS = {
  projectName: 200,
  projectDescription: 2000,
  taskTitle: 300,
  taskDescription: 5000,
  statusLabel: 50,
  tagName: 50,
  holidayName: 100,
} as const;
