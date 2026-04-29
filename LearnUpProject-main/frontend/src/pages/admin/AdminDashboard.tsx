import { CalendarCheck, Settings, Shield, UserPlus, Users } from "lucide-react";
import { DashboardCard } from "../../components/DashboardCard";
import { useAuth } from "../../context/AuthContext";

export default function AdminDashboard() {
  const { user } = useAuth();
  const isSuperAdmin = user?.role === "super_admin";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold text-slate-900">
          {isSuperAdmin ? "Super Administration" : "Administration"}
        </h1>
        <p className="text-slate-600 mt-1">
          {isSuperAdmin
            ? "Manage administrator accounts."
            : "Directory, accounts, and course staffing."}
        </p>
      </div>
      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
        {isSuperAdmin ? (
          <>
            <DashboardCard title="Manage admins" subtitle="Edit or delete admin accounts" icon={Users} to="/admin/users" />
            <DashboardCard title="Create admin" subtitle="Provision a regular admin account" icon={Shield} to="/admin/create-admin" />
          </>
        ) : (
          <>
            <DashboardCard title="Manage users" subtitle="Full user directory" icon={Users} to="/admin/users" />
            <DashboardCard title="Create student" subtitle="New student account + profile" icon={UserPlus} to="/admin/create-student" />
            <DashboardCard title="Create instructor" subtitle="Faculty account" icon={UserPlus} to="/admin/create-instructor" />
            <DashboardCard title="Assign instructor" subtitle="Link instructor to offering" icon={Settings} to="/admin/assign" />
            <DashboardCard title="System overview" subtitle="Counts and health" icon={Users} to="/admin/overview" />
            <DashboardCard
              title="Complete student term"
              subtitle="Mark a six-course term passed (opens next term)"
              icon={CalendarCheck}
              to="/admin/complete-term"
            />
            <DashboardCard
              title="Final grades window"
              subtitle="Open/close instructor grade posting period"
              icon={CalendarCheck}
              to="/admin/final-grades-window"
            />
          </>
        )}
      </div>
    </div>
  );
}
