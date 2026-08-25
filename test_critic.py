from app.dependencies.agentic_rag import get_critic_agent


class FakeChunk:
    document_id = 1
    original_filename = "password_policy.txt"
    chunk_text = """
    Password Policy:
    Users must use a strong password containing at least 12 characters.
    Passwords must be changed every 90 days.
    Users must not reuse their previous 5 passwords.
    """


def main():

    critic = get_critic_agent()

    result = critic.evaluate(
        query="What is our password policy?",
        answer=(
            "What is my department, and what operational checks should my department perform before making a service change?"
        ),
        chunks=[FakeChunk()],
        database_result=None,
    )

    print()
    print("========== CRITIC RESULT ==========")
    print(result)
    print("===================================")


if __name__ == "__main__":
    main()