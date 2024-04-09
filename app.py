from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import asyncpg


app = FastAPI()
secret_key = "l5h49PKyBb3GG0qIhay-Dk4zyL53FGuN8cn2Eax3NVo" # to_vault

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def connect_to_database():
    return await asyncpg.connect(user='asocuser', password='asocpass',
                                 database='asocdb', host='asoc-pgsql')


async def get_user(username: str):
    db_connection = await connect_to_database()
    row = await db_connection.fetchrow("SELECT * FROM users WHERE username = $1 ORDER BY disabled desc", username)
    user = dict(row)
    await db_connection.close()
    return user

    
async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    print("user", user)
    if not user:
        return False
    if not pwd_context.verify(password, user["hashed_password"]):
        return False
    return user


def create_access_token(username: str, expires_delta: int = None):
    to_encode = {"sub": username}
    if expires_delta:
        expire = datetime.now(datetime.UTC) + timedelta(seconds=expires_delta)
        to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Здесь мы создаем JWT-токен с данными пользователя
    access_token = create_access_token(user["username"])
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db_connection = await connect_to_database()
    row = await db_connection.fetchrow("SELECT * FROM users WHERE username = $1 ORDER BY disabled desc", username)
    await db_connection.close()
    user = dict(row)
    if not user:
        return {"error": 'No such user'}
    return {'username': user['username'], 'full_name': user['full_name'], 'email': user['email'], 'hashed_password': user['hashed_password'], 'disabled': user['disabled']}


@app.get("/hash/{password}")
async def hash_password(password: str):   # Debug
    return {"hash": pwd_context.hash(password)}


@app.get("/user_from_db/{username}")
async def user_from_db(username: str, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        actor_username = payload.get("sub")
        if actor_username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        db_connection = await connect_to_database()
        row = await db_connection.fetchrow("SELECT * FROM users WHERE username = $1 ORDER BY disabled desc", username)
        await db_connection.close()
        user = dict(row)
        if not user:
            return {"error": 'No such user'}
        return {'username': user['username'], 'full_name': user['full_name'], 'email': user['email'], 'hashed_password': user['hashed_password'], 'disabled': user['disabled']}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except (Exception, Error) as error:
        return {"error": error}