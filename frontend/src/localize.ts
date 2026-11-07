import en from "./translations/en.json";
import nb from "./translations/nb.json";

/** English is the default language, and every language has the same keys (SPR-001). */
type Translations = typeof en;

const TRANSLATIONS: Record<string, Translations> = { en, nb };
const DEFAULT_LANGUAGE = "en";

type KeyPaths<T> = {
  [Key in keyof T & string]: T[Key] extends string ? Key : `${Key}.${KeyPaths<T[Key]>}`;
}[keyof T & string];

/** A key in the translations, like `tabs.status`. */
export type TranslationKey = KeyPaths<Translations>;

export type Localize = (key: TranslationKey, params?: Record<string, string | number>) => string;

/**
 * Return a function that looks up the panel's texts in the user's language (B8, SPR-002).
 *
 * A language without its own translations falls back to its base language, and
 * then to English. `{name}` in a text is replaced by the parameter `name`.
 */
export function localizer(language: string): Localize {
  const translations =
    TRANSLATIONS[language] ?? TRANSLATIONS[language.split("-")[0]] ?? TRANSLATIONS[DEFAULT_LANGUAGE];
  return (key, params = {}) => {
    const text = lookup(translations, key) ?? lookup(TRANSLATIONS[DEFAULT_LANGUAGE], key) ?? key;
    return text.replace(/\{(\w+)\}/g, (placeholder, name: string) =>
      name in params ? String(params[name]) : placeholder,
    );
  };
}

function lookup(translations: Translations, key: string): string | undefined {
  let value: unknown = translations;
  for (const part of key.split(".")) {
    value = (value as Record<string, unknown> | undefined)?.[part];
  }
  return typeof value === "string" ? value : undefined;
}
