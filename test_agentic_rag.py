from app.database.database import SessionLocal
from app.models.users import User
from app.dependencies.agentic_rag import get_agentic_rag_service


def main():

    db = SessionLocal()

    try:
        current_user = (
            db.query(User)
            .filter(User.user_id == 9)
            .first()
        )

        if current_user is None:
            raise RuntimeError("User id=9 not found.")

        print("Authenticated user:")
        print("  id =", current_user.user_id)
        print("  email =", current_user.email)
        print("  organization_id =", current_user.organization_id)
        print("  role =", current_user.role)

        print("\nCreating Agentic RAG service...")

        service = get_agentic_rag_service()

        print("Agentic RAG service created.")

        print("\nSending query...")

        result = service.answer(
            db=db,
            query="What is my department, and what operational checks should my department perform before making a service change?",
            current_user=current_user,
        )

        print("\n========== RESULT ==========")
        print(result.answer)
        print("============================")

    finally:
        db.close()


if __name__ == "__main__":
    main()