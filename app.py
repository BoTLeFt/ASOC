from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import asyncpg
import json
from pydantic import BaseModel

class StatusChangeRequest(BaseModel):
    matchBasedId: str
    status: str

class NotificationStatusChangeRequest(BaseModel):
    matchBasedId: str
    notification_status: str


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
    

async def send_message_to_user(email, message, button_payload):
    # Здесь необходимо вставить логику отправки сообщения в Mattermost
    # Например, используя Mattermost API или Mattermost Python SDK
    # Это может потребовать аутентификации, получения токена и т.д.
    # Важно сформировать корректный запрос с текстом сообщения и кнопками.
    # Пример отправки сообщения через Mattermost API:
    url = "http://host.docker.internal:8065/api/v4/posts"
    headers = {
        "Authorization": "Bearer your_access_token",   # Add smthing
        "Content-Type": "application/json"
    }
    data = {
        "channel_id": "your_channel_id",   # TODO: Make a way to generate channel_id for direct message
        "message": message,
        "props": {
            "attachments": [
                {
                    "actions": [
                        {"name": "Подтверждаю", "integration": {"url": "http://yourserver.com/change-status-by-bot", "context": {"action": "confirm", "payload": button_payload}}},
                        {"name": "Это ошибка", "integration": {"url": "http://yourserver.com/change-status-by-bot", "context": {"action": "error", "payload": button_payload}}}
                    ]
                }
            ]
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to send message to Mattermost")


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
    

# Ручка для загрузки файла
@app.post("/upload_file/")
async def upload_file(file: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        actor_username = payload.get("sub")
        if actor_username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        
        db_connection = await connect_to_database()

        contents = await file.read()
        author, commit_hash = file.filename.split("_")
        results = json.loads(contents)["runs"][0]["results"]
        
        vulns_to_bd = []

        for result in results:
            vuln = dict()
            vuln["matchBasedId"] = result["fingerprints"]["matchBasedId/v1"]
            vuln["uri_line"] = result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]+":"+str(result["locations"][0]["physicalLocation"]["region"]["startLine"])
            vuln["collumns"] = str(result["locations"][0]["physicalLocation"]["region"]["startColumn"]) + ":" + str(result["locations"][0]["physicalLocation"]["region"]["endColumn"])
            vuln["code_line"] = result["locations"][0]["physicalLocation"]["region"]["snippet"]["text"].strip()
            vuln["commit_hash"] = commit_hash
            vuln["author"] = author
            vuln["ruleId"] = result["ruleId"]
            vuln["message"] = result["message"]["text"]
            vuln["timestamp"] = str(datetime.now())
            vuln["status"] = "created"
            vuln["notification_status"] = "Need_to_send"
            vulns_to_bd.append(vuln)
            row = await db_connection.fetchrow("SELECT * FROM sast_vulns WHERE ruleid = $1 and (matchBasedId = $2 or code_line = $3)", vuln["ruleId"], vuln["matchBasedId"], vuln["code_line"])
            if row:
                print("Dublicate", row)
                continue
            await db_connection.execute('''INSERT INTO sast_vulns(matchBasedId, uri_line, collumns, code_line, commit_hash, author, ruleId, message, timestamp, status, notification_status) 
                               VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)''', vuln["matchBasedId"], vuln["uri_line"], vuln["collumns"], vuln["code_line"], vuln["commit_hash"], vuln["author"], vuln["ruleId"], vuln["message"], vuln["timestamp"], vuln["status"], vuln["notification_status"])

        await db_connection.close()
        to_return = ""
        for vuln in vulns_to_bd:
            for key in vuln.keys():
                if to_return:
                    to_return+=","
                to_return+=str("\'"+key+"\'"+":"+"\'"+vuln[key]+"\'")
        return {to_return}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=404, detail="Send valid file")


# Ручка для смены статуса уязвимости
@app.post("/change_status")
async def change_status(request_data: StatusChangeRequest, token: str = Depends(oauth2_scheme)): 
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        actor_username = payload.get("sub")
        if actor_username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        db_connection = await connect_to_database()
        await db_connection.execute('''UPDATE sast_vulns SET status = $1 WHERE matchBasedId = $2;''', request_data.status, request_data.matchBasedId)
        await db_connection.close()
        return {
            "status": "changed"
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    

# Ручка для получения данных из бд
@app.get("/data")
async def data(token: str = Depends(oauth2_scheme)): 
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        actor_username = payload.get("sub")
        if actor_username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        db_connection = await connect_to_database()
        data = await db_connection.fetch("SELECT * FROM sast_vulns")
        await db_connection.close()
        return data
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=404, detail="Something wrong")
    

# Ручка для смены статуса уязвимости
@app.post("/change_notification_status")
async def change_status(request_data: NotificationStatusChangeRequest, token: str = Depends(oauth2_scheme)): 
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        actor_username = payload.get("sub")
        if actor_username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        db_connection = await connect_to_database()
        await db_connection.execute('''UPDATE sast_vulns SET notification_status = $1 WHERE matchBasedId = $2;''', request_data.notification_status, request_data.matchBasedId)
        await db_connection.close()
        return {
            "status": "changed"
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Ручка для отправки нотификации по всем уязвимостям, где статус - Need_to_send
@app.get("/send-notifications")
async def fetch_and_send(background_tasks: BackgroundTasks, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        actor_username = payload.get("sub")
        if actor_username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        db_connection = await connect_to_database()
        vuln_to_send = await db_connection.fetch('''SELECT * FROM sast_vulns WHERE notification_status='Need_to_send';''')
        await db_connection.close()
        for row in vuln_to_send:
            email = row["author"]
            message = row["message"]
            button_payload = {"matchBasedId": row["matchBasedId"]}
            background_tasks.add_task(send_message_to_user, email, message, button_payload)
        return {"message": "Messages sent to users"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    

# Ручка для бота в Mattermost
@app.post("/change-status-by-bot")
async def change_status_by_bot(action: str, payload: dict):
    # TODO: Add logic to change status with validation
    return {"action": action, "payload": payload}