import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getPercentage(value: number): number {
  value = Math.min(Math.max(value, 10), 40);
  return ((40 - value) / 30) * 100;
}
