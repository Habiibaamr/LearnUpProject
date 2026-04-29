import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import { Spinner } from "../../components/Spinner";
import { useInstructorStudentUid } from "../../hooks/useInstructorStudentUid";
import * as instructorApi from "../../services/instructor";
import { getApiErrorMessage } from "../../services/api";

export default function InstructorStudentProfile() {
  const { uid } = useInstructorStudentUid();
  const [data, setData] = useState<instructorApi.InstructorStudentProfile | null>(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!uid) {
      setData(null);
      return;
    }
    (async () => {
      setLoading(true);
      setErr("");
      try {
        setData(await instructorApi.getStudentByUniversityId(uid));
      } catch (e) {
        setErr(getApiErrorMessage(e));
        setData(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [uid]);

  if (!uid) {
    return (
      <FeaturePageLayout title="Student profile" subtitle="Select a student first">
        <p className="text-slate-600 mb-4">No student selected.</p>
        <Link to="/instructor/search" className="text-brand-600 font-semibold hover:underline">
          Go to search →
        </Link>
      </FeaturePageLayout>
    );
  }

  if (loading)
    return (
      <div className="flex justify-center py-20">
        <Spinner />
      </div>
    );

  if (err)
    return (
      <FeaturePageLayout title="Student profile">
        <p className="text-red-600">{err}</p>
        <Link to="/instructor/search" className="inline-block mt-4 text-brand-600 font-semibold">
          Try another ID
        </Link>
      </FeaturePageLayout>
    );

  if (!data) return null;

  return (
    <FeaturePageLayout title="Student profile" subtitle={data.university_id}>
      <div className="flex flex-wrap gap-6">
        <div className="w-32 h-40 rounded-xl bg-brand-100 overflow-hidden border border-white shadow">
          {data.photo_url ? (
            <img src={data.photo_url} alt="" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-2xl font-bold text-brand-700">
              {data.full_name.charAt(0)}
            </div>
          )}
        </div>
        <dl className="grid sm:grid-cols-2 gap-4 flex-1 text-sm">
          {Object.entries({
            Name: data.full_name,
            Email: data.email,
            "Faculty ID": data.faculty_id ?? "—",
            "Department ID": data.department_id ?? "—",
            Level: data.level ?? "—",
            CGPA: data.cgpa ?? "—",
            "Passed credits": data.passed_credit_hours ?? "—",
            Phone: data.phone ?? "—",
            "Advisor instructor ID": data.advisor_instructor_id ?? "—",
          }).map(([k, v]) => (
            <div key={k}>
              <dt className="text-slate-400 text-xs uppercase font-semibold">{k}</dt>
              <dd className="font-medium text-slate-900">{String(v)}</dd>
            </div>
          ))}
        </dl>
      </div>
      <div className="mt-6 flex gap-3">
        <Link
          to="/instructor/student-courses"
          className="rounded-xl bg-brand-600 text-white px-4 py-2 text-sm font-semibold"
        >
          View courses
        </Link>
        <Link
          to="/instructor/student-course-board"
          className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold"
        >
          Course board (add / drop)
        </Link>
      </div>
    </FeaturePageLayout>
  );
}
