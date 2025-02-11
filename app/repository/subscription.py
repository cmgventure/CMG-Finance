from app.models.subscription import Subscription
from app.repository.base import SQLAlchemyRepository


class SubscriptionRepository(SQLAlchemyRepository[Subscription]):
    model = Subscription
    join_load_list = [Subscription.user]
