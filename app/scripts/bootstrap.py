from app.database.database import SessionLocal

from app.enums.enums import UserRole
from dotenv import load_dotenv
import os
from app.services.user_service import create_user,get_user_by_email
import app.models

from app.services.organization_service import create_organization

load_dotenv()

def bootstrap():

    db=SessionLocal()

    try:
        organization=create_organization(
            db=db,
            name=os.getenv("ORGANIZATION_NAME"),
            industry=os.getenv("INDUSTRY")
        )

        admin = get_user_by_email(
            db=db,
            email=os.getenv("ADMIN_EMAIL")
            )        
           
        if admin is None: 
            admin = create_user(
                db=db,
                name=os.getenv("ADMIN_NAME"),
                email=os.getenv("ADMIN_EMAIL"),
                password=os.getenv("ADMIN_PASSWORD"),
                role=UserRole.ORG_ADMIN,
                organization_id=organization.organization_id,
                department_id=None,
                team_id=None
            )
            
        print("\n===================================")
        print("Intellex Bootstrapped Successfully")
        print("===================================")
        
        print(f"Organization : {organization.name}")
        
        print("\nAdmin Credentials")
        print(f"Email    : {admin.email}")
        print(f"Password : {os.getenv('ADMIN_PASSWORD')}")

    finally:
        db.close()

if __name__ == "__main__":
    bootstrap()
