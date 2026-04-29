import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import { useInstructorStudentUid } from "../../hooks/useInstructorStudentUid";

export default function InstructorSearch() {
  const [q, setQ] = useState("");
  const { setUid } = useInstructorStudentUid();
  const navigate = useNavigate();

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const uid = q.trim();
    if (!uid) return;
    setUid(uid);
    navigate("/instructor/profile");
  };

  return (
    <FeaturePageLayout
      title="Search student"
      subtitle="Enter the student's university ID (e.g. U000041)"
    >
      <form onSubmit={submit} className="max-w-lg space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="w-full rounded-xl border border-slate-200 pl-11 pr-4 py-3 focus:ring-2 focus:ring-brand-500 outline-none"
            placeholder="University ID"
          />
        </div>
        <button
          type="submit"
          className="rounded-xl bg-brand-600 text-white px-6 py-3 font-semibold hover:bg-brand-700"
        >
          Load student
        </button>
      </form>
    </FeaturePageLayout>
  );
}
