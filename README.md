# VisionTutor AI — Image Understanding and Machine Learning Concept Explainer

Upload an image containing an ML/AI diagram, graph, neural network, decision tree,
confusion matrix, equation, flowchart, handwritten question, or screenshot — VisionTutor
AI analyzes it with a vision-language model, grounds the explanation with a RAG
knowledge base, and returns a structured, multi-level explanation (beginner,
technical, interview-ready), formulas, real-world examples, advantages/limitations,
related concepts, and interview Q&A.

---

## 1. Project Overview

VisionTutor AI is a full-stack application: a React + Vite frontend for upload and
results, and a FastAPI backend that validates/preprocesses the image, sends it to a
configurable vision-language model, optionally retrieves grounding context from a
local FAISS knowledge base, validates the model's structured JSON output with
Pydantic, and returns it to the UI.

## 2. Features

- Drag-and-drop image upload with preview, validation, and safe error handling
- Vision-language analysis: concept detection, confidence score, OCR-style text
  extraction, step-by-step explanation
- Three explanation depths: beginner, technical, interview
- Formula rendering with KaTeX
- Real-world example, advantages, limitations, related concepts
- 5–10 auto-generated interview questions with short answers, shown as an
  expandable FAQ
- Optional RAG grounding over a curated ML/DL/NLP/CV/Statistics knowledge base
- Follow-up chat ("chat with the uploaded image") using the prior analysis as context
- Copy / download explanation, dark mode, optional analysis history (MongoDB)
- Provider-agnostic AI service abstraction (OpenAI, Gemini, Qwen-VL, LLaVA/local)
- Dockerized: frontend, backend, and optional MongoDB

## 3. Architecture

```
User
  ↓
React Frontend (Vite, Tailwind, Axios)
  ↓  multipart/form-data POST /api/analyze
FastAPI Backend
  ↓
Image Validation  →  Image Preprocessing (RGB, resize, strip metadata)
  ↓
AIService (provider-agnostic facade)
  ↓
Vision-Language Model (OpenAI / Gemini / Qwen-VL / LLaVA)
  ↓
Visual Understanding + ML Concept Detection (via prompt contract)
  ↓
RAG Knowledge Retrieval (FAISS over knowledge_base/)  [optional, ENABLE_RAG]
  ↓
LLM produces structured JSON
  ↓
Pydantic validation + safe-parse/repair fallback
  ↓
Structured Response (AnalysisResult)
  ↓
React UI (14 result cards + interview Q&A + follow-up chat)
```

## 4. Technology Stack

**Frontend:** React 18, Vite, Tailwind CSS, Axios, React Router, KaTeX (formulas)

**Backend:** Python 3.11, FastAPI, Uvicorn, Pydantic v2, Pillow, OpenCV
(headless), httpx, tenacity (retries), slowapi (rate limiting)

**AI:** Configurable VLM/LLM via a single `AIService` abstraction
(`app/services/ai_service.py`) — swap providers with one `.env` variable.

**RAG:** FAISS (flat inner-product index) over chunked `.txt` documents in
`knowledge_base/`.

**Database (optional):** MongoDB via Motor (async driver), used only for
analysis *metadata* history — uploaded images are never persisted.

## 5. Folder Structure

```
visiontutor-ai/
├── frontend/
│   ├── src/
│   │   ├── components/   ImageUpload, ResultCard, Loader, ConfidenceBadge,
│   │   │                 FormulaBlock, InterviewQA, FollowUpChat, Header
│   │   ├── pages/        Home, Results, History
│   │   ├── services/     api.js (Axios client)
│   │   ├── hooks/        useAnalyze.js
│   │   ├── App.jsx, main.jsx, index.css
│   ├── index.html, vite.config.js, tailwind.config.js, package.json
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── routes/       analyze.py, health.py, history.py
│   │   ├── services/     ai_service.py, image_service.py, rag_service.py
│   │   ├── models/       schemas.py (Pydantic)
│   │   ├── utils/        validators.py, file_utils.py
│   │   ├── prompts/      analysis_prompt.py
│   │   ├── rag/          (FAISS index cache lives here at runtime)
│   │   ├── config.py, db.py, main.py
│   ├── requirements.txt, .env.example
│   └── Dockerfile
├── knowledge_base/        sample ML/DL/CV/Stats .txt documents for RAG
├── docker-compose.yml
└── README.md
```

## 6. Installation

Requires: Python 3.11+, Node.js 18+, and (optionally) Docker Desktop.

```bash
git clone <this-repo-or-unzip-the-provided-archive>
cd visiontutor-ai
```

