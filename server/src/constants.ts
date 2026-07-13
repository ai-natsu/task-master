export const PRIORITIES = ["LOW", "MEDIUM", "HIGH", "URGENT"] as const;

export type Priority = (typeof PRIORITIES)[number];
