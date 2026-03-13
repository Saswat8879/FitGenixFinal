"""RAG-powered health chatbot: sentence-transformers + FAISS + Gemini 1.5 Flash."""
import logging
import os
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.models.chat import ChatHistory

logger = logging.getLogger(__name__)

# Lazy-loaded globals
_embedder = None
_index = None
_chunks: list[str] = []
_initialized = False

GUARDRAIL_TOPICS = {"medical diagnosis", "prescription", "drug dosage", "self-harm", "suicide"}


def _initialize():
    """Load knowledge base, build FAISS index on first call."""
    global _embedder, _index, _chunks, _initialized
    if _initialized:
        return

    try:
        from sentence_transformers import SentenceTransformer
        import faiss

        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Loaded sentence-transformers embedding model")

        # Load knowledge base text files
        kb_dir = settings.knowledge_base_dir
        _chunks = []
        if kb_dir.exists():
            for txt_file in sorted(kb_dir.glob("*.txt")):
                text = txt_file.read_text(encoding="utf-8")
                # Split into ~300 char chunks at paragraph boundaries
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                for para in paragraphs:
                    if len(para) > 500:
                        # Split long paragraphs
                        words = para.split()
                        for i in range(0, len(words), 60):
                            chunk = " ".join(words[i:i + 60])
                            if chunk:
                                _chunks.append(chunk)
                    else:
                        _chunks.append(para)

        if _chunks:
            embeddings = _embedder.encode(_chunks, show_progress_bar=False, convert_to_numpy=True)
            dim = embeddings.shape[1]
            _index = faiss.IndexFlatIP(dim)
            faiss.normalize_L2(embeddings)
            _index.add(embeddings)
            logger.info(f"FAISS index built: {len(_chunks)} chunks, dim={dim}")
        else:
            logger.warning("No knowledge base chunks found")

        _initialized = True

    except Exception as e:
        logger.error(f"Chat service initialization failed: {e}")
        _initialized = True  # Don't retry on every request


def _retrieve(query: str, top_k: int = 3) -> list[str]:
    """Retrieve top-k relevant chunks from FAISS index."""
    if not _index or not _embedder or not _chunks:
        return []

    import faiss

    q_emb = _embedder.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(q_emb)
    scores, indices = _index.search(q_emb, min(top_k, len(_chunks)))

    results = []
    for i, idx in enumerate(indices[0]):
        if idx >= 0 and scores[0][i] > 0.25:
            results.append(_chunks[idx])
    return results


def _check_guardrails(query: str) -> str | None:
    """Return a disclaimer if query is off-topic or dangerous."""
    query_lower = query.lower()
    for topic in GUARDRAIL_TOPICS:
        if topic in query_lower:
            return (
                "I'm a wellness assistant and cannot provide medical diagnoses, prescriptions, "
                "or advice about drug dosages. Please consult a qualified healthcare professional."
            )
    return None


def _build_system_prompt(user: User) -> str:
    """Create a system prompt personalized to the user."""
    profile = user.profile
    parts = [
        "You are FitGenix AI, a friendly health and wellness assistant.",
        "You give evidence-based advice about fitness, nutrition, sleep, stress management, and lifestyle.",
        "Keep answers concise (2-4 paragraphs max). Use bullet points when listing recommendations.",
        "Never diagnose diseases or prescribe medication. Always suggest consulting a doctor for medical concerns.",
    ]
    if profile:
        parts.append(f"The user is {profile.age or 'unknown age'} years old, "
                     f"goal: {profile.goal.value if profile.goal else 'general fitness'}, "
                     f"diet: {profile.diet_type.value if profile.diet_type else 'no preference'}.")
    if user.conditions:
        conds = []
        for attr in ["type_2_diabetes", "pre_diabetes", "hypertension", "high_cholesterol",
                      "obesity", "asthma_copd", "back_pain", "knee_pain", "shoulder_pain"]:
            if getattr(user.conditions, attr, False):
                conds.append(attr.replace("_", " "))
        if conds:
            parts.append(f"Known conditions: {', '.join(conds)}. Be mindful of these in your advice.")
    return "\n".join(parts)


async def chat(user: User, query: str, db: Session) -> dict:
    """Process a chat query through RAG pipeline and return response."""
    _initialize()

    # Guardrails
    disclaimer = _check_guardrails(query)
    if disclaimer:
        _save_history(user.id, query, disclaimer, [], db)
        return {"response": disclaimer, "context_used": []}

    # Retrieve relevant context
    context_chunks = _retrieve(query)
    context_text = "\n---\n".join(context_chunks) if context_chunks else ""

    # Build prompt for Gemini
    system_prompt = _build_system_prompt(user)

    user_message = query
    if context_text:
        user_message = (
            f"Context from knowledge base:\n{context_text}\n\n"
            f"User question: {query}\n\n"
            "Use the context above if relevant to answer the question accurately."
        )

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            [
                {"role": "user", "parts": [{"text": system_prompt}]},
                {"role": "model", "parts": [{"text": "Understood. I'll follow these guidelines."}]},
                {"role": "user", "parts": [{"text": user_message}]},
            ]
        )
        reply = response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        reply = _fallback_response(query, context_chunks)

    _save_history(user.id, query, reply, context_chunks, db)
    return {"response": reply, "context_used": context_chunks}


def _fallback_response(query: str, context: list[str]) -> str:
    """Provide a basic response when Gemini is unavailable."""
    if context:
        return (
            "I'm having trouble connecting to my AI backend, but here's what I found "
            "in the knowledge base:\n\n" + "\n\n".join(context[:2])
        )
    return (
        "I'm currently unable to process your request. Please try again in a moment, "
        "or check the app's health tips section for general guidance."
    )


def _save_history(user_id: int, query: str, response: str, context: list[str], db: Session):
    """Save user query and bot response to chat history."""
    db.add(ChatHistory(user_id=user_id, role="user", message=query, timestamp=datetime.now(timezone.utc)))
    db.add(ChatHistory(user_id=user_id, role="assistant", message=response,
                       retrieved_context=context, timestamp=datetime.now(timezone.utc)))
    db.commit()


def get_chat_history(user_id: int, db: Session, limit: int = 50) -> list[dict]:
    """Return recent chat messages for a user."""
    msgs = db.query(ChatHistory).filter(
        ChatHistory.user_id == user_id
    ).order_by(ChatHistory.timestamp.desc()).limit(limit).all()

    return [
        {"id": m.id, "role": m.role, "message": m.message, "timestamp": m.timestamp.isoformat()}
        for m in reversed(msgs)
    ]
