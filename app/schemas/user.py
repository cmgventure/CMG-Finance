from app.schemas.base import Base, BaseRequest
from app.schemas.subscription import Subscription


class User(Base):
    id: str
    email: str
    subscription: Subscription | None = None
    superuser: bool = False
    password_hash: str | None = None


class UserSignInRequest(BaseRequest):
    email: str
    password: str
