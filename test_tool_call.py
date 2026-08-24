from dotenv import load_dotenv

load_dotenv()

import os

from langchain_openrouter import ChatOpenRouter

from app.agents.tools.user_data_tools import DATA_AGENT_TOOLS


def main():

    model = ChatOpenRouter(
        model=os.getenv("OPENROUTER_MODEL"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0,
    )

    print("MODEL:", os.getenv("OPENROUTER_MODEL"))
    print("TOOLS:", len(DATA_AGENT_TOOLS))

    for tool in DATA_AGENT_TOOLS:
        print("-", tool.name)

    model_with_tools = model.bind_tools(DATA_AGENT_TOOLS)

    response = model_with_tools.invoke(
        "List all users in my organization."
    )

    print("\nCONTENT:")
    print(response.content)

    print("\nTOOL CALLS:")
    print(response.tool_calls)


if __name__ == "__main__":
    main()