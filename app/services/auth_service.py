from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests
from google.oauth2 import id_token
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.core.config import settings
from app.core.connection import get_db
from app.database.database import Database
from app.schemas.schemas import User

token_auth_scheme = HTTPBearer()


async def verify_token(token: str) -> str:
    try:
        # Try verifying as a custom JWT token first
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_email
    except JWTError:
        # If the token is not a valid custom JWT, try verifying it as a Google token
        try:
            id_info = id_token.verify_oauth2_token(token, requests.Request())
            user_email = id_info.get("email")
            if not user_email:
                logger.error("Email not found in token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                )
            return user_email
        except ValueError:
            logger.error("Invalid token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(token_auth_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_email = await verify_token(token.credentials)

    database = Database(session=db)
    user = await database.get_user(user_email)
    if not user:
        logger.error(f"User not found with email: {user_email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    user_subscription = await database.get_subscription(user)
    if user_subscription:
        user_subscription = user_subscription.__dict__

    return User(
        id=user.id,
        email=user.email,
        subscription=user_subscription,
        superuser=user.superuser,
    )
