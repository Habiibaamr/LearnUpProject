import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";

export function DashboardCard({
  title,
  subtitle,
  icon: Icon,
  to,
}: {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  to: string;
}) {
  return (
    <Link
      to={to}
      className="group flex gap-4 rounded-2xl bg-white p-6 shadow-soft border border-slate-100
        transition-all duration-300 hover:shadow-card hover:border-brand-200 hover:-translate-y-0.5"
    >
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 group-hover:bg-brand-600 group-hover:text-white transition-colors">
        <Icon className="h-6 w-6" strokeWidth={1.75} />
      </div>
      <div className="min-w-0">
        <h3 className="font-semibold text-slate-900 group-hover:text-brand-800 transition-colors">
          {title}
        </h3>
        <p className="mt-1 text-sm text-slate-500 line-clamp-2">{subtitle}</p>
      </div>
    </Link>
  );
}
