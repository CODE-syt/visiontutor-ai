import { useEffect, useState } from "react";
import { fetchHistory } from "../services/api.js";

export default function History() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHistory()
      .then((data) => setItems(data.items || []))
      .catch(() => setError("Could not load history (is ENABLE_HISTORY=true and MongoDB running?)."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-bold mb-6">Analysis History</h1>

      {loading && <p className="text-slate-400">Loading…</p>}
      {error && <p className="text-amber-600 dark:text-amber-400 text-sm">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <p className="text-slate-400 italic">
          No history yet. Enable it by setting ENABLE_HISTORY=true and MONGODB_URI in your backend .env.
        </p>
      )}

      {!!items.length && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b border-slate-200 dark:border-slate-800">
                <th className="py-2 pr-4">Concept</th>
                <th className="py-2 pr-4">Date</th>
                <th className="py-2 pr-4">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id} className="border-b border-slate-100 dark:border-slate-900">
                  <td className="py-2 pr-4 font-medium">{it.concept}</td>
                  <td className="py-2 pr-4 text-slate-500">{new Date(it.timestamp).toLocaleString()}</td>
                  <td className="py-2 pr-4">{Math.round(it.confidence * 100)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
