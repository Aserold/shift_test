from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
import jwt

from models import create_tables, delete_tables, User, async_session, engine
from users_script import load_users
from schemas import UserLoginSchema, LoginTokenSchema, SalarySchema
from config import SECRET


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables(engine)
    print(load_users('user_data.csv'))
    yield
    await delete_tables(engine)


app = FastAPI(title="salaries", lifespan=lifespan)


TOKEN_EXP_MIN = 30
api_key_header = HTTPBearer()


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
            detail="Incorrect username or password")
    if data.password != user.password:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password")
    token = jwt.encode(
        {'id': user.id,
         'exp': datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXP_MIN)},
        SECRET,
        algorithm='HS256'
        )
    return {'token': token}


async def verify_token(
        credentials: HTTPAuthorizationCredentials = Security(api_key_header)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET, algorithms=["HS256"],
                             options={'verify_exp': True})
        return payload

    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail=f"Invalid token. {e}")


@app.get('/salary', response_model=SalarySchema)
async def get_salary(payload: Annotated[dict, Depends(verify_token)]):
    async with async_session() as session:
        user_stmt = select(
            User.username,
            User.salary,
            User.promotion_date).where(User.id == payload['id'])

        user_result = await session.execute(user_stmt)
        user_data = user_result.first()
        if user_data:
            username = user_data[0]
            salary = user_data[1]
            promotion_date = user_data[2].strftime(
                '%d.%m.%Y') if user_data[2] else None
            return {
                'username': username,
                'salary': salary,
                'promotion_date': promotion_date
                }
        else:
            raise HTTPException(404, 'User not found.')
