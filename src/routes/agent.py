import uuid

import aiohttp
from fastapi import APIRouter, Depends, HTTPException
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.rag_sql import NotesAppDeps, notes_agent
from src.config import settings
from src.db.models.chat import Chat
from src.db.models.chat_messages import ChatMessage
from src.db.session import get_db
from src.dependencies import get_current_user
from src.schemas.agent import ChatRequest, ChatResponse

router = APIRouter(tags=["agents"])


@router.post("/agent/chat/{chat_id}")
async def chat_with_agent(
    request: ChatRequest,
    chat_id: int,
    user_id: uuid.UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    await db.execute(text("SET ROLE authenticated"))
    await db.execute(
        text("SELECT set_config('request.jwt.claim.sub', :user_id, true)"),
        {"user_id": str(user_id)},
    )

    # Get existing chat
    chat = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = chat.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages_query = await db.execute(
        select(ChatMessage.message)
        .where(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at)
    )

    messages: list[ModelMessage] = []

    for message in messages_query.scalars().all():
        messages.extend(ModelMessagesTypeAdapter.validate_json(str(message)))

    async with aiohttp.ClientSession() as session:
        result = await notes_agent.run(
            request.query,
            message_history=messages,
            deps=NotesAppDeps(db=db, env_vars=settings, http_session=session),
        )

    # Decode bytes to string if necessary and create chat message
    chat_message = ChatMessage(
        chat_id=chat_id,
        user_id=user_id,
        message=result.new_messages_json().decode("utf-8"),
    )

    db.add(chat_message)
    await db.commit()

    return ChatResponse(response=result.data)
