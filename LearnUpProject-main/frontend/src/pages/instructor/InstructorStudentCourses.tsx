import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import { Spinner } from "../../components/Spinner";
import { useInstructorStudentUid } from "../../hooks/useInstructorStudentUid";
import * as instructorApi from "../../services/instructor";
import { getApiErrorMessage } from "../../services/api";

export default function InstructorStudentCourses() {
  const { uid } = useInstructorStudentUid();
  const [rows, setRows] = useState<instructorApi.InstructorCourseRow[]>([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!uid) return;
    (async () => {
      setLoading(true);
      try {
        setRows(await instructorApi.getStudentCourses(uid));
      } catch (e) {
        setErr(getApiErrorMessage(e));
      } finally {
        setLoading(false);
      }
    })();
  }, [uid]);

  if (!uid)
    return (
      <FeaturePageLayout title="Student courses">
        <Link to="/instructor/search" className="text-brand-600 font-semibold">
          Search a student first →
        </Link>
      </FeaturePageLayout>
    );

  if (loading)
    return (
      <div className="flex justify-center py-20">
        <Spinner />
      </div>
    );

  return (
    <FeaturePageLayout title="Registered courses" subtitle={`Student ${uid}`}>
      {err ? <p className="text-red-600 mb-4">{err}</p> : null}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-slate-500">
              <th className="pb-2">Code</th>
              <th className="pb-2">Title</th>
              <th className="pb-2">Credits</th>
              <th className="pb-2">Offering</th>
              <th className="pb-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.registration_id} className="border-b border-slate-50">
                <td className="py-2 font-mono text-brand-700">{r.course_code}</td>
                <td className="py-2">{r.course_title}</td>
                <td className="py-2">{r.credit_hours}</td>
                <td className="py-2">{r.course_offering_id}</td>
                <td className="py-2 capitalize">{r.registration_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </FeaturePageLayout>
  );
}
