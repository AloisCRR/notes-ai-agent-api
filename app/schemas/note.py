from pydantic import BaseModel


class NoteCreate(BaseModel):
    content: str


class NoteCreateResponse(BaseModel):
    id: int
