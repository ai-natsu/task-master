import { ApiError, UNEXPECTED_ERROR } from "../api/client";

/**
 * 画面に出すエラーメッセージ。サーバーが返した共通メッセージ（日本語）を、現在の言語に翻訳する。
 * API 以外のエラーや内容が分からないエラーは、想定外のエラーの共通メッセージにする。
 */
export function errorMessage(
  error: unknown,
  t: (text: string, vars?: Record<string, string | number>) => string
): string {
  if (error instanceof ApiError) return t(error.key ?? error.message, error.params);
  return t(UNEXPECTED_ERROR);
}
