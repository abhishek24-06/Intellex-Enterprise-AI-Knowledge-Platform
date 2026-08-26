"use client";

import { useRouter } from "next/navigation";
import * as React from "react";

import { getMe, login as loginApi } from "@/lib/api/auth";
import {
  clearStoredToken,
  getStoredToken,
  storeToken,
  UNAUTHORIZED_EVENT,
} from "@/lib/api/client";
import type { CurrentUser } from "@/types/api";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  user: CurrentUser | null;
  status: AuthStatus;
  login: (email: string, password: string) => Promise<CurrentUser>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = React.useState<CurrentUser | null>(null);
  const [status, setStatus] = React.useState<AuthStatus>("loading");

  React.useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const token = getStoredToken();
      if (!token) {
        setStatus("unauthenticated");
        return;
      }
      try {
        const me = await getMe();
        if (!cancelled) {
          setUser(me);
          setStatus("authenticated");
        }
      } catch {
        clearStoredToken();
        if (!cancelled) setStatus("unauthenticated");
      }
    }

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, []);

  React.useEffect(() => {
    function onUnauthorized() {
      setUser(null);
      setStatus("unauthenticated");
    }

    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, []);

  const login = React.useCallback(
    async (email: string, password: string): Promise<CurrentUser> => {
      const token = await loginApi(email, password);
      storeToken(token.access_token);

      try {
        const me = await getMe();
        setUser(me);
        setStatus("authenticated");
        return me;
      } catch (error) {
        clearStoredToken();
        throw error;
      }
    },
    [],
  );

  const logout = React.useCallback(() => {
    clearStoredToken();
    setUser(null);
    setStatus("unauthenticated");
    router.push("/login");
  }, [router]);

  const refresh = React.useCallback(async () => {
    const me = await getMe();
    setUser(me);
    setStatus("authenticated");
  }, []);

  const value = React.useMemo<AuthContextValue>(
    () => ({ user, status, login, logout, refresh }),
    [user, status, login, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = React.useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}
