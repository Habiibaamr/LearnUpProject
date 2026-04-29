import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, Lock, Mail } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage } from "../services/api";
import { getDashboardPath } from "../types";

export default function Login() {
  const { login, getIntendedRole } = useAuth();
  const navigate = useNavigate();
  const intended = getIntendedRole();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email.trim(), password.trim());
      const role = localStorage.getItem("learnup_role");
      if (role) {
        navigate(getDashboardPath(role), { replace: true });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : getApiErrorMessage(err);
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <div className="gradient-hero h-48 md:h-56 shrink-0" />
      <div className="flex-1 flex items-start justify-center px-4 -mt-24 pb-16">
        <div className="w-full max-w-md rounded-2xl bg-white shadow-card border border-slate-100 p-8 md:p-10">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-sm text-brand-600 hover:text-brand-800 font-medium mb-6"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to home
          </Link>
          <h1 className="font-display text-2xl font-bold text-slate-900">Sign in</h1>
          <p className="text-slate-500 text-sm mt-1 capitalize">
            {intended ? `${intended.replace(/_/g, " ")} portal` : "Use your university email"}
          </p>

          <form onSubmit={submit} className="mt-8 space-y-5">
            {error ? (
              <div className="rounded-xl bg-red-50 border border-red-100 text-red-700 text-sm px-4 py-3">
                {error}
              </div>
            ) : null}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 pl-11 pr-4 py-3 text-slate-900
                    focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-shadow"
                  placeholder="you@university.edu"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  type="password"
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 pl-11 pr-4 py-3 text-slate-900
                    focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-shadow"
                  placeholder="••••••••"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-brand-600 text-white font-semibold py-3.5 shadow-lg shadow-brand-600/25
                hover:bg-brand-700 active:scale-[0.98] transition-all disabled:opacity-60 disabled:pointer-events-none"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
