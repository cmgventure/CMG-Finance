from enum import StrEnum


class BaseStrEnum(StrEnum):
    @classmethod
    def list(cls) -> list["BaseStrEnum"]:
        return list(cls.__members__.values())


class RequestMethod(BaseStrEnum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"
