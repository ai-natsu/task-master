import { describe, it, expect } from "vitest";
import { truncateTagName, visibleTags } from "./tags";
import type { Tag } from "../types";

const tag = (id: string, name: string): Tag => ({ id, name, color: "#0ea5e9" });

describe("truncateTagName", () => {
  it("4文字まではそのまま、超えたら4文字＋「...」", () => {
    expect(truncateTagName("design")).toBe("desi...");
    expect(truncateTagName("abcd")).toBe("abcd");
    expect(truncateTagName("とても長いタグ名")).toBe("とても長...");
  });

  it("絵文字などサロゲートペアを1文字として数える", () => {
    expect(truncateTagName("😀😀😀😀")).toBe("😀😀😀😀");
    expect(truncateTagName("😀😀😀😀😀")).toBe("😀😀😀😀...");
  });
});

describe("visibleTags", () => {
  it("2件までは全部表示し、隠れるタグはない", () => {
    const r = visibleTags([tag("1", "a"), tag("2", "b")]);
    expect(r.shown.map((s) => s.label)).toEqual(["a", "b"]);
    expect(r.hidden).toEqual([]);
  });

  it("3件以上は先頭2件を表示し、残りは隠れるタグにする", () => {
    const r = visibleTags([tag("1", "alpha"), tag("2", "b"), tag("3", "c"), tag("4", "d")]);
    expect(r.shown.map((s) => s.label)).toEqual(["alph...", "b"]);
    expect(r.hidden.map((t) => t.id)).toEqual(["3", "4"]);
  });

  it("タグなしは何も表示しない", () => {
    expect(visibleTags([])).toEqual({ shown: [], hidden: [] });
  });
});
