from fastapi import FastAPI
import app.models
from app.models.users import User
from app.models.department import Department
from app.models.organization import Organization 
from app.models.team import Team

from app.api.auth import router as auth_router

app=FastAPI()

app.include_router(auth_router)
