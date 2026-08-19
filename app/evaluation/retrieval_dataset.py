from app.evaluation.models import EvaluationCase


CASES = [
    EvaluationCase(
        query=(
            "What are the common working practices for "
            "Apple employees?"
        ),
        relevant_document_ids={33},
    ),

    EvaluationCase(
        query=(
            "What should an operator check before "
            "changing an internal service?"
        ),
        relevant_document_ids={35},
    ),

    EvaluationCase(
        query=(
            "What is the validation marker in my "
            "private operations notes?"
        ),
        relevant_document_ids={40},
    ),

    EvaluationCase(
        query=(
            "What is the IT department infrastructure "
            "incident handling process?"
        ),
        relevant_document_ids={41},
    ),
]