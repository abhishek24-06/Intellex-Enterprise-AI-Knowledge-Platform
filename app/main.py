from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api import departments, organizations

app=FastAPI()

app.include_router(auth_router)

app.include_router(organizations.router)

app.include_router(departments.router)