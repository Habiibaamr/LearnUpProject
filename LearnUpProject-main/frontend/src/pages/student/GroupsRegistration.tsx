import { useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import * as studentApi from "../../services/student";
import { getApiErrorMessage } from "../../services/api";

export default function GroupsRegistration() {
  const [offeringId, setOfferingId] = useState("");
  const [groups, setGroups] = useState<Awaited<ReturnType<typeof studentApi.getAvailableGroups>> | null>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  const loadGroups = async () => {
    setErr("");
    setMsg("");
    const id = parseInt(offeringId, 10);
    if (Number.isNaN(id)) {
      setErr("Invalid offering ID.");
      return;
    }
    setLoading(true);
    try {
      setGroups(await studentApi.getAvailableGroups(id));
    } catch (e) {
      setErr(getApiErrorMessage(e));
      setGroups(null);
    } finally {
      setLoading(false);
    }
  };

  const act = async (
    fn: (n: number) => ReturnType<typeof studentApi.registerLecture>,
    idStr: string,
    label: string
  ) => {
    setMsg("");
    const n = parseInt(idStr, 10);
    if (Number.isNaN(n)) return;
    try {
      await fn(n);
      setMsg(`${label} OK. Refresh groups if needed.`);
      if (groups) loadGroups();
    } catch (e) {
      setMsg(getApiErrorMessage(e));
    }
  };

  return (
    <FeaturePageLayout
      title="Lecture & Section Registration"
      subtitle="Load groups for a course offering you are registered in, then pick lecture/section IDs."
    >
      <div className="space-y-6">
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Course offering ID</label>
            <input
              type="number"
              value={offeringId}
              onChange={(e) => setOfferingId(e.target.value)}
              className="rounded-xl border border-slate-200 px-4 py-2.5 w-40"
            />
          </div>
          <button
            type="button"
            onClick={loadGroups}
            disabled={loading}
            className="rounded-xl bg-brand-600 text-white px-5 py-2.5 font-semibold hover:bg-brand-700 disabled:opacity-50"
          >
            {loading ? "Loading…" : "Load groups"}
          </button>
        </div>
        {err ? <p className="text-red-600 text-sm">{err}</p> : null}
        {msg ? <p className="text-sm text-brand-700">{msg}</p> : null}

        {groups ? (
          <div className="grid lg:grid-cols-2 gap-8">
            <section>
              <h3 className="font-semibold text-slate-900 mb-3">Lecture groups</h3>
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {(groups.lecture_groups as Array<Record<string, unknown>>).map((g) => (
                  <div
                    key={String(g.id)}
                    className="rounded-xl border border-slate-100 p-4 flex flex-wrap justify-between gap-2 items-center bg-slate-50/50"
                  >
                    <div className="text-sm">
                      <span className="font-mono font-semibold text-brand-800">#{String(g.id)}</span>{" "}
                      {String(g.group_code)} — seats {String(g.current_count)}/{String(g.capacity)} (left:{" "}
                      {String(g.remaining_capacity)})
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => act(studentApi.registerLecture, String(g.id), "Lecture register")}
                        className="text-xs font-semibold text-white bg-brand-600 px-3 py-1.5 rounded-lg"
                      >
                        Register
                      </button>
                      <button
                        type="button"
                        onClick={() => act(studentApi.dropLecture, String(g.id), "Lecture drop")}
                        className="text-xs font-semibold border border-slate-200 px-3 py-1.5 rounded-lg"
                      >
                        Drop
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
            <section>
              <h3 className="font-semibold text-slate-900 mb-3">Section groups</h3>
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {(groups.section_groups as Array<Record<string, unknown>>).map((g) => (
                  <div
                    key={String(g.id)}
                    className="rounded-xl border border-slate-100 p-4 flex flex-wrap justify-between gap-2 items-center bg-slate-50/50"
                  >
                    <div className="text-sm">
                      <span className="font-mono font-semibold text-brand-800">#{String(g.id)}</span>{" "}
                      {String(g.group_code)} — seats {String(g.current_count)}/{String(g.capacity)}
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => act(studentApi.registerSection, String(g.id), "Section register")}
                        className="text-xs font-semibold text-white bg-brand-600 px-3 py-1.5 rounded-lg"
                      >
                        Register
                      </button>
                      <button
                        type="button"
                        onClick={() => act(studentApi.dropSection, String(g.id), "Section drop")}
                        className="text-xs font-semibold border border-slate-200 px-3 py-1.5 rounded-lg"
                      >
                        Drop
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        ) : null}
      </div>
    </FeaturePageLayout>
  );
}
