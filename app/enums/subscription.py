from app.enums.base import BaseStrEnum


class FulfillmentStatus(BaseStrEnum):
    PENDING = "PENDING"
    CANCELED = "CANCELED"
    FULFILLED = "FULFILLED"
    EXPIRED = "EXPIRED"


class ProductId(BaseStrEnum):
    Free = "66b288c881b4155bf9e53c57"
    Basic = "073642cd-7456-4c26-8158-66a9b440ecda"
    Premium = "0fbcfeb2-b8bc-4211-8108-d87de08f24e0"


class SubscriptionType(BaseStrEnum):
    Free = "Free Trial"
    Basic = "Basic Subscription"
    Premium = "Premium Subscription"
    AnnualBasic = "Basic Subscription"
    AnnualPremium = "Premium Subscription"
