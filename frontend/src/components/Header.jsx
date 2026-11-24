import { Link, useLocation } from "react-router-dom";

export default function Header({ darkMode, onToggleDark }) {
  const location = useLocation();

  return (
    <header className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur sticky top-0 z-20">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex flex-col">
          <span className="text-xl font-bold text-brand-600 dark:text-brand-400">
            VisionTutor AI
          </span>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Upload an image and understand the AI behind it.
          </span>
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link
            to="/"
            className={`hover:text-brand-500 ${location.pathname === "/" ? "text-brand-500 font-medium" : "text-slate-600 dark:text-slate-300"}`}
          >
            Analyze
          </Link>
          <Link
            to="/history"
            className={`hover:text-brand-500 ${location.pathname === "/history" ? "text-brand-500 font-medium" : "text-slate-600 dark:text-slate-300"}`}
          >
            History
          </Link>
          <button onClick={onToggleDark} className="btn-secondary !px-3 !py-1.5 text-xs">
            {darkMode ? "☀️ Light" : "🌙 Dark"}
          </button>
        </nav>
      </div>
    </header>
  );
}
