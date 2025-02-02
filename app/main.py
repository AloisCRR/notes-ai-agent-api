import google.generativeai as genai
from fastapi import FastAPI

from app.config import settings
from app.db import lifespan_context
from app.routes.notes import router as notes_router

# Configure the generative AI API key using the middleware settings
genai.configure(api_key=settings.gemini_api_key)

# Create the FastAPI app with the database lifecycle context
app = FastAPI(lifespan=lifespan_context)

# Include the notes routes
app.include_router(notes_router)
