from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import agent, notes

# Create the FastAPI app with the database lifecycle context
app = FastAPI(
    title="Notes AI Agent API",
    contact={
        "name": "Notes AI Agent API",
        "url": "https://github.com/aloiscrr/notes-ai-agent-api",
    },
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(notes.router)
app.include_router(agent.router)
