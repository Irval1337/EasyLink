## Быстрый старт

1.  **Клонируйте репозиторий и перейдите в `backend`:**
    ```bash
    cd backend
    ```
2.  **Соберите и запустите сервис через Docker Compose:**
    ```bash
    docker-compose up --build -d
    ```
3.  **Микросервис доступен через:**
    - API: http://localhost:8000
    - Swagger Docs: http://localhost:8000/docs
    - PostgreSQL Database: localhost:5432
4.  **Остановка:**
    ```bash
    docker-compose down
    ```

## Переменные среды

Создайте файл `.env` в папке `auth-service`. Установите необходимые значения следующим переменным:

- `DATABASE_URL` - Строка для подключения к PostgreSQL (пример `postgresql://user:password@db:5432/authdb`)
- `SECRET_KEY` - Ключ для генерации JWT
- `ALLOWED_ORIGINS` - Настройки доменов для CORS (пример `http://localhost:3000,http://127.0.0.1:3000`)
