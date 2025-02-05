from datetime import datetime

from pydantic import BaseModel

from app.enums.subscription import FulfillmentStatus, SubscriptionType


class Subscription(BaseModel):
    id: str
    user_id: str
    transaction_id: str
    type: SubscriptionType
    status: FulfillmentStatus
    created_at: datetime
    expired_at: datetime
