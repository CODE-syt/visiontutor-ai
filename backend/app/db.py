"""
Optional MongoDB connection for analysis history.

Only used when ENABLE_HISTORY=true. Uploaded images are never stored here
by design -- only metadata (concept, confidence, generated explanation,
timestamp) -- per the "do not permanently store uploaded images" requirement.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.config import Settings

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except ImportError:  # pragma: no cover
    AsyncIOMotorClient = None


class HistoryStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None
        self._collection = None
        if settings.enable_history and AsyncIOMotorClient is not None:
            self._client = AsyncIOMotorClient(settings.mongodb_uri)
            self._collection = self._client[settings.mongodb_db]["analyses"]

    @property
    def enabled(self) -> bool:
        return self._collection is not None

    async def save(self, concept: str, confidence: float, result: dict[str, Any]) -> Optional[str]:
        if not self.enabled:
            return None
        doc = {
            "concept": concept,
            "confidence": confidence,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        inserted = await self._collection.insert_one(doc)
        return str(inserted.inserted_id)

    async def list_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        cursor = self._collection.find().sort("timestamp", -1).limit(limit)
        items = []
        async for doc in cursor:
            items.append(
                {
                    "id": str(doc["_id"]),
                    "concept": doc.get("concept", "Unknown"),
                    "confidence": doc.get("confidence", 0.0),
                    "timestamp": doc.get("timestamp", ""),
                }
            )
        return items

    async def get(self, analysis_id: str) -> Optional[dict[str, Any]]:
        if not self.enabled:
            return None
        from bson import ObjectId  # local import: only needed when history enabled

        doc = await self._collection.find_one({"_id": ObjectId(analysis_id)})
        return doc
