"""
POST /api/analyze  -- the core image-to-explanation endpoint.
POST /api/followup -- "chat with the uploaded image" follow-up Q&A.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.config import Settings, get_settings
from app.models.schemas import (
    AnalysisResult,
    AnalyzeResponse,
    FollowUpRequest,
    FollowUpResponse,
)
from app.prompts.analysis_prompt import (
    SYSTEM_INSTRUCTIONS,
    build_followup_prompt,
    build_user_prompt,
)
from app.services.ai_service import AIService, AIServiceError
from app.services.image_service import prepare_image_for_analysis
from app.services.rag_service import RAGService

logger = logging.getLogger("visiontutor.analyze")
router = APIRouter()


def get_ai_service(settings: Settings = Depends(get_settings)) -> AIService:
    return AIService(settings)


def get_rag_service(settings: Settings = Depends(get_settings)) -> RAGService:
    # NOTE: for a production deployment, build this once at app startup
    # (see app/main.py lifespan) instead of per-request; kept simple here.
    return RAGService(settings)


@router.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    request: Request,
    image: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    ai_service: AIService = Depends(get_ai_service),
) -> AnalyzeResponse:
    try:
        image_b64 = await prepare_image_for_analysis(image, settings)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    rag_service: RAGService = request.app.state.rag_service
    rag_context = ""
    used_rag = False
    if rag_service.is_ready:
        try:
            # First-pass: retrieve broadly on a generic ML query; the concept
            # isn't known yet at this point, so this seeds the prompt with
            # general ML/DL/CV/Stats grounding context.
            rag_context = rag_service.retrieve("machine learning deep learning concept diagram")
            used_rag = bool(rag_context)
        except Exception:  # noqa: BLE001
            logger.warning("RAG retrieval failed; continuing without it.", exc_info=True)

    user_prompt = build_user_prompt(rag_context or None)

    try:
        raw_result = await ai_service.analyze_image_structured(
            image_b64, SYSTEM_INSTRUCTIONS, user_prompt
        )
    except AIServiceError as exc:
        logger.error("AI analysis failed: %s", exc)
        return AnalyzeResponse(success=False, error=f"AI analysis failed: {exc}")

    try:
        result = AnalysisResult.model_validate(raw_result)
    except Exception as exc:  # noqa: BLE001
        logger.error("AI response failed schema validation: %s", exc)
        return AnalyzeResponse(
            success=False, error="AI returned a response that could not be validated."
        )

    result.rag_context_used = used_rag

    history = request.app.state.history_store
    if history.enabled:
        try:
            await history.save(result.concept, result.confidence, result.model_dump())
        except Exception:  # noqa: BLE001
            logger.warning("Failed to persist analysis history.", exc_info=True)

    return AnalyzeResponse(success=True, result=result)


@router.post("/api/followup", response_model=FollowUpResponse)
async def followup_question(
    request: Request,
    payload: FollowUpRequest,
    ai_service: AIService = Depends(get_ai_service),
) -> FollowUpResponse:
    rag_service: RAGService = request.app.state.rag_service
    rag_context = ""
    if rag_service.is_ready:
        try:
            rag_context = rag_service.retrieve(f"{payload.previous_result.concept} {payload.question}")
        except Exception:  # noqa: BLE001
            logger.warning("RAG retrieval failed on follow-up; continuing without it.", exc_info=True)

    prompt = build_followup_prompt(
        payload.previous_result.model_dump_json(), payload.question, rag_context or None
    )

    try:
        answer = await ai_service.chat_text(SYSTEM_INSTRUCTIONS, prompt)
    except AIServiceError as exc:
        return FollowUpResponse(success=False, error=f"Follow-up failed: {exc}")

    return FollowUpResponse(success=True, answer=answer.strip())
