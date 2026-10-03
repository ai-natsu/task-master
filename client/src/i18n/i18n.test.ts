import { describe, it, expect } from "vitest";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { en } from "./en";
import { translate } from "./index";

describe("translate", () => {
  it("日本語はそのまま返し、英語は辞書を引く", () => {
    expect(translate("ja", "キャンセル")).toBe("キャンセル");
    expect(translate("en", "キャンセル")).toBe("Cancel");
  });

  it("辞書にない文字列は原文のまま返す（未翻訳でも画面は壊れない）", () => {
    expect(translate("en", "辞書にない文言")).toBe("辞書にない文言");
  });

  it("{name} 形式のプレースホルダを置き換える", () => {
    expect(translate("en", "{count} 件のタスク", { count: 3 })).toBe("3 tasks");
    expect(translate("ja", "{count} 件のタスク", { count: 3 })).toBe("3 件のタスク");
  });

  it("値が渡されないプレースホルダはそのまま残す", () => {
    expect(translate("en", "{count} 件のタスク", {})).toBe("{count} tasks");
  });
});

function listSources(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return name === "i18n" ? [] : listSources(path);
    return /\.tsx?$/.test(name) && !/\.test\./.test(name) ? [path] : [];
  });
}

describe("英語辞書の網羅性", () => {
  it('ソース中の t("...") の日本語キーはすべて辞書にある', () => {
    const missing: string[] = [];
    for (const file of listSources(join(__dirname, ".."))) {
      const source = readFileSync(file, "utf-8");
      for (const m of source.matchAll(/\bt\("((?:[^"\\]|\\.)*)"/g)) {
        const key = m[1].replace(/\\"/g, '"').replace(/\\\\/g, "\\");
        if (!(key in en)) missing.push(`${file}: ${key}`);
      }
    }
    expect(missing).toEqual([]);
  });
});
