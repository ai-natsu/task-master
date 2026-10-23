import type { Response } from "express";
import type { ZodError } from "zod";

// 利用者に見せるエラーメッセージ（V2 と共通。日本語を原文とし、英語表示は画面側の辞書で翻訳する）。
// `{name}` はパラメータ。パラメータ付きは `key`（テンプレート）と `params` も返し、画面側が翻訳に使う。
export const MSG = {
  projectNotFound: "プロジェクトが見つかりません",
  taskNotFound: "タスクが見つかりません",
  statusNotFound: "ステータスが見つかりません",
  tagNotFound: "タグが見つかりません",
  holidayNotFound: "祝日が見つかりません",
  parentNotFound: "親タスクが見つかりません",
  invalidStatus: "指定のステータスが存在しません",
  noStatuses: "ステータスが1件もありません",
  invalidInput: "入力内容を確認してください",
  invalidInputField: "入力内容を確認してください（{field}）",
  tagExists: "タグが既に存在します",
  statusInUse: "このステータスは {count} 件のタスクで使用中のため削除できません",
  lastStatus: "最後のステータスは削除できません",
  cycle: "タスクを自分自身またはその配下には移動できません",
  unexpected: "予期しないエラーが発生しました。もう一度お試しください",
} as const;

type Params = Record<string, string | number>;

function fill(template: string, params: Params): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) => (key in params ? String(params[key]) : match));
}

export function sendError(res: Response, status: number, message: string, params?: Params) {
  if (!params) return res.status(status).json({ error: message });
  return res.status(status).json({ error: fill(message, params), key: message, params });
}

/** zod の検証エラーを、先頭の指摘の項目名つきの共通メッセージにして 400 で返す。 */
export function sendValidationError(res: Response, error: ZodError) {
  const field = error.issues[0]?.path.join(".");
  return field
    ? sendError(res, 400, MSG.invalidInputField, { field })
    : sendError(res, 400, MSG.invalidInput);
}
