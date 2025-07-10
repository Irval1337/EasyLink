## Начало работы

1.  **Клонируйте репозиторий и перейдите в `backend`:**
    ```bash
    cd backend
    ```
2.  **Настройте переменные среды**
3.  **Соберите и запустите сервис через Docker Compose:**
    ```bash
    docker-compose up --build -d
    ```
4.  **Микросервис доступен через:**
    - API: http://localhost:8000
    - Swagger Docs: http://localhost:8000/docs
    - PostgreSQL Database: localhost:5432
5.  **Остановка:**
    ```bash
    docker-compose down
    ```

## Переменные среды

Создайте файл `.env` в папке `users-service`. Установите необходимые значения следующим переменным:

### Настройки базы данныз
- `POSTGRES_USER` - Имя пользователя (по умолчанию: `users_user`)
- `POSTGRES_PASSWORD` - Пароль (**обязательно измените!**)
- `POSTGRES_DB` - Название бд (по умолчанию: `users_db`)
- `POSTGRES_HOST` - Хост бд (по умолчанию: `users_db` для Docker'а)
- `POSTGRES_PORT` - Порт (по умолчанию: `5432`)
- `DATABASE_URL` - Строка подключения, созданная из переменных выше

### Общие настройки
- `SECRET_KEY` - Ключ для генерации JWT
- `DEBUG` - установите `False` в продакшене
- `ALLOWED_ORIGINS` - Настройки доменов для CORS (пример `http://localhost:3000,http://127.0.0.1:3000`)
