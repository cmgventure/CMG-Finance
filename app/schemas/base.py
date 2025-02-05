from pydantic import BaseModel, ConfigDict


class Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
