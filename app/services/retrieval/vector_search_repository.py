from sqlalchemy import and_, or_, select,exists
from sqlalchemy.orm import Session

from app.models.document_chunks import DocumentChunk
from app.models.documents import Document
from app.models.document_acl import DocumentACL
from app.models.users import User
from app.enums.enums import DocumentVisibility,PrincipalType,UserRole
from app.dto.retrieved_chunk import RetrievedChunk

class VectorSearchRepository:
    """
    Ensure ACL-aware pgvector similarity search.
    """
    def search(self,db:Session,query_embedding:list[float],current_user:User,top_k:int=30)->list[RetrievedChunk]:

        if not query_embedding:
            raise ValueError("Query embedding cannot be empty.")

        if len(query_embedding) != 1024:
            raise ValueError("Query embedding must 1024 dimensions.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

    #Check ACL exists conditions

        user_acl = exists(
            select(1)
            .select_from(DocumentACL)
            .where(
                    DocumentACL.document_id == Document.document_id,
                    DocumentACL.principal_type == PrincipalType.USER,
                    DocumentACL.principal_id == current_user.user_id,
                ))

        team_acl = exists(
            select(1)
            .select_from(DocumentACL)
            .where(
                DocumentACL.document_id == Document.document_id,
                DocumentACL.principal_type == PrincipalType.TEAM,
                DocumentACL.principal_id == current_user.team_id,
            )
        )

        department_acl = exists(
            select(1)
            .select_from(DocumentACL)
            .where(
                DocumentACL.document_id == Document.document_id,
                DocumentACL.principal_type == PrincipalType.DEPARTMENT,
                DocumentACL.principal_id == current_user.department_id,
            )
        )

        authorization_conditions = [
            Document.visibility == DocumentVisibility.ORGANIZATION,

            user_acl,

            team_acl,

            department_acl,
        ]

        if current_user.role == UserRole.ORG_ADMIN:

            admin_acl = exists(
                select(1)
                .select_from(DocumentACL)
                .where(
                    DocumentACL.document_id== Document.document_id,
                    DocumentACL.principal_type== PrincipalType.ORG_ADMIN,
                )
            )

            authorization_conditions.append(admin_acl)

        cosine_distance = (DocumentChunk.embedding.cosine_distance(query_embedding))

        vector_score = (1.0 - cosine_distance)  #cosine simi = 1 - cosine distance

        stmt = (
            select(
                DocumentChunk,
                Document.original_filename,
                vector_score.label("vector_score"),
            )
            .join(
                Document,
                Document.document_id == DocumentChunk.document_id,
            )
            .where(
                # Organization isolation
                Document.organization_id == current_user.organization_id,
        
                # Ignore deleted documents
                Document.is_deleted.is_(False),
        
                # Only embedded chunks
                DocumentChunk.embedding.is_not(None),
        
                # Authorization
                or_(
                    *authorization_conditions
                ),
            )
            .order_by(
                cosine_distance.asc()
            )
            .limit(top_k)
        )            
        
        rows = (
            db.execute(stmt)
            .all()
        )
        results: list[RetrievedChunk] = []
        for chunk, original_filename , score in rows:
            results.append(
                RetrievedChunk(
                    document_id=chunk.document_id,
                    original_filename=original_filename,
                    chunk_id=chunk.chunk_id,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    token_count=chunk.token_count,
                    metadata=chunk.metadata_json,
                    vector_score=float(score),
                )    
            )
        return results
                
    