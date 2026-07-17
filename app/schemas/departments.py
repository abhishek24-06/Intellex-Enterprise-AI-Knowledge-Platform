from pydantic import BaseModel, ConfigDict
from datetime import datetime

class CreateDepartmentRequest(BaseModel):
    name:str
    description:str | None = None

class DepartmentResponse(BaseModel):
    department_id:int
    organization_id:int
    name:str
    description:str
    created_at: datetime
    # is_active:bool
    model_config=ConfigDict(
        from_attributes=True
    )
