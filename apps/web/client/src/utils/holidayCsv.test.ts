import { readFileSync } from "node:fs";
import { describe, it, expect } from "vitest";
import { parseDate, parseHolidayCsv, splitCsv } from "./holidayCsv";

const bytes = (text: string) => new TextEncoder().encode(text).buffer;

describe("parseDate", () => {
  it("YYYY-MM-DD と YYYY/M/D を YYYY-MM-DD にそろえる", () => {
    expect(parseDate("2026-01-01")).toBe("2026-01-01");
    expect(parseDate("2026/1/5")).toBe("2026-01-05");
    expect(parseDate(" 2026/12/31 ")).toBe("2026-12-31");
  });

  it("存在しない日付・別形式は null", () => {
    expect(parseDate("2026-02-30")).toBeNull();
    expect(parseDate("日付")).toBeNull();
    expect(parseDate("01/01/2026")).toBeNull();
  });
});

describe("splitCsv", () => {
  it("引用符・カンマ入りの値・各種改行・BOM を扱える", () => {
    expect(splitCsv('﻿a,"b,c"\r\n"d""e",f\rg,h\n')).toEqual([
      ["a", "b,c"],
      ['d"e', "f"],
      ["g", "h"],
    ]);
  });
});

describe("parseHolidayCsv", () => {
  it("ヘッダー行と名称が空の行を読み飛ばす", () => {
    const rows = parseHolidayCsv(bytes("日付,名称\n2026-01-01,元日\n2026/2/11,建国記念の日\n2026-03-20,\n"));
    expect(rows).toEqual([
      { date: "2026-01-01", name: "元日" },
      { date: "2026-02-11", name: "建国記念の日" },
    ]);
  });

  it("Shift_JIS の CSV も読み込める", () => {
    // "2026-01-01,元日" を Shift_JIS で表したバイト列
    const sjis = new Uint8Array([
      0x32, 0x30, 0x32, 0x36, 0x2d, 0x30, 0x31, 0x2d, 0x30, 0x31, 0x2c, 0x8c, 0xb3, 0x93, 0xfa, 0x0a,
    ]);
    expect(parseHolidayCsv(sjis.buffer)).toEqual([{ date: "2026-01-01", name: "元日" }]);
  });

  it("どちらの文字コードでも読めないバイト列は null", () => {
    expect(parseHolidayCsv(new Uint8Array([0xff, 0xff, 0xfe, 0x80, 0x81, 0xff]).buffer)).toBeNull();
  });
});

describe("サンプルの祝日 CSV（samples/holidays_sample.csv）", () => {
  const file = readFileSync(new URL("../../../samples/holidays_sample.csv", import.meta.url));
  const buffer = file.buffer.slice(file.byteOffset, file.byteOffset + file.byteLength);

  it("そのまま取り込める（BOM つき UTF-8、ヘッダー行つき）", () => {
    const rows = parseHolidayCsv(buffer);
    expect(rows).not.toBeNull();
    expect(rows?.length).toBe(18);
    expect(rows?.[0]).toEqual({ date: "2026-01-01", name: "元日" });
  });

  it("全ての日付が 2026 年で、重複がない", () => {
    const rows = parseHolidayCsv(buffer) ?? [];
    expect(rows.every((r) => r.date.startsWith("2026-"))).toBe(true);
    expect(new Set(rows.map((r) => r.date)).size).toBe(rows.length);
  });
});
