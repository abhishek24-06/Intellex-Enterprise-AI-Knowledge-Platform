from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api import departments, organizations, team, users, documents,document_access, retrieval, chat, chat_sessions, chat_messages, chat_history, observability
from app.core.exceptions import value_error_handler
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ValueError,value_error_handler,)

app.include_router(auth_router)

app.include_router(organizations.router)

app.include_router(departments.router)

app.include_router(team.router)

app.include_router(users.router)

app.include_router(documents.router)

app.include_router(document_access.router)

app.include_router(retrieval.router)

app.include_router(chat.router)

app.include_router(chat_sessions.router)

app.include_router(chat_messages.router)

app.include_router(chat_history.router)

app.include_router(observability.router)