

import requests
import json

url = 'http://127.0.0.1:5000//users'
headers = {"Content-Type": "application/json"}
user_data = {"name": "ads"}

response = requests.post(url=url, data=json.dumps(user_data), headers=headers)

print(response.status_code) # Ожидаемый код ответа - 200 OK
print(response.json()) # Вывод информации о созданном пользователе
