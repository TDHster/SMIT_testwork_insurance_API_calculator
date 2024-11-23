#send_tariff_data.py

import requests
import json

# URL, на который будут отправлены данные
url = 'http://127.0.0.1:8000/api/update_tariff/'

# Путь к файлу с данными JSON
json_file_path = 'tariff_1.json'

# Загрузка данных из файла
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Преобразование данных в формат JSON (если нужно)
json_data = json.dumps(data)

# Заголовки запроса
headers = {
    'Content-Type': 'application/json'
}

# Отправка POST-запроса с данными
response = requests.post(url, headers=headers, data=json_data)

# Проверка статуса ответа
if response.status_code == 200:
    print('Данные успешно отправлены')
else:
    print(f'Ошибка при отправке данных: {response.status_code}')
    print(f'Текст ошибки: {response.text}')
