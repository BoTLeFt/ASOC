from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import asyncpg
import json
from pydantic import BaseModel
import requests

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
    

async def send_message_to_user(author, message, matchbasedid):
    headers = {
        "Authorization": "bearer hi8x8dw4gfgzzjujzb4zuf3bfh",   # security_bot
        "Content-Type": "application/json"
    }

    users = ["security_bot", author]
    usermaps = dict()
    button_payload = {"matchbasedid": matchbasedid}
    for user in users:
        try:
            userid = requests.post("http://host.docker.internal:8065/api/v4/users/usernames", headers=headers, json=[user]).json()[0]['id']
            usermaps[user]=userid
        except Exception:
            usermaps[user]="none"
    
    print(usermaps)
    channel_id = requests.post("http://host.docker.internal:8065/api/v4/channels/direct", headers=headers, json=[usermaps["security_bot"], usermaps[author]]).json()['id']
    # channel_team_id = "oyc7i4hwsibsdbk1pm8ra8an7e"
    url = "http://host.docker.internal:8065/api/v4/posts"
    
    data = {
        "channel_id": channel_id,
        "props": {
            "attachments": [
                {
                    "color": "#FF8000",
                    "title": "Найдена уязвимость в коде!",
                    "title_link": "http://host.docker.internal:90/projects/SECISSUE/issues/?filter=allopenissues",
                    "text": message,
                    "fields": [
                    {
                    "short": False,
                    "title":"Vulnerability Id",
                    "value": matchbasedid
                    },
                    {
                    "short": True,
                    "title":"Критичность",
                    "value":"Высокая"
                    },
                    ],
                    "actions": [
                        {"name": "Подтверждаю", "integration": {"url": "http://host.docker.internal:8080/change-status-by-bot", "context": {"action": "True Positive", "payload": button_payload}}},
                        {"name": "Это ошибка", "integration": {"url": "http://host.docker.internal:8080/change-status-by-bot", "context": {"action": "Need review", "payload": button_payload}}}
                    ]
                }
            ]
        }
    }
    response = requests.post(url, headers=headers, json=data)
    print(response, response.json())
    # TODO: Добавить смену статуса отправляемой коммуникации на "SEND" в бд
    if response.status_code != 201:
        return False
    db_connection = await connect_to_database()
    await db_connection.execute('''UPDATE sast_vulns SET notification_status = $1 WHERE matchBasedId = $2;''', "Sended", matchbasedid)
    await db_connection.close()
    return True


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


@app.get("/hash/{password}")
async def hash_password(password: str):   # Debug
    return {"hash": pwd_context.hash(password)}
    

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
            row = await db_connection.fetchrow("SELECT * FROM sast_vulns WHERE ruleid = $1 and (matchBasedId = $2 or code_line = $3)", vuln["ruleId"], vuln["matchBasedId"], vuln["code_line"])
            if row:
                print("Dublicate", row)
                continue
            flag_of_send = send_message_to_user(vuln["author"], vuln["message"], vuln["matchBasedId"])
            if flag_of_send:
                vuln["notification_status"] = "Sended"
            else:
                vuln["notification_status"] = "Need_to_send"
            vulns_to_bd.append(vuln)
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
async def fetch_and_send(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        actor_username = payload.get("sub")
        if actor_username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        db_connection = await connect_to_database()
        vuln_to_send = await db_connection.fetch('''SELECT * FROM sast_vulns WHERE notification_status='Need_to_send';''')
        await db_connection.close()
        for row in vuln_to_send:
            print(row["matchbasedid"])
            await send_message_to_user(row["author"].split("+")[0].strip().lower(), row["message"], row["matchbasedid"])
        return {"message": "Messages sent to users"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    

# Ручка для бота в Mattermost
@app.post("/change-status-by-bot")
async def change_status_by_bot(data: dict):
    # TODO: Add logic to change status with validation
    print(data)
    matchbasedid = data['context']['payload']['matchbasedid']
    status = data['context']['action']
    print({"status": status, "matchbasedid": matchbasedid})
    if status=="True Positive":
        db_connection = await connect_to_database()
        await db_connection.execute('''UPDATE sast_vulns SET status = $1 WHERE matchBasedId = $2;''', status, matchbasedid)
        await db_connection.close()
        return {"update": {"props": {"attachments": [{"color": "#99FF99","title": "Спасибо за помощь!","text": "Уязвимость с id **_"+ matchbasedid + "_** теперь имеет статус **" + status+"**. Теперь важно устранить эту уязвимость до выхода ПО в общий доступ. По всем вопросам обращайтесь в команду ИБ."}]}}}
    elif status=="Need review":
        db_connection = await connect_to_database()
        await db_connection.execute('''UPDATE sast_vulns SET status = $1 WHERE matchBasedId = $2;''', status, matchbasedid)
        await db_connection.close()
        return {"update": {"props": {"attachments": [{"color": "#004DFF","title": "Спасибо за помощь!","text": "Уязвимость с id **_"+ matchbasedid + "_** теперь имеет статус **" + status+"**. Команда ИБ проверит верность этого решения и в случае чего свяжется с Вами. По всем вопросам обращайтесь в команду ИБ."}]}}}
    else:
        raise HTTPException(status_code=450, detail="Not valid status")
