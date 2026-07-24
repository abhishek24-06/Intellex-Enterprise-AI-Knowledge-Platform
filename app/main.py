from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api import departments, organizations, team, users
from app.core.exceptions import value_error_handler

app=FastAPI()

app.add_exception_handler(ValueError,value_error_handler,)

app.include_router(auth_router)

app.include_router(organizations.router)

app.include_router(departments.router)

app.include_router(team.router)

app.include_router(users.router)