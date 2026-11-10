"""Router API Chatbot Semantik & External Linked Data (DBpedia)."""
from typing import Any
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.chatbot_service import process_chat_message
from app.services.dbpedia_service import get_dbpedia_info

router = APIRouter(prefix="/api")


class ChatPayload(BaseModel):
    messages: list[dict[str, Any]] | None = None
    text: str | None = None


@router.post("/chat")
async def chat_endpoint(request: Request, payload: ChatPayload | None = None):
    """Menerima pesan dari Deep-Chat widget dan mengembalikan respons cerdas."""
    user_text = ""
    if payload and payload.messages and len(payload.messages) > 0:
        last_msg = payload.messages[-1]
        user_text = last_msg.get("text", "")
    elif payload and payload.text:
        user_text = payload.text
    else:
        try:
            body = await request.json()
            if isinstance(body, dict):
                if "messages" in body and isinstance(body["messages"], list) and len(body["messages"]) > 0:
                    user_text = body["messages"][-1].get("text", "")
                elif "text" in body:
                    user_text = body.get("text", "")
        except Exception:
            pass

    bot_reply = await process_chat_message(user_text)
    return {"text": bot_reply}


@router.get("/external/city/{city_name}")
async def external_city_info(city_name: str):
    """Endpoint untuk mengambil informasi profil kota/kabupaten langsung dari DBpedia SPARQL."""
    info = await get_dbpedia_info(city_name)
    return info
