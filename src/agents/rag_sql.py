import re
from dataclasses import dataclass
from datetime import datetime

from aiohttp import ClientSession
from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.format_as_xml import format_as_xml
from pydantic_ai.models.openai import OpenAIModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.types import EmbeddingResponse
from src.config import Settings, settings
from src.db.models.note import Note


def is_valid_select_query(sql: str) -> bool:
    sql = sql.strip()

    if not sql:
        return False

    # Split into parts by semicolon and check each non-empty part
    parts = [p.strip() for p in sql.split(";") if p.strip()]
    for part in parts:
        # Check if the part starts with SELECT (case-insensitive)
        if not re.match(r"^\s*SELECT\s", part, re.IGNORECASE):
            return False

        # Check for forbidden commands (case-insensitive)
        forbidden_commands = (
            r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE)\b"
        )
        if re.search(forbidden_commands, part, re.IGNORECASE):
            return False

    return True


DB_SCHEMA = """
create table notes (
  id bigint generated always as identity not null,
  content text not null,
  embedding extensions.vector null,
  created_at timestamp with time zone not null default (now() AT TIME ZONE 'utc'::text),
  updated_at timestamp with time zone not null default (now() AT TIME ZONE 'utc'::text),
  constraint notes_pkey primary key (id),
) TABLESPACE pg_default;
"""

SQL_EXAMPLES = [
    {
        "request": "Give me a resume of what I did last week",
        "response": "SELECT * FROM notes WHERE created_at >= '2024-01-01' AND created_at <= '2024-01-31'",
    },
    {
        "request": "Give me a resume of my week so far",
        "response": "SELECT * FROM notes WHERE created_at >= '2024-01-01' AND created_at <= '2024-01-31'",
    },
    {
        "request": "What did I wrote on sunday?",
        "response": "SELECT * FROM notes WHERE created_at::date = '2024-01-01'",
    },
    {
        "request": "Give me a resume of my notes today",
        "response": "SELECT * FROM notes WHERE created_at::date = '2024-01-01'",
    },
]


@dataclass
class NotesAppDeps:
    db: AsyncSession
    http_session: ClientSession
    env_vars: Settings


class SearchResult(BaseModel):
    content: str
    created_at: str
    updated_at: str


model = OpenAIModel("gpt-4o-mini", api_key=settings.notes_ai_agent_openai_api_key)


notes_agent = Agent(
    model=model,
    deps_type=NotesAppDeps,
    system_prompt="""
You are a helpful assistant for a notes app.
You can search notes using semantic search or query note metadata using SQL. You're a read-only assistant, so you can't help the user with operations that will modify the database.
Don't return responses in markdown format. Use plain text with line breaks if needed.

- If the user asks a question that requires searching the content of notes, use the `search_notes` tool.
    - Example: "Do I have a note about the meeting with John?"
    - Example: "What are the fruits that I usually buy?"

- If the user asks a question about note metadata (like dates), generate an SQL query and use the `query_notes_metadata` tool.
    - Example: "Give me a resume of what I did last week"

- If the user asks a question that requires both searching the content and metadata, use both tools and combine the results.

- Before generating SQL queries, make sure to check the database schema using the `get_database_schema` tool.
    """,
    retries=2,
)


@notes_agent.system_prompt
def add_db_schema() -> str:
    return f"""
Here is the database schema (PostgreSQL):
{DB_SCHEMA}

Today is {datetime.now().strftime("%A (%d) of %B (%m), %Y")}.

Here are some examples of how to query the database:
{format_as_xml(SQL_EXAMPLES)}
"""


@notes_agent.tool
async def search_notes_rag(ctx: RunContext[NotesAppDeps], query: str) -> str:
    """Searches notes using semantic search (RAG) based on the query.

    Args:
        ctx: The call context.
        query: Natural language query to search for.
    """
    api_key = ctx.deps.env_vars.notes_ai_agent_gemini_api_key

    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"

    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": query}]},
    }

    async with ctx.deps.http_session.post(
        url,
        json=payload,
    ) as response:
        response.raise_for_status()

        result = await response.json()

        embedding: EmbeddingResponse = result.get("embedding")

        if not embedding.get("values"):
            raise ValueError("Failed to generate embedding")

        embedding_values = embedding.get("values")

        if not embedding_values:
            raise ValueError("Failed to generate embedding")

    result = await ctx.deps.db.execute(
        select(Note)
        .filter(Note.embedding.cosine_distance(embedding_values) < 0.5)
        .order_by(Note.embedding.cosine_distance(embedding_values))
        .limit(5)
    )

    notes = result.scalars().all()

    return "\n\n".join(
        [
            f"Content: {note.content}\nCreated at: {note.created_at.strftime('%Y-%m-%d')}\n"
            for note in notes
        ]
    )


@notes_agent.tool
async def query_notes_metadata(ctx: RunContext[NotesAppDeps], query: str) -> str:
    """Queries note metadata using SQL based on the query.

    Args:
        ctx: The call context.
        query: SQL query code to search for.
    """
    if not is_valid_select_query(query):
        raise ModelRetry("Invalid SELECT SQL query")

    try:
        # Execute the query directly without mapping to Note objects
        result = await ctx.deps.db.execute(text(query))
        rows = result.all()

        if not rows:
            return "No notes found."

        return format_as_xml(str(rows))

    except Exception as e:
        raise ModelRetry(f"Failed to query notes metadata: {e}") from e
