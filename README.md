# AI Sales Pro — B2B Web-сервис и Telegram Bot 🚀⚡

Полноценный B2B Web-сервис и автономный Telegram-бот на Python (FastAPI + aiogram 3.x + Google Gemini AI + SQLite + Async SQLAlchemy).

## 🌟 Возможности сервиса

1. **Единый Backend (FastAPI)**: Запуск сервера и фонового Telegram-бота одной командой `python main.py`.
2. **База данных (SQLite + Async SQLAlchemy)**: Автоматическое хранение заявка-лидов (`Leads`), истории диалогов с сайта и из Telegram (`ChatMessage`), а также динамического системного промпта Gemini AI (`SystemPromptConfig`).
3. **B2B Лендинг с AI Чат-виджетом**: Адаптивный современный веб-сайт (`templates/index.html`) с формой записи на демо и всплывающим AI-виджетом консультанта по продажам.
4. **Мгновенные уведомления в Telegram**: При отправке формы заявки на сайте данные заносятся в БД и отправляются администратору прямо в Telegram.
5. **Админ-Панель (`/admin`)**: Панель управления с таблицами лидов, чатов и возможностью динамически менять системный промпт Gemini без перезапуска сервера.

---

## 📁 Структура проекта

```
telegram_ai_sales_bot/
├── .env                       # Токены: BOT_TOKEN, GEMINI_API_KEY, ADMIN_TELEGRAM_ID и БД
├── .gitignore                 # Исключения Git
├── requirements.txt           # Зависимости проекта
├── config.py                  # Конфигурация приложения
├── database/
│   ├── connection.py          # Подключение к SQLite с Async SQLAlchemy
│   └── models.py              # Модели Lead, ChatMessage, SystemPromptConfig
├── services/
│   ├── ai_service.py          # Интеграция с Google Gemini AI
│   └── telegram_service.py    # Экземпляр бота и функция отправки уведомлений админу
├── bot/
│   ├── handlers.py            # Обработчики команд и сообщений Telegram-бота
│   └── keyboards.py           # Клавиатуры Telegram
├── web/
│   └── app.py                 # Маршруты FastAPI (Лендинг, /api/leads, /api/chat, /admin)
├── templates/
│   ├── index.html             # Лендинг с формой заявки и чат-виджетом
│   └── admin.html             # Панель администратора
├── static/
│   ├── css/ (style.css, admin.css)
│   └── js/ (lead_form.js, chat_widget.js)
├── main.py                    # Единая точка входа (FastAPI + Telegram Bot)
└── README.md
```

---

## 🛠️ Запуск одной командой

### 1. Перейдите в каталог проекта

```bash
cd telegram_ai_sales_bot
```

### 2. Установите новые зависимости

```bash
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Запустите сервис

```bash
.\venv\Scripts\python.exe main.py
```

После запуска:
- **Веб-сайт**: [`http://127.0.0.1:8000`](http://127.0.0.1:8000)
- **Админ-панель**: [`http://127.0.0.1:8000/admin`](http://127.0.0.1:8000/admin)
- **Telegram Bot**: Запущен в фоновом режиме и слушает сообщения.
