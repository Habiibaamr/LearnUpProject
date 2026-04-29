import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import { useEffect, useMemo, useState } from "react";
import { getApiErrorMessage } from "../../services/api";
import * as instructorApi from "../../services/instructor";

export default function InstructorAssigned() {
  const [offerings, setOfferings] = useState<instructorApi.InstructorAssignedOffering[]>([]);
  const [selectedOfferingId, setSelectedOfferingId] = useState<number | null>(null);
  const [rows, setRows] = useState<instructorApi.InstructorOfferingRegistration[]>([]);
  const [windowStatus, setWindowStatus] = useState<instructorApi.InstructorFinalGradesWindowStatus | null>(null);
  const [gradeDraft, setGradeDraft] = useState<Record<number, string>>({});
  const [passDraft, setPassDraft] = useState<Record<number, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [submittingId, setSubmittingId] = useState<number | null>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");

  const selectedOffering = useMemo(
    () => offerings.find((o) => o.course_offering_id === selectedOfferingId) ?? null,
    [offerings, selectedOfferingId]
  );

  const loadInitial = async () => {
    setLoading(true);
    setErr("");
    try {
      const [myOfferings, status] = await Promise.all([
        instructorApi.getMyAssignedOfferings(),
        instructorApi.getFinalGradesWindowStatus(),
      ]);
      setOfferings(myOfferings);
      setWindowStatus(status);
      if (myOfferings.length > 0) setSelectedOfferingId(myOfferings[0].course_offering_id);
    } catch (e) {
      setErr(getApiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  const loadRegistrations = async (offeringId: number) => {
    setLoading(true);
    setErr("");
    setMsg("");
    try {
      const data = await instructorApi.getOfferingRegistrations(offeringId);
      setRows(data);
      const gradeMap: Record<number, string> = {};
      const passMap: Record<number, boolean> = {};
      data.forEach((r) => {
        gradeMap[r.registration_id] = r.final_grade ?? "";
        passMap[r.registration_id] = Boolean(r.is_passed);
      });
      setGradeDraft(gradeMap);
      setPassDraft(passMap);
    } catch (e) {
      setErr(getApiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadInitial();
  }, []);

  useEffect(() => {
    if (selectedOfferingId !== null) {
      void loadRegistrations(selectedOfferingId);
    } else {
      setRows([]);
    }
  }, [selectedOfferingId]);

  const submitGrade = async (registrationId: number) => {
    if (selectedOfferingId === null) return;
    const finalGrade = (gradeDraft[registrationId] ?? "").trim().toUpperCase();
    if (!finalGrade) {
      setErr("Enter a final grade before submitting.");
      return;
    }
    setSubmittingId(registrationId);
    setErr("");
    setMsg("");
    try {
      await instructorApi.submitFinalGrade(selectedOfferingId, registrationId, {
        final_grade: finalGrade,
        is_passed: Boolean(passDraft[registrationId]),
      });
      setMsg("Final grade posted.");
      await loadRegistrations(selectedOfferingId);
    } catch (e) {
      setErr(getApiErrorMessage(e));
    } finally {
      setSubmittingId(null);
    }
  };

  return (
    <FeaturePageLayout
      title="Assigned courses"
      subtitle="Post final grades for students in your assigned course offerings."
    >
      <div className="space-y-5">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
          <p>
            Grade posting window:{" "}
            <strong className={windowStatus?.is_open ? "text-emerald-700" : "text-red-700"}>
              {windowStatus?.is_open ? "OPEN" : "CLOSED"}
            </strong>
            {windowStatus?.term_index !== null ? ` (term index ${windowStatus?.term_index})` : ""}
          </p>
          {!windowStatus?.is_open ? (
            <p className="mt-1 text-red-600">Grades are locked until admins open the posting window.</p>
          ) : null}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Assigned course offering</label>
          <select
            value={selectedOfferingId ?? ""}
            onChange={(e) => setSelectedOfferingId(Number(e.target.value))}
            className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 focus:ring-2 focus:ring-brand-500 outline-none"
          >
            {offerings.length === 0 ? <option value="">No assigned offerings</option> : null}
            {offerings.map((o) => (
              <option key={o.course_offering_id} value={o.course_offering_id}>
                {o.course_code} - {o.course_title} (Offering #{o.course_offering_id})
              </option>
            ))}
          </select>
          {selectedOffering ? (
            <p className="mt-2 text-xs text-slate-500">
              Semester: {selectedOffering.semester_id} | Credits: {selectedOffering.credit_hours}
            </p>
          ) : null}
        </div>

        {loading ? <p className="text-sm text-slate-500">Loading…</p> : null}
        {err ? <p className="text-sm text-red-600">{err}</p> : null}
        {msg ? <p className="text-sm text-emerald-600">{msg}</p> : null}

        <div className="space-y-3">
          {rows.map((r) => (
            <div key={r.registration_id} className="rounded-xl border border-slate-200 p-4">
              <p className="font-medium text-slate-900">
                {r.student_full_name} ({r.student_university_id})
              </p>
              <p className="text-xs text-slate-500 mt-1">Registration #{r.registration_id}</p>
              <div className="mt-3 flex flex-wrap items-end gap-3">
                <div>
                  <label className="block text-xs text-slate-600">Final grade</label>
                  <input
                    type="text"
                    value={gradeDraft[r.registration_id] ?? ""}
                    onChange={(e) =>
                      setGradeDraft((prev) => ({ ...prev, [r.registration_id]: e.target.value.toUpperCase() }))
                    }
                    className="mt-1 w-28 rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    placeholder="A, B+, C..."
                  />
                </div>
                <label className="inline-flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={Boolean(passDraft[r.registration_id])}
                    onChange={(e) => setPassDraft((prev) => ({ ...prev, [r.registration_id]: e.target.checked }))}
                  />
                  Passed
                </label>
                <button
                  type="button"
                  disabled={!windowStatus?.is_open || submittingId === r.registration_id}
                  onClick={() => void submitGrade(r.registration_id)}
                  className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
                >
                  {submittingId === r.registration_id ? "Submitting…" : "Post final grade"}
                </button>
              </div>
            </div>
          ))}
          {!loading && rows.length === 0 ? <p className="text-sm text-slate-500">No student registrations found.</p> : null}
        </div>
      </div>
    </FeaturePageLayout>
  );
}
