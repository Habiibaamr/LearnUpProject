import { useEffect, useMemo, useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import { Spinner } from "../../components/Spinner";
import * as studentApi from "../../services/student";
import { getApiErrorMessage } from "../../services/api";

export default function Schedule() {
  const [rows, setRows] = useState<studentApi.StudentCourseRow[]>([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        setRows(await studentApi.getStudentCourses());
      } catch (e) {
        setErr(getApiErrorMessage(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const bySemester = useMemo(() => {
    const m = new Map<number, studentApi.StudentCourseRow[]>();
    for (const r of rows) {
      const list = m.get(r.semester_id) || [];
      list.push(r);
      m.set(r.semester_id, list);
    }
    return Array.from(m.entries()).sort((a, b) => a[0] - b[0]);
  }, [rows]);

  if (loading)
    return (
      <div className="flex justify-center py-20">
        <Spinner />
      </div>
    );

  return (
    <FeaturePageLayout title="Schedule overview" subtitle="Registered courses grouped by semester ID">
      {err ? <p className="text-red-600 mb-4">{err}</p> : null}
      <div className="space-y-8">
        {bySemester.length === 0 ? (
          <p className="text-slate-500">No active courses to display.</p>
        ) : (
          bySemester.map(([semId, courses]) => (
            <section key={semId}>
              <h3 className="font-display text-lg font-semibold text-brand-900 mb-3">
                Semester {semId}
              </h3>
              <ul className="space-y-2">
                {courses.map((c) => (
                  <li
                    key={c.registration_id}
                    className="rounded-xl border border-slate-100 bg-slate-50/80 px-4 py-3 flex flex-wrap justify-between gap-2"
                  >
                    <span className="font-medium text-slate-900">
                      {c.course_code} — {c.course_title}
                    </span>
                    <span className="text-sm text-slate-500">{c.credit_hours} cr</span>
                  </li>
                ))}
              </ul>
            </section>
          ))
        )}
      </div>
    </FeaturePageLayout>
  );
}
