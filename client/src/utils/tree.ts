import type { Task } from "../types";

export interface TaskTreeNode extends Task {
  children: TaskTreeNode[];
}

export function buildTaskTree(tasks: Task[]): TaskTreeNode[] {
  const map = new Map<string, TaskTreeNode>();
  for (const t of tasks) map.set(t.id, { ...t, children: [] });

  const roots: TaskTreeNode[] = [];
  for (const node of map.values()) {
    if (node.parentId && map.has(node.parentId)) {
      map.get(node.parentId)!.children.push(node);
    } else {
      roots.push(node);
    }
  }

  const sortRec = (nodes: TaskTreeNode[]) => {
    nodes.sort((a, b) => a.order - b.order);
    nodes.forEach((n) => sortRec(n.children));
  };
  sortRec(roots);
  return roots;
}

export function countAll(nodes: TaskTreeNode[]): number {
  return nodes.reduce((sum, n) => sum + 1 + countAll(n.children), 0);
}

export function flattenNodes(
  nodes: TaskTreeNode[],
  depth = 0
): { node: TaskTreeNode; depth: number }[] {
  return nodes.flatMap((n) => [{ node: n, depth }, ...flattenNodes(n.children, depth + 1)]);
}

export function flattenWithDepth(
  nodes: TaskTreeNode[],
  depth = 0
): { id: string; title: string; depth: number }[] {
  return nodes.flatMap((n) => [
    { id: n.id, title: n.title, depth },
    ...flattenWithDepth(n.children, depth + 1),
  ]);
}
