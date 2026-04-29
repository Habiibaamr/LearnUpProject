import { useEffect, useMemo, useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import * as studentApi from "../../services/student";
import { getApiErrorMessage } from "../../services/api";

export default function AddDropCourses() {
  const [rows, setRows] = useState<studentApi.CourseBoardRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyCourseId, setBusyCourseId] = useState<number | null>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [tab, setTab] = useState<"all" | "available" | "enrolled" | "locked" | "passed">("all");

  const loadBoard = async () => {
    setLoading(true);
    setErr("");
    try {
      setRows(await studentApi.getCourseBoard());
    } catch (e) {
      setErr(getApiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBoard();
  }, []);

  const filtered = useMemo(() => {
    if (tab === "all") return rows;
    return rows.filter((r) => r.status === tab);
  }, [rows, tab]);

  const tabs: Array<{ key: typeof tab; label: string }> = [
    { key: "all", label: `All (${rows.length})` },
    {
      key: "available",
      label: `Available (${rows.filter((r) => r.status === "available").length})`,
    },
    {
      key: "enrolled",
      label: `Enrolled (${rows.filter((r) => r.status === "enrolled").length})`,
    },
    { key: "locked", label: `Locked (${rows.filter((r) => r.status === "locked").length})` },
    { key: "passed", label: `Passed (${rows.filter((r) => r.status === "passed").length})` },
  ];

  const runAction = async (row: studentApi.CourseBoardRow, action: "add" | "drop") => {
    setMsg("");
    setErr("");
    setBusyCourseId(row.course_id);
    try {
      if (action === "add") await studentApi.addStudentCourseByCourse(row.course_id);
      else await studentApi.dropStudentCourseByCourse(row.course_id);
      setMsg(action === "add" ? "Course enrolled successfully." : "Course dropped successfully.");
      await loadBoard();
    } catch (e) {
      setErr(getApiErrorMessage(e));
    } finally {
      setBusyCourseId(null);
    }
  };

  const badgeClasses = (status: studentApi.CourseBoardStatus) => {
    if (status === "available") return "bg-blue-50 text-blue-700 border-blue-200";
    if (status === "enrolled") return "bg-emerald-50 text-emerald-700 border-emerald-200";
    if (status === "passed") return "bg-amber-50 text-amber-700 border-amber-200";
    return "bg-rose-50 text-rose-700 border-rose-200";
  };

  return (
    <FeaturePageLayout
      title="Course Board"
      subtitle="Enroll or drop courses based on your level and completed prerequisites."
    >
      <div className="space-y-5">
        <div className="flex flex-wrap gap-2">
          {tabs.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setTab(t.key)}
              className={`rounded-full border px-4 py-1.5 text-sm font-medium transition ${
                tab === t.key
                  ? "border-brand-600 bg-brand-600 text-white"
                  : "border-slate-200 bg-white text-slate-600 hover:border-brand-300 hover:text-brand-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {loading ? <p className="text-slate-500">Loading course board...</p> : null}
        {err ? <p className="text-red-600">{err}</p> : null}
        {msg ? <p className="text-emerald-600">{msg}</p> : null}

        {!loading && filtered.length === 0 ? (
          <p className="text-slate-500">No courses in this view.</p>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((row) => (
            <div key={row.course_id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  {row.course_code}
                </p>
                <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${badgeClasses(row.status)}`}>
                  {row.status}
                </span>
              </div>
              <h3 className="mt-2 text-lg font-bold text-slate-900">{row.title}</h3>
              <p className="mt-1 text-sm text-slate-600">
                Level {row.level ?? "—"} • {row.credit_hours} credit hours
              </p>

              {row.status === "locked" ? (
                <p className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">
                  {row.lock_reason ?? "Locked"}
                </p>
              ) : null}

              <div className="mt-4 flex gap-2">
                <button
                  type="button"
                  disabled={!row.can_add || busyCourseId === row.course_id}
                  onClick={() => runAction(row, "add")}
                  className="flex-1 rounded-xl bg-brand-600 px-3 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-500"
                >
                  Enroll
                </button>
                <button
                  type="button"
                  disabled={!row.can_drop || busyCourseId === row.course_id}
                  onClick={() => runAction(row, "drop")}
                  className="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
                >
                  Drop
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </FeaturePageLayout>
  );
}
