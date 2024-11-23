## Описание
Проект представляет собой API для работы с тарифами страхования грузов. API предоставляет следующие функции:

- Добавление тарифов.
- Просмотр тарифов.
- Удаление тарифов.
- Логирование изменений в Kafka (если доступно).

## Стек технологий
Python 
FastAPI
SQLAlchemy
SQLite (по умолчанию) или PostgreSQL (в Docker)
Kafka (опционально)
Docker и Docker Compose

##  Установка и запуск
1. Клонирование репозитория
Склонируйте проект на ваш локальный компьютер:

```bash
git clone <URL_репозитория>
cd <название_папки_репозитория>
```
1. Настройка окружения
Создайте файл .env в корневой папке проекта и укажите переменные окружения:

```env
DATABASE_URL=sqlite:///./tariffs.db  # Для SQLite
#DATABASE_URL=postgresql://postgres:password@db:5432/tariffs  # Для PostgreSQL в Docker
KAFKA_BOOTSTRAP_SERVERS=localhost:9092  # Настройка Kafka (опционально)
```
3. Запуск локально (без Docker)

_Рекомендуется использовать виртуальное окружение._

Установите зависимости:

```bash
pip install -r requirements.txt
```
Запустите FastAPI приложение:

```bash
python insurance_api.py
```
Приложение будет доступно по адресу: http://127.0.0.1:8000

1. Развертывание с Docker и Docker Compose
Убедитесь, что установлены Docker и Docker Compose.

Соберите и запустите контейнеры :

```bash
docker-compose up --build
```
Приложение будет доступно по адресу: http://127.0.0.1:8000

## Использование API
1. Добавление тарифов
URL: POST /api/update_tariff/
Пример данных:
JSON файл (tariff_1.json):

json
Копировать код
{
  "2024-11-23": [
    {
      "cargo_type": "Fragile Goods",
      "rate": 0.02
    },
    {
      "cargo_type": "Electronics",
      "rate": 0.03
    }
  ]
}

Первичное введение тестовых данных о тарифах через скрипт:

```bash
python send_tariff_data.py
```
2. Удаление тарифа
URL: DELETE /api/delete_tariff/{tariff_id}
Пример запроса через curl:

```bash
curl -X DELETE http://127.0.0.1:8000/api/delete_tariff/1 -H "x-user-id: 123"
```
Логирование в Kafka
Если Kafka настроен и доступен, все изменения тарифов (добавление/удаление) будут логироваться в топик tariff_changes. Если Kafka недоступен, приложение продолжит работать без логирования.


### Тестирование
Для тестирования используйте встроенную документацию Swagger:

Открыть в браузере: http://127.0.0.1:8000/docs
