# Orion Home

Редактор пользовательских сценариев для умного дома на базе Ujin OS. Житель описывает устройства и правила «когда — то», а сервис исполняет их на эмуляторах или устройствах стенда Ujin: протечка → кран перекрыт → консьержу тревога → жителю уведомление.

---

## Стек технологий

* **Backend Core**: FastAPI (Python 3.12)
* **Database**: SQLite (асинхронный драйвер `aiosqlite`)
* **ORM & Migrations**: SQLAlchemy 2.0 (Async) + Alembic
* **Integrations**: HTTPX (AsyncClient), Ujin OS
* **Real-time Push**: Server-Sent Events (SSE)
* **Containerization**: Docker & Docker Compose (с автоматическим Healthcheck)
* **Security**: OAuth2 Password Flow, JWT-токены с блэклистингом при выходе (Logout)

---

## Быстрый запуск (Docker)

```bash
./local_up.sh
```

На Windows (в PowerShell — `.\local_up.bat`):
```bat
local_up.bat
```

После этого:
* API доступен по адресу: `http://localhost:8000`
* Swagger UI: `http://localhost:8000/docs`
* ReDoc: `http://localhost:8000/redoc`

При старте контейнер применяет миграции и заполняет справочники, пользователей и дом жителя Ujin.

Для остановки:
```bash
./local_down.sh
```

На Windows: `local_down.bat` (в PowerShell — `.\local_down.bat`)

---

## Локальный запуск (без Docker)

1. **Создайте и активируйте виртуальное окружение:**
   ```bash
   cd api_gateway
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```
   На Windows: `py -3.12 -m venv .venv` и `.venv\Scripts\activate`.
2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Настройте переменные окружения:**
   ```bash
   cp .env.example .env
   ```
   На Windows: `copy .env.example .env`.
   Укажите `SECRET_KEY` и данные жителя Ujin (`UJIN_RESIDENT_PHONE`, `UJIN_RESIDENT_PASSWORD`, `UJIN_UST`).
4. **Запустите миграции и заполните базу:**
   ```bash
   alembic upgrade head
   python -m app.seed
   ```
5. **Запустите сервер:**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## Тестовые пользователи

| кто | телефон | пароль |
|---|---|---|
| Житель без умного дома | `79000000001` | `orion2026` |
| Консьерж | `79000000002` | `orion2026` |
| Житель Ujin (дом «Квартира 2761») | из `.env` | из `.env` |

---

## Маршруты API (Endpoints)

### Авторизация
* `POST /api/auth/login` — Вход по телефону и паролю (получение JWT токена).
* `POST /api/auth/logout` — Выход (блэклистинг токена).
* `GET /api/me` — Текущий пользователь и его дом.

### Дом и комнаты
* `POST /api/homes` — Создать дом с комнатами.
* `GET /api/homes/{id}` — Дом: комнаты, устройства, сценарии.
* `PATCH /api/homes/{id}` — Название и режим дома (дома / ушёл / ночь).
* `POST /api/homes/{id}/rooms`, `GET/PATCH/DELETE /api/rooms/{id}` — Комнаты.
* `GET /api/room-types` — Типы комнат.

### Устройства и эмуляторы
* `GET/POST /api/device-types`, `PUT/DELETE /api/device-types/{id}`, `POST /api/device-types/{id}/clone` — Каталог и свои типы устройств.
* `POST /api/devices`, `GET/PATCH/DELETE /api/devices/{id}` — Устройства.
* `POST /api/devices/{id}/commands`, `GET /api/devices/{id}/commands` — Команды и журнал команд.
* `POST /api/devices/{id}/simulate`, `POST /api/devices/{id}/simulate/online` — Проверка устройства и отключение связи.

### Сценарии
* `GET /api/homes/{id}/scenario-templates`, `POST /api/scenarios/from-template` — Заготовки под комнаты.
* `GET /api/homes/{id}/scenarios`, `POST /api/scenarios`, `GET/PUT/PATCH/DELETE /api/scenarios/{id}` — Сценарии.
* `GET /api/homes/{id}/editor-catalog`, `POST /api/scenarios/validate` — Редактор.
* `POST /api/scenarios/{id}/test`, `POST /api/scenarios/{id}/run` — Проверка и ручной запуск.
* `POST /api/assistant/messages`, `POST /api/assistant/messages/{id}/accept` — Помощник.

### Журнал и уведомления
* `GET /api/homes/{id}/journal` — Журнал событий.
* `GET /api/runs/{id}` — Запуск сценария по шагам.
* `GET /api/homes/{id}/notifications`, `GET /api/concierge/notifications`, `POST /api/notifications/{id}/ack` — Уведомления.
* `GET /api/homes/{id}/stream`, `GET /api/concierge/stream` — SSE.

### Ujin и демо
* `GET /api/ujin/status`, `GET /api/ujin/log`, `POST /api/ujin/sync` — Обмен с Ujin.
* `POST /api/demo/leak`, `POST /api/demo/leak-offline`, `POST /api/demo/reset` — Демо-цепочка.

---

## Как это работает

Устройства описываются декларацией: параметры, команды, настройки и события. Виртуальные устройства и устройства стенда живут в эмуляторе — раз в несколько секунд меняются батарея, счётчики, температура. Любое изменение значения проверяется движком сценариев: когда условия становятся верными, выполняются действия по порядку. Если устройство не отвечает, движок повторяет команду и выполняет запасной план. Все изменения уходят в приложение по SSE, а значения устройств стенда публикуются в Ujin.
