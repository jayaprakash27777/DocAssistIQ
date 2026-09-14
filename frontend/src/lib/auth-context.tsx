/* eslint-disable @typescript-eslint/no-unused-vars */
/**
 * DocAssistIQ — Authentication Context.
 *
 * Provides the current authenticated user and loading state to all
 * shell components. Avoids calling authGetMe() in every page component.
 *
 * Usage:
 *   // In any shell child:
 *   const { user, loading, refetch } = useAuth();
 */

"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { authGetMe, clearStoredToken, getStoredToken, type MeResponse } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────

export type AuthState =
  | { status: "loading" }
  | { status: "authenticated"; user: MeResponse }
  | { status: "unauthenticated" }
  | { status: "forbidden" };

interface AuthContextValue {
  state: AuthState;
  user: MeResponse | null;
  loading: boolean;
  refetch: () => void;
  hasPermission: (resource: string, action: string) => boolean;
}

// ── Context ──────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

// ── Provider ─────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "loading" });

  const fetchUser = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      setState({ status: "unauthenticated" });
      return;
    }

    setState(prev => prev.status === "loading" ? prev : { status: "loading" });
    const result = await authGetMe();

    if (result.ok) {
      setState({ status: "authenticated", user: result.data });
    } else if (result.statusCode === 403) {
      setState({ status: "forbidden" });
    } else {
      clearStoredToken();
      setState({ status: "unauthenticated" });
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchUser();
  }, [fetchUser]);

  const user = state.status === "authenticated" ? state.user : null;
  const loading = state.status === "loading";

  const hasPermission = useCallback((resource: string, action: string) => {
    if (!user) return false;
    if (user.permissions.includes("*")) return true;
    return user.permissions.includes(`${resource}:${action}`);
  }, [user]);

  return (
    <AuthContext.Provider value={{ state, user, loading, refetch: fetchUser, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ─────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth() must be used inside <AuthProvider>");
  }
  return ctx;
}
