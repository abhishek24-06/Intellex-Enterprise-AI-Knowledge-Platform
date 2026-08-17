from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.database.database import SessionLocal

from app.enums.enums import (
    DocumentStatus,
    DocumentType,
    DocumentVisibility,
    UserRole,
)

from app.models.organization import Organization
from app.models.department import Department
from app.models.team import Team
from app.models.users import User
from app.models.documents import Document
from app.models.document_chunks import DocumentChunk

from app.services.retrieval.vector_search_repository import (
    VectorSearchRepository,
)


# ======================================================================
# DATABASE
# ======================================================================


@pytest.fixture
def db():

    session = SessionLocal()

    try:
        yield session

    finally:
        session.rollback()
        session.close()


@pytest.fixture
def repository():
    return VectorSearchRepository()


# ======================================================================
# USER CONTEXT
# ======================================================================


def user_context(user):

    return SimpleNamespace(
        user_id=user.user_id,
        organization_id=user.organization_id,
        department_id=user.department_id,
        team_id=user.team_id,
        role=user.role,
    )


# ======================================================================
# TEST ORGANIZATION
# ======================================================================


def create_test_user_graph(
    db,
    prefix: str,
):

    unique = uuid4().hex[:8]

    organization = Organization(
        name=f"{prefix}_org_{unique}",
        industry="TEST",
        is_active=True,
    )

    db.add(organization)
    db.flush()

    department = Department(
        organization_id=organization.organization_id,
        name=f"{prefix}_department_{unique}",
        description="ACL integration test department",
    )

    db.add(department)
    db.flush()

    team = Team(
        organization_id=organization.organization_id,
        department_id=department.department_id,
        name=f"{prefix}_team_{unique}",
        description="ACL integration test team",
        is_active=True,
    )

    db.add(team)
    db.flush()

    user = User(
        organization_id=organization.organization_id,
        department_id=department.department_id,
        team_id=team.team_id,
        name=f"{prefix}_user_{unique}",
        role=UserRole.EMPLOYEE,
        email=f"{prefix}_{unique}@acl-test.local",
        hashed_password="test-password",
        is_active=True,
    )

    db.add(user)
    db.flush()

    return organization, user


# ======================================================================
# EMBEDDED DOCUMENT
# ======================================================================


def create_embedded_document(
    db,
    organization,
    user,
    title,
):

    document = Document(
        organization_id=organization.organization_id,
        uploaded_by=user.user_id,

        document_type=DocumentType.TECHNICAL,

        visibility=DocumentVisibility.ORGANIZATION,

        title=title,
        description="ACL integration test document",

        original_filename="acl_test.txt",
        stored_filename=f"{uuid4().hex}.txt",

        status=DocumentStatus.READY,

        file_path="/acl-test/test.txt",
        file_size=100,
        mime_type="text/plain",

        processing_error=None,
        is_deleted=False,

        version=1,

        embedding_model="test",
    )

    db.add(document)
    db.flush()

    # Exact 1024-dimensional vector.
    embedding = [0.001] * 1024

    chunk = DocumentChunk(
        document_id=document.document_id,
        chunk_index=0,
        chunk_text="ACL organization isolation test chunk.",
        token_count=10,
        embedding=embedding,
        metadata_json={
            "test": True,
            "document_id": document.document_id,
        },
    )

    db.add(chunk)
    db.flush()

    return document, chunk


# ======================================================================
# TEST 1
# ======================================================================


def test_organization_visibility_allows_same_organization_user(
    db,
    repository,
):

    organization, user = create_test_user_graph(
        db,
        "same_org",
    )

    document, chunk = create_embedded_document(
        db,
        organization,
        user,
        "Same Organization Test Document",
    )

    results = repository.search(
        db=db,
        query_embedding=list(chunk.embedding),
        current_user=user_context(user),
        top_k=30,
    )

    returned_document_ids = {
        result.document_id
        for result in results
    }

    assert document.document_id in returned_document_ids


# ======================================================================
# TEST 2
# ======================================================================


def test_cross_organization_document_is_not_visible(
    db,
    repository,
):

    organization_a, user_a = create_test_user_graph(
        db,
        "org_a",
    )

    organization_b, user_b = create_test_user_graph(
        db,
        "org_b",
    )

    document_b, chunk_b = create_embedded_document(
        db,
        organization_b,
        user_b,
        "Organization B Private Test Document",
    )

    # User A searches using Organization B's exact vector.
    #
    # Therefore vector similarity strongly favors document B.
    # The only thing that should prevent its retrieval is:
    #
    # Document.organization_id == current_user.organization_id

    results = repository.search(
        db=db,
        query_embedding=list(chunk_b.embedding),
        current_user=user_context(user_a),
        top_k=30,
    )

    returned_document_ids = {
        result.document_id
        for result in results
    }

    assert document_b.document_id not in returned_document_ids