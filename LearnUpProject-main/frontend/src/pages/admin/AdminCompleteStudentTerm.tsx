import { useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import * as adminApi from "../../services/admin";
import { getApiErrorMessage } from "../../services/api";

const TERM_OPTIONS = [
  { value: 0, label: "Level 1 — Semester 1 (courses 1–6)" },
  { value: 1, label: "Level 1 — Semester 2 (courses 7–12)" },
  { value: 2, label: "Level 2 — Semester 1" },
  { value: 3, label: "Level 2 — Semester 2" },
  { value: 4, label: "Level 3 — Semester 1" },
  { value: 5, label: "Level 3 — Semester 2" },
  { value: 6, label: "Level 4 — Semester 1" },
  { value: 7, label: "Level 4 — Semester 2" },
];

export default function AdminCompleteStudentTerm() {
  const [termIndex, setTermIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [lastResult, setLastResult] = useState<Record<string, unknown> | null>(null);

  const submit = async () => {
    setErr("");
    setMsg("");
    setLastResult(null);
    setLoading(true);
    try {
      const { data } = await adminApi.completeTermAllStudents({ term_index: termIndex });
      setLastResult(data as Record<string, unknown>);
      setMsg(String((data as { message?: string }).message ?? "Done."));
    } catch (e) {
      setErr(getApiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <FeaturePageLayout
      title="Complete term for all students"
      subtitle="Admin only: mark all six courses in a catalog term as passed for every student, and open the next term."
    >
      <div className="max-w-xl space-y-5">
        <div>
          <label className="block text-sm font-medium text-slate-700">Term to complete</label>
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
          <p className="mt-2 text-xs text-slate-500">
            Earlier terms must already be completed for each student. All six courses in the selected term are set to
            passed for every eligible student; the following term is opened with active registrations where needed.
          </p>
        </div>
        <button
          type="button"
          disabled={loading}
          onClick={submit}
          className="rounded-xl bg-brand-600 px-6 py-2.5 font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? "Processing…" : "Complete term for all students"}
        </button>
        {err ? <p className="text-sm text-red-600">{err}</p> : null}
        {msg ? <p className="text-sm text-emerald-600">{msg}</p> : null}
        {lastResult ? (
          <pre className="overflow-x-auto rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-800">
            {JSON.stringify(lastResult, null, 2)}
          </pre>
        ) : null}
      </div>
    </FeaturePageLayout>
  );
}
