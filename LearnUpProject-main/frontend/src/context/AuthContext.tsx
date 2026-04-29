import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useNavigate } from "react-router-dom";
import * as authApi from "../services/auth";
import { LEARNUP_TOKEN_KEY } from "../services/api";
import { getDashboardPath, type Role, type UserMe } from "../types";

const TOKEN_KEY = LEARNUP_TOKEN_KEY;
const ROLE_KEY = "learnup_role";
const INTENDED_ROLE_KEY = "learnup_intended_role";

type AuthContextValue = {
  user: UserMe | null;
  token: string | null;
  loading: boolean;
  setIntendedRole: (role: Role | null) => void;
  getIntendedRole: () => Role | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserMe | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t) {
      setUser(null);
      return;
    }
    const me = await authApi.fetchMe();
    setUser(me);
    localStorage.setItem(ROLE_KEY, me.role);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        if (token) await refreshUser();
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(ROLE_KEY);
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [token, refreshUser]);

  const setIntendedRole = useCallback((role: Role | null) => {
    if (role) sessionStorage.setItem(INTENDED_ROLE_KEY, role);
    else sessionStorage.removeItem(INTENDED_ROLE_KEY);
  }, []);

  const getIntendedRole = useCallback((): Role | null => {
    const r = sessionStorage.getItem(INTENDED_ROLE_KEY) as Role | null;
    if (
      r === "student" ||
      r === "instructor" ||
      r === "admin" ||
      r === "super_admin"
    ) {
      return r;
    }
    return null;
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await authApi.login(email, password);
      const intended = getIntendedRole();
      if (intended && res.role !== intended) {
        throw new Error(
          `This account is registered as ${res.role}. Please use the ${res.role} entrance or pick the correct role on the home page.`
        );
      }
      sessionStorage.removeItem(INTENDED_ROLE_KEY);
      localStorage.setItem(TOKEN_KEY, res.access_token);
      localStorage.setItem(ROLE_KEY, res.role);
      try {
        const me = await authApi.fetchMe(res.access_token);
        setToken(res.access_token);
        setUser(me);
      } catch (e) {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(ROLE_KEY);
        throw e;
      }
    },
    [getIntendedRole]
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(ROLE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      setIntendedRole,
      getIntendedRole,
      login,
      logout,
      refreshUser,
    }),
    [user, token, loading, setIntendedRole, getIntendedRole, login, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function useAuthNavigate() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return {
    user,
    logout: () => {
      logout();
      navigate("/");
    },
    goDashboard: () => {
      if (!user) return;
      navigate(getDashboardPath(user.role));
    },
  };
}
