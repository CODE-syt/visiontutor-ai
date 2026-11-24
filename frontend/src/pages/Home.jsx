import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ImageUpload from "../components/ImageUpload.jsx";
import Loader from "../components/Loader.jsx";
import useAnalyze from "../hooks/useAnalyze.js";

export default function Home({ setLastResult, setLastPreview }) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const { loading, progress, result, error, runAnalysis } = useAnalyze();
  const navigate = useNavigate();

  const handleFile = (f) => {
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
  };

  // Once the hook resolves a successful result, stash it for the Results page and navigate.
  useEffect(() => {
    if (result) {
      setLastResult(result);
      setLastPreview(previewUrl);
      navigate("/results");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result]);

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">Upload an ML/AI image to explain</h1>
        <p className="text-slate-500 dark:text-slate-400">
          Diagrams, graphs, neural networks, decision trees, confusion matrices, equations,
          flowcharts, handwritten questions, or screenshots.
        </p>
      </div>

      <ImageUpload onFileSelected={handleFile} previewUrl={previewUrl} />

      <div className="mt-6 flex justify-center">
        <button className="btn-primary" disabled={!file || loading} onClick={() => runAnalysis(file)}>
          {loading ? "Analyzing…" : "Analyze Image"}
        </button>
      </div>

      {loading && <Loader progress={progress} />}
      {error && (
        <p className="mt-4 text-center text-red-500 text-sm bg-red-50 dark:bg-red-950/40 rounded-xl px-4 py-3">
          {error}
        </p>
      )}
    </div>
  );
}
