import { useState } from "react";
import { LIMITS } from "../constants/limits";
import { useCreateTag, useDeleteTag, useTags, useUpdateTag } from "../api/tags";
import { useT } from "../i18n";
import { errorMessage } from "../utils/errorMessage";
import { ConfirmDialog } from "./ConfirmDialog";
import type { Tag } from "../types";

function TagRow({
  tag,
  onSuccess,
  onError,
  onDelete,
}: {
  tag: Tag;
  onSuccess: () => void;
  onError: (message: string) => void;
  onDelete: (tag: Tag) => void;
}) {
  const t = useT();
  const update = useUpdateTag({ inline: true });
  const [name, setName] = useState(tag.name);
  const handlers = { onSuccess, onError: (e: unknown) => onError(errorMessage(e, t)) };

  const commit = () => {
    const next = name.trim();
    if (!next || next === tag.name) {
      setName(tag.name); // 空や未変更は元に戻す
      return;
    }
    update.mutate({ id: tag.id, name: next }, { ...handlers, onError: (e) => {
      setName(tag.name); // 重複などで拒否されたら元の名前に戻す
      handlers.onError(e);
    } });
  };

  return (
    <div className="flex items-center gap-2">
      <input
        type="color"
        value={tag.color}
        onChange={(e) => update.mutate({ id: tag.id, color: e.target.value }, handlers)}
        title={t("カラー")}
        className="h-8 w-8 shrink-0 cursor-pointer rounded border border-slate-300 dark:border-slate-600"
      />
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
        aria-label={t("名前")}
        maxLength={LIMITS.tagName}
        className="flex-1 rounded-lg border border-slate-300 px-3 py-1 text-sm dark:border-slate-600 dark:bg-slate-900"
      />
      <button
        onClick={() => onDelete(tag)}
        className="rounded px-2 py-1 text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30"
      >
        {t("削除")}
      </button>
    </div>
  );
}

/** 設定画面の「タグ」セクション（V2 と同じ仕様：一覧・追加・改名・色変更・削除（件数つき確認）・重複名エラー）。 */
export function TagSettings() {
  const t = useT();
  const { data: tags = [] } = useTags();
  const create = useCreateTag({ inline: true });
  const remove = useDeleteTag({ inline: true });
  const [name, setName] = useState("");
  const [color, setColor] = useState("#94a3b8");
  const [deleting, setDeleting] = useState<Tag | undefined>();
  // 失敗（名前の重複など）は、タグの節の下に赤字で表示する
  const [error, setError] = useState("");
  const fail = (e: unknown) => setError(errorMessage(e, t));
  const clearError = () => setError("");

  const handleAdd = () => {
    const trimmed = name.trim();
    if (!trimmed) {
      setError(t("{field}を入力してください", { field: t("名前") }));
      return;
    }
    create.mutate(
      { name: trimmed, color },
      {
        onSuccess: () => {
          clearError();
          setName("");
        },
        onError: fail,
      }
    );
  };

  return (
    <section className="mt-8">
      <h2 className="text-sm font-semibold">{t("タグ")}</h2>
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
        {t("タグを管理します。プロジェクトを問わず全体で共有されます。新しいタグの作成もここから行えます。")}
      </p>

      <div className="mt-4 space-y-2">
        {tags.map((tag) => (
          <TagRow key={`${tag.id}:${tag.name}`} tag={tag} onSuccess={clearError} onError={setError} onDelete={setDeleting} />
        ))}
      </div>

      {error && (
        <p role="alert" className="mt-2 text-xs text-red-600">
          {error}
        </p>
      )}

      <div className="mt-4 flex items-center gap-2 rounded-lg border border-dashed border-slate-300 p-3 dark:border-slate-700">
        <input
          type="color"
          value={color}
          onChange={(e) => setColor(e.target.value)}
          title={t("カラー")}
          className="h-8 w-8 cursor-pointer rounded border border-slate-300 dark:border-slate-600"
        />
        <input
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            clearError();
          }}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          placeholder={t("新しいタグ名")}
          maxLength={LIMITS.tagName}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-900"
        />
        <button
          onClick={handleAdd}
          className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
        >
          {t("追加")}
        </button>
      </div>

      <ConfirmDialog
        open={!!deleting}
        title={t("タグを削除")}
        message={t("「{name}」タグを削除しますか？{count}件のタスクからこのタグが外れます。", {
          name: deleting?.name ?? "",
          count: deleting?._count?.tasks ?? 0,
        })}
        onConfirm={() => {
          if (deleting) remove.mutate(deleting.id, { onSuccess: clearError, onError: fail });
          setDeleting(undefined);
        }}
        onCancel={() => setDeleting(undefined)}
      />
    </section>
  );
}
