from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from src.config import SETTINGS
from src.database.repository import UserRepository
from src.database.models import User
from fastapi import HTTPException, WebSocketException, status
from fastapi.responses import JSONResponse

ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)

def authenticate_user(email: str, password: str) -> str:
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
    access_token = create_access_token(data={"user_id": user.id.hex}, expires_delta=access_token_expires)
    return access_token

def validate_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SETTINGS.secret_key, algorithms=[SETTINGS.algorithm])
        return payload["user_id"]
    except InvalidTokenError:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
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
        content={"success": True, "token": token, "user_id": str(user.id)}
    )