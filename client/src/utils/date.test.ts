import { describe, it, expect } from "vitest";
import { formatDate } from "./date";

describe("formatDate", () => {
  it("日本語は YYYY年MM月DD日", () => {
    expect(formatDate("2026-10-05T00:00:00.000Z", "ja")).toBe("2026年10月05日");
    expect(formatDate("2026-01-09", "ja")).toBe("2026年01月09日");
  });

  it("英語は YYYY-MM-DD", () => {
    expect(formatDate("2026-10-05T00:00:00.000Z", "en")).toBe("2026-10-05");
    expect(formatDate("2026-10-05", "en")).toBe("2026-10-05");
  });
});
