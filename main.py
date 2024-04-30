from contextlib import asynccontextmanager
from datetime import datetime, timedelta, UTC
from typing import Annotated
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy import select
import jwt

from database.models import create_tables, delete_tables, User, async_session
from users_script import load_users
from schemas import UserLoginSchema, LoginTokenSchema, SalarySchema
from config import SECRET


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    print(load_users('user_data.csv'))
    yield
    await delete_tables()


app = FastAPI(title="salaries", lifespan=lifespan)


TOKEN_EXP_MIN = 30
API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)


async def get_user(username: str):
    async with async_session() as session:
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalars().first()


@app.post('/login', response_model=LoginTokenSchema, status_code=200)
async def login_user(data: UserLoginSchema):
    user = await get_user(data.username)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
            )
    if data.password != user.password:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
            )
    token = jwt.encode(
        {'id': user.id, 'exp': datetime.now(UTC) + timedelta(minutes=30)},
        SECRET,
        algorithm='HS256'
        )
    return {'token': token}


async def verify_token(authorization: str = Security(api_key_header)):
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme. Bearer token required."
                )

        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        if datetime.now(UTC) > datetime.fromtimestamp(payload['exp'], UTC):
            raise HTTPException(
                status_code=401, detail='Expired token. Please log in again'
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401, detail="Invalid token"
            )


@app.get('/salary', response_model=SalarySchema)
async def get_salary(payload: Annotated[dict, Depends(verify_token)]):
    async with async_session() as session:
        user_stmt = select(
            User.username, User.salary, User.promotion_date
            ).where(User.id == payload['id'])
        user_result = await session.execute(user_stmt)
        user_data = user_result.first()
        if user_data:
            username = user_data[0]
            salary = user_data[1]
            promotion_date = user_data[2].strftime(
                '%d.%m.%Y'
                ) if user_data[2] else None
            return {
                'username': username,
                'salary': salary,
                'promotion_date': promotion_date
                }
        else:
            raise HTTPException(404, 'User not found.')
