import { BlockMath } from "react-katex";
import "katex/dist/katex.min.css";

/** Renders a formula string with KaTeX; falls back to plain text if it can't parse. */
export default function FormulaBlock({ formula }) {
  if (!formula) return <p className="text-slate-400 italic">No formula extracted for this concept.</p>;
  try {
    return <BlockMath math={formula} />;
  } catch {
    return <p className="font-mono text-sm">{formula}</p>;
  }
}
