"""Router API Chatbot Semantik & External Linked Data (DBpedia)."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.chatbot_service import process_chat_message
from app.services.dbpedia_service import get_dbpedia_info

router = APIRouter(prefix="/api")


class ChatMessage(BaseModel):
    text: str = Field(default="", strict=True, max_length=4000)
    role: str | None = None


class ChatPayload(BaseModel):
    messages: list[ChatMessage] | None = Field(default=None, max_length=100)
    text: str | None = Field(default=None, strict=True, max_length=4000)


@router.post("/chat")
async def chat_endpoint(payload: ChatPayload):
    user_text = payload.messages[-1].text if payload.messages else (payload.text or "")
    return {"text": await process_chat_message(user_text)}


@router.get("/external/city/{city_name}")
async def external_city_info(city_name: str):
    """Endpoint untuk mengambil informasi profil kota/kabupaten langsung dari DBpedia SPARQL."""
    info = await get_dbpedia_info(city_name)
    return info
