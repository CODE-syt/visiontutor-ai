import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 90000,
});

export async function analyzeImage(file, onUploadProgress) {
  const form = new FormData();
  form.append("image", file);
  const { data } = await api.post("/analyze", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress,
  });
  return data;
}

export async function askFollowUp(previousResult, question) {
  const { data } = await api.post("/followup", {
    previous_result: previousResult,
    question,
  });
  return data;
}

export async function fetchHistory() {
  const { data } = await api.get("/history");
  return data;
}

export async function fetchHealth() {
  const { data } = await api.get("/health");
  return data;
}

export default api;
