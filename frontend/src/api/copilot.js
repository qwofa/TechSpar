import { AUTH_EXPIRED_EVENT } from "./interview";

const API_BASE = "/api";

function notifyAuthExpired() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));
  }
}

function authHeaders(extra = {}) {
  const token = localStorage.getItem("token");
  const headers = { ...extra };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function authFetch(url, options = {}) {
  const headers = authHeaders(options.headers);
  const res = await fetch(url, { ...options, headers });
  if (res.status === 401) {
    notifyAuthExpired();
    throw new Error("Session expired");
  }
  return res;
}

// Safe error extractor — handles HTML responses from nginx/proxy.
async function extractError(res) {
  const ct = (res.headers.get("content-type") || "").toLowerCase();
  const text = await res.text();
  if (ct.includes("application/json")) {
    try {
      const json = JSON.parse(text);
      return json.detail || json.message || text.slice(0, 200);
    } catch {
      return text.slice(0, 200);
    }
  }
  if (text.trim().startsWith("<")) {
    return `请求失败 (HTTP ${res.status})，请稍后重试`;
  }
  return text.slice(0, 200);
}

/** 列出所有 Prep 会话 */
export async function listCopilotPreps() {
  const res = await authFetch(`${API_BASE}/copilot/preps`);
  if (!res.ok) throw new Error(await extractError(res));
  return res.json();
}

/** 删除 Prep 会话 */
export async function deleteCopilotPrep(prepId) {
  const res = await authFetch(`${API_BASE}/copilot/prep/${prepId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await extractError(res));
  return res.json();
}

/** 启动 Copilot Prep Phase */
export async function startCopilotPrep({ jdText, company, position }) {
  const form = new FormData();
  form.append("jd_text", jdText);
  if (company) form.append("company", company);
  if (position) form.append("position", position);

  const res = await authFetch(`${API_BASE}/copilot/prep`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await extractError(res));
  return res.json();
}

/** 查询 Prep 进度 */
export async function getCopilotPrepStatus(prepId) {
  const res = await authFetch(`${API_BASE}/copilot/prep/${prepId}`);
  if (!res.ok) throw new Error(await extractError(res));
  return res.json();
}

/** 获取策略树 */
export async function getCopilotStrategyTree(prepId) {
  const res = await authFetch(`${API_BASE}/copilot/prep/${prepId}/tree`);
  if (!res.ok) throw new Error(await extractError(res));
  return res.json();
}
