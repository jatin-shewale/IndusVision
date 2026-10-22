import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import api from "../api/client";
import type { User } from "../types";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("indusvision_user");
    const token = localStorage.getItem("indusvision_access_token");
    if (stored && token) {
      setUser(JSON.parse(stored));
    }
    setLoading(false);
  }, []);

  async function login(email: string, password: string) {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    const res = await api.post("/api/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    localStorage.setItem("indusvision_access_token", res.data.access_token);
    localStorage.setItem("indusvision_refresh_token", res.data.refresh_token);
    localStorage.setItem("indusvision_user", JSON.stringify(res.data.user));
    setUser(res.data.user);
  }

  function logout() {
    localStorage.removeItem("indusvision_access_token");
    localStorage.removeItem("indusvision_refresh_token");
    localStorage.removeItem("indusvision_user");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
