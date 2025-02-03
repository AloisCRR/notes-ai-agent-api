import uuid

import jwt
from fastapi import HTTPException, Request, status

from app.config import settings


async def get_current_user(request: Request) -> uuid.UUID:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )
    try:
        # Expect header format: "Bearer <token>"
        token_type, token = auth_header.split(" ")
        if token_type.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication type",
            )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
        ) from exc

    try:
        # Decode using the Supabase JWT secret. Adjust algorithm as needed.
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token",
            )
        # Convert the string to a UUID object
        user_id = uuid.UUID(user_id_str)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from e

    return user_id
