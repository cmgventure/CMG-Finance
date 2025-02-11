import uuid
from datetime import datetime

import aiohttp
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from loguru import logger
from starlette import status

from app.core.config import settings
from app.enums.subscription import FulfillmentStatus, ProductId, SubscriptionType
from app.utils.unitofwork import ABCUnitOfWork


class SquarespaceService:
    api_url = "https://api.squarespace.com/1.0"
    default_headers = {
        "Content-Type": "application/json",
        "User-Agent": "CMG-Finance",
        "Authorization": f"Bearer {settings.SQUARESPACE_API_KEY}",
    }

    async def _get(self, url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=self.default_headers) as response:
                return await response.json()

    @staticmethod
    def get_product(product_id: str, price: float) -> SubscriptionType:
        if product_id == ProductId.Free:
            return SubscriptionType.Free
        elif product_id == ProductId.Basic and price == 17:
            return SubscriptionType.Basic
        elif product_id == ProductId.Basic and price == 170:
            return SubscriptionType.AnnualBasic
        elif product_id == ProductId.Premium and price == 25:
            return SubscriptionType.Premium
        elif product_id == ProductId.Premium and price == 250:
            return SubscriptionType.AnnualPremium
        else:
            logger.error(f"Unknown product: {product_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unknown product",
            )

    async def get_profile(self, user_email: str) -> dict:
        url = f"{self.api_url}/profiles"

        params = {"filter": f"email,{user_email}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, headers=self.default_headers) as response:
                data = await response.json()
                return data["profiles"][0]

    async def get_order(self, order_id: str) -> dict:
        url = f"{self.api_url}/commerce/orders/{order_id}"
        return await self._get(url)

    async def get_orders(self) -> dict:
        url = f"{self.api_url}/commerce/orders"
        return await self._get(url)

    async def get_transaction(self, transaction_id: str) -> dict:
        url = f"{self.api_url}/commerce/transactions/{transaction_id}"
        return await self._get(url)

    async def get_order_transaction(self, order_id: str) -> dict | None:
        transactions = await self.get_transactions()
        for transaction in transactions.get("documents", []):
            if transaction["salesOrderId"] == order_id:
                return transaction

    async def get_transactions(self) -> dict:
        url = f"{self.api_url}/commerce/transactions"
        return await self._get(url)

    async def save_user(self, unit_of_work: ABCUnitOfWork, user_email: str) -> str:
        profile = await self.get_profile(user_email)
        if not profile:
            logger.error("User profile not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user = {"id": profile["id"], "email": profile["email"]}
        await unit_of_work.user.create(user)

        return profile["id"]

    async def save_subscription(
        self, unit_of_work: ABCUnitOfWork, user_id: str, order: dict, transaction: dict | None = None
    ) -> None:
        subscription_type = self.get_product(
            order["lineItems"][0]["productId"],
            float(order["lineItems"][0]["unitPricePaid"]["value"]),
        )
        fulfillment_status = FulfillmentStatus(order["fulfillmentStatus"])
        created_at = datetime.strptime(order["createdOn"], "%Y-%m-%dT%H:%M:%S.%fZ")
        if created_at.microsecond > 999:
            created_at = created_at.replace(microsecond=int(created_at.microsecond / 1000))

        if subscription_type is SubscriptionType.Free:
            timedelta = relativedelta(weeks=1)
        elif subscription_type in (SubscriptionType.Basic, SubscriptionType.Premium):
            timedelta = relativedelta(months=1)
        elif subscription_type in (
            SubscriptionType.AnnualBasic,
            SubscriptionType.AnnualPremium,
        ):
            timedelta = relativedelta(year=1)
        else:
            logger.error(f"Invalid subscription type: {subscription_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid subscription type",
            )

        transaction_id = transaction["payments"][0]["externalTransactionId"]

        subscription = {
            "id": order["id"],
            "type": subscription_type,
            "status": fulfillment_status,
            "user_id": user_id,
            "transaction_id": transaction_id,
            "created_at": created_at,
            "expired_at": created_at + timedelta,
        }
        await unit_of_work.subscription.create(subscription)

    async def update_subscription(self, unit_of_work: ABCUnitOfWork, order_data: dict) -> None:
        async with unit_of_work:
            order_id = order_data["data"]["orderId"]
            event_order = await self.get_order(order_id)
            profile = await self.get_profile(event_order["customerEmail"])

            transaction = await self.get_order_transaction(order_id)

            await self.save_subscription(unit_of_work, profile["id"], event_order, transaction)

    async def create_subscription(self, unit_of_work: ABCUnitOfWork, order_data: dict) -> None:
        async with unit_of_work:
            order_id = order_data["data"]["orderId"]
            event_order = await self.get_order(order_id)
            user_id = await self.save_user(unit_of_work, event_order["customerEmail"])

            subscription_type = self.get_product(
                event_order["lineItems"][0]["productId"],
                float(event_order["lineItems"][0]["unitPricePaid"]["value"]),
            )

            if subscription_type == SubscriptionType.Free:
                if await unit_of_work.subscription.get_one_or_none(
                    order_by="created_at", user_id=user_id, expired_at__gt=datetime.utcnow()
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Free trial already used",
                    )

                orders = await self.get_orders()
                for order in orders["result"]:
                    if (
                        order["customerEmail"] == event_order["customerEmail"]
                        and order["fulfillmentStatus"] == FulfillmentStatus.FULFILLED
                    ):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Free trial already used",
                        )

            if event_order["fulfillmentStatus"] != FulfillmentStatus.FULFILLED:
                await self.save_subscription(unit_of_work, user_id, event_order)
                await self.fulfill_order(order_id)
            else:
                transaction = await self.get_order_transaction(order_id)
                await self.save_subscription(unit_of_work, user_id, event_order, transaction)

    async def fulfill_order(self, order_id):
        url = f"{self.api_url}/commerce/orders/{order_id}/fulfillments"

        payload = {
            "shouldSendNotification": True,
            "shipments": [
                {
                    "shipDate": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "carrierName": "CMG",
                    "service": "CMG",
                    "trackingNumber": str(uuid.uuid4()),
                }
            ],
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, json=payload, headers=self.default_headers) as response:
                if response.status not in [200, 204]:
                    text = await response.text()
                    logger.info(text)
