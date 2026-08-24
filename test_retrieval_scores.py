from app.database.database import SessionLocal
from app.models.users import User
from app.dependencies.rag import get_retrieval_service


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

        query = (
            "What operational checks should my department "
            "perform before making a service change?"
        )

        print("USER")
        print("  id =", current_user.user_id)
        print("  organization_id =", current_user.organization_id)
        print("  role =", current_user.role)

        print("\nQUERY")
        print(query)

        print("\nCreating Retrieval Service...")

        retrieval_service = get_retrieval_service()

        print("Retrieval Service created.")

        print("\nRunning retrieval...")

        results = retrieval_service.retrieve(
            db=db,
            query=query,
            current_user=current_user,
            vector_top_k=30,
            rerank_top_k=10,
        )

        print("\n========== RETRIEVAL RESULTS ==========")
        print("Total results:", len(results))

        for i, chunk in enumerate(results, start=1):

            print("\n----------------------------------------")
            print(f"RESULT #{i}")

            print("Document ID :", chunk.document_id)
            print("Chunk ID    :", chunk.chunk_id)
            print("Chunk index :", chunk.chunk_index)
            print("Filename    :", chunk.original_filename)

            print(
                "Vector score:",
                getattr(chunk, "vector_score", None)
            )

            print(
                "Rerank score:",
                getattr(chunk, "rerank_score", None)
            )

            print("\nTEXT:")
            print(chunk.chunk_text[:1000])

        print("\n========================================")

    finally:
        db.close()


if __name__ == "__main__":
    main()