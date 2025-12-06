import os
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# Use Argon2 instead of bcrypt
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    # truncate to 72 bytes max (keeps same behavior as before)
    trimmed = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.hash(trimmed)

def verify_password(password: str, hashed: str) -> bool:
    trimmed = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.verify(trimmed, hashed)

def create_access_token(subject: str, expires_delta: timedelta = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": str(subject), "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
