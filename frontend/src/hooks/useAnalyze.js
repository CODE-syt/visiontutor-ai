import { useCallback, useState } from "react";
import { analyzeImage, askFollowUp } from "../services/api.js";

export default function useAnalyze() {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const runAnalysis = useCallback(async (file) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setProgress(0);
    try {
      const data = await analyzeImage(file, (evt) => {
        if (evt.total) setProgress(Math.round((evt.loaded * 100) / evt.total));
      });
      if (!data.success) {
        setError(data.error || "Analysis failed.");
      } else {
        setResult(data.result);
      }
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          "Something went wrong while analyzing the image."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const ask = useCallback(
    async (question) => {
      if (!result) return null;
      try {
        const data = await askFollowUp(result, question);
        return data.success ? data.answer : data.error;
      } catch (err) {
        return err?.response?.data?.detail || "Follow-up question failed.";
      }
    },
    [result]
  );

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setProgress(0);
  }, []);

  return { loading, progress, result, error, runAnalysis, ask, reset };
}
