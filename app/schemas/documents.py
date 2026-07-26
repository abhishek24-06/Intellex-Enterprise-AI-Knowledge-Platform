from pydantic import BaseModel,ConfigDict, Field
from datetime import datetime
from app.enums.enums import DocumentVisibility, DocumentStatus,DocumentType,PrincipalType

class DocumentACLRequest(BaseModel):
    principal_type: PrincipalType
    principal_id: int| None=None

class CreateDocumentRequest(BaseModel):
    title:str
    description:str|None=None
    document_type:DocumentType
    visibility:DocumentVisibility
    permissions: list[DocumentACLRequest] = Field(default_factory=list)

class DocumentResponse(BaseModel):
    document_id: int
    title: str
    description: str | None
    original_filename: str
    document_type: DocumentType
    visibility: DocumentVisibility
    status: DocumentStatus
    organization_id: int
    uploaded_by: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)    

class DocumentACLResponse(BaseModel):
    principal_type: PrincipalType
    principal_id: int

    model_config=ConfigDict(from_attributes=True)

class DocumentDetailResponse(DocumentResponse):
    permissions: list[DocumentACLResponse] = Field(default_factory=list)

