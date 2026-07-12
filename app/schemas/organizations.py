from pydantic import BaseModel, ConfigDict

class CreateOrganizationRequest(BaseModel):
    organization_name:str
    industry_name:str
    admin_name:str
    admin_email:str
    admin_password:str

class OrganizationResponse(BaseModel):
    organization_id: int
    name: str
    industry: str
    is_active: bool
    model_config = ConfigDict(
        from_attributes=True
    )

class OrganizationOnboardingResponse(BaseModel):
    organization:OrganizationResponse
    admin_email:str
    message:str