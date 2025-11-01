from pydantic import EmailStr
from .base import BaseSchema, TimestampSchema


class UserBase(BaseSchema):
    username: str
    email: EmailStr
    fullname: str


class UserCreate(UserBase):
    pass


class UserUpdate(BaseSchema):
    username: str | None = None
    email: EmailStr | None = None
    fullname: str | None = None


class UserResponse(UserBase, TimestampSchema):
    pass
