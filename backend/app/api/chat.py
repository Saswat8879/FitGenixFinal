"""AI Chatbot endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.chat import ChatQuery, ChatResponse, ChatMessageOut
from app.api.deps import get_current_user
from app.services.chat_service import chat, get_chat_history

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def send_message(body: ChatQuery, user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    result = await chat(user, body.message, db)
    return ChatResponse(
        response=result["response"],
        retrieved_sources=result.get("context_used", []),
    )


@router.get("/history", response_model=list[ChatMessageOut])
def history(limit: int = 50, user: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    msgs = get_chat_history(user.id, db, limit)
    return [ChatMessageOut(**m) for m in msgs]
