import axios from "axios";

export function apiErrorMessage(err: unknown, fallback: string): string {
  if (!axios.isAxiosError(err)) return fallback;
  const data = err.response?.data;
  if (typeof data === "string" && data.trim()) return data;
  if (data && typeof data === "object") {
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail) && detail.length) return String(detail[0]);
    // field errors: { email: ["..."] }
    for (const value of Object.values(data as Record<string, unknown>)) {
      if (typeof value === "string" && value.trim()) return value;
      if (Array.isArray(value) && value.length) return String(value[0]);
    }
  }
  return fallback;
}