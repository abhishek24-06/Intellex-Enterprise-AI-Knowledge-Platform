from sqlalchemy.orm import Session, joinedload
from fastapi import UploadFile
from sqlalchemy import and_, or_, select
from pathlib import Path
import uuid,shutil
import magic

from app.models.document_acl import DocumentACL
from app.models.documents import Document
from app.models.users import User
from app.schemas.documents import CreateDocumentRequest,DocumentACLRequest
from app.enums.enums import DocumentVisibility,DocumentStatus,PrincipalType, UserRole
from app.services.user_service import get_user_by_id
from app.services.team_service import get_team_by_id
from app.services.department_service import get_department_by_id

MAX_FILE_SIZE=50*1024*1024
##ALLOWED FILE TYPES
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/markdown",
}

EXPECTED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".md": "text/markdown",
}

ALLOWED_DETECTED_MIME_TYPES = {
    ".pdf": {
        "application/pdf",
    },
    ".txt": {
        "text/plain",
    },
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    ".md": {
        "text/plain",
        "text/markdown",
    },
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

def validate_file(file:UploadFile)->str:

    if not file.filename :
        raise ValueError("Invalid file")
    
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported file type: {file.content_type}")

    extension=Path(file.filename).suffix.lower()

    if extension not in EXPECTED_MIME_TYPES:
        raise ValueError(f"Unsupported file extension: {extension}")

    file.file.seek(0) #Resets the file cursor to the absolute beginning (position 0) 

    detected_mime=magic.from_buffer(file.file.read(4096),
                               mime=True)

    file.file.seek(0)

    if detected_mime not in ALLOWED_MIME_TYPES :
        raise ValueError(f"Invalid file content: {detected_mime}")

    allowed_detected_mimes = (
    ALLOWED_DETECTED_MIME_TYPES[extension])

    if detected_mime not in allowed_detected_mimes:
        raise ValueError(
            "File extension does not match actual file content."
    )
    return EXPECTED_MIME_TYPES[extension]

def create_document(db:Session,
                    document_data:CreateDocumentRequest,
                    organization_id:int,
                    uploaded_by:int,
                    file:UploadFile)->Document:

    if document_data.visibility == DocumentVisibility.ORGANIZATION and document_data.permissions:
        raise ValueError("Organization documents cannot have permissions.")

    if document_data.visibility == DocumentVisibility.RESTRICTED and not document_data.permissions:
        raise ValueError("Restricted documents require at least one permission.")

    verified_mime=validate_file(file)
    
    #Calculate file size 
    file.file.seek(0,2)
    file_size=file.file.tell()
    file.file.seek(0)


    if file_size > MAX_FILE_SIZE:
        raise ValueError("File size exceeds 50 MB.")

    #Generate Storage Filename
    extension=Path(file.filename).suffix.lower()

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
                          mime_type=verified_mime,
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
        document.status=DocumentStatus.PROCESSING
    
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

def has_document_access(document:Document,current_user:User)->bool :

    if document.organization_id != current_user.organization_id:
        return False

    if document.visibility == DocumentVisibility.ORGANIZATION:
        return True

    for permission in document.acl_entries:

        if(permission.principal_type == PrincipalType.USER and
           permission.principal_id == current_user.user_id):  

           return True

        if(permission.principal_type == PrincipalType.TEAM and
           permission.principal_id == current_user.team_id):

            return True

        if(permission.principal_type == PrincipalType.DEPARTMENT and
           permission.principal_id == current_user.department_id):

            return True

        if(permission.principal_type == PrincipalType.ORG_ADMIN and
           current_user.role == UserRole.ORG_ADMIN):

            return True

    return False        

def get_accessible_document(db:Session,document_id:int,current_user:User):

    stmt = select(Document).options(joinedload(Document.acl_entries)).where(
        Document.document_id==document_id,
        Document.is_deleted==False
    )

    document=db.execute(stmt).unique().scalar_one_or_none()

    if document is None:
        raise ValueError("Document not found")

    if not has_document_access(document,current_user):
        raise ValueError("Access denied")

    return document
    
def get_all_accessible_documents(db:Session,current_user:User)->list[DocumentACL]:

    acl_conditions=[
        and_(
            DocumentACL.principal_type==PrincipalType.USER,
            DocumentACL.principal_id==current_user.user_id
        ),
        and_(
            DocumentACL.principal_type == PrincipalType.TEAM,
            DocumentACL.principal_id == current_user.team_id,
        ),
        and_(
            DocumentACL.principal_type == PrincipalType.DEPARTMENT,
            DocumentACL.principal_id == current_user.department_id,
        ),
    ]

    if current_user.role == UserRole.ORG_ADMIN:
        acl_conditions.append(
            and_(
                DocumentACL.principal_type == PrincipalType.ORG_ADMIN,
            )
        )

    stmt = (
        select(Document)
        .outerjoin(DocumentACL)
        .where(
            Document.organization_id == current_user.organization_id,
            Document.is_deleted == False,
            or_(
                Document.visibility == DocumentVisibility.ORGANIZATION,
                *acl_conditions,
            ),
        )
        .order_by(Document.uploaded_at.desc())
    )

    return db.execute(stmt).unique().scalars().all()

