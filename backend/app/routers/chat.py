"""Router API Chatbot Semantik & External Linked Data (DBpedia)."""
from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.services.chatbot_service import process_chat_message
from app.services.dbpedia_service import get_dbpedia_info

router = APIRouter(prefix="/api")


class ChatMessage(BaseModel):
    text: str = Field(default="", strict=True, max_length=4000)
    role: str | None = None


class ChatPayload(BaseModel):
    messages: list[ChatMessage] | None = Field(default=None, max_length=100)
    text: str | None = Field(default=None, strict=True, max_length=4000)
    lat: float | None = None
    lon: float | None = None
    history: list[dict] | None = Field(default=None, max_length=50)
    state: dict | None = None
    location_status: str | None = None

    @field_validator("lat", mode="before")
    @classmethod
    def validate_lat(cls, v):
        if v is None:
            return None
        try:
            val = float(v)
            if -90.0 <= val <= 90.0:
                return val
        except (ValueError, TypeError):
            pass
        return None

    @field_validator("lon", mode="before")
    @classmethod
    def validate_lon(cls, v):
        if v is None:
            return None
        try:
            val = float(v)
            if -180.0 <= val <= 180.0:
                return val
        except (ValueError, TypeError):
            pass
        return None


@router.get("/chat/health")
async def chat_health():
    return {"status": "ok", "service": "chatbot"}


@router.post("/chat")
async def chat_endpoint(payload: ChatPayload):
    user_text = payload.messages[-1].text if payload.messages else (payload.text or "")
    history = payload.history
    if history is None and payload.messages and len(payload.messages) > 1:
        history = [
            {"role": m.role or "user", "text": m.text}
            for m in payload.messages[:-1]
        ]
    history = history or []
    result = await process_chat_message(
        user_text,
        lat=payload.lat,
        lon=payload.lon,
        history=history,
        state=payload.state,
        location_status=payload.location_status,
    )
    return result


@router.get("/external/city/{city_name}")
async def external_city_info(city_name: str):
    """Endpoint untuk mengambil informasi profil kota/kabupaten langsung dari DBpedia SPARQL."""
    info = await get_dbpedia_info(city_name)
    return info
