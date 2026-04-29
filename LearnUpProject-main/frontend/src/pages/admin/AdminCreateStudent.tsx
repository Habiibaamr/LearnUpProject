import { useState } from "react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import * as adminApi from "../../services/admin";
import { getApiErrorMessage } from "../../services/api";

const empty = {
  full_name: "",
  email: "",
  password: "",
  faculty_id: "" as string | number,
  department_id: "" as string | number,
  level: "" as string | number,
  cgpa: "" as string | number,
  passed_credit_hours: "" as string | number,
  phone: "",
  advisor_instructor_id: "" as string | number,
};

export default function AdminCreateStudent() {
  const [f, setF] = useState(empty);
  const [msg, setMsg] = useState("");

  const num = (v: string | number) => {
    if (v === "" || v == null) return undefined;
    const n = Number(v);
    return Number.isNaN(n) ? undefined : n;
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg("");
    try {
      await adminApi.createStudentAccount({
        full_name: f.full_name,
        email: f.email,
        password: f.password,
        faculty_id: num(f.faculty_id),
        department_id: num(f.department_id),
        level: num(f.level),
        cgpa: num(f.cgpa),
        passed_credit_hours: num(f.passed_credit_hours),
        phone: f.phone || undefined,
        advisor_instructor_id: num(f.advisor_instructor_id),
      });
      setMsg("Student account created. University ID was generated automatically.");
      setF(empty);
    } catch (err) {
      setMsg(getApiErrorMessage(err));
    }
  };

  const field = (key: keyof typeof f, label: string, type = "text", required = false) => (
    <div>
      <label className="block text-xs font-semibold text-slate-500 mb-1">{label}</label>
      <input
        type={type}
        required={required}
        value={f[key] as string}
        onChange={(e) => setF({ ...f, [key]: e.target.value })}
        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
      />
    </div>
  );

  return (
    <FeaturePageLayout title="Create student account" subtitle="User + student profile in one step">
      <form onSubmit={submit} className="grid sm:grid-cols-2 gap-4 max-w-3xl">
        {field("full_name", "Full name *", "text", true)}
        {field("email", "Email *", "email", true)}
        {field("password", "Password *", "password", true)}
        {field("phone", "Phone")}
        {field("faculty_id", "Faculty ID", "number")}
        {field("department_id", "Department ID", "number")}
        {field("level", "Level", "number")}
        {field("cgpa", "CGPA", "number")}
        {field("passed_credit_hours", "Passed credit hours", "number")}
        {field("advisor_instructor_id", "Advisor instructor ID", "number")}
        <div className="sm:col-span-2">
          <button type="submit" className="rounded-xl bg-brand-600 text-white px-6 py-2.5 font-semibold">
            Create
          </button>
          {msg ? <p className="mt-3 text-sm text-slate-700">{msg}</p> : null}
        </div>
      </form>
    </FeaturePageLayout>
  );
}
