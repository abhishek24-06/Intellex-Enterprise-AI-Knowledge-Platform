from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session


from app.database.database import get_db
from app.schemas.organizations import OrganizationOnboardingResponse
from app.services.onboarding_service import CreateOrganizationRequest,onboard_organization
from app.dependencies.roles import require_super_admin
from app.models.users import User


router=APIRouter(
    prefix="/organizations",
    tags=["Organizations"]
)

@router.post("",response_model=OrganizationOnboardingResponse)
def create_organization(organization_data:CreateOrganizationRequest,
                        db:Session=Depends(get_db),
                        current_user:User=Depends(require_super_admin)
                        ):
    
    organization=onboard_organization(db=db,
                                      organization_data=organization_data)
    
    return OrganizationOnboardingResponse(
    organization=organization,
    admin_email=organization_data.admin_email,
    message="Organization onboarded successfully.",
    )