## 7. Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in your key:

```env
AI_PROVIDER=openai            # openai | gemini | qwen | llava
AI_API_KEY=your_key_here
AI_MODEL=gpt-4o-mini
AI_BASE_URL=                  # optional override, e.g. local vLLM/Ollama server
AI_TIMEOUT=60

ENABLE_RAG=true
KNOWLEDGE_BASE_DIR=../knowledge_base
VECTOR_INDEX_PATH=./app/rag/index.faiss

ENABLE_HISTORY=false
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=visiontutor

MAX_UPLOAD_MB=8
ALLOWED_ORIGINS=http://localhost:5173
RATE_LIMIT_PER_MINUTE=20
```

`AI_API_KEY` is read only on the backend and is **never** exposed to the
frontend bundle.

## 8. Backend Setup (Windows + VS Code)

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# edit .env and paste your AI_API_KEY
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/api/health` → `{"status": "healthy"}`.
Interactive API docs: `http://localhost:8000/docs`.

## 9. Frontend Setup (Windows + VS Code)

```powershell
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. The Vite dev server proxies `/api/*` to
`http://localhost:8000` (see `vite.config.js`), so no CORS setup is needed
in development beyond `ALLOWED_ORIGINS` in the backend `.env`.

## 10. RAG Setup

RAG is optional and controlled by `ENABLE_RAG` in `backend/.env`.

1. Drop plain-text `.txt` reference documents into `knowledge_base/` (five
   sample files covering decision trees, regression, clustering, neural
   networks, and model evaluation are included).
2. On backend startup, `RAGService` chunks each document (500 words,
   50-word overlap), embeds every chunk, and builds an in-memory FAISS
   `IndexFlatIP`. This happens once at app startup (see the `lifespan`
   handler in `app/main.py`), not per-request.
3. At analysis time, the top-3 most similar chunks are retrieved and
   appended to the LLM prompt as grounding context.

By default the embedding step uses a dependency-free deterministic hashed
bag-of-words vectorizer so RAG works out of the box with zero extra API
calls or cost. For production-quality retrieval, swap
`app/services/rag_service.py`'s `_hash_embed()` for a call to a real
embedding model (e.g. your provider's `text-embedding-3-small` /
`text-embedding-004`) — the FAISS index and chunking logic don't need to
change.

Set `ENABLE_RAG=false` to disable the whole pipeline — the app works
identically otherwise, just without the grounding context in the prompt.

## 11. Running Locally

1. Start the backend: `uvicorn app.main:app --reload --port 8000` (from `backend/`)
2. Start the frontend: `npm run dev` (from `frontend/`)
3. Open `http://localhost:5173`, upload an image, click **Analyze Image**.

## 12. Docker Instructions

```bash
cd visiontutor-ai
# create backend/.env first (see section 7)
docker compose up --build
```

- Frontend: `http://localhost:4173`
- Backend: `http://localhost:8000`
- MongoDB (only used if `ENABLE_HISTORY=true`): `localhost:27017`

## 13. API Documentation

### `GET /api/health`
Returns `{"status": "healthy"}`.

### `POST /api/analyze`
`multipart/form-data`, field name `image` (JPG/JPEG/PNG/WEBP, ≤ `MAX_UPLOAD_MB`).
Returns `AnalyzeResponse`:
```json
{ "success": true, "result": { ...AnalysisResult... } }
```
or on failure:
```json
{ "success": false, "error": "human-readable message" }
```

### `POST /api/followup`
JSON body: `{ "previous_result": <AnalysisResult>, "question": "string" }`
Returns `{ "success": true, "answer": "string" }`.

### `GET /api/history` / `GET /api/history/{id}`
Only functional when `ENABLE_HISTORY=true`; returns an empty list otherwise.

## 14. Example Request

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "image=@decision_tree_diagram.png"
```

## 15. Example Response

```json
{
  "success": true,
  "result": {
    "image_type": "decision_tree",
    "concept": "Decision Tree",
    "confidence": 0.94,
    "image_summary": "The image shows a binary tree with feature-based splits leading to leaf predictions.",
    "extracted_text": ["Age <= 30?", "Yes", "No", "Buys = Yes", "Buys = No"],
    "visual_elements": ["root node", "branch arrows", "leaf nodes"],
    "beginner_explanation": "A decision tree asks yes/no questions about your data to reach a final decision, like a flowchart.",
    "technical_explanation": "The tree recursively partitions the feature space by selecting the split that maximizes information gain (or minimizes Gini impurity) at each node.",
    "step_by_step": ["Root node evaluates Age <= 30", "Branch to Yes/No subtrees", "Leaves output the predicted class"],
    "how_it_works": ["Input data is provided.", "The algorithm evaluates features.", "A splitting criterion is calculated.", "The best feature is selected.", "Data is divided.", "The process continues recursively.", "The final prediction is generated."],
    "formula": "IG(D, A) = H(D) - \\sum_{v \\in Values(A)} \\frac{|D_v|}{|D|} H(D_v)",
    "real_world_example": "Predicting loan default risk from applicant income, age, and credit history.",
    "advantages": ["Easy to interpret", "No feature scaling needed", "Handles non-linear relationships"],
    "limitations": ["Prone to overfitting", "High variance", "Unstable to small data changes"],
    "related_concepts": ["Random Forest", "Gradient Boosting", "Entropy", "Gini Impurity"],
    "interview_answer": "A decision tree is a non-parametric supervised model that splits data recursively on the feature that best separates classes, using criteria like Gini impurity or information gain.",
    "interview_questions": [
      {"question": "What is entropy in the context of decision trees?", "answer": "A measure of impurity/uncertainty in a set of labels, used to compute information gain for splits."}
    ],
    "rag_context_used": true
  }
}
```

## 16. Troubleshooting

| Problem | Fix |
|---|---|
| `422`/`415` on upload | Check the file is JPG/PNG/WEBP and under `MAX_UPLOAD_MB`. |
| `AI analysis failed` | Verify `AI_API_KEY`, `AI_PROVIDER`, and `AI_MODEL` in `backend/.env`; check provider status/quota. |
| CORS errors in browser console | Add your frontend origin to `ALLOWED_ORIGINS` in `backend/.env`. |
| RAG not returning context | Confirm `ENABLE_RAG=true`, `knowledge_base/` has `.txt` files, and `faiss-cpu` installed correctly for your platform. |
| History page empty | Set `ENABLE_HISTORY=true` and a running `MONGODB_URI`; history is opt-in and images are never stored, only metadata. |
| Slow analysis | Large images are downscaled to 1600px automatically; also check your provider's latency/timeout (`AI_TIMEOUT`). |

## 17. Future Improvements

- Real embedding-model integration for RAG (currently a hashed fallback)
- Streaming LLM responses token-by-token in the UI
- Multi-image / batch analysis and comparison
- Voice narration of explanations (TTS)
- Dedicated "Interview Mode" that quizzes the user on generated questions
- Persisted per-user history with auth, instead of a single shared collection

---

## How to Explain This Project in an Interview

### Problem Statement
Students and practitioners frequently encounter ML/AI diagrams, plots, and
equations (in papers, slides, or handwritten notes) they don't fully
understand. There's no fast way to point a camera/screenshot at a diagram and
get a structured, leveled explanation with interview-ready framing.

### Proposed Solution
A web app that accepts an image, uses a vision-language model to interpret it,
grounds the explanation with a small retrieval-augmented knowledge base of ML
fundamentals, and returns a structured JSON explanation rendered as readable
UI cards — spanning beginner to interview-level depth, plus generated
practice questions.

### Architecture
Decoupled React frontend and FastAPI backend communicating over a REST API.
The backend has clean separation of concerns: `routes` (HTTP layer),
`services` (AI provider abstraction, image preprocessing, RAG retrieval),
`models` (Pydantic schemas as the API contract), and `prompts` (versioned
prompt templates). This mirrors a typical production ML-application
architecture: ingestion → preprocessing → model inference →
retrieval-augmentation → validation → response.

### AI/ML Concepts Used
- **Computer Vision** — image preprocessing (RGB conversion, resizing,
  metadata stripping) prepares input for the model.
- **Vision-Language Models (VLMs)** — models like GPT-4o or Gemini that
  jointly process image and text tokens to produce grounded descriptions.
- **Transformers & Attention** — the underlying architecture of modern
  VLMs/LLMs; self-attention lets the model relate visual regions and text
  tokens to each other.
- **Embeddings** — dense vector representations of text chunks, used to
  measure semantic similarity for retrieval.
- **LLM** — used both for the structured analysis and for open-ended
  follow-up chat.
- **Prompt Engineering** — a carefully constrained system prompt forces a
  strict JSON schema, three explanation depths, and separation of "observed
  vs. inferred" information to reduce hallucination.
- **RAG (Retrieval-Augmented Generation)** — retrieves relevant ML knowledge
  chunks before generation, improving factual grounding without fine-tuning.
- **Vector Database** — FAISS stores chunk embeddings and performs
  approximate/exact nearest-neighbor search efficiently.
- **Classification** — the "detect ML concept" step is itself a
  classification task performed by the VLM over a fixed taxonomy.
- **OCR** — text extraction from the image is one of the VLM's outputs.
- **REST API** — FastAPI exposes stateless JSON endpoints consumed by the
  React frontend.

### End-to-End Data Flow
1. User drags/drops or selects an image in the React UI; a local preview
   renders immediately.
2. On "Analyze Image", Axios POSTs the file as `multipart/form-data` to
   `POST /api/analyze`.
3. FastAPI validates file type/size, decodes it with Pillow, strips
   metadata, resizes if needed, and base64-encodes it.
4. `RAGService` (built once at startup) retrieves the most relevant
   knowledge-base chunks.
5. `AIService` builds the system + user prompt (including RAG context) and
   calls the configured provider's vision endpoint.
6. The raw text response is parsed as JSON; on failure, the app pipes the
   model's own output back to it with a "fix your JSON" repair prompt before
   giving up (with retries via `tenacity`).
7. The result is validated against the `AnalysisResult` Pydantic schema
   (defaults + clamping protect the client from malformed fields).
8. The validated JSON returns to React, which renders the 14 explanation
   cards, interview Q&A accordion, and follow-up chat panel.
9. If enabled, the metadata (concept, confidence, explanation, timestamp —
   never the raw image) is saved to MongoDB for the history page.

### Why Use a VLM?
Because the primary signal is visual — diagram structure, arrows, axes,
handwriting — a text-only LLM can't see the image. A VLM jointly encodes
image and text, letting the model describe layout and content directly.

### Why Use an LLM?
Once visual content is understood, generating multi-level natural-language
explanations, formulas, examples, and interview questions is fundamentally a
language-generation task, which is what LLMs (often the same multimodal
model) are best at.

### Why Use RAG?
VLMs can hallucinate specifics (exact formulas, terminology). Grounding the
prompt with retrieved, curated reference text reduces hallucination and
keeps explanations consistent with a known-correct knowledge base, without
needing to fine-tune the model.

### Why Use a Vector Database?
Naively comparing a query against every knowledge-base chunk in a Python
loop doesn't scale. FAISS provides fast, in-memory nearest-neighbor search
over chunk embeddings, which is the standard approach for RAG retrieval at
any nontrivial knowledge-base size.

### How Can Hallucination Be Reduced?
- Strict JSON-schema prompting with explicit "don't invent information" and
  "separate observed vs. inferred" instructions.
- RAG grounding with curated reference text.
- Lower `temperature` (0.2) for more deterministic, less creative output.
- Confidence scoring so low-certainty detections are visibly flagged rather
  than presented as fact.
- Schema validation with safe defaults, so a malformed field never silently
  becomes wrong information in the UI.

### How Can the System Be Scaled?
- Move RAG index building out of the request path (already done — built
  once at startup) and persist the FAISS index to disk (`VECTOR_INDEX_PATH`)
  to avoid rebuilding on every restart.
- Run multiple Uvicorn/Gunicorn workers behind a load balancer; the backend
  is stateless per request (RAG index and DB connections are shared app
  state).
- Cache repeated identical-image analyses (hash the image) to avoid
  redundant model calls.
- Move MongoDB to a managed cluster and add pagination/indexes on the
  history collection.

### How Can the System Be Made Faster?
- Stream the LLM response token-by-token to the UI instead of waiting for
  the full JSON (a listed future improvement).
- Downscale images more aggressively before sending to the VLM (already
  capped at 1600px).
- Use a smaller/faster model tier for a "quick preview" pass, with a
  slower/higher-quality model for the full explanation.
- Swap the hashed-embedding RAG fallback for a batched real embedding call
  computed once at index-build time (already the case) rather than per query.

### How Can the System Be Deployed?
- Containerized via the included `docker-compose.yml` (frontend, backend,
  optional MongoDB); push images to a registry and deploy to any
  container platform (Render, Railway, ECS, Cloud Run, AKS/EKS/GKE).
- Serve the built frontend as static files behind a CDN, with the backend
  behind its own domain/path and CORS configured via `ALLOWED_ORIGINS`.
- Store secrets (`AI_API_KEY`, `MONGODB_URI`) in the platform's secret
  manager, never in the image or frontend bundle.
- Add a managed MongoDB (e.g. Atlas) and a persistent volume or object
  store for the FAISS index if scaling beyond a single instance.
