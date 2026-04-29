import { useEffect, useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import { Spinner } from "../../components/Spinner";
import * as adminApi from "../../services/admin";
import { getApiErrorMessage } from "../../services/api";

export default function AdminSystemOverview() {
  const [users, setUsers] = useState<adminApi.AdminUserRow[] | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      try {
        setUsers(await adminApi.listUsers());
      } catch (e) {
        setErr(getApiErrorMessage(e));
      }
    })();
  }, []);

  const counts = users
    ? users.reduce(
        (acc, u) => {
          acc[u.role] = (acc[u.role] || 0) + 1;
          return acc;
        },
        {} as Record<string, number>
      )
    : null;

  return (
    <FeaturePageLayout title="System overview" subtitle="High-level directory stats">
      {err ? <p className="text-red-600">{err}</p> : null}
      {!users && !err ? (
        <Spinner />
      ) : counts ? (
        <div className="grid sm:grid-cols-3 gap-4">
          {(["student", "instructor", "admin", "super_admin"] as const).map((role) => (
            <div
              key={role}
              className="rounded-2xl bg-gradient-to-br from-white to-brand-50 border border-brand-100 p-6 shadow-soft"
            >
              <p className="text-sm text-slate-500 capitalize">{role.replace(/_/g, " ")}s</p>
              <p className="text-4xl font-display font-bold text-brand-800 mt-1">{counts[role] ?? 0}</p>
            </div>
          ))}
          <div className="sm:col-span-3 rounded-xl bg-slate-50 border border-slate-100 p-4 text-sm text-slate-600">
            Total registered users: <strong>{users?.length ?? 0}</strong>
          </div>
        </div>
      ) : null}
    </FeaturePageLayout>
  );
}
