const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

function formatErrorDetail(detail) {
  if (!detail) return "Ошибка запроса";
  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item?.msg) return item.msg;
        return JSON.stringify(item);
      })
      .join(". ");
  }

  if (typeof detail === "object") {
    if (detail.msg) return detail.msg;
    return JSON.stringify(detail);
  }

  return String(detail);
}

export function getToken() {
  return localStorage.getItem("plusbally_token") || sessionStorage.getItem("plusbally_token");
}

export function setToken(token, remember = true) {
  if (remember) {
    localStorage.setItem("plusbally_token", token);
    sessionStorage.removeItem("plusbally_token");
    return;
  }

  sessionStorage.setItem("plusbally_token", token);
  localStorage.removeItem("plusbally_token");
}

export function logout() {
  localStorage.removeItem("plusbally_token");
  sessionStorage.removeItem("plusbally_token");
}

export async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Ошибка запроса" }));
    throw new Error(formatErrorDetail(error.detail));
  }

  return response.json();
}

export async function uploadFileWithPresign(file, purpose = "homework") {
  const presign = await api("/files/presign", {
    method: "POST",
    body: { file_name: file.name, content_type: file.type || "application/octet-stream", purpose }
  });

  await fetch(presign.upload_url, {
    method: "PUT",
    headers: { "Content-Type": file.type || "application/octet-stream" },
    body: file
  });

  return presign.file_key;
}
