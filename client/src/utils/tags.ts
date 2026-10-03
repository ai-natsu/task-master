import type { Tag } from "../types";

/** 一覧・カードに出すタグの最大件数（V2 のカンバンと同じ）。 */
export const MAX_VISIBLE_TAGS = 2;
/** タグ名を表示する最大文字数。超えたら「...」で省略する（V2 と同じ）。 */
export const MAX_TAG_NAME_LEN = 4;

export function truncateTagName(name: string): string {
  const chars = Array.from(name); // サロゲートペア（絵文字など）を1文字として数える
  return chars.length <= MAX_TAG_NAME_LEN ? name : `${chars.slice(0, MAX_TAG_NAME_LEN).join("")}...`;
}

/**
 * 表示するタグ（先頭から最大2件、名前は4文字まで）と、表示しきれずに隠れるタグを分ける。
 * 隠れるタグがあるときは、画面側で「...」のピルを添える。
 */
export function visibleTags(tags: Tag[]): { shown: { tag: Tag; label: string }[]; hidden: Tag[] } {
  return {
    shown: tags.slice(0, MAX_VISIBLE_TAGS).map((tag) => ({ tag, label: truncateTagName(tag.name) })),
    hidden: tags.slice(MAX_VISIBLE_TAGS),
  };
}
