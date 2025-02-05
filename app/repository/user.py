from app.models.user import User
from app.repository.base import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository[User]):
    model = User
