import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { fetchMe, login as loginRequest, type User } from "../api/accounts";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const access = localStorage.getItem("access");
    if (!access) {
      setUser(null);
      return;
    }
    const me = await fetchMe();
    setUser(me);
  }, []);

  useEffect(() => {
    refreshUser()
      .catch(() => {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await loginRequest(email, password);
    localStorage.setItem("access", tokens.access);
    localStorage.setItem("refresh", tokens.refresh);
    const me = await fetchMe();
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, logout, refreshUser }),
    [user, loading, login, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
