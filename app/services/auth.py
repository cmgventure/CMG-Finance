from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests
from google.oauth2 import id_token
from jose import ExpiredSignatureError, JWTError, jwt
from loguru import logger
from passlib.context import CryptContext

from app.core.config import settings
from app.schemas.subscription import Subscription
from app.schemas.user import User, UserLoginRequest
from app.utils.unitofwork import ABCUnitOfWork, UnitOfWork

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
auth_scheme = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())]


class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    async def verify_token(token: str) -> str:
        try:
            # Try verifying as a custom JWT token first
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_email: str = payload.get("sub")
            if user_email is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            return user_email
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Token has expired",
            )
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

    @staticmethod
    def create_token(data: dict, expires_delta: timedelta | None = None) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)

        data.update({"exp": expire})

        encoded_jwt = jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @classmethod
    async def get_access_token(cls, unit_of_work: ABCUnitOfWork, credentials: UserLoginRequest) -> dict[str, str]:
        user = await unit_of_work.user.get_one_or_none(email=credentials.email)
        if not user or not cls.verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = cls.create_token(data={"sub": user.email}, expires_delta=access_token_expires)
        refresh_token = cls.create_token(data={"sub": user.email}, expires_delta=timedelta(days=7))

        return {"access_token": access_token, "refresh_token": refresh_token}

    @classmethod
    async def get_google_access_token(cls, user: User) -> str:
        return cls.create_token(data={"sub": user.email}, expires_delta=timedelta(days=7))

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> dict[str, str]:
        try:
            payload = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_email: str = payload.get("sub")
            if user_email is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = cls.create_token(data={"sub": user_email}, expires_delta=access_token_expires)
            return {"access_token": access_token}
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    @classmethod
    async def get_current_user(
        cls,
        token: auth_scheme,
    ) -> User:
        async with UnitOfWork() as unit_of_work:
            api_key = await unit_of_work.api_key.get_one_or_none(key=token.credentials)
            if not api_key:
                email = await cls.verify_token(token.credentials)
                user = await unit_of_work.user.get_one_or_none(email=email)
                if not user:
                    logger.error(f"User not found with email: {email}")
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            else:
                user = api_key.user

            user_subscription = await unit_of_work.subscription.get_one_or_none(
                order_by="created_at", user_id=user.id, expired_at__gt=datetime.utcnow()
            )
            if user_subscription:
                user_subscription = Subscription.model_validate(user_subscription.__dict__)

        if not user_subscription and not user.superuser:
            logger.error(f"Access Denied, user {user.email} is not a superuser")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")

        return User(
            id=user.id,
            email=user.email,
            subscription=user_subscription,
            superuser=user.superuser,
        )
