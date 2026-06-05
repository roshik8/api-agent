# Минимальный агент на LangChain

Учебный проект: LangChain-агент, который управляет пользователями через REST API, используя локальную LLM (Ollama).

## Архитектура

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   CLI       │         │   Agent     │         │   Ollama    │
│ (main.py)   │  <──→  │ (agent.py)  │  <──→  │ (llama3.1)  │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              ↓
                        ┌─────────────┐
                        │   Tools     │
                        │(api_tool.py)│
                        └─────────────┘
                              │
                              ↓
                        ┌─────────────┐
                        │  FastAPI    │
                        │  (server.py)│
                        └─────────────┘
```

## LLM: Ollama

**Модель**: `llama3.1:8b`  
**URL**: `http://localhost:11434` (по умолчанию)

### Установка и запуск Ollama

1. Скачайте [Ollama](https://ollama.ai)
2. Установите `llama3.1:8b`:
   ```bash
   ollama pull llama3.1:8b
   ```
3. Запустите сервер:
   ```bash
   ollama serve
   ```

**Переменные окружения** (`.env`):
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

## API: FastAPI

**Базовый URL**: `http://localhost:8000`  
**Хранилище**: в памяти (без БД)

### Поддерживаемые операции

| Метод | Эндпоинт | Описание |
|-------|----------|---------|
| `POST` | `/users` | Создать пользователя (name, email) → возвращает User с id, status=active |
| `GET` | `/users/{id}` | Получить пользователя по id → возвращает User или 404 |
| `PATCH` | `/users/{id}` | Обновить статус (active\|inactive\|banned) → возвращает обновленный User |
| `GET` | `/users` | Список всех пользователей + статистика (count, by_status) |
| `GET` | `/health` | Проверка доступности сервера |

### Модель User

```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com",
  "status": "active",
  "created_at": "2026-06-02T09:14:35.529684+00:00"
}
```

## Агент: ReAct с LangChain + LangGraph

**Компоненты**:
- **LLM**: ChatOllama (локальная Ollama)
- **Фреймворк**: langgraph.prebuilt.create_react_agent
- **Tools**: 4 LangChain tool'а для API (create_user, get_user, update_user_status, list_users)
- **Промпт**: системный промпт с описанием ролей, ограничений и контракта ответа

### Контракт ответа агента

Каждый ответ агента структурирован:

```
Status: success | error
Action: <описание действия>
Data: <результат от API или —>
Errors: <ошибка или —>
```

## Установка зависимостей

```bash
pip install fastapi uvicorn httpx python-dotenv
pip install langchain-core langchain-ollama langgraph
```

## Запуск проекта

Откройте **три отдельных терминала**:

### Терминал 1: Ollama

```bash
ollama serve
```

Проверка: `curl http://127.0.0.1:11434/api/tags`

### Терминал 2: FastAPI мок-API

```bash
python -m uvicorn api.server:app --port 8000 --reload
```

Проверка: `curl http://127.0.0.1:8000/health`

### Терминал 3: Запуск агента

```bash
python main.py "создай пользователя с именем Alex"
```

## Использование агента

**Синтаксис**:
```bash
python main.py "<запрос на русском или английском>"
```

**Примеры**:
```bash
# Создать пользователя
python main.py "создай пользователя с именем Bob и email bob@example.com"

# Получить пользователя
python main.py "покажи информацию о пользователе с id 1"

# Изменить статус
python main.py "заблокируй пользователя с id 1"

# Список всех
python main.py "покажи всех пользователей и статистику по статусам"

# Отказ вне области
python main.py "какая погода в Москве?"
```

## Результаты тестирования

### Тест 1: Создание пользователя

**Запрос**:
```bash
python main.py "создай пользователя с именем Alice и email alice@example.com"
```

**Ответ агента** (формат контракта):
```
Status: success
Action: Создал пользователя Alice
Data: Пользователь Alice (id 2), email alice@example.com, статус active
Errors: —
```

### Тест 2: Получение пользователя

**Запрос**:
```bash
python main.py "дай информацию о пользователе с id 2"
```

**Ответ агента**:
```
Status: success
Action: Получил информацию о пользователе с id 2
Data: Пользователь Alice (id 2), email alice@example.com, статус active
Errors: —
```

### Тест 3: Обновление статуса

**Запрос**:
```bash
python main.py "измени статус пользователя с id 2 на inactive"
```

**Ответ агента**:
```
Status: success
Action: Обновил статус пользователя с id 2 на inactive
Data: Пользователь Alice (id 2), email alice@example.com, статус inactive
Errors: —
```

### Тест 4: Список пользователей и статистика

**Запрос**:
```bash
python main.py "покажи всех пользователей со статистикой по статусам"
```

**Ответ агента**:
```
Status: success
Action: Получил список пользователей и посчитал их статусы
Data: 1 пользователь: Alice (id 2, inactive); всего active 0, inactive 1, banned 0
Errors: —
```

### Тест 5: Ошибка - пользователь не найден (404)

**Запрос**:
```bash
python main.py "покажи информацию о пользователе с id 999"
```

**Ответ агента**:
```
Status: error
Action: Попытка получить пользователя с id 999 не удалась
Data: —
Errors: Пользователь с id 999 не найден.
```

### Тест 6: Запрос вне темы

**Запрос**:
```bash
python main.py "привет, как дела?"
```

**Ответ агента**:
```
Status: error
Action: Запрос не относится к управлению пользователями
Data: —
Errors: Я могу только работать с пользователями: создать, получить, обновить статус или вывести список пользователей.
```

## Структура проекта

```
api-agent/
├── .env                    # Переменные окружения (локально)
├── .env.example            # Шаблон .env
├── .gitignore              # Исключает .env, venv/
├── README.md               # Этот файл
├── main.py                 # CLI точка входа
├── agent.py                # Агент с системным промптом
├── api/
│   ├── __init__.py
│   └── server.py           # FastAPI мок-API с User моделью
├── tools/
│   ├── __init__.py
│   └── api_tool.py         # 4 LangChain tool'а для HTTP-запросов
└── test_agent_quick.py     # Проверка компонентов (опционально)
```

## Как это работает

1. **Пользователь** вводит запрос через CLI: `python main.py "создай пользователя"`
2. **main.py** передает запрос функции `run_agent()`
3. **agent.py** инициализирует ChatOllama и создает ReAct-агента
4. **Агент** читает системный промпт, понимает задачу и выбирает tool
5. **Tool** делает HTTP-запрос к FastAPI
6. **FastAPI** выполняет операцию (создает, обновляет, получает пользователя)
7. **Tool** возвращает JSON-ответ агенту
8. **Агент** интегрирует результат и форматирует ответ по контракту
9. **main.py** выводит ответ в консоль

## Пример полного диалога

```bash
$ python main.py "создай пользователя Bob"
Query: создай пользователя Bob

--------------------------------------------------------------------------------
Status: success
Action: Создал пользователя Bob
Data: Пользователь Bob (id 2), email —, статус active
Errors: —

--------------------------------------------------------------------------------
```

## Ограничения и особенности

- ✅ Локальная LLM — нет зависимости от интернета
- ✅ Минимальный стек — FastAPI, LangChain, Ollama
- ✅ Структурированные ответы — контракт Status/Action/Data/Errors
- ✅ Обработка ошибок — 404, 422, timeout, connection errors
- ⚠️ Нет памяти диалога — каждый запрос независим
- ⚠️ In-memory хранилище — данные теряются при перезапуске API
- ⚠️ Нет аутентификации — для учебы

## Дальнейшее развитие

- Добавить базу данных (SQLite / PostgreSQL)
- Добавить историю диалога (ConversationBufferMemory)
- Добавить веб-интерфейс (FastAPI WebSocket + React)
- Добавить более сложные tool'ы (поиск, фильтрация, аналитика)
- Интегрировать с облачными LLM (OpenAI, Anthropic) через переменные окружения

---

**Автор**: Учебный проект LangChain  
**Дата**: июнь 2026
