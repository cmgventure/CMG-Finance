from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.schemas.subscription import FulfillmentStatus, SubscriptionType


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String, primary_key=True)
    transaction_id = Column(String)
    type = Column(Enum(SubscriptionType))
    status = Column(Enum(FulfillmentStatus))
    created_at = Column(DateTime, default=datetime.utcnow)
    expired_at = Column(DateTime)

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)

    user = relationship("User", back_populates="subscriptions")
