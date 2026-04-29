import { BookOpen, GraduationCap, Layers, Search, UserCircle } from "lucide-react";
import { DashboardCard } from "../../components/DashboardCard";

export default function InstructorDashboard() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold text-slate-900">Instructor workspace</h1>
        <p className="text-slate-600 mt-1">Advising tools connected to your SIS backend.</p>
      </div>
      <div className="grid sm:grid-cols-2 gap-5">
        <DashboardCard
          title="Search student"
          subtitle="Find a student by university ID"
          icon={Search}
          to="/instructor/search"
        />
        <DashboardCard
          title="Student profile"
          subtitle="View details for the selected student"
          icon={UserCircle}
          to="/instructor/profile"
        />
        <DashboardCard
          title="Student courses"
          subtitle="Registrations for the selected student"
          icon={BookOpen}
          to="/instructor/student-courses"
        />
        <DashboardCard
          title="Student course board"
          subtitle="Add or drop courses (same rules as students)"
          icon={Layers}
          to="/instructor/student-course-board"
        />
        <DashboardCard
          title="Advising tools"
          subtitle="Shortcuts and guidance"
          icon={GraduationCap}
          to="/instructor/advising"
        />
      </div>
    </div>
  );
}
