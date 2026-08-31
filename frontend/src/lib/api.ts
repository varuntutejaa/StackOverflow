"use client";

import type { TokenPair } from "./types";

const RAW_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";
export const API_PREFIX = "/api/v1";
export const API_BASE = `${RAW_BASE}${API_PREFIX}`;
export const API_ROOT = RAW_BASE;

const ACCESS_KEY = "kaushai.access";
const REFRESH_KEY = "kaushai.refresh";
const USER_KEY = "kaushai.user";

export const tokenStore = {
  get access() {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(REFRESH_KEY);
  },
  set(pair: TokenPair) {
    localStorage.setItem(ACCESS_KEY, pair.access_token);
    localStorage.setItem(REFRESH_KEY, pair.refresh_token);
    localStorage.setItem(USER_KEY, JSON.stringify(pair.user));
    document.cookie = `kaushai_auth=1; path=/; max-age=${60 * 60 * 24 * 7}; samesite=lax`;
  },
  setAccess(token: string) {
    localStorage.setItem(ACCESS_KEY, token);
  },
  get user() {
    if (typeof window === "undefined") return null;
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    document.cookie = "kaushai_auth=; path=/; max-age=0";
  },
};

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `Request failed (${status})`);
    this.status = status;
    this.detail = detail;
  }
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = tokenStore.refresh;
  if (!refresh) return null;
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!res.ok) return null;
  const data = await res.json();
  tokenStore.setAccess(data.access_token);
  return data.access_token;
}

interface RequestOpts extends Omit<RequestInit, "body"> {
  body?: unknown;
  auth?: boolean;
  raw?: boolean;
}

export async function apiFetch<T = unknown>(path: string, opts: RequestOpts = {}): Promise<T> {
  const { body, auth = true, raw = false, headers, ...rest } = opts;
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;

  const doRequest = async (token: string | null): Promise<Response> => {
    const h: Record<string, string> = { ...(headers as Record<string, string>) };
    if (body !== undefined && !(body instanceof FormData)) h["content-type"] = "application/json";
    if (auth && token) h["authorization"] = `Bearer ${token}`;
    return fetch(url, {
      ...rest,
      headers: h,
      body:
        body === undefined
          ? undefined
          : body instanceof FormData
            ? body
            : JSON.stringify(body),
    });
  };

  let res = await doRequest(tokenStore.access);
  if (res.status === 401 && auth) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      res = await doRequest(newToken);
    } else {
      tokenStore.clear();
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
  }

  if (raw) return res as unknown as T;

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new ApiError(res.status, data?.detail ?? data ?? res.statusText);
  }
  return data as T;
}

export function qs(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}
