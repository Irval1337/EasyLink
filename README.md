## О проекте
Easylink — это сервис для сокращения ссылок с поддержкой аналитики, управления пользователями и безопасностью. Система построена на микросервисной архитектуре, что обеспечивает масштабируемость и гибкость.

## Технологии
- Python 3.11+
- FastAPI — backend для всех микросервисов
- PostgreSQL — основная база данных
- Docker, Docker Compose — контейнеризация
- Traefik — обратный прокси и маршрутизация
- SMTP — отправка email
- HTML, CSS, JavaScript — фронтенд

## Структура сервиса
```
src/
  analytics-service/   # сервис аналитики переходов
  url-service/         # сервис сокращения и редиректа ссылок
  users-service/       # сервис управления пользователями и авторизацией
  frontend/            # клиентская часть (SPA)
docker-compose.yml     # запуск всех сервисов
```
Каждый сервис содержит свою бизнес-логику, API, модели и схемы. Взаимодействие между сервисами происходит по HTTP внутри Docker-сети. Для балансировки и маршрутизации используется Traefik.

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
    - Swagger Docs: http://localhost/docs/
    - Фронтенд: http://localhost
    - Traefik: http://localhost:8081
5.  **Остановка:**
    ```bash
    docker-compose down
    ```

## Переменные среды
Создайте файл `.env` в папке `users-service`. Установите необходимые значения следующим переменным:

### Настройки базы данныз
- `*_POSTGRES_USER` - Имя пользователя (по умолчанию: `*_user`)
- `*_POSTGRES_PASSWORD` - Пароль (**обязательно измените!**)
- `*_POSTGRES_DB` - Название бд (по умолчанию: `*_db`)
- `*_POSTGRES_HOST` - Хост бд (по умолчанию: `*_db` для Docker'а)
- `*_POSTGRES_PORT` - Порт (по умолчанию: `5432`)
- `*_DATABASE_URL` - Строка подключения, созданная из переменных выше

### Настройки URL
- `*_SERVICE_URL` - Ссылка на микросервис внутри сети докера
- `FRONTEND_URL` - Ссылка на фронтенд (не указывайте localhost, если запускаете на выделенном сервере)

### Общие настройки
- `SECRET_KEY` - Ключ для генерации JWT
- `DEBUG` - Просто флаг дебага
- `ALLOWED_ORIGINS` - Настройки доменов для CORS (пример `http://localhost,http://127.0.0.1:3000`)
- `ADMIN_TOKEN` - Админский токен (**обязательно измените!**)
- `MAX_URL_LENGTH` - Максимальная длина сокращенного кода
- `SHORT_CODE_LENGTH` - Длина автоматически генерируемого кода
- `MAX_EXPORT_RECORDS` - Количество экспортируемых записей в статистике

### Настройки slowapi
- `RATE_LIMIT_ENABLED` - Использование slowapi
- `USERS_RATE_LIMIT_GENERAL` - Ограничение на запросы по профилю пользователя (пример `100/minute`)
- `URL_RATE_LIMIT_GENERAL` - Ограничение на эндпоинты общего назначения (пример `100/minute`)
- `ANALYTICS_RATE_LIMIT_GENERAL` - Ограничение на запросы по аналитике (пример `100/minute`)
- `RATE_LIMIT_STRICT` - Ограничение на некоторые нагруженные эндпоинты (пример `100/minute`)
- `RATE_LIMIT_AUTH` - Ограничение на запросы авторизации/регистрации (пример `100/minute`)

### Настройки почты (обязательная часть для запуска)
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `FROM_EMAIL` - стандартные настройки для SMTP
- `EMAIL_ACTIVATION_TOKEN_EXPIRE_HOURS` - время жизни токена подтверждения email
- `EMAIL_ACTIVATION_RESEND_COOLDOWN_MINUTES` - минимальная частота переотправки писем

### Google safe browsing
- `GOOGLE_SAFE_BROWSING_API_KEY` - Токен из https://console.cloud.google.com/apis/credentials
- `SAFE_BROWSING_ENABLED` - Использование проверки ссылок

`*` - микросервис из списка [USERS, URL, ANALYTICS]

## Скриншоты фронтенда
https://ibb.co/PZyS3RMj
