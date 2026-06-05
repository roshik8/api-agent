import os
import json
import re
from dotenv import load_dotenv
from typing import Any

from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from tools.api_tool import TOOLS

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

SYSTEM_PROMPT = """
You are an API operator agent for a user management service.

## Role
Your role is to help users interact with the user management API. You can:
1. Create new users
2. Retrieve user information by ID
3. Update user status (active, inactive, banned)
4. List all users and see status statistics

## Constraints
- You ONLY perform the four operations listed above.
- You do NOT invent or guess data; you always call the appropriate tool to fetch or modify data.
- You do NOT perform operations outside of user management.
- You do NOT call tools for unrelated queries such as greetings, chit-chat, weather, time, or anything outside user management.
- If a request is unrelated to user management, do not call tools and answer with a refusal in the contract format.
- Only call tools when the user explicitly asks to create a user, get a user by id, update user status, or list users.

## Tool Usage Rules
- For ANY operation involving user data, you MUST call the corresponding tool. Never make up results.
- Do NOT call any tool if the request is not clearly about users.
- Use create_user to create new users.
- Use get_user to retrieve a user by ID.
- Use update_user_status to change a user's status.
- Use list_users to get all users and statistics.

## Response Contract
Your final response MUST follow this exact format:

Status: success | error
Action: <brief description of what you did>
Data: <result in natural, human-readable language — NO raw JSON>
Errors: <error message in plain language, or — if none>

Response consistency rules:
- If a tool returns an error or a message like "API недоступен", use Status: error.
- If Status: error, then Action must describe an attempted operation that failed, not a success.
- If Status: error, do not use phrasing that implies success such as "Получил информацию", "Создал", "Обновил" or "Удалось".
- If Status: error, prefer phrasing like "Попытка ... не удалась", "Не удалось ...", "Запрос ... завершился с ошибкой".
- If Status: error, Data must be "—" and Errors must contain the tool error text.
- If Status: success, Errors must be "—" and Data must contain the result.
- Never invent ids, names, or success confirmations when the tool returned an error or no real data.
- Base your final output only on what the tool really returned.

Data must be a readable summary of the result. Do not output raw JSON in the Data field.
If a tool returns structured user data, convert it into a sentence like:
"Пользователь Alex (id 1), email alex@example.com, статус active."
If the result is a list, summarize the items briefly and include counts/statistics in words.
If there is no data to show, use "—" in Data.

Examples:
Status: success
Action: Создал пользователя Alex
Data: Пользователь Alex (id 1), email alex@example.com, статус active
Errors: —

Status: success
Action: Получил список пользователей и посчитал их статусы
Data: 3 пользователя: Alex (id 1, active), Maria (id 2, inactive), Boris (id 3, banned); всего active 1, inactive 1, banned 1
Errors: —

Example of an error case:
Запрос: «создай пользователя Anna»
tool вернул «API недоступен: не удалось подключиться к серверу.»
Правильный ответ:
Status: error
Action: Попытка создать пользователя Anna не удалась
Data: —
Errors: API недоступен: не удалось подключиться к серверу.

Другой пример ошибки:
Запрос: «получи информацию о пользователе с id 9999»
tool вернул «Ошибка 404: {"detail": "User with id 9999 not found"}»
Правильный ответ:
Status: error
Action: Попытка получить информацию о пользователе с id 9999 не удалась
Data: —
Errors: Пользователь с id 9999 не найден.

Пример нерелевантного запроса:
Запрос: «привет, как дела?»
Правильный ответ:
Status: error
Action: Запрос не относится к управлению пользователями
Data: —
Errors: Я могу только работать с пользователями: создать, получить, обновить статус или вывести список пользователей.

Всегда отвечай в этом формате и не вызывай инструменты для нерелевантных запросов.
Always use this format, no exceptions.
"""


def validate_agent_response(response: str) -> None:
    lines = [line.strip() for line in response.strip().splitlines() if line.strip()]
    if len(lines) < 4:
        raise ValueError(
            f"Agent response must contain at least 4 non-empty lines, got {len(lines)}: {response!r}"
        )

    def parse_line(prefix: str, line: str) -> str:
        if not line.startswith(prefix):
            raise ValueError(f"Expected line starting with '{prefix}', got: {line!r}")
        return line[len(prefix):].strip()

    status = parse_line("Status:", lines[0]).lower()
    if status not in {"success", "error"}:
        raise ValueError(f"Status must be 'success' or 'error', got: {status!r}")

    action = parse_line("Action:", lines[1])
    data = parse_line("Data:", lines[2])
    errors = parse_line("Errors:", lines[3])

    if status == "error":
        if data != "—":
            raise ValueError("For error status, Data must be '—'.")
        if errors == "—":
            raise ValueError("For error status, Errors must not be '—'.")

        bad_success_phrases = [
            r"(?<!\bне\s)(создал|получил|обновил|удалил|успешно|выполнил|получено|создан|обновлен|добавил|отправил|удалось|завершился успешно)",
        ]
        lowered = action.lower()
        for pattern in bad_success_phrases:
            if re.search(pattern, lowered):
                raise ValueError(
                    f"Error response Action contains success phrasing: {action!r}."
                )
    else:
        if errors != "—":
            raise ValueError("For success status, Errors must be '—'.")
        if data == "—":
            raise ValueError("For success status, Data must not be '—'.")


def run_agent(user_query: str) -> str:
    """
    Run the agent with a user query and return the final response.
    
    Args:
        user_query: The user's request
        
    Returns:
        The agent's response in the contract format
    """
    # Initialize the model
    model = ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=0.3,  # Lower temperature for more deterministic responses
    )
    
    # Create the agent
    agent = create_react_agent(model, TOOLS)
    
    # Run the agent
    # The agent expects messages in input
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_query),
    ]
    
    result = agent.invoke({"messages": messages})
    
    # Extract the final message
    if "messages" in result:
        final_messages = result["messages"]
        if final_messages:
            last_msg = final_messages[-1]
            if hasattr(last_msg, "content"):
                response = last_msg.content
                validate_agent_response(response)
                return response
    
    return "Error: No response from agent"


if __name__ == "__main__":
    # Test the agent
    test_query = "создай пользователя с именем TestUser и email test@example.com"
    print(f"Query: {test_query}\n")
    print(run_agent(test_query))
