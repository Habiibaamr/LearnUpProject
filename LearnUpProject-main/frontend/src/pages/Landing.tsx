import { useNavigate } from "react-router-dom";
import { GraduationCap, Shield, Sparkles, UserCircle } from "lucide-react";
import { RoleCard } from "../components/RoleCard";
import { useAuth } from "../context/AuthContext";
import { getDashboardPath, type Role } from "../types";
import { useEffect } from "react";

export default function Landing() {
  const navigate = useNavigate();
  const { setIntendedRole, user, token } = useAuth();

  useEffect(() => {
    if (token && user) {
      navigate(getDashboardPath(user.role), { replace: true });
    }
  }, [token, user, navigate]);

  const go = (role: Role) => {
    setIntendedRole(role);
    navigate("/login");
  };

  return (
    <div className="min-h-screen">
      <div className="gradient-hero relative overflow-hidden">
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-20 left-10 w-72 h-72 bg-white/20 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-10 right-20 w-96 h-96 bg-blue-300/30 rounded-full blur-3xl animate-float" style={{ animationDelay: "2s" }} />
        </div>
        <div className="relative max-w-6xl mx-auto px-4 pt-16 pb-28 md:pt-24 md:pb-36 text-center">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-4 py-1.5 text-sm text-white/95 backdrop-blur mb-8">
            <Sparkles className="h-4 w-4" />
            Student Information System
          </div>
          <h1 className="font-display text-4xl md:text-6xl font-bold text-white tracking-tight max-w-3xl mx-auto leading-tight">
            LearnUp Academic Portal
          </h1>
          <p className="mt-6 text-lg md:text-xl text-blue-100 max-w-2xl mx-auto leading-relaxed">
            One secure platform for students, instructors, and administrators — courses, advising, and support in one place.
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 -mt-16 relative z-10 pb-20">
        <p className="text-center text-slate-600 font-medium mb-8">Choose how you want to sign in</p>
        <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-6 md:gap-8">
          <RoleCard
            title="Student"
            description="View your ID card, manage courses, register for lectures, and chat with the AI advisor."
            icon={GraduationCap}
            onSelect={() => go("student")}
            delay={0}
          />
          <RoleCard
            title="Instructor"
            description="Look up students, review registrations, and help with add/drop as an academic advisor."
            icon={UserCircle}
            onSelect={() => go("instructor")}
            delay={100}
          />
          <RoleCard
            title="Administrator"
            description="Create student and instructor accounts, assign instructors to offerings, and oversee academic operations."
            icon={Shield}
            onSelect={() => go("admin")}
            delay={200}
          />
          <RoleCard
            title="Super Admin"
            description="Create, update, and delete administrator accounts."
            icon={Shield}
            onSelect={() => go("super_admin")}
            delay={300}
          />
        </div>
      </div>

      <footer className="border-t border-slate-200 bg-white py-8 text-center text-sm text-slate-500">
        LearnUp SIS · Graduation project demo
      </footer>
    </div>
  );
}
