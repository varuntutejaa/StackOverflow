"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { apiFetch, tokenStore } from "./api";
import { isSupabaseAuthConfigured, supabase } from "./supabase";
import type { Role, TokenPair, UserPublic } from "./types";

interface AuthCtx {
  user: UserPublic | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<UserPublic>;
  register: (payload: RegisterPayload) => Promise<UserPublic>;
  logout: () => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  refreshUser: () => Promise<void>;
  hasRole: (...roles: Role[]) => boolean;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  role: Role;
  organisation?: string;
  district?: string;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refreshUser = useCallback(async () => {
    if (!tokenStore.access) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await apiFetch<UserPublic>("/auth/me");
      setUser(me);
    } catch {
      setUser(tokenStore.user);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setUser(tokenStore.user);
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const pair = await apiFetch<TokenPair>("/auth/login", {
      method: "POST",
      auth: false,
      body: { email, password },
    });
    tokenStore.set(pair);
    setUser(pair.user);
    return pair.user;
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    const pair = await apiFetch<TokenPair>("/auth/register", {
      method: "POST",
      auth: false,
      body: payload,
    });
    tokenStore.set(pair);
    setUser(pair.user);
    return pair.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiFetch("/auth/logout", { method: "POST" });
    } catch {
      /* ignore */
    }
    tokenStore.clear();
    setUser(null);
    router.push("/login");
  }, [router]);

  const loginWithGoogle = useCallback(async () => {
    if (!isSupabaseAuthConfigured || !supabase) {
      throw new Error("Supabase Auth is not configured");
    }
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
        queryParams: {
          access_type: "offline",
          prompt: "consent",
        },
      },
    });
    if (error) throw error;
  }, []);

  const hasRole = useCallback(
    (...roles: Role[]) => !!user && (roles.length === 0 || roles.includes(user.role)),
    [user],
  );

  return (
    <Ctx.Provider value={{ user, loading, login, register, logout, loginWithGoogle, refreshUser, hasRole }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
