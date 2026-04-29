import { useEffect, useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import { Spinner } from "../../components/Spinner";
import { useAuth } from "../../context/AuthContext";
import * as adminApi from "../../services/admin";
import { getApiErrorMessage } from "../../services/api";

export default function AdminManageUsers() {
  const { user } = useAuth();
  const [rows, setRows] = useState<adminApi.AdminUserRow[]>([]);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({
    full_name: "",
    email: "",
    position: "",
    password: "",
    is_active: true,
  });
  const [actionMessage, setActionMessage] = useState("");
  const isSuperAdmin = user?.role === "super_admin";

  const loadRows = async () => {
    try {
      setRows(await adminApi.listUsers());
      setErr("");
    } catch (e) {
      setErr(getApiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRows();
  }, []);

  const visibleRows = isSuperAdmin
    ? rows.filter((row) => row.role === "admin" || row.role === "super_admin")
    : rows;

  const startEdit = (row: adminApi.AdminUserRow) => {
    setEditingUserId(row.id);
    setActionMessage("");
    setEditForm({
      full_name: row.full_name,
      email: row.email,
      position: row.position ?? "",
      password: "",
      is_active: row.is_active,
    });
  };

  const saveEdit = async () => {
    if (editingUserId == null) return;
    setActionMessage("");
    try {
      await adminApi.updateAdminAccount(editingUserId, {
        full_name: editForm.full_name,
        email: editForm.email,
        position: editForm.position || undefined,
        password: editForm.password || undefined,
        is_active: editForm.is_active,
      });
      setActionMessage("Admin account updated successfully.");
      setEditingUserId(null);
      await loadRows();
    } catch (e) {
      setActionMessage(getApiErrorMessage(e));
    }
  };

  const deleteAdmin = async (row: adminApi.AdminUserRow) => {
    if (!window.confirm(`Delete admin account for ${row.full_name}?`)) return;
    setActionMessage("");
    try {
      await adminApi.deleteAdminAccount(row.id);
      setActionMessage("Admin account deleted successfully.");
      if (editingUserId === row.id) {
        setEditingUserId(null);
      }
      await loadRows();
    } catch (e) {
      setActionMessage(getApiErrorMessage(e));
    }
  };

  if (loading)
    return (
      <div className="flex justify-center py-20">
        <Spinner />
      </div>
    );

  return (
    <FeaturePageLayout
      title={isSuperAdmin ? "Manage admins" : "Manage users"}
      subtitle={
        isSuperAdmin
          ? "Edit or delete regular admin accounts."
          : "All accounts (newest first)."
      }
    >
      {err ? <p className="text-red-600 mb-4">{err}</p> : null}
      {actionMessage ? <p className="text-sm text-slate-700 mb-4">{actionMessage}</p> : null}
      <div className="overflow-x-auto max-h-[60vh]">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-white">
            <tr className="border-b text-left text-slate-500">
              <th className="pb-2 pr-2">ID</th>
              <th className="pb-2 pr-2">Name</th>
              <th className="pb-2 pr-2">Email</th>
              <th className="pb-2 pr-2">Uni ID</th>
              <th className="pb-2 pr-2">Role</th>
              <th className="pb-2 pr-2">Position</th>
              <th className="pb-2">Active</th>
              {isSuperAdmin ? <th className="pb-2 pl-2">Actions</th> : null}
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((u) => (
              <tr key={u.id} className="border-b border-slate-50 hover:bg-slate-50/80">
                <td className="py-2 pr-2">{u.id}</td>
                <td className="py-2 pr-2 font-medium">{u.full_name}</td>
                <td className="py-2 pr-2">{u.email}</td>
                <td className="py-2 pr-2 font-mono text-xs">{u.university_id}</td>
                <td className="py-2 pr-2 capitalize">{u.role}</td>
                <td className="py-2 pr-2">{u.position || "-"}</td>
                <td className="py-2">{u.is_active ? "Yes" : "No"}</td>
                {isSuperAdmin ? (
                  <td className="py-2 pl-2">
                    {u.role === "admin" ? (
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => startEdit(u)}
                          className="rounded-lg border border-slate-200 px-3 py-1 text-xs font-medium text-slate-700"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => void deleteAdmin(u)}
                          className="rounded-lg border border-red-200 px-3 py-1 text-xs font-medium text-red-600"
                        >
                          Delete
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-400">Read only</span>
                    )}
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {isSuperAdmin && editingUserId != null ? (
        <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-5 space-y-4 max-w-2xl">
          <div>
            <h3 className="font-semibold text-slate-900">Edit admin account</h3>
            <p className="text-sm text-slate-600">Leave the password blank to keep the current password.</p>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">Full name</label>
              <input
                value={editForm.full_name}
                onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">Email</label>
              <input
                type="email"
                value={editForm.email}
                onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">Position</label>
              <input
                value={editForm.position}
                onChange={(e) => setEditForm({ ...editForm, position: e.target.value })}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">New password</label>
              <input
                type="password"
                value={editForm.password}
                onChange={(e) => setEditForm({ ...editForm, password: e.target.value })}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={editForm.is_active}
                onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
              />
              Active account
            </label>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => void saveEdit()}
              className="rounded-xl bg-brand-600 text-white px-5 py-2 font-semibold"
            >
              Save changes
            </button>
            <button
              type="button"
              onClick={() => setEditingUserId(null)}
              className="rounded-xl border border-slate-200 px-5 py-2 font-semibold text-slate-700"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : null}
    </FeaturePageLayout>
  );
}
