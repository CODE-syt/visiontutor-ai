import { useCallback, useRef, useState } from "react";

const ACCEPTED = ["image/jpeg", "image/jpg", "image/png", "image/webp"];

export default function ImageUpload({ onFileSelected, previewUrl }) {
  const [dragOver, setDragOver] = useState(false);
  const [localError, setLocalError] = useState(null);
  const inputRef = useRef(null);

  const handleFiles = useCallback(
    (files) => {
      const file = files?.[0];
      if (!file) return;
      if (!ACCEPTED.includes(file.type)) {
        setLocalError("Unsupported file type. Please upload JPG, PNG, or WEBP.");
        return;
      }
      setLocalError(null);
      onFileSelected(file);
    },
    [onFileSelected]
  );

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition-colors ${
          dragOver
            ? "border-brand-500 bg-brand-50 dark:bg-slate-800"
            : "border-slate-300 dark:border-slate-700 hover:border-brand-400"
        }`}
      >
        {previewUrl ? (
          <img src={previewUrl} alt="Preview" className="mx-auto max-h-72 rounded-lg shadow" />
        ) : (
          <div className="space-y-2">
            <div className="text-4xl">🖼️</div>
            <p className="font-medium">Drag & drop an image, or click to upload</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              ML diagrams, graphs, neural networks, equations, flowcharts, screenshots — JPG, PNG, WEBP
            </p>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED.join(",")}
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>
      {localError && <p className="mt-2 text-sm text-red-500">{localError}</p>}
    </div>
  );
}
