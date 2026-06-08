import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { AUTH_EXPIRED_EVENT } from "../api/interview";

const AuthContext = createContext(null);

function readStoredUser() {
  const stored = localStorage.getItem("user");
  if (!stored) return null;
  try {
    return JSON.parse(stored);
  } catch {
    localStorage.removeItem("user");
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredUser);
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [loading, setLoading] = useState(() => Boolean(localStorage.getItem("token")));
  const [needsOnboarding, setNeedsOnboarding] = useState(false);

  const login = useCallback((tokenStr, userData) => {
    localStorage.setItem("token", tokenStr);
    localStorage.setItem("user", JSON.stringify(userData));
    setLoading(true);
    setToken(tokenStr);
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
    setLoading(false);
    setNeedsOnboarding(false);
  }, []);

  useEffect(() => {
    const handleAuthExpired = () => logout();
    const handleStorage = (event) => {
      if (event.key === "token") {
        const nextToken = event.newValue;
        setToken(nextToken);
        if (!nextToken) {
          setUser(null);
          setLoading(false);
          setNeedsOnboarding(false);
          return;
        }
        setLoading(true);
        setUser(readStoredUser());
      }
      if (event.key === "user" && event.newValue) {
        setUser(readStoredUser());
      }
    };

    window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    window.addEventListener("storage", handleStorage);
    return () => {
      window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
      window.removeEventListener("storage", handleStorage);
    };
  }, [logout]);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    const headers = { Authorization: `Bearer ${token}` };

    setLoading(true);
    fetch("/api/auth/me", { headers })
      .then(async (res) => {
        if (res.status === 401 || res.status === 403) {
          const error = new Error("Invalid session");
          error.code = "AUTH_INVALID";
          throw error;
        }
        if (!res.ok) {
          const error = new Error(`Auth service unavailable (${res.status})`);
          error.code = "AUTH_UNAVAILABLE";
          throw error;
        }
        return res.json();
      })
      .then((data) => {
        if (cancelled) return;
        const nextUser = data.user || data;
        localStorage.setItem("user", JSON.stringify(nextUser));
        setUser(nextUser);
        setLoading(false);

        fetch("/api/settings", { headers })
          .then(async (settingsRes) => {
            if (!settingsRes.ok) return null;
            return settingsRes.json();
          })
          .then((settingsData) => {
            if (cancelled || !settingsData) return;
            const c = settingsData.configured || {};
            setNeedsOnboarding(!(c.llm && c.embedding));
          })
          .catch(() => {});
      })
      .catch((err) => {
        if (cancelled) return;
        if (err?.code === "AUTH_INVALID") {
          logout();
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token, logout]);

  return (
    <AuthContext.Provider value={{ user, token, loading, needsOnboarding, setNeedsOnboarding, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
