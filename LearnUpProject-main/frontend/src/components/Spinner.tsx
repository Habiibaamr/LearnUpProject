export function Spinner({ className = "" }: { className?: string }) {
  return (
    <div
      className={`h-10 w-10 rounded-full border-2 border-brand-200 border-t-brand-600 animate-spin ${className}`}
      role="status"
      aria-label="Loading"
    />
  );
}
