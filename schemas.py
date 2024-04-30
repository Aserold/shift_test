from decimal import Decimal
from pydantic import BaseModel


class UserLoginSchema(BaseModel):
    username: str
    password: str


class LoginTokenSchema(BaseModel):
    token: str


class SalarySchema(BaseModel):
    username: str
    salary: Decimal
    promotion_date: str
