import { useState } from "react";

const SUGGESTIONS = [
  "What is the formula?",
  "Explain this like I'm a beginner.",
  "Give me an interview answer.",
  "What are common mistakes with this concept?",
];

export default function FollowUpChat({ onAsk }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [asking, setAsking] = useState(false);

  const send = async (q) => {
    const text = (q ?? question).trim();
    if (!text || asking) return;
    setAsking(true);
    setMessages((m) => [...m, { role: "user", text }]);
    setQuestion("");
    const answer = await onAsk(text);
    setMessages((m) => [...m, { role: "ai", text: answer || "No answer returned." }]);
    setAsking(false);
  };

  return (
    <div className="card">
      <h3 className="card-title">Chat with this image</h3>
      <div className="flex flex-wrap gap-2 mb-3">
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => send(s)} className="tag hover:bg-brand-100 dark:hover:bg-slate-700">
            {s}
          </button>
        ))}
      </div>
      <div className="space-y-2 max-h-64 overflow-y-auto mb-3">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`text-sm px-3 py-2 rounded-xl max-w-[85%] ${
              m.role === "user"
                ? "bg-brand-500 text-white ml-auto"
                : "bg-slate-100 dark:bg-slate-800"
            }`}
          >
            {m.text}
          </div>
        ))}
        {asking && <div className="text-xs text-slate-400">Thinking…</div>}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="flex gap-2"
      >
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a follow-up question about this image…"
          className="flex-1 rounded-xl border border-slate-300 dark:border-slate-700 bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
        />
        <button type="submit" className="btn-primary !px-4 !py-2" disabled={asking}>
          Send
        </button>
      </form>
    </div>
  );
}
