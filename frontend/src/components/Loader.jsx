export default function Loader({ progress }) {
  return (
    <div className="flex flex-col items-center justify-center py-10 gap-4">
      <div className="h-12 w-12 rounded-full border-4 border-brand-200 border-t-brand-500 animate-spin" />
      <p className="font-medium text-slate-600 dark:text-slate-300">
        Analyzing image{progress ? ` (${progress}% uploaded)` : "..."}
      </p>
      <p className="text-xs text-slate-400">Running the image through the vision model and RAG pipeline…</p>
    </div>
  );
}
