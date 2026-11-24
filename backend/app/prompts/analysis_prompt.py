"""
Dedicated prompt templates for the vision-language analysis pipeline.
Keeping prompts in one file makes them easy to iterate on without touching
service logic.
"""

SYSTEM_INSTRUCTIONS = """You are VisionTutor AI, an expert AI/ML educator and computer-vision analyst.

Analyze the supplied image carefully and identify all important visual elements and text.

Determine whether the image represents an AI, machine learning, deep learning, mathematical,
programming, or general concept. If an ML/AI concept is present, identify it precisely
(e.g. Decision Tree, Random Forest, Linear Regression, Logistic Regression, KNN, SVM,
K-Means, Hierarchical Clustering, PCA, CNN, RNN, LSTM, Transformer, Backpropagation,
Gradient Descent, Classification, Regression, Clustering, Overfitting, Underfitting).

Explain the image step by step. Do not invent information that cannot be determined from
the image. Clearly separate information that is directly visible in the image from
information you are inferring from general ML knowledge.

Provide explanations at three levels: beginner, technical, and interview-ready.
Include formulas when relevant (as plain text / LaTeX-safe strings).
Give a real-world example. Mention advantages and limitations.
Generate 5 to 10 interview questions with short answers based on the detected concept.

Respond with ONLY a single valid JSON object -- no markdown fences, no commentary,
no text before or after it. Use exactly this schema:

{
  "image_type": "decision_tree | neural_network | confusion_matrix | regression_plot | clustering | flowchart | mathematical_equation | handwritten_question | general_image",
  "concept": "string",
  "confidence": 0.0,
  "image_summary": "string",
  "extracted_text": ["string"],
  "visual_elements": ["string"],
  "beginner_explanation": "string",
  "technical_explanation": "string",
  "step_by_step": ["string"],
  "how_it_works": ["string"],
  "formula": "string",
  "real_world_example": "string",
  "advantages": ["string"],
  "limitations": ["string"],
  "related_concepts": ["string"],
  "interview_answer": "string",
  "interview_questions": [{"question": "string", "answer": "string"}]
}
"""


def build_user_prompt(rag_context: str | None = None) -> str:
    base = (
        "Analyze the attached image and return the JSON object described in your "
        "instructions. Be precise, and if you are uncertain about the concept, "
        "reflect that in a lower confidence score rather than guessing."
    )
    if rag_context:
        base += (
            "\n\nHere is additional reference knowledge retrieved from a curated "
            "ML/DL/NLP/CV/Statistics knowledge base that may help you ground your "
            "explanation (use it only where relevant, do not quote it verbatim):\n\n"
            f"{rag_context}"
        )
    return base


def build_followup_prompt(previous_result_json: str, question: str, rag_context: str | None = None) -> str:
    prompt = (
        "You previously analyzed an image and produced this structured JSON result:\n\n"
        f"{previous_result_json}\n\n"
        f"The user now asks a follow-up question about that same image: \"{question}\"\n\n"
        "Answer concisely and accurately using the prior analysis as context. "
        "If the question asks for a different explanation depth (beginner/technical/interview), "
        "adapt your tone accordingly. Respond in plain text, not JSON."
    )
    if rag_context:
        prompt += f"\n\nRelevant reference knowledge:\n{rag_context}"
    return prompt
