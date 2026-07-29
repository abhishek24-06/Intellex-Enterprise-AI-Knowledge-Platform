from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session 

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.schemas.documents import DocumentResponse
from app.services.document_services import get_accessible_document,get_all_accessible_documents

router=APIRouter(prefix="/my_documents",
                 tags=["My Documents"])

@router.get("/{document_id}")
def get_my_document_api(document_id:int,
                        db:Session=Depends(get_db),
                        current_user:User=Depends(get_current_user)):
 
    document=get_accessible_document(db=db,
                                     document_id=document_id,
                                    current_user=current_user)

    return document

@router.get("/",response_model=list[DocumentResponse])
def get_all_my_document_api(db:Session=Depends(get_db),
                            current_user:User=Depends(get_current_user)):

    document=get_all_accessible_documents(db=db,
                                          current_user=current_user)

    return document
