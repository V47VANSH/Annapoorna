// Backend URL, set NEXT_PUBLIC_API_BASE_URL when deploying.
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

export function apiUrl(path) {
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

// fetch that throws on error responses and returns the JSON body
export async function apiFetch(path, options = {}) {
  const response = await fetch(apiUrl(path), options);

  let body = null;
  try {
    body = await response.json();
  } catch {
    // some endpoints return no JSON body
  }

  if (!response.ok) {
    const message =
      body?.detail || body?.error || `Request failed (${response.status})`;
    throw new Error(message);
  }
  return body;
}

export function apiPostJson(path, payload) {
  return apiFetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
