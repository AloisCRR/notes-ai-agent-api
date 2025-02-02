import uuid

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException

from app.db import db_pool
from app.dependencies import get_current_user
from app.schemas.note import NoteCreate

router = APIRouter()


@router.post("/notes")
async def create_note(note: NoteCreate, user_id: uuid.UUID = Depends(get_current_user)):
    if db_pool is None:
        raise HTTPException(
            status_code=500, detail="Database connection not initialized"
        )

    # Generate embedding using the generative AI service
    result = genai.embed_content(
        model="models/text-embedding-004", content=note.content
    )
    embedding = result.get("embedding")
    if embedding is None:
        raise HTTPException(status_code=500, detail="Failed to generate embedding")

    # Insert the note into the database, including the associated user_id and embedding.
    query = """
        INSERT INTO public.notes (user_id, content, embedding)
        VALUES ($1, $2, $3)
        RETURNING id
    """
    try:
        async with db_pool.acquire() as connection:
            record = await connection.fetchrow(query, user_id, note.content, embedding)
            note_id = record["id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database insertion failed") from e

    return {"id": note_id, "user_id": str(user_id)}
