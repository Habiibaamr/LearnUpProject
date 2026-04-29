import { useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import * as adminApi from "../../services/admin";
import { getApiErrorMessage } from "../../services/api";

export default function AdminCreateInstructor() {
  const [f, setF] = useState({
    full_name: "",
    email: "",
    password: "",
    faculty_id: "",
    department_id: "",
    specialization: "",
    office_location: "",
    phone: "",
  });
  const [msg, setMsg] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg("");
    try {
      await adminApi.createInstructorAccount({
        full_name: f.full_name,
        email: f.email,
        password: f.password,
        faculty_id: f.faculty_id ? Number(f.faculty_id) : undefined,
        department_id: f.department_id ? Number(f.department_id) : undefined,
        specialization: f.specialization || undefined,
        office_location: f.office_location || undefined,
        phone: f.phone || undefined,
      });
      setMsg("Instructor created. University ID was generated automatically.");
    } catch (err) {
      setMsg(getApiErrorMessage(err));
    }
  };

  return (
    <FeaturePageLayout title="Create instructor account">
      <form onSubmit={submit} className="grid sm:grid-cols-2 gap-4 max-w-3xl">
        {(["full_name", "email", "password"] as const).map((k) => (
          <div key={k}>
            <label className="block text-xs font-semibold text-slate-500 mb-1">{k}</label>
            <input
              type={k === "password" ? "password" : k === "email" ? "email" : "text"}
              required
              value={f[k]}
              onChange={(e) => setF({ ...f, [k]: e.target.value })}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>
        ))}
        {(["faculty_id", "department_id", "specialization", "office_location", "phone"] as const).map((k) => (
          <div key={k}>
            <label className="block text-xs font-semibold text-slate-500 mb-1">{k}</label>
            <input
              type={k.includes("id") ? "number" : "text"}
              value={f[k]}
              onChange={(e) => setF({ ...f, [k]: e.target.value })}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>
        ))}
        <div className="sm:col-span-2">
          <button type="submit" className="rounded-xl bg-brand-600 text-white px-6 py-2.5 font-semibold">
            Create
          </button>
          {msg ? <p className="mt-3 text-sm">{msg}</p> : null}
        </div>
      </form>
    </FeaturePageLayout>
  );
}
