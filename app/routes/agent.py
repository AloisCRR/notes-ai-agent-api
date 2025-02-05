import uuid

import aiohttp
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.agent import ChatRequest, ChatResponse

router = APIRouter(tags=["notes"])


@router.post("/agent/chat")
async def chat_with_agent(
    request: ChatRequest,
    user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    from app.agents.rag_sql import NotesAppDeps, notes_agent

    await db.execute(text("SET ROLE authenticated"))

    await db.execute(
        text("SELECT set_config('request.jwt.claim.sub', :user_id, true)"),
        {"user_id": str(user_id)},
    )

    async with aiohttp.ClientSession() as session:
        result = await notes_agent.run(
            request.query,
            deps=NotesAppDeps(db=db, env_vars=settings, http_session=session),
        )

    return ChatResponse(response=result.data)
