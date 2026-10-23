import { createContext, useContext, type PointerEvent } from "react";
import type { RowDropZone } from "../utils/dnd";

export interface TreeDragState {
  id: string;
  startY: number;
  /** しきい値（5px）を超えて動いたらドラッグ。それまではクリック扱いにしない・ドラッグ扱いにもしない。 */
  moved: boolean;
  target: { id: string; zone: RowDropZone } | null;
}

export interface TreeDragContextValue {
  drag: TreeDragState | null;
  onHandlePointerDown: (id: string, e: PointerEvent<HTMLElement>) => void;
  onHandlePointerMove: (e: PointerEvent<HTMLElement>) => void;
  onHandlePointerUp: () => void;
  onHandleCancel: () => void;
}

const noop = () => undefined;

export const TreeDragContext = createContext<TreeDragContextValue>({
  drag: null,
  onHandlePointerDown: noop,
  onHandlePointerMove: noop,
  onHandlePointerUp: noop,
  onHandleCancel: noop,
});

export function useTreeDrag(): TreeDragContextValue {
  return useContext(TreeDragContext);
}
