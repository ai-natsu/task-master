import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProjectFormModal } from "./ProjectFormModal";
import { ConfirmDialog } from "./ConfirmDialog";

describe("ProjectFormModal", () => {
  it("名前が空のまま送信すると onSubmit は呼ばれず、必須の赤字を表示する", async () => {
    const onSubmit = vi.fn();
    render(<ProjectFormModal open mode="create" onSubmit={onSubmit} onClose={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: "作成" }));
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("名前を入力してください");
  });

  it("名前を入力し直すと赤字が消え、送信できる", async () => {
    const onSubmit = vi.fn();
    render(<ProjectFormModal open mode="create" onSubmit={onSubmit} onClose={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: "作成" }));
    await userEvent.type(screen.getByPlaceholderText("プロジェクト名"), "A");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "作成" }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });
});

describe("ConfirmDialog", () => {
  it("確定ボタンの文言と色を指定できる（アーカイブ・復元用）", () => {
    render(
      <ConfirmDialog
        open
        title="プロジェクトをアーカイブ"
        message="本当に？"
        confirmLabel="アーカイブする"
        danger={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    const button = screen.getByRole("button", { name: "アーカイブする" });
    expect(button.className).toContain("bg-indigo-600");
  });

  it("省略時は、従来どおり赤い「削除する」ボタン", () => {
    render(<ConfirmDialog open title="削除" message="本当に？" onConfirm={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByRole("button", { name: "削除する" }).className).toContain("bg-red-600");
  });
});
