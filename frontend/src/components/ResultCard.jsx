export default function ResultCard({ title, children, action }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="card-title !mb-0">{title}</h3>
        {action}
      </div>
      <div className="text-sm leading-relaxed text-slate-700 dark:text-slate-200">{children}</div>
    </div>
  );
}
