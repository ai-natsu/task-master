import { describe, it, expect } from "vitest";
import { format } from "date-fns";
import { computeBar, computeMonths, computeRange } from "./gantt";
import { makeTask } from "../test/factories";

// `today` is passed in rather than read from the clock, so these need no fake
// timers and never drift with the calendar.
//
// Dates are built without a "Z" so they parse as local time, and asserted with
// date-fns `format` (also local). startOfDay works in local time, so mixing in
// UTC would make these assertions shift by a day depending on the machine's
// timezone.
const at = (day: string) => `${day}T00:00:00`;
const day = (d: Date) => format(d, "yyyy-MM-dd");
const TODAY = new Date(at("2026-07-14"));

describe("computeRange", () => {
  it("GA-4a: 全タスクの開始日〜期限を含み、前3日・後7日の余白が付く", () => {
    const tasks = [
      makeTask({ startDate: at("2026-07-10"), dueDate: at("2026-07-12") }),
      makeTask({ startDate: at("2026-07-20"), dueDate: at("2026-07-22") }),
    ];
    const { rangeStart, days } = computeRange(tasks, TODAY);

    // min は 07-10 → -3日 = 07-07、max は 07-22 → +7日 = 07-29
    expect(day(rangeStart)).toBe("2026-07-07");
    expect(day(days.at(-1)!)).toBe("2026-07-29");
    expect(days).toHaveLength(23); // 07-07 〜 07-29 は両端含めて23日
  });

  it("GA-4b: today が全タスクより前なら today を含むまで範囲が広がる", () => {
    const tasks = [makeTask({ startDate: at("2026-08-01"), dueDate: at("2026-08-02") })];
    const { rangeStart } = computeRange(tasks, TODAY);

    // today(07-14) が min(08-01) より前 → today基準 -3日 = 07-11
    expect(day(rangeStart)).toBe("2026-07-11");
  });

  it("GA-4c: today が全タスクより後なら today を含むまで範囲が広がる", () => {
    const tasks = [makeTask({ startDate: at("2026-06-01"), dueDate: at("2026-06-02") })];
    const { days } = computeRange(tasks, TODAY);

    // today(07-14) が max(06-02) より後 → today基準 +7日 = 07-21
    expect(day(days.at(-1)!)).toBe("2026-07-21");
  });

  it("GA-4d: 日付を持つタスクが無ければ today 起点の2週間+余白", () => {
    const tasks = [makeTask({ startDate: null, dueDate: null })];
    const { rangeStart, days } = computeRange(tasks, TODAY);

    expect(day(rangeStart)).toBe("2026-07-11"); // today -3
    expect(day(days.at(-1)!)).toBe("2026-08-03"); // today +13 +7
  });

  it("GA-4e: タスクが空配列でも破綻しない", () => {
    const { days } = computeRange([], TODAY);
    expect(days.length).toBeGreaterThan(0);
  });

  it("GA-4f: days は rangeStart から1日刻みで連続している", () => {
    const { rangeStart, days } = computeRange([makeTask({ dueDate: at("2026-07-20") })], TODAY);
    expect(day(days[0])).toBe(day(rangeStart));
    expect(day(days[1])).toBe(format(new Date(at("2026-07-12")), "yyyy-MM-dd")); // 07-11 の翌日
  });
});

describe("computeBar", () => {
  const rangeStart = new Date(at("2026-07-07"));

  it("GA-1: 開始日と期限の両方があるとき、幅は日数+1（両端を含む）", () => {
    const bar = computeBar({ startDate: at("2026-07-10"), dueDate: at("2026-07-12") }, rangeStart);
    expect(bar).toEqual({ offsetDays: 3, spanDays: 3 }); // 07-07→07-10 で3日、10〜12 で3日分
  });

  it("GA-1b: 開始日と期限が同日なら 1 日分", () => {
    const bar = computeBar({ startDate: at("2026-07-10"), dueDate: at("2026-07-10") }, rangeStart);
    expect(bar).toEqual({ offsetDays: 3, spanDays: 1 });
  });

  it("GA-2a: 期限のみのときは 1 日分のバー", () => {
    const bar = computeBar({ startDate: null, dueDate: at("2026-07-12") }, rangeStart);
    expect(bar).toEqual({ offsetDays: 5, spanDays: 1 });
  });

  it("GA-2b: 開始日のみのときは 1 日分のバー", () => {
    const bar = computeBar({ startDate: at("2026-07-09"), dueDate: null }, rangeStart);
    expect(bar).toEqual({ offsetDays: 2, spanDays: 1 });
  });

  it("GA-3: 開始日も期限も無いときはバーを描かない（null）", () => {
    expect(computeBar({ startDate: null, dueDate: null }, rangeStart)).toBeNull();
  });

  it("GA-3b: rangeStart より前の日付は負のオフセットになる", () => {
    const bar = computeBar({ startDate: at("2026-07-05"), dueDate: at("2026-07-06") }, rangeStart);
    expect(bar?.offsetDays).toBe(-2);
  });
});

describe("computeMonths", () => {
  it("GA-6: 月をまたぐ日付列を、月ごとの列数にまとめる", () => {
    const days = [
      new Date(at("2026-07-30")),
      new Date(at("2026-07-31")),
      new Date(at("2026-08-01")),
    ];
    expect(computeMonths(days)).toEqual([
      { label: "2026年7月", count: 2 },
      { label: "2026年8月", count: 1 },
    ]);
  });

  it("GA-6b: 空配列なら空", () => {
    expect(computeMonths([])).toEqual([]);
  });
});
