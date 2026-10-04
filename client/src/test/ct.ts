import type { Page } from "@playwright/test";
import type { Holiday, StatusDef, Tag } from "../types";

export const statuses: StatusDef[] = [
  { id: "TODO", label: "未着手", color: "#64748b", order: 0, isDone: false },
  { id: "DONE", label: "完了", color: "#10b981", order: 1, isDone: true },
];

export const tags: Tag[] = [{ id: "tag1", name: "backend", color: "#0ea5e9" }];

/** UI 部品が呼ぶ API（ステータス・タグ・祝日の一覧）を、テスト用の固定値に差し替える。 */
export async function mockApi(
  page: Page,
  data: { statuses?: StatusDef[]; tags?: Tag[]; holidays?: Holiday[] } = {}
) {
  await page.route("**/api/statuses", (route) => route.fulfill({ json: data.statuses ?? statuses }));
  await page.route("**/api/tags", (route) => route.fulfill({ json: data.tags ?? tags }));
  await page.route("**/api/holidays", (route) => route.fulfill({ json: data.holidays ?? [] }));
}
