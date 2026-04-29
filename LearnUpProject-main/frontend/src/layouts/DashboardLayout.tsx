import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  BookOpen,
  Bot,
  CalendarCheck,
  CalendarDays,
  GraduationCap,
  LayoutDashboard,
  Layers,
  LogOut,
  Menu,
  Search,
  Settings,
  Shield,
  UserCircle,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import { useState } from "react";
import { useAuthNavigate } from "../context/AuthContext";
import type { Role } from "../types";

type NavItem = { to: string; label: string; icon: typeof LayoutDashboard };

const studentNav: NavItem[] = [
  { to: "/student/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/student/identity", label: "Identity Card", icon: UserCircle },
  { to: "/student/courses", label: "My Courses", icon: BookOpen },
  { to: "/student/add-drop", label: "Add / Drop Courses", icon: Layers },
  { to: "/student/groups", label: "Lecture & Section", icon: GraduationCap },
  { to: "/student/chatbot", label: "AI Advisor", icon: Bot },
  { to: "/student/schedule", label: "Schedule", icon: CalendarDays },
];

const instructorNav: NavItem[] = [
  { to: "/instructor/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/instructor/search", label: "Search Student", icon: Search },
  { to: "/instructor/profile", label: "Student Profile", icon: UserCircle },
  { to: "/instructor/student-courses", label: "Student Courses", icon: BookOpen },
  { to: "/instructor/student-course-board", label: "Student course board", icon: Layers },
  { to: "/instructor/advising", label: "Advising Tools", icon: GraduationCap },
  { to: "/instructor/assigned", label: "Assigned Courses", icon: CalendarDays },
];

const adminNav: NavItem[] = [
  { to: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/admin/users", label: "Manage Users", icon: Users },
  { to: "/admin/create-student", label: "Create Student", icon: UserPlus },
  { to: "/admin/create-instructor", label: "Create Instructor", icon: UserPlus },
  { to: "/admin/assign", label: "Assign Instructor", icon: Settings },
  { to: "/admin/overview", label: "System Overview", icon: CalendarDays },
  { to: "/admin/complete-term", label: "Complete term", icon: CalendarCheck },
  { to: "/admin/final-grades-window", label: "Final grades window", icon: CalendarCheck },
];

const superAdminNav: NavItem[] = [
  { to: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/admin/users", label: "Manage Admins", icon: Users },
  { to: "/admin/create-admin", label: "Create Admin", icon: Shield },
];

function navForRole(role: Role): NavItem[] {
  if (role === "student") return studentNav;
  if (role === "instructor") return instructorNav;
  if (role === "super_admin") return superAdminNav;
  return adminNav;
}

export function DashboardLayout({ role }: { role: Role }) {
  const { user, logout } = useAuthNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const actualRole = user?.role ?? role;
  const items = navForRole(actualRole);
  const roleLabel = actualRole === "super_admin" ? "super admin" : role;

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200
    ${isActive ? "bg-brand-600 text-white shadow-md" : "text-slate-600 hover:bg-brand-50 hover:text-brand-800"}`;

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar desktop */}
      <aside className="hidden lg:flex w-64 flex-col fixed inset-y-0 z-30 border-r border-slate-200/80 bg-white shadow-soft">
        <div className="p-6 border-b border-slate-100">
          <div className="font-display text-xl font-bold text-gradient">LearnUp</div>
          <p className="text-xs text-slate-500 mt-1 capitalize">{roleLabel} portal</p>
        </div>
        <nav className="flex-1 overflow-y-auto p-4 space-y-1">
          {items.map((item) => (
            <NavLink key={item.to} to={item.to} className={linkClass} end={item.to.endsWith("dashboard")}>
              <item.icon className="h-5 w-5 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-slate-100">
          <button
            type="button"
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
          >
            <LogOut className="h-5 w-5" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Mobile drawer */}
      <div
        className={`fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm lg:hidden transition-opacity
          ${mobileOpen ? "opacity-100" : "opacity-0 pointer-events-none"}`}
        onClick={() => setMobileOpen(false)}
        aria-hidden
      />
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] bg-white shadow-xl transform transition-transform lg:hidden
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        <div className="flex items-center justify-between p-4 border-b">
          <span className="font-display font-bold text-brand-800">Menu</span>
          <button type="button" onClick={() => setMobileOpen(false)} className="p-2 rounded-lg hover:bg-slate-100">
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="p-4 space-y-1">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to.endsWith("dashboard")}
              onClick={() => setMobileOpen(false)}
              className={linkClass}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen">
        <header className="sticky top-0 z-20 glass border-b border-slate-200/60 px-4 md:px-8 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="lg:hidden p-2 rounded-xl hover:bg-slate-100 text-slate-700"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="h-6 w-6" />
            </button>
            <div>
              <p className="text-xs uppercase tracking-wider text-brand-600 font-semibold">Welcome back</p>
              <p className="text-lg font-semibold text-slate-900 truncate max-w-[200px] sm:max-w-md">
                {user?.full_name ?? "User"}
              </p>
            </div>
          </div>
          <div className="text-right hidden sm:block">
            <p className="text-xs text-slate-500">{user?.email}</p>
            <p className="text-sm font-medium text-slate-700">{user?.university_id}</p>
          </div>
        </header>

        <main className="flex-1 p-4 md:p-8">
          <Outlet key={location.pathname} />
        </main>
      </div>
    </div>
  );
}
