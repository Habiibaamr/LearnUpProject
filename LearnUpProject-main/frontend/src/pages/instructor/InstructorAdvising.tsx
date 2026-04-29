import { Link } from "react-router-dom";
import { BookOpen, Search, UserCircle } from "lucide-react";
import { FeaturePageLayout } from "../../components/FeaturePageLayout";
import { useInstructorStudentUid } from "../../hooks/useInstructorStudentUid";

export default function InstructorAdvising() {
  const { uid } = useInstructorStudentUid();

  return (
    <FeaturePageLayout
      title="Advising tools"
      subtitle="Workflow for academic advising with the live API"
    >
      <div className="grid sm:grid-cols-3 gap-4">
        <Link
          to="/instructor/search"
          className="rounded-2xl border border-slate-100 bg-slate-50 p-6 hover:border-brand-200 hover:shadow-soft transition-all"
        >
          <Search className="h-8 w-8 text-brand-600 mb-3" />
          <h3 className="font-semibold">1. Find student</h3>
          <p className="text-sm text-slate-600 mt-1">University ID lookup</p>
        </Link>
        <Link
          to="/instructor/profile"
          className="rounded-2xl border border-slate-100 bg-slate-50 p-6 hover:border-brand-200 hover:shadow-soft transition-all"
        >
          <UserCircle className="h-8 w-8 text-brand-600 mb-3" />
          <h3 className="font-semibold">2. Review profile</h3>
          <p className="text-sm text-slate-600 mt-1">Level, GPA, advisor</p>
        </Link>
        <Link
          to="/instructor/student-course-board"
          className="rounded-2xl border border-slate-100 bg-slate-50 p-6 hover:border-brand-200 hover:shadow-soft transition-all"
        >
          <BookOpen className="h-8 w-8 text-brand-600 mb-3" />
          <h3 className="font-semibold">3. Course board</h3>
          <p className="text-sm text-slate-600 mt-1">Add or drop with the same rules as students</p>
        </Link>
      </div>
      <p className="mt-8 text-sm text-slate-600">
        Current selection:{" "}
        <strong className="text-brand-800">{uid || "— none —"}</strong>
      </p>
    </FeaturePageLayout>
  );
}
