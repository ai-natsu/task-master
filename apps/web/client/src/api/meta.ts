export interface MutationOpts {
  /**
   * true のとき、失敗を画面全体のエラーダイアログに出さず、呼び出し側（フォームや設定画面の節）が
   * 自分の場所に赤字で表示する。false（既定）なら、共通のエラーダイアログに表示する。
   */
  inline?: boolean;
}

export function inlineMeta(opts?: MutationOpts) {
  return opts?.inline ? { inline: true } : undefined;
}
