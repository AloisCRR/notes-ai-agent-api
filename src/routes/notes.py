import uuid

import aiohttp
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.types import EmbeddingResponse
from src.config import settings
from src.db.models.note import Note
from src.db.session import get_db
from src.dependencies import get_current_user
from src.schemas.note import NoteCreate, NoteCreateResponse

router = APIRouter(tags=["notes"])


@router.post("/notes")
async def create_note(
    note: NoteCreate,
    user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NoteCreateResponse:
    # Generate embedding using the Gemini API
    api_key = settings.notes_ai_agent_gemini_api_key

    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"

    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": note.content}]},
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            json=payload,
        ) as response:
            response.raise_for_status()

            result = await response.json()

            embedding: EmbeddingResponse = result.get("embedding")

    if not embedding.get("values"):
        raise HTTPException(status_code=500, detail="Failed to generate embedding")

    db_note = Note(
        user_id=user_id,
        content=note.content,
        embedding=embedding.get("values"),
    )

    db.add(db_note)

    await db.commit()
    await db.refresh(db_note)

    return NoteCreateResponse(id=db_note.id)
