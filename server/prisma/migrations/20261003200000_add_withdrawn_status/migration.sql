-- 初期ステータスを V2 と同じ4件（未着手/進行中/完了/取下げ）にそろえる。
-- 初期の3件（TODO/IN_PROGRESS/DONE）だけが存在する状態のデータベースにのみ「取下げ」を追加する。
-- 利用者がステータスを編集・追加・削除済みのデータベースには何もしない。
INSERT INTO "Status" ("id", "label", "color", "order", "isDone")
SELECT 'WITHDRAWN', '取下げ', '#94a3b8', 3, 1
WHERE (SELECT COUNT(*) FROM "Status") = 3
  AND (SELECT COUNT(*) FROM "Status" WHERE "id" IN ('TODO', 'IN_PROGRESS', 'DONE')) = 3;
