import { createContext, useContext, useState, useEffect } from "react";

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

  function login(tokenStr, userData) {
    localStorage.setItem("token", tokenStr);
    localStorage.setItem("user", JSON.stringify(userData));
    setLoading(true);
    setToken(tokenStr);
    setUser(userData);
  }

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
    setLoading(false);
    setNeedsOnboarding(false);
  }

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
        if (!res.ok) throw new Error("Invalid session");
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
      .catch(() => {
        if (!cancelled) logout();
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, loading, needsOnboarding, setNeedsOnboarding, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
