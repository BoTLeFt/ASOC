import requests
from mattermostdriver import Driver


# Замените этими данными реальные значения
MATTERMOST_URL = "host.docker.internal"
TOKEN = "hi8x8dw4gfgzzjujzb4zuf3bfh"
TEAM_NAME = "inovating-tech"
CHANNEL_NAME = "sec-team"

author = "creep"
message = "Мы нашли XSS, срочно пофикси"
button_payload = {"matchbasedid": 1}

headers = {
        "Authorization": "bearer "+str(TOKEN),   # security_bot
        "Content-Type": "application/json"
    }

# Инициализация клиента Mattermost
client = Driver({
    'url': MATTERMOST_URL,
    'token': TOKEN,
    'scheme': 'http',
    'port': 8065,
    'verify': True,
})

# Аутентификация
client.login()

# Получение информации о команде
team = client.teams.get_team_by_name(TEAM_NAME)
team_id = team['id']
channel = client.channels.get_channel_by_name(team_id, CHANNEL_NAME)
channel_team_id = channel['id']
print(channel_team_id)

# Получение информации о канале
users = ["security_bot", author]
usermaps = dict()
for user in users:
    try:
        userid = requests.post("http://host.docker.internal:8065/api/v4/users/usernames", headers=headers, json=[user]).json()[0]['id']
        usermaps[user]=userid
    except Exception:
        usermaps[user]="none"
    
print(usermaps)
channel_id = requests.post("http://host.docker.internal:8065/api/v4/channels/direct", headers=headers, json=[usermaps["security_bot"], usermaps[author]]).json()['name']

# Отправка интерактивного сообщения
interactive_message = {
    "channel_id": channel_id,
        "message": message,
        "props": {
            "attachments": [
                {
                    "actions": [
                        {"name": "Подтверждаю", "integration": {"url": "http://host.docker.internal:8080/change-status-by-bot", "context": {"action": "confirm", "payload": button_payload}}},
                        {"name": "Это ошибка", "integration": {"url": "http://host.docker.internal:8080/change-status-by-bot", "context": {"action": "error", "payload": button_payload}}}
                    ]
                }
            ]
        }
    }
client.posts.create_post(interactive_message)

# Выход
client.logout()