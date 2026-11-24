import { useState } from "react";

export default function InterviewQA({ items = [] }) {
  const [open, setOpen] = useState(null);

  if (!items.length) return <p className="text-slate-400 italic">No interview questions generated.</p>;

  return (
    <div className="space-y-2">
      {items.map((qa, idx) => (
        <div key={idx} className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
          <button
            className="w-full text-left px-4 py-3 font-medium flex justify-between items-center hover:bg-slate-50 dark:hover:bg-slate-800"
            onClick={() => setOpen(open === idx ? null : idx)}
          >
            <span>{idx + 1}. {qa.question}</span>
            <span className="text-slate-400">{open === idx ? "−" : "+"}</span>
          </button>
          {open === idx && (
            <div className="px-4 pb-3 text-sm text-slate-600 dark:text-slate-300">{qa.answer}</div>
          )}
        </div>
      ))}
    </div>
  );
}
