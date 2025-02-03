import uuid
from typing import TypedDict

import aiohttp
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.note import notes
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.note import NoteCreate, NoteCreateResponse

router = APIRouter(tags=["notes"])


class EmbeddingResponse(TypedDict):
    values: list[float]


@router.post("/notes")
async def create_note(
    note: NoteCreate,
    user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NoteCreateResponse:
    # Generate embedding using the Gemini API
    api_key = settings.gemini_api_key

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

    query = (
        insert(notes)
        .values(
            user_id=user_id,
            content=note.content,
            embedding=embedding.get("values"),
        )
        .returning(notes.c.id)
    )

    result = await db.execute(query)
    await db.commit()

    note_id = result.scalar_one()
    return NoteCreateResponse(id=note_id)
