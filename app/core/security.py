#To Hash Password ,Verify Password ,Create JWT ,Decode JWT

from datetime import datetime,timedelta,UTC
from jose import JWTError,jwt
from pwdlib import PasswordHash

from app.core.config import settings
from typing import Any

from datetime import datetime,UTC,timedelta

password_hash=PasswordHash.recommended() #PASSWORD HASHER

def hash_password(password:str)-> str:#HASHES PASSWORD
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:#VERIFY PASSWORD with EXISTING HASHED PASSWORD
    return password_hash.verify(password, hashed_password)

def create_access_token(data:dict[str,Any])->str:
    to_encode=data.copy()

    expire=datetime.now(UTC)+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp":expire})

    encoded_jwt=jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt

def decode_access_token(token:str)->dict:
    try:
        payload=jwt.decode(
            token,
            settings.SECRET_KEY
            ,
            algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        return{}

