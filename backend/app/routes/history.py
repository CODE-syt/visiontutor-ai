"""GET /api/history and GET /api/history/{id} -- optional analysis history (MongoDB)."""
from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import HistoryItem, HistoryListResponse

router = APIRouter()


@router.get("/api/history", response_model=HistoryListResponse)
async def list_history(request: Request) -> HistoryListResponse:
    store = request.app.state.history_store
    if not store.enabled:
        return HistoryListResponse(items=[])
    raw_items = await store.list_recent()
    return HistoryListResponse(items=[HistoryItem(**item) for item in raw_items])


@router.get("/api/history/{analysis_id}")
async def get_history_item(analysis_id: str, request: Request):
    store = request.app.state.history_store
    if not store.enabled:
        raise HTTPException(status_code=404, detail="History is disabled (ENABLE_HISTORY=false).")
    doc = await store.get(analysis_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    doc["_id"] = str(doc["_id"])
    return doc
