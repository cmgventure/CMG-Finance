from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Sequence, Type, TypeVar

from loguru import logger
from pydantic import BaseModel
from sqlalchemy import Column, ColumnClause, Executable, Result, Select, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import QueryableAttribute, joinedload

from app.enums.base import OrderDirection
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


action_map = {
    "gt": "__gt__",
    "lt": "__lt__",
    "ge": "__ge__",
    "le": "__le__",
    "in": "in_",
    "ilike": "ilike",
    "contains": "contains",
    "eq": "__eq__",
    "ne": "__ne__",
}


class AbstractRepository(ABC, Generic[ModelType]):
    @abstractmethod
    async def get_one(self, **filters: Any) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    async def get_multi(self, offset: int, limit: int | None = None, **filters: Any) -> Sequence[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, obj_in: BaseModel | dict[str, Any]) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self, obj_in: BaseModel | dict[str, Any], *, return_object: bool = False, **filters: Any
    ) -> int | ModelType:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, return_object: bool = False, **filters: Any) -> int | ModelType:
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository, Generic[ModelType]):
    model: Type[ModelType]
    join_load_list: list[QueryableAttribute] = []

    def __init__(self, session: AsyncSession):
        self.session = session
        self.model_name = self.model.__name__

    async def execute(self, statement: Executable, action: Callable[[Any], Any] | None = None) -> Any:
        """
        Execute statement

        Args:
            statement: statement
            action: action

        Returns:
            Result of the statement

        """
        result: Result = await self.session.execute(statement)
        if action:
            result = action(result)
        return result

    async def get_one(
        self, order_by: str | None = None, order_direction: OrderDirection = OrderDirection.DESC, **filters: Any
    ) -> ModelType:
        """
        Get one object

        Args:
            order_by: order by
            order_direction: order direction

        Kwargs:
            filters: filters

        Returns:
            Object
        """

        statement = select(self.model).where(*self.get_where_clauses(filters))
        if order_by:
            statement = self.add_order_clause(statement, order_by, order_direction)

        statement = self.add_loading_options(statement)
        return await self.execute(statement=statement, action=lambda result: result.unique().scalars().one())

    async def get_one_or_none(
        self, order_by: str | None = None, order_direction: OrderDirection = OrderDirection.DESC, **filters: Any
    ) -> ModelType | None:
        """
        Get one object or None

        Args:
            order_by: order by
            order_direction: order direction

        Kwargs:
            filters: filters

        Returns:
            Object or None
        """

        statement = select(self.model).where(*self.get_where_clauses(filters))
        if order_by:
            statement = self.add_order_clause(statement, order_by, order_direction)

        statement = self.add_loading_options(statement)
        return await self.execute(statement=statement, action=lambda result: result.unique().scalars().one_or_none())

    async def get_multi(
        self,
        offset: int = 0,
        limit: int | None = None,
        order_by: str | None = None,
        order_direction: OrderDirection = OrderDirection.DESC,
        **filters: Any,
    ) -> Sequence[ModelType]:
        """
        Get multiple objects

        Args:
            offset: offset
            limit: limit
            order_by: order by
            order_direction: order direction

        Kwargs:
            filters: filters

        Returns:
            List of objects
        """

        statement = select(self.model).where(*self.get_where_clauses(filters))
        if order_by:
            statement = self.add_order_clause(statement, order_by, order_direction)

        statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)

        statement = self.add_loading_options(statement)
        return await self.execute(statement=statement, action=lambda result: result.unique().scalars().all())

    def get_where_clauses(self, filters: dict[str, Any]) -> list[ColumnClause]:
        """
        Get where clauses for statement

        Args:
            filters: dict with filters

        Raises:
            ValueError: if operator is not supported
            ValueError: if column is not found

        Returns:
            list of where clauses
        """
        clauses: list[ColumnClause] = []

        for key, value in filters.items():
            if "__" not in key:
                key = f"{key}__eq"

            column_name, action_name = key.split("__")

            column: Column = getattr(self.model, column_name, None)
            if column is None:
                raise ValueError(f"Invalid column {column_name} for {self.model_name}")

            action: str | None = action_map.get(action_name, None)
            if action is None:
                raise ValueError(
                    f"Unsupported action: {action_name}, supported actions: {', '.join(action_map.keys())}"
                )

            clause: ColumnClause = getattr(column, action)(value)
            clauses.append(clause)

        return clauses

    def add_order_clause(
        self, statement: Select, order_by: str, order_direction: OrderDirection = OrderDirection.DESC
    ) -> Select:
        """
        Add order clause to statement

        Args:
            statement: statement
            order_by: order by
            order_direction: order direction

        Returns:
            statement
        """
        field = getattr(self.model, order_by, None)
        order_clause = getattr(field, order_direction, None)
        if order_clause:
            statement = statement.order_by(order_clause())

        return statement

    async def create(self, obj_in: BaseModel | dict[str, Any]) -> ModelType:
        """
        Create object

        Args:
            obj_in: object to create

        Returns:
            Created object
        """
        logger.debug(f"Creating {self.model_name}")

        data = obj_in.model_dump() if isinstance(obj_in, BaseModel) else obj_in
        statement = insert(self.model).values(**data).returning(self.model)

        statement = self.add_loading_options(statement)
        return await self.execute(statement=statement, action=lambda result: result.unique().scalar_one())

    async def create_many(self, obj_in: list[dict[str, Any]]) -> None:
        """
        Create objects

        Args:
            obj_in: objects to create
        """
        logger.debug(f"Creating {self.model_name}")

        for i in range(0, len(obj_in), 5000):
            values = obj_in[i : i + 5000]
            statement = insert(self.model).values(values).on_conflict_do_nothing()
            statement = self.add_loading_options(statement)
            return await self.execute(statement=statement)

    async def update(
        self, obj_in: BaseModel | dict[str, Any], *, return_object: bool = False, **filters: Any
    ) -> int | ModelType:
        """
        Update object

        Args:
            obj_in: object to update
            return_object: return updated object

        Kwargs:
            filters: filters

        Returns:
            Number of updated objects or object itself
        """
        logger.debug(f"Updating {self.model_name} with {filters=}")

        obj_in = obj_in.model_dump() if isinstance(obj_in, BaseModel) else obj_in
        statement = update(self.model).where(*self.get_where_clauses(filters)).values(**obj_in)

        if return_object:
            statement = statement.returning(self.model)
            return await self.execute(statement=statement, action=lambda result: result.scalars().one())

        return await self.execute(statement=statement, action=lambda result: result.rowcount)

    async def delete(self, return_object: bool = False, **filters: Any) -> int | ModelType:
        """
        Delete object

        Args:
            return_object: return deleted object

        Kwargs:
            filters: filters

        Returns:
            Number of deleted objects or object itself
        """
        logger.debug(f"Deleting {self.model_name} with {filters=}")

        statement = delete(self.model).where(*self.get_where_clauses(filters))

        if return_object:
            statement = statement.returning(self.model)  # type:ignore
            return await self.execute(statement=statement, action=lambda result: result.scalars().one())

        return await self.execute(statement=statement, action=lambda result: result.rowcount)

    async def get_count(self, **filters: Any) -> int:
        """
        Get count of objects

        Kwargs:
            filters: Filters

        Returns:
            Count of objects
        """

        statement = select(func.count(self.model.id)).where(*self.get_where_clauses(filters))

        return await self.execute(statement, action=lambda result: result.scalar())

    def add_loading_options(self, statement: Executable) -> Executable:
        for join_load in self.join_load_list:
            statement = statement.options(joinedload(join_load))
        return statement
