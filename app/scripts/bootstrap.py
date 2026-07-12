from app.database.database import SessionLocal

from app.enums.enums import UserRole
from dotenv import load_dotenv
import os
from app.services.user_service import create_user,get_user_by_email

load_dotenv()

def bootstrap():

    db=SessionLocal()

    try:
        admin = get_user_by_email(
            db=db,
            email=os.getenv("SUPER_ADMIN_EMAIL")
            )        
           
        if admin is None: 
            admin = create_user(
                db=db,
                name=os.getenv("SUPER_ADMIN_NAME"),
                email=os.getenv("SUPER_ADMIN_EMAIL"),
                password=os.getenv("SUPER_ADMIN_PASSWORD"),
                role=UserRole.SUPER_ADMIN,
                organization_id=None,
                department_id=None,
                team_id=None
            )
        db.commit()
        
        print("\n===================================")
        print("Intellex Bootstrapped Successfully")
        print("===================================")
        
        
        print("\n Super Admin Credentials")
        print(f"Email    : {admin.email}")
        print(f"Password : {os.getenv('SUPER_ADMIN_PASSWORD')}")

    finally:
        db.close()

if __name__ == "__main__":
    bootstrap()
