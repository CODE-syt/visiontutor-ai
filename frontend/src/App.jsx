import { useEffect, useState } from "react";
import { Routes, Route } from "react-router-dom";
import Header from "./components/Header.jsx";
import Home from "./pages/Home.jsx";
import Results from "./pages/Results.jsx";
import History from "./pages/History.jsx";

export default function App() {
  const [darkMode, setDarkMode] = useState(
    () => window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false
  );
  const [lastResult, setLastResult] = useState(null);
  const [lastPreview, setLastPreview] = useState(null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  return (
    <div className="min-h-screen">
      <Header darkMode={darkMode} onToggleDark={() => setDarkMode((d) => !d)} />
      <Routes>
        <Route
          path="/"
          element={<Home setLastResult={setLastResult} setLastPreview={setLastPreview} />}
        />
        <Route path="/results" element={<Results result={lastResult} previewUrl={lastPreview} />} />
        <Route path="/history" element={<History />} />
      </Routes>
    </div>
  );
}
