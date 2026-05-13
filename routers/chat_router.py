"""
Chat router for RAG-based conversational API.
Developed by: Developer B
This module handles chat-related endpoints including:
- Message sending and response generation
- Chat history retrieval
- Context-aware responses using ChromaDB and Gemini API
"""
import os
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from shared_utils import get_context

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Gemini setup ─────────────────────────────────────────────────────────────
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# ── In-memory session store  {session_id: [Message, ...]} ────────────────────
sessions: dict = {}

# ── Models ───────────────────────────────────────────────────────────────────
class Message(BaseModel):
    """Chat message model"""
    id: Optional[str] = None
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    session_id: Optional[str] = "default"
    temperature: Optional[float] = 0.7
    max_results: Optional[int] = 5

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    context_documents: List[str]
    session_id: str


# ── Helpers ───────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
Sen KOBİ işletmelerine yardımcı olan bir yapay zeka iş asistanısın.
Sipariş takibi, stok durumu ve genel iş sorularında yardımcı olursun.

Kurallar:
- Her zaman Türkçe cevap ver
- Net ve kısa cevaplar ver (max 4 cümle)
- Veritabanında olmayan bilgileri uydurma

Veritabanı bağlamı:
{context}

Sohbet geçmişi:
{history}
"""

def _format_history(messages: List[Message]) -> str:
    recent = messages[-10:]  # son 5 tur
    lines = []
    for m in recent:
        role = "Kullanıcı" if m.role == "user" else "Asistan"
        lines.append(f"{role}: {m.content}")
    return "\n".join(lines) if lines else "Henüz geçmiş yok."


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message and get RAG-based response.

    Args:
        request: ChatRequest containing user message and parameters

    Returns:
        ChatResponse with AI response and context documents
    """
    try:
        # 1. Validate input message
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")

        session_id = request.session_id or "default"

        # 2. Retrieve context from ChromaDB
        context_data = get_context(request.message, n_results=request.max_results)
        context_docs = context_data.get("documents", [])
        context_text = "\n".join([f"- {doc}" for doc in context_docs]) if context_docs else "İlgili kayıt bulunamadı."

        # 3. Build prompt with history
        history = sessions.get(session_id, [])
        history_text = _format_history(history)
        prompt = SYSTEM_PROMPT.format(context=context_text, history=history_text)
        full_prompt = f"{prompt}\n\nKullanıcı: {request.message}"

        # 4. Call Gemini API
        gemini_response = model.generate_content(full_prompt)
        reply = gemini_response.text.strip()

        # 5. Save to session history
        msg_id = datetime.now().isoformat()
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append(Message(id=msg_id, role="user", content=request.message))
        sessions[session_id].append(Message(id=msg_id + "_r", role="assistant", content=reply))

        logger.info(f"💬 Chat | session={session_id} | context={len(context_docs)} docs")

        return ChatResponse(
            response=reply,
            context_documents=context_docs,
            session_id=session_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 50):
    """
    Retrieve chat history for a session.

    Args:
        session_id: Unique session identifier
        limit: Maximum number of messages to retrieve

    Returns:
        List of Message objects
    """
    try:
        history = sessions.get(session_id, [])
        recent = history[-limit:]
        return {
            "session_id": session_id,
            "message_count": len(recent),
            "messages": recent
        }

    except Exception as e:
        logger.error(f"History retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear chat history for a session.

    Args:
        session_id: Unique session identifier

    Returns:
        Confirmation message
    """
    try:
        if session_id in sessions:
            del sessions[session_id]
        return {"success": True, "message": f"Session '{session_id}' temizlendi."}

    except Exception as e:
        logger.error(f"Session clear failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Integration hints for Developer B:
# 
# 1. Import in main.py:
#    from routers import chat_router
#    app.include_router(chat_router.router, prefix="/api/chat", tags=["Chat"])
#
# 2. Required functions from shared_utils:
#    - init_db(): Initialize database
#    - get_context(query): Retrieve relevant documents
#
# 3. Gemini API integration:
#    import google.generativeai as genai
#    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
#    model = genai.GenerativeModel('gemini-pro')
#    response = model.generate_content(prompt)
#
# 4. Session management options:
#    - Use Redis for distributed sessions
#    - Use in-memory dict with timestamp cleanup
#    - Use database for persistence

