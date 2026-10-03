import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { en } from "./en";

export type Language = "ja" | "en";

export const LANGUAGES: { code: Language; label: string }[] = [
  { code: "ja", label: "日本語" },
  { code: "en", label: "English" },
];

const STORAGE_KEY = "taskmaster.language";

/**
 * 日本語の原文をキーに翻訳する。辞書にないキーは原文のまま返すので、未翻訳があっても
 * 画面は壊れない。`{name}` 形式のプレースホルダは vars で置き換える。
 */
export function translate(language: Language, text: string, vars?: Record<string, string | number>): string {
  const base = language === "en" ? (en[text] ?? text) : text;
  if (!vars) return base;
  return base.replace(/\{(\w+)\}/g, (match, key: string) => (key in vars ? String(vars[key]) : match));
}

function loadLanguage(): Language {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved === "en" || saved === "ja" ? saved : "ja";
  } catch {
    return "ja";
  }
}

interface LanguageContextValue {
  language: Language;
  setLanguage: (language: Language) => void;
}

// Provider なし（単体テストなど）では日本語固定で動く。
const LanguageContext = createContext<LanguageContextValue>({
  language: "ja",
  setLanguage: () => undefined,
});

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(loadLanguage);

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  const setLanguage = useCallback((next: Language) => {
    setLanguageState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // 保存できない環境（プライベートモード等）では、そのセッション中だけ有効
    }
  }, []);

  const value = useMemo(() => ({ language, setLanguage }), [language, setLanguage]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  return useContext(LanguageContext);
}

/** 現在の言語に翻訳する関数を返す。言語を切り替えると、これを使う画面は再描画される。 */
export function useT(): (text: string, vars?: Record<string, string | number>) => string {
  const { language } = useLanguage();
  return useCallback((text, vars) => translate(language, text, vars), [language]);
}
