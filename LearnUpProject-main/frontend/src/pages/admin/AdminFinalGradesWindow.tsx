import { useEffect, useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import * as adminApi from "../../services/admin";
import { getApiErrorMessage } from "../../services/api";

const TERM_OPTIONS = [
  { value: 0, label: "Level 1 — Semester 1" },
  { value: 1, label: "Level 1 — Semester 2" },
  { value: 2, label: "Level 2 — Semester 1" },
  { value: 3, label: "Level 2 — Semester 2" },
  { value: 4, label: "Level 3 — Semester 1" },
  { value: 5, label: "Level 3 — Semester 2" },
  { value: 6, label: "Level 4 — Semester 1" },
  { value: 7, label: "Level 4 — Semester 2" },
];

export default function AdminFinalGradesWindow() {
  const [termIndex, setTermIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<adminApi.FinalGradesWindowStatus | null>(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const loadStatus = async () => {
    setErr("");
    try {
      const s = await adminApi.getFinalGradesWindow();
      setStatus(s);
      if (s.term_index !== null) setTermIndex(s.term_index);
    } catch (e) {
      setErr(getApiErrorMessage(e));
    }
  };

  useEffect(() => {
    void loadStatus();
  }, []);

  const openWindow = async () => {
    setLoading(true);
    setErr("");
    setMsg("");
    try {
      const { data } = await adminApi.openFinalGradesWindow({ term_index: termIndex });
      setMsg(String((data as { message?: string }).message ?? "Opened."));
      await loadStatus();
    } catch (e) {
      setErr(getApiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  const closeWindow = async () => {
    setLoading(true);
    setErr("");
    setMsg("");
    try {
      const { data } = await adminApi.closeFinalGradesWindow();
      setMsg(String((data as { message?: string }).message ?? "Closed."));
      await loadStatus();
    } catch (e) {
      setErr(getApiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <FeaturePageLayout
      title="Final grades posting window"
      subtitle="Admin controls when instructors can submit final grades, and for which term."
    >
      <div className="max-w-xl space-y-5">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
          <p>
            Current status:{" "}
            <strong className={status?.is_open ? "text-emerald-700" : "text-red-700"}>
              {status?.is_open ? "OPEN" : "CLOSED"}
            </strong>
          </p>
          <p className="mt-1">
            Active term index: <strong>{status?.term_index ?? "-"}</strong>
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Term for final grade posting</label>
          <select
            value={termIndex}
            onChange={(e) => setTermIndex(Number(e.target.value))}
            className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 focus:ring-2 focus:ring-brand-500 outline-none"
          >
            {TERM_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            disabled={loading}
            onClick={openWindow}
            className="rounded-xl bg-emerald-600 px-5 py-2.5 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {loading ? "Working…" : "Open posting window"}
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={closeWindow}
            className="rounded-xl bg-slate-700 px-5 py-2.5 font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {loading ? "Working…" : "Close posting window"}
          </button>
        </div>

        {err ? <p className="text-sm text-red-600">{err}</p> : null}
        {msg ? <p className="text-sm text-emerald-600">{msg}</p> : null}
      </div>
    </FeaturePageLayout>
  );
}
