import { useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import * as adminApi from "../../services/admin";
import { getApiErrorMessage } from "../../services/api";

export default function AdminCreateAdmin() {
  const [f, setF] = useState({
    full_name: "",
    email: "",
    password: "",
    position: "",
  });
  const [msg, setMsg] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg("");
    try {
      await adminApi.createAdminAccount({
        full_name: f.full_name,
        email: f.email,
        password: f.password,
        position: f.position || undefined,
      });
      setMsg("Admin created. University ID was generated automatically.");
      setF({
        full_name: "",
        email: "",
        password: "",
        position: "",
      });
    } catch (err) {
      setMsg(getApiErrorMessage(err));
    }
  };

  return (
    <FeaturePageLayout
      title="Create admin account"
      subtitle="Super admins can provision regular admin users here."
    >
      <form onSubmit={submit} className="max-w-md space-y-4">
        {(["full_name", "email", "password", "position"] as const).map((k) => (
          <div key={k}>
            <label className="block text-xs font-semibold text-slate-500 mb-1">{k}</label>
            <input
              type={k === "password" ? "password" : k === "email" ? "email" : "text"}
              required={k !== "position"}
              value={f[k]}
              onChange={(e) => setF({ ...f, [k]: e.target.value })}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>
        ))}
        <button type="submit" className="rounded-xl bg-brand-600 text-white px-6 py-2.5 font-semibold">
          Create
        </button>
        {msg ? <p className="text-sm">{msg}</p> : null}
      </form>
    </FeaturePageLayout>
  );
}
