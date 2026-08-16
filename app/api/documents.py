from fastapi import APIRouter,Depends,UploadFile,File,Form
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.database.database import get_db
from app.dependencies.roles import require_org_admin
from app.models.users import User
from app.services.document_processing_service import DocumentProcessingService
from app.services.document_services import create_document, delete_document, get_document
from app.schemas.documents import DocumentResponse,CreateDocumentRequest
from app.services.document_services import get_documents_by_organization
from app.services.ingestion.ingestion_dependencies import build_document_ingestion_pipeline

router=APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

@router.post("/upload",response_model=DocumentResponse)
def upload_document(metadata:str=Form(...),
                    file:UploadFile=File(...),
                    db:Session=Depends(get_db),
                    current_user:User=Depends(require_org_admin)
                    )-> DocumentResponse:
    
    try:
        document_data=CreateDocumentRequest.model_validate_json(metadata)

    except ValidationError as e:
        raise ValueError(str(e))
    
    document = create_document(db=db,
                    document_data=document_data,
                    organization_id=current_user.organization_id,
                    uploaded_by=current_user.user_id,
                    file=file
                    )

    pipeline = (
        build_document_ingestion_pipeline()
    )

    processing_service = (
        DocumentProcessingService(
            ingestion_pipeline=pipeline
        )
    )

    processing_service.process(
        db=db,
        document=document,
    )

    return document

    

@router.get("/",response_model=list[DocumentResponse])
def get_documents_api(db:Session=Depends(get_db),
                      current_user:User=Depends(require_org_admin))-> DocumentResponse:

    return get_documents_by_organization(db=db,
                                         organization_id=current_user.organization_id)

@router.get("/{document_id}",response_model=DocumentResponse)
def get_document_api(document_id:int,
                     db:Session=Depends(get_db),
                     current_user:User=Depends(require_org_admin))-> DocumentResponse:

    return get_document(db=db,
                        document_id=document_id,
                        organization_id=current_user.organization_id)

@router.delete("/{document_id}",response_model=DocumentResponse)
def delete_document_api(document_id:int,
                        db:Session=Depends(get_db),
                        current_user:User=Depends(require_org_admin))-> DocumentResponse:

    return delete_document(db=db,
                           document_id=document_id,
                           organization_id=current_user.organization_id)
