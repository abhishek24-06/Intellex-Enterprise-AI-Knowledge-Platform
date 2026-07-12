from sqlalchemy.orm import Session

from app.schemas.organizations import CreateOrganizationRequest
from app.models.organization import Organization
from app.enums.enums import UserRole
from app.services.user_service import create_user
from app.services.organization_service import create_organization


def onboard_organization(db:Session,organization_data:CreateOrganizationRequest)->Organization:
    try:
        organization=create_organization(db=db,
                                        name=organization_data.organization_name,
                                        industry=organization_data.industry_name
                                        )

        create_user(db=db,
                    name=organization_data.admin_name,
                    email=organization_data.admin_email,
                    password=organization_data.admin_password,
                    role=UserRole.ORG_ADMIN,
                    organization_id=organization.organization_id,
                    department_id=None,
                    team_id=None
                    )
        
        db.commit()
        db.refresh(organization)

        return organization
      
    except Exception:
        db.rollback()
        raise

        