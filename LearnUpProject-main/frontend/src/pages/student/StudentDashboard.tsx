import {
  BookOpen,
  Bot,
  CalendarDays,
  GraduationCap,
  Layers,
  LayoutDashboard,
  UserCircle,
} from "lucide-react";
import { DashboardCard } from "../../components/DashboardCard";

export default function StudentDashboard() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-600 mt-1">Quick access to your academic tools.</p>
      </div>
      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        <DashboardCard
          title="Identity Card"
          subtitle="Photo, ID, faculty, CGPA, and advisor"
          icon={UserCircle}
          to="/student/identity"
        />
        <DashboardCard
          title="My Courses"
          subtitle="Current registrations and details"
          icon={BookOpen}
          to="/student/courses"
        />
        <DashboardCard
          title="Add / Drop"
          subtitle="Register or withdraw from course offerings"
          icon={Layers}
          to="/student/add-drop"
        />
        <DashboardCard
          title="Lecture & Section"
          subtitle="Groups, capacity, and seat availability"
          icon={GraduationCap}
          to="/student/groups"
        />
        <DashboardCard
          title="AI Advisor"
          subtitle="Chat with the graduation assistant"
          icon={Bot}
          to="/student/chatbot"
        />
        <DashboardCard
          title="Schedule overview"
          subtitle="Semesters and courses at a glance"
          icon={CalendarDays}
          to="/student/schedule"
        />
      </div>
      <div className="rounded-2xl border border-brand-100 bg-gradient-to-r from-brand-50 to-white p-6 flex items-start gap-4">
        <LayoutDashboard className="h-10 w-10 text-brand-600 shrink-0" />
        <div>
          <h3 className="font-semibold text-brand-900">Tip</h3>
          <p className="text-sm text-slate-600 mt-1">
            Use the sidebar on desktop or the menu button on mobile to move between sections anytime.
          </p>
        </div>
      </div>
    </div>
  );
}
