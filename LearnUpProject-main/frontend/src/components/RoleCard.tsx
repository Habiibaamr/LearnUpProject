import type { LucideIcon } from "lucide-react";

export function RoleCard({
  title,
  description,
  icon: Icon,
  onSelect,
  delay = 0,
}: {
  title: string;
  description: string;
  icon: LucideIcon;
  onSelect: () => void;
  delay?: number;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className="group relative w-full text-left rounded-2xl bg-white p-8 shadow-card border border-slate-100
        transition-all duration-300 hover:shadow-glow hover:border-brand-200 hover:-translate-y-1 opacity-0 animate-fadeUp"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-brand-500/0 to-brand-600/0 group-hover:from-brand-500/5 group-hover:to-brand-600/10 transition-all duration-300" />
      <div className="relative flex flex-col gap-4">
        <div className="inline-flex h-14 w-14 items-center justify-center rounded-xl bg-brand-50 text-brand-600 group-hover:bg-brand-600 group-hover:text-white transition-colors duration-300">
          <Icon className="h-7 w-7" strokeWidth={1.75} />
        </div>
        <div>
          <h3 className="font-display text-xl font-semibold text-slate-900 group-hover:text-brand-800 transition-colors">
            {title}
          </h3>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">{description}</p>
        </div>
        <span className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 group-hover:gap-2 transition-all">
          Continue
          <span aria-hidden>→</span>
        </span>
      </div>
    </button>
  );
}
