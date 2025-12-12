from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from src.config import SETTINGS
from src.database.repository import UserRepository
from src.database.models import User
from fastapi import HTTPException, WebSocketException, status
from fastapi.responses import JSONResponse
import uuid
from uuid import UUID
from src.session_manager import SessionManager
from src.agents.calendar_agent import register_agent

ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
session_manager = SessionManager()

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)

async def authenticate_user(email: str, password: str) -> str:
    users = UserRepository()
    # Fetch User data from database
    user = users.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=400, detail="User does not exist")
    
    hashed_password = user.password
    if not verify_password(password, hashed_password):
        raise HTTPException(status_code=400, detail="Wrong Password")
    # Create token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(user, expires_delta=access_token_expires)
    return access_token

def validate_token(token: str):
    try:
        payload = jwt.decode(token, SETTINGS.secret_key, algorithms=[SETTINGS.algorithm])
        print(payload)
        return payload["user_id"], payload["session_id"]
    except InvalidTokenError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

async def create_access_token(user: User, expires_delta: timedelta | None = None):
    to_encode = {"user_id": user.id.hex}
    # Create session
    session_id = await session_manager.create(user.id)
    # Register Agent
    await register_agent(user, session_id)

    to_encode.update({"session_id": session_id})
    print(f"Session ID: {session_id}")
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SETTINGS.secret_key, algorithm=SETTINGS.algorithm)
    return encoded_jwt

def create_new_user(user: User):
    hashed_passoword = get_password_hash(user.password)
    user.password = hashed_passoword

    # Add user to database
    users = UserRepository()
    users.create(user)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True, "user_id": str(user.id)}
    )