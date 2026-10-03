import { describe, it, expect } from "vitest";
import { isDueSoon, isOverdue } from "./due";

const now = new Date(2026, 6, 14, 15, 30); // 2026-07-14 15:30（ローカル）
const iso = (day: string) => `${day}T00:00:00.000Z`;

describe("isOverdue", () => {
  it("前日は期限超過、当日は超過ではない（時刻に関係なく）", () => {
    expect(isOverdue(iso("2026-07-13"), now)).toBe(true);
    expect(isOverdue(iso("2026-07-14"), now)).toBe(false);
    expect(isOverdue(iso("2026-07-15"), now)).toBe(false);
  });
});

describe("isDueSoon", () => {
  it("本日〜3日後の4日間が対象", () => {
    expect(isDueSoon(iso("2026-07-13"), now)).toBe(false);
    expect(isDueSoon(iso("2026-07-14"), now)).toBe(true);
    expect(isDueSoon(iso("2026-07-17"), now)).toBe(true);
    expect(isDueSoon(iso("2026-07-18"), now)).toBe(false);
  });

  it("月またぎでも4日間", () => {
    const end = new Date(2026, 6, 30);
    expect(isDueSoon(iso("2026-08-02"), end)).toBe(true);
    expect(isDueSoon(iso("2026-08-03"), end)).toBe(false);
  });
});
