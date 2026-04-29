import { useEffect, useMemo, useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import * as adminApi from "../../services/admin";
import { getApiErrorMessage } from "../../services/api";

export default function AdminAssignInstructor() {
  const [offeringId, setOfferingId] = useState("");
  const [instructorId, setInstructorId] = useState("");
  const [assignMsg, setAssignMsg] = useState("");
  const [listRows, setListRows] = useState<Array<{ id: number; instructor_id: number }>>([]);
  const [instructors, setInstructors] = useState<adminApi.AdminInstructorRow[]>([]);
  const [offerings, setOfferings] = useState<adminApi.AdminCourseOfferingRow[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(false);

  const selectedOfferingId = Number(offeringId || "0");

  const selectedOfferingLabel = useMemo(() => {
    if (!selectedOfferingId) return "";
    const o = offerings.find((x) => x.course_offering_id === selectedOfferingId);
    if (!o) return "";
    return `${o.course_code} - ${o.course_title} (offering #${o.course_offering_id})`;
  }, [offerings, selectedOfferingId]);

  const instructorNameById = useMemo(() => {
    const map = new Map<number, string>();
    instructors.forEach((i) => {
      map.set(i.instructor_id, `${i.full_name} (${i.university_id})`);
    });
    return map;
  }, [instructors]);

  const assign = async () => {
    setAssignMsg("");
    if (!offeringId || !instructorId) {
      setAssignMsg("Please select both a course offering and an instructor.");
      return;
    }
    try {
      await adminApi.assignInstructor({
        course_offering_id: Number(offeringId),
        instructor_id: Number(instructorId),
      });
      setAssignMsg("Assigned successfully.");
      const data = await adminApi.listOfferingInstructors(Number(offeringId));
      setListRows(data);
    } catch (e) {
      setAssignMsg(getApiErrorMessage(e));
    }
  };

  const loadLookups = async () => {
    setLoadingLookups(true);
    setAssignMsg("");
    try {
      const [ins, offs] = await Promise.all([
        adminApi.listInstructors(),
        adminApi.listCourseOfferings(),
      ]);
      setInstructors(ins);
      setOfferings(offs);
    } catch (e) {
      setAssignMsg(getApiErrorMessage(e));
    } finally {
      setLoadingLookups(false);
    }
  };

  const loadList = async (offeringIdValue: number) => {
    setListRows([]);
    try {
      const data = await adminApi.listOfferingInstructors(offeringIdValue);
      setListRows(data);
    } catch (e) {
      setAssignMsg(getApiErrorMessage(e));
    }
  };

  useEffect(() => {
    void loadLookups();
  }, []);

  useEffect(() => {
    if (selectedOfferingId > 0) {
      void loadList(selectedOfferingId);
    } else {
      setListRows([]);
    }
  }, [selectedOfferingId]);

  return (
    <FeaturePageLayout title="Assign instructor to offering" subtitle="Course staffing with quick selection">
      <div className="grid lg:grid-cols-2 gap-10">
        <div className="space-y-3">
          <h3 className="font-semibold text-slate-900">New assignment</h3>
          <label className="block text-sm font-medium text-slate-700">Select course offering</label>
          <select
            value={offeringId}
            onChange={(e) => setOfferingId(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2"
          >
            <option value="">Choose offering...</option>
            {offerings.map((o) => (
              <option key={o.course_offering_id} value={o.course_offering_id}>
                {o.course_code} - {o.course_title} (ID {o.course_offering_id})
              </option>
            ))}
          </select>

          <label className="block text-sm font-medium text-slate-700">Select instructor</label>
          <select
            value={instructorId}
            onChange={(e) => setInstructorId(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2"
          >
            <option value="">Choose instructor...</option>
            {instructors.map((i) => (
              <option key={i.instructor_id} value={i.instructor_id}>
                {i.full_name} ({i.university_id}) - ID {i.instructor_id}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={assign}
            disabled={loadingLookups}
            className="rounded-xl bg-brand-600 text-white px-5 py-2 font-semibold disabled:opacity-50"
          >
            Assign
          </button>
          {loadingLookups ? <p className="text-sm text-slate-500">Loading instructors and offerings...</p> : null}
        </div>
        <div className="space-y-3">
          <h3 className="font-semibold text-slate-900">Current instructors</h3>
          <p className="text-sm text-slate-600">{selectedOfferingLabel || "Select an offering to view assigned instructors."}</p>
          <ul className="text-sm space-y-1">
            {listRows.map((r) => (
              <li key={r.id} className="bg-slate-50 rounded px-2 py-1">
                {instructorNameById.get(r.instructor_id) ?? `Instructor #${r.instructor_id}`} - ID {r.instructor_id}
              </li>
            ))}
          </ul>
        </div>
      </div>
      {assignMsg ? <p className="mt-6 text-sm text-slate-700">{assignMsg}</p> : null}
    </FeaturePageLayout>
  );
}
