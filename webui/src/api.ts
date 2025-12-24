// webui/src/api.ts
export const API_BASE = "http://localhost:8000/api";

export async function postJSON(path: string, body: any) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {})
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || data.detail || "Request failed");
  }
  return data;
}

export async function getJSON(path: string) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "GET"
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || data.detail || "Request failed");
  }
  return data;
}
