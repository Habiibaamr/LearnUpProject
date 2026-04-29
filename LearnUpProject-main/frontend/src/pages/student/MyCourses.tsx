import { useEffect, useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import { Spinner } from "../../components/Spinner";
import * as studentApi from "../../services/student";
import { getApiErrorMessage } from "../../services/api";

export default function MyCourses() {
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

  if (loading)
    return (
      <div className="flex justify-center py-20">
        <Spinner />
      </div>
    );

  return (
    <FeaturePageLayout title="My Courses" subtitle="Active registrations">
      {err ? <p className="text-red-600 mb-4">{err}</p> : null}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-slate-500">
              <th className="pb-3 pr-4 font-medium">Code</th>
              <th className="pb-3 pr-4 font-medium">Title</th>
              <th className="pb-3 pr-4 font-medium">Credits</th>
              <th className="pb-3 pr-4 font-medium">Semester</th>
              <th className="pb-3 pr-4 font-medium">Offering</th>
              <th className="pb-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500">
                  No registered courses yet.
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr key={r.registration_id} className="border-b border-slate-100 hover:bg-slate-50/80">
                  <td className="py-3 pr-4 font-mono text-brand-700">{r.course_code}</td>
                  <td className="py-3 pr-4">{r.course_title}</td>
                  <td className="py-3 pr-4">{r.credit_hours}</td>
                  <td className="py-3 pr-4">{r.semester_id}</td>
                  <td className="py-3 pr-4">{r.course_offering_id}</td>
                  <td className="py-3">
                    <span className="rounded-full bg-emerald-50 text-emerald-700 px-2.5 py-0.5 text-xs font-medium capitalize">
                      {r.registration_status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </FeaturePageLayout>
  );
}
