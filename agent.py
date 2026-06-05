import os
import json
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
- If a request is unrelated to user management, politely decline and explain what you can do.

## Tool Usage Rules
- For ANY operation involving user data, you MUST call the corresponding tool. Never make up results.
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

Always use this format, no exceptions.
"""


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
                return last_msg.content
    
    return "Error: No response from agent"


if __name__ == "__main__":
    # Test the agent
    test_query = "создай пользователя с именем TestUser и email test@example.com"
    print(f"Query: {test_query}\n")
    print(run_agent(test_query))
