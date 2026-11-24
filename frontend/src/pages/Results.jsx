import { Link, useNavigate } from "react-router-dom";
import ResultCard from "../components/ResultCard.jsx";
import ConfidenceBadge from "../components/ConfidenceBadge.jsx";
import FormulaBlock from "../components/FormulaBlock.jsx";
import InterviewQA from "../components/InterviewQA.jsx";
import FollowUpChat from "../components/FollowUpChat.jsx";
import { askFollowUp } from "../services/api.js";

function BulletList({ items }) {
  if (!items?.length) return <p className="text-slate-400 italic">None listed.</p>;
  return (
    <ul className="list-disc list-inside space-y-1">
      {items.map((it, i) => (
        <li key={i}>{it}</li>
      ))}
    </ul>
  );
}

function NumberedList({ items }) {
  if (!items?.length) return <p className="text-slate-400 italic">None listed.</p>;
  return (
    <ol className="list-decimal list-inside space-y-1">
      {items.map((it, i) => (
        <li key={i}>{it}</li>
      ))}
    </ol>
  );
}

function downloadExplanation(result) {
  const text = `VisionTutor AI — Analysis Report
================================
Concept: ${result.concept}
Confidence: ${Math.round(result.confidence * 100)}%

SUMMARY
${result.image_summary}

BEGINNER EXPLANATION
${result.beginner_explanation}

TECHNICAL EXPLANATION
${result.technical_explanation}

HOW IT WORKS
${(result.how_it_works || []).map((s, i) => `${i + 1}. ${s}`).join("\n")}

FORMULA
${result.formula}

REAL-WORLD EXAMPLE
${result.real_world_example}

ADVANTAGES
${(result.advantages || []).map((a) => `- ${a}`).join("\n")}

LIMITATIONS
${(result.limitations || []).map((l) => `- ${l}`).join("\n")}

RELATED CONCEPTS
${(result.related_concepts || []).join(", ")}

INTERVIEW ANSWER
${result.interview_answer}

INTERVIEW QUESTIONS
${(result.interview_questions || []).map((q, i) => `${i + 1}. Q: ${q.question}\n   A: ${q.answer}`).join("\n")}
`;
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `visiontutor-${result.concept.replace(/\s+/g, "_")}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

function copyExplanation(result) {
  navigator.clipboard?.writeText(result.technical_explanation || result.image_summary || "");
}

export default function Results({ result, previewUrl }) {
  const navigate = useNavigate();

  if (!result) {
    return (
      <div className="max-w-xl mx-auto px-6 py-16 text-center">
        <p className="mb-4 text-slate-500">No analysis yet. Upload an image first.</p>
        <Link to="/" className="btn-primary">Go to Upload</Link>
      </div>
    );
  }

  const handleAsk = async (question) => {
    const data = await askFollowUp(result, question);
    return data.success ? data.answer : data.error;
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-10 space-y-6">
      <div className="flex items-center justify-between">
        <button onClick={() => navigate("/")} className="btn-secondary">← Analyze another image</button>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={() => copyExplanation(result)}>📋 Copy</button>
          <button className="btn-secondary" onClick={() => downloadExplanation(result)}>⬇️ Download</button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <ResultCard title="Image Preview">
          {previewUrl ? (
            <img src={previewUrl} alt="Analyzed" className="rounded-xl w-full object-contain max-h-80" />
          ) : (
            <p className="text-slate-400 italic">Preview unavailable.</p>
          )}
        </ResultCard>

        <ResultCard title="Detected Concept">
          <div className="space-y-3">
            <p className="text-2xl font-bold">{result.concept}</p>
            <p className="text-xs uppercase tracking-wide text-slate-400">{result.image_type}</p>
            <ConfidenceBadge confidence={result.confidence} />
            {result.rag_context_used && (
              <span className="tag">Grounded with RAG knowledge base</span>
            )}
          </div>
        </ResultCard>
      </div>

      <ResultCard title="What Is In The Image?">
        <p>{result.image_summary}</p>
        {!!result.visual_elements?.length && (
          <div className="mt-3">
            <p className="font-medium mb-1">Visual elements detected:</p>
            <BulletList items={result.visual_elements} />
          </div>
        )}
      </ResultCard>

      <ResultCard title="Extracted Text">
        {result.extracted_text?.length ? (
          <div className="space-y-1 font-mono text-xs bg-slate-100 dark:bg-slate-800 rounded-lg p-3">
            {result.extracted_text.map((t, i) => (
              <p key={i}>{t}</p>
            ))}
          </div>
        ) : (
          <p className="text-slate-400 italic">No text detected in the image.</p>
        )}
      </ResultCard>

      <div className="grid md:grid-cols-2 gap-6">
        <ResultCard title="Beginner Explanation">
          <p>{result.beginner_explanation}</p>
        </ResultCard>
        <ResultCard title="Technical Explanation">
          <p>{result.technical_explanation}</p>
        </ResultCard>
      </div>

      <ResultCard title="How It Works">
        <NumberedList items={result.how_it_works} />
      </ResultCard>

      {!!result.step_by_step?.length && (
        <ResultCard title="Step-by-Step Breakdown of the Image">
          <NumberedList items={result.step_by_step} />
        </ResultCard>
      )}

      <ResultCard title="Formula">
        <FormulaBlock formula={result.formula} />
      </ResultCard>

      <ResultCard title="Real-World Example">
        <p>{result.real_world_example}</p>
      </ResultCard>

      <div className="grid md:grid-cols-2 gap-6">
        <ResultCard title="Advantages">
          <BulletList items={result.advantages} />
        </ResultCard>
        <ResultCard title="Limitations">
          <BulletList items={result.limitations} />
        </ResultCard>
      </div>

      <ResultCard title="Related Concepts">
        <div>
          {result.related_concepts?.length ? (
            result.related_concepts.map((c) => <span key={c} className="tag">{c}</span>)
          ) : (
            <p className="text-slate-400 italic">None listed.</p>
          )}
        </div>
      </ResultCard>

      <ResultCard title="Interview Answer">
        <p className="italic">{result.interview_answer}</p>
      </ResultCard>

      <ResultCard title="Interview Questions">
        <InterviewQA items={result.interview_questions} />
      </ResultCard>

      <FollowUpChat onAsk={handleAsk} />
    </div>
  );
}
