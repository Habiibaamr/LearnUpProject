import type { ReactNode } from "react";

export function FeaturePageLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold text-slate-900 tracking-tight">{title}</h1>
        {subtitle ? <p className="mt-2 text-slate-600 max-w-2xl">{subtitle}</p> : null}
      </div>
      <div className="rounded-2xl bg-white border border-slate-100 shadow-soft p-6 md:p-8">
        {children}
      </div>
    </div>
  );
}
