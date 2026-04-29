import { useEffect, useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import { Spinner } from "../../components/Spinner";
import * as studentApi from "../../services/student";
import { API_BASE_URL, getApiErrorMessage } from "../../services/api";

function formatCgpa(value: number | null) {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(2);
}

function formatCreditProgress(passed: number | null, total: number) {
  if (passed == null || Number.isNaN(passed)) return `— / ${total}`;
  return `${passed} / ${total}`;
}

export default function IdentityCard() {
  const [data, setData] = useState<studentApi.StudentCard | null>(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setData(await studentApi.getStudentCard());
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
  if (err)
    return (
      <FeaturePageLayout title="Identity Card" subtitle="Your campus profile">
        <p className="text-red-600">{err}</p>
        {import.meta.env.DEV ? (
          <p className="mt-4 max-w-xl text-sm text-slate-600">
            API base is <code className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-800">{API_BASE_URL}</code>. The
            card uses <code className="rounded bg-slate-100 px-1.5 py-0.5">GET /learnup/student/identity-card</code>.
            If you see &quot;Not Found&quot;, stop Uvicorn (Ctrl+C), start it again from the{" "}
            <code className="rounded bg-slate-100 px-1.5 py-0.5">backend</code> folder, then hard-refresh (Ctrl+Shift+R).
          </p>
        ) : null}
      </FeaturePageLayout>
    );
  if (!data) return null;

  const facultyLabel =
    data.faculty_name ??
    (data.faculty_id != null ? `Faculty #${data.faculty_id}` : "—");
  const departmentLabel =
    data.department_name ??
    (data.department_id != null ? `Department #${data.department_id}` : "—");
  const levelLabel = data.level != null ? `Level ${data.level}` : "—";
  const advisorLabel = data.advisor_name ?? "—";
  const uploadPhoto = async (file: File | null) => {
    if (!file) return;
    setUploadMsg("");
    setErr("");
    setUploading(true);
    try {
      const res = await studentApi.uploadStudentPhoto(file);
      setData({ ...data, photo_url: res.photo_url });
      setUploadMsg("Profile picture updated.");
    } catch (e) {
      setErr(getApiErrorMessage(e));
    } finally {
      setUploading(false);
    }
  };

  return (
    <FeaturePageLayout title="Identity Card" subtitle="Official student profile on LearnUp">
      <div className="relative overflow-hidden rounded-2xl border border-slate-200/90 bg-gradient-to-br from-white via-white to-brand-50/50 shadow-card">
        <div
          className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-brand-400/15 blur-2xl"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute -bottom-12 -left-12 h-40 w-40 rounded-full bg-brand-600/10 blur-2xl"
          aria-hidden
        />

        <div className="relative border-b border-brand-100/80 bg-gradient-to-r from-brand-600 to-brand-700 px-6 py-5 md:px-8 md:py-6">
          <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-start sm:gap-8">
            <div className="relative shrink-0">
              <div className="absolute -inset-1 rounded-2xl bg-white/25 blur-sm" aria-hidden />
              <div className="relative h-36 w-28 overflow-hidden rounded-xl border-4 border-white/90 shadow-lg sm:h-40 sm:w-32">
                {data.photo_url ? (
                  <img
                    src={data.photo_url}
                    alt=""
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-gradient-to-b from-brand-100 to-brand-200 font-display text-4xl font-bold text-brand-800">
                    {data.full_name.charAt(0)}
                  </div>
                )}
              </div>
              <label className="mt-3 inline-block cursor-pointer rounded-lg bg-white/90 px-3 py-1.5 text-xs font-semibold text-slate-700 shadow hover:bg-white">
                {uploading ? "Uploading..." : "Upload photo"}
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  disabled={uploading}
                  onChange={(e) => void uploadPhoto(e.target.files?.[0] ?? null)}
                />
              </label>
            </div>
            <div className="min-w-0 flex-1 text-center text-white sm:text-left">
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-brand-100/90">
                LearnUp Student
              </p>
              <h2 className="mt-1 font-display text-2xl font-bold tracking-tight text-white md:text-3xl">
                {data.full_name}
              </h2>
              <div className="mt-3 flex flex-wrap items-center justify-center gap-2 sm:justify-start">
                <span className="inline-flex items-center rounded-lg bg-white/15 px-3 py-1 font-mono text-sm font-semibold tracking-wide text-white ring-1 ring-white/25 backdrop-blur-sm">
                  ID {data.university_id}
                </span>
                {data.faculty_code ? (
                  <span className="rounded-lg bg-white/10 px-2.5 py-1 text-xs font-medium text-brand-100">
                    {data.faculty_code}
                  </span>
                ) : null}
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-4 p-6 sm:grid-cols-2 md:gap-5 md:p-8">
          <div className="rounded-xl border border-slate-100 bg-slate-50/80 p-4 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Faculty
            </p>
            <p className="mt-1.5 text-base font-semibold text-slate-900">{facultyLabel}</p>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50/80 p-4 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Specialization
            </p>
            <p className="mt-1.5 text-base font-semibold text-slate-900">{departmentLabel}</p>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50/80 p-4 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Level
            </p>
            <p className="mt-1.5 text-base font-semibold text-slate-900">{levelLabel}</p>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50/80 p-4 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">CGPA</p>
            <p className="mt-1.5 font-display text-2xl font-bold text-brand-700">
              {formatCgpa(data.cgpa)}
            </p>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50/80 p-4 shadow-sm sm:col-span-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Passed Credit Hours
            </p>
            <p className="mt-1.5 text-base font-semibold text-slate-900">
              {formatCreditProgress(data.passed_credit_hours, data.total_credit_hours)}
            </p>
          </div>
          <div className="rounded-xl border border-brand-100 bg-brand-50/60 p-4 shadow-sm sm:col-span-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-600/80">
              Academic advisor
            </p>
            <p className="mt-1.5 text-base font-semibold text-slate-900">{advisorLabel}</p>
          </div>
        </div>

        <div className="border-t border-slate-100 bg-slate-50/50 px-6 py-4 md:px-8">
          {uploadMsg ? <p className="mb-2 text-center text-xs text-emerald-600">{uploadMsg}</p> : null}
          <p className="text-center text-xs text-slate-500">
            <span className="font-medium text-slate-600">{data.email}</span>
            {data.phone ? (
              <>
                <span className="mx-2 text-slate-300">·</span>
                {data.phone}
              </>
            ) : null}
          </p>
        </div>
      </div>
    </FeaturePageLayout>
  );
}
