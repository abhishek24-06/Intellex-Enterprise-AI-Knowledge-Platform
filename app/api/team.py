from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.users import User
from app.services.team_service import create_team
from app.dependencies.roles import require_org_admin
from app.schemas.teams import CreateTeamRequest, TeamResponse

router=APIRouter(
    prefix="/teams",
    tags=['Teams']
)

@router.post("",response_model=TeamResponse)
def create_team_api(team_data:CreateTeamRequest,
                    db:Session=Depends(get_db),
                    current_user:User=Depends(require_org_admin)):
    
    team=create_team(
        db=db,
        team_data=team_data,
        organization_id=current_user.organization_id
    )
    
    return team
