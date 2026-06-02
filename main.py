import sys
from agent import run_agent


def main():
    """CLI entry point for the agent."""
    if len(sys.argv) < 2:
        print("Usage: python main.py \"<user query>\"")
        print("\nExample:")
        print('  python main.py "создай пользователя с именем Alex"')
        print('  python main.py "покажи данные пользователя с id 1"')
        print('  python main.py "покажи всех пользователей"')
        print('  python main.py "забани пользователя с id 1"')
        sys.exit(1)
    
    user_query = " ".join(sys.argv[1:])
    
    print(f"Query: {user_query}\n")
    print("-" * 80)
    
    response = run_agent(user_query)
    
    print(response)
    print("-" * 80)


if __name__ == "__main__":
    main()
