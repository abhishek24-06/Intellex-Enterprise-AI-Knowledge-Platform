from dotenv import load_dotenv

load_dotenv()

from app.database.database import SessionLocal
from app.dependencies.agents import get_database_agent
from app.services.user_service import get_user_by_id


# CHANGE THIS TO YOUR ACTUAL USER ID
USER_ID = 9


def main():
    db = SessionLocal()

    try:
        current_user = get_user_by_id(
            db=db,
            id=USER_ID,
        )

        if current_user is None:
            raise RuntimeError(
                f"User with ID {USER_ID} was not found."
            )

        print("Authenticated user:")
        print(
            f"  id={current_user.user_id}"
        )
        print(
            f"  email={current_user.email}"
        )
        print(
            f"  organization_id={current_user.organization_id}"
        )
        print(
            f"  role={current_user.role}"
        )

        print("\nCreating Database Agent...")

        agent = get_database_agent()

        print("Database Agent created.")
        print("\nSending query...")

        result = agent.invoke(
            query="What is my name?",
            db=db,
            current_user=current_user,
        )

        print("\n========== RESULT ==========")
        print(result)
        print("============================")


    finally:
        db.close()


if __name__ == "__main__":
    main()