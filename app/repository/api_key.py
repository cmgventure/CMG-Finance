from app.models.api_key import ApiKey
from app.repository.base import SQLAlchemyRepository


class ApiKeyRepository(SQLAlchemyRepository[ApiKey]):
    model = ApiKey
    join_load_list = [ApiKey.user]
