from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt
import logging


logging.basicConfig(level=logging.INFO, filename="py_log.log",filemode="w")
app = FastAPI()
secret_key = "l5h49PKyBb3GG0qIhay-Dk4zyL53FGuN8cn2Eax3NVo" # to_vault

# Здесь вы можете использовать фиктивные данные для пользователей.
# В реальном приложении данные пользователей следует хранить в базе данных.
fake_users_db = {
    "user@example.com": {
        "username": "user@example.com",
        "full_name": "User",
        "email": "user@example.com",
        "hashed_password": "$2b$12$6zN3HJIxgg6Xe1jpjTzQj.0Pc431KF2XIflxNSfU6ByLM9OIQ9kBi", # хэш пароля: 123456
        "disabled": False,
    }
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(email: str):
    if email in fake_users_db:
        user_dict = fake_users_db[email]
        return user_dict
    

def hash_password(password: str):   # For register
    return pwd_context.hash(password)


def authenticate_user(fake_db, email: str, password: str):
    user = get_user(email)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


def create_access_token(email: str, expires_delta: int = None):
    to_encode = {"sub": email}
    if expires_delta:
        expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        to_encode.update({"exp": expire})
    logging.info("In creating access token function", to_encode)
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    logging.info("Token", encoded_jwt)
    return encoded_jwt


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Здесь мы создаем JWT-токен с данными пользователя
    access_token = create_access_token(user["email"], expires_delta=3600)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"email": email}