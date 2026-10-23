const BASE = "/api";

/** 想定外のエラー（通信できない、サーバーの不具合など）の共通メッセージ。 */
export const UNEXPECTED_ERROR = "予期しないエラーが発生しました。もう一度お試しください";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    /** パラメータ付きメッセージのテンプレート（例：「{count} 件…」）。翻訳に使う。 */
    public key?: string,
    public params?: Record<string, string | number>
  ) {
    super(message);
  }
}

interface ErrorBody {
  error?: unknown;
  key?: string;
  params?: Record<string, string | number>;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });
  } catch {
    throw new ApiError(0, UNEXPECTED_ERROR);
  }
  if (!res.ok) {
    const body = (await res.json().catch(() => ({}))) as ErrorBody;
    const message = typeof body.error === "string" ? body.error : UNEXPECTED_ERROR;
    throw new ApiError(res.status, message, body.key, body.params);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(data) }),
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(data) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
