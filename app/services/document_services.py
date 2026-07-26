from sqlalchemy.orm import Session
from fastapi import UploadFile
from sqlalchemy import select
from pathlib import Path
import uuid,shutil

from app.models.document_acl import DocumentACL
from app.models.documents import Document
from app.schemas.documents import CreateDocumentRequest,DocumentACLRequest
from app.enums.enums import DocumentVisibility,DocumentStatus,PrincipalType
from app.services.user_service import get_user_by_id
from app.services.team_service import get_team_by_id
from app.services.department_service import get_department_by_id

##ALLOWED FILE TYPES
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/markdown",
}

def get_document_by_id(db:Session,document_id:int)->Document|None:

    stmt=(select(Document).where(Document.document_id==document_id,Document.is_deleted==False))

    return db.execute(stmt).scalar_one_or_none()

def get_document(db:Session,document_id:int,organization_id:int)->Document:

    document = get_document_by_id(db=db,document_id=document_id)

    if document is None:
        raise ValueError("Document not found.")

    if document.organization_id != organization_id:
        raise ValueError("Access denied.")

    return document
    
def get_documents_by_organization(db:Session,organization_id:int)->list[Document]:

    stmt=(select(Document).where(Document.organization_id==organization_id,Document.is_deleted == False)).order_by(Document.uploaded_at.desc())

    return db.execute(stmt).scalars().all()

def validate_file(file:UploadFile)->None:

    if not file.filename :
        raise ValueError("Invalid file")
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported file type: {file.content_type}")
    
def create_document(db:Session,
                    document_data:CreateDocumentRequest,
                    organization_id:int,
                    uploaded_by:int,
                    file:UploadFile)->Document:

    if document_data.visibility == DocumentVisibility.ORGANIZATION and document_data.permissions:
        raise ValueError("Organization documents cannot have permissions.")

    if document_data.visibility == DocumentVisibility.RESTRICTED and not document_data.permissions:
        raise ValueError("Restricted documents require at least one permission.")

    validate_file(file)
    
    #Calculate file size 
    file.file.seek(0,2)
    file_size=file.file.tell()
    file.file.seek(0)

    MAX_FILE_SIZE=25*1024*1024

    if file_size > MAX_FILE_SIZE:
        raise ValueError("File size exceeds 25 MB.")

    #Generate Storage Filename
    extension=Path(file.filename).suffix

    stored_filename=f"{uuid.uuid4()}{extension}"

    #Create Storage Folder
    folder=Path("storage")/"organizations"/str(organization_id)

    folder.mkdir(parents=True,#create the whole chain.
                 exist_ok=True)#don't crash if the folder is already there.

    #Save File
    file_path=folder/stored_filename

    try:
        #Save file to storage 
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file,buffer)

        #Create Document
        document=Document(organization_id=organization_id,
                          uploaded_by=uploaded_by,
                          title=document_data.title,
                          description=document_data.description,
                          document_type=document_data.document_type,
                          visibility=document_data.visibility,
                          original_filename=file.filename,
                          stored_filename=stored_filename,
                          file_path=str(file_path),
                          file_size=file_size,
                          mime_type=file.content_type or "application/octet-stream",
                          status=DocumentStatus.UPLOADING
        )
    
        db.add(document)
        db.flush()
    
        if document.visibility == DocumentVisibility.RESTRICTED:

            validate_acl_permissions(
                db=db,
                permissions=document_data.permissions,
                organization_id=organization_id
            )
        
            for permission in document_data.permissions:
        
                acl = DocumentACL(
                    document_id=document.document_id,
                    principal_type=permission.principal_type,
                    principal_id=permission.principal_id,
                )

                db.add(acl)
    
        #Update status
        document.status=DocumentStatus.READY
    
        db.commit()
        db.refresh(document)
    
        return document

    except Exception:

        db.rollback()

        if file_path.exists():
            file_path.unlink()

        raise
        
def validate_acl_permissions(db:Session,
                             permissions:list[DocumentACLRequest],
                             organization_id:int):

    for permission in permissions:

        if permission.principal_type == PrincipalType.USER:

            user=get_user_by_id(db=db,id=permission.principal_id)

            if user is None:
                raise ValueError("User not found")

            if user.organization_id != organization_id:
                raise ValueError("User does not belong to this organization.")

        elif permission.principal_type == PrincipalType.TEAM:

            team=get_team_by_id(db=db,team_id=permission.principal_id)

            if team is None:
                raise ValueError("Team not found.")

            if team.department.organization_id != organization_id:
                raise ValueError("Team does not belong to this organization.")

        elif permission.principal_type == PrincipalType.DEPARTMENT:
           
            department=get_department_by_id(db=db,department_id=permission.principal_id)

            if department is None:
                raise ValueError("Department not found.")

            if department.organization_id != organization_id:
                raise ValueError("Department does not belong to this organization.")

        elif permission.principal_type == PrincipalType.ORG_ADMIN:
            if permission.principal_id is not None:
                raise ValueError("ORG_ADMIN should not have a principal_id.")

def delete_document(db:Session,document_id:int,organization_id)->Document:

    document=get_document(db=db,document_id=document_id,organization_id=organization_id)

    if document.is_deleted:
        raise ValueError("Document already deleted")

    document.is_deleted=True

    db.commit()
    db.refresh(document)

    return document 

