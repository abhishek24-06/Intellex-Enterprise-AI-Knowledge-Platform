from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy import select

from app.database.database import SessionLocal
from app.enums.enums import (
    DocumentVisibility,
    PrincipalType,
    UserRole,
)
from app.models.document_acl import DocumentACL
from app.models.document_chunks import DocumentChunk
from app.models.documents import Document
from app.models.users import User
from app.services.retrieval.vector_search_repository import (
    VectorSearchRepository,
)


# ======================================================================
# DATABASE FIXTURE
# ======================================================================


@pytest.fixture
def db():
    """
    Real PostgreSQL / Supabase database session.

    Same database setup used by the existing integration tests.
    """

    session = SessionLocal()

    try:
        yield session

    finally:
        session.rollback()
        session.close()


# ======================================================================
# REPOSITORY
# ======================================================================


@pytest.fixture
def repository():
    return VectorSearchRepository()


# ======================================================================
# HELPERS
# ======================================================================


def make_user(
    *,
    user_id: int,
    organization_id: int,
    department_id: int | None,
    team_id: int | None,
    role: UserRole,
):
    """
    Lightweight authenticated-user object.

    VectorSearchRepository only needs these fields:

        user_id
        organization_id
        department_id
        team_id
        role
    """

    return SimpleNamespace(
        user_id=user_id,
        organization_id=organization_id,
        department_id=department_id,
        team_id=team_id,
        role=role,
    )


def get_embedded_chunk(
    db,
    document_id: int,
):
    """
    Get one real embedded chunk from a document.

    We use its existing embedding as the query vector so this
    ACL test does NOT need to load BGE-M3.
    """

    chunk = db.execute(
        select(DocumentChunk)
        .where(
            DocumentChunk.document_id == document_id,
            DocumentChunk.embedding.is_not(None),
        )
        .limit(1)
    ).scalar_one_or_none()

    return chunk


def find_restricted_document_with_acl(
    db,
    principal_type: PrincipalType,
):
    """
    Find a real restricted document that:

    1. belongs to an organization
    2. is not deleted
    3. has an embedded chunk
    4. has an ACL for the requested principal type

    Returns:

        document
        acl
        chunk
    """

    rows = db.execute(
        select(
            Document,
            DocumentACL,
        )
        .join(
            DocumentACL,
            DocumentACL.document_id
            == Document.document_id,
        )
        .where(
            Document.visibility
            == DocumentVisibility.RESTRICTED,

            Document.is_deleted.is_(False),

            DocumentACL.principal_type
            == principal_type,
        )
        .order_by(
            Document.document_id.asc()
        )
    ).all()

    for document, acl in rows:

        chunk = get_embedded_chunk(
            db,
            document.document_id,
        )

        if chunk is not None:
            return (
                document,
                acl,
                chunk,
            )

    pytest.skip(
        f"No embedded restricted document "
        f"with {principal_type.value} ACL "
        f"exists in the current database."
    )


def find_user_for_acl(
    db,
    document,
    acl,
):
    """
    Find a real user who should satisfy the ACL.
    """

    if acl.principal_type == PrincipalType.USER:

        user = db.execute(
            select(User)
            .where(
                User.user_id
                == acl.principal_id,

                User.organization_id
                == document.organization_id,
            )
        ).scalar_one_or_none()

    elif acl.principal_type == PrincipalType.TEAM:

        user = db.execute(
            select(User)
            .where(
                User.organization_id
                == document.organization_id,

                User.team_id
                == acl.principal_id,
            )
            .limit(1)
        ).scalar_one_or_none()

    elif acl.principal_type == PrincipalType.DEPARTMENT:

        user = db.execute(
            select(User)
            .where(
                User.organization_id
                == document.organization_id,

                User.department_id
                == acl.principal_id,
            )
            .limit(1)
        ).scalar_one_or_none()

    elif acl.principal_type == PrincipalType.ORG_ADMIN:

        user = db.execute(
            select(User)
            .where(
                User.organization_id
                == document.organization_id,

                User.role
                == UserRole.ORG_ADMIN,
            )
            .limit(1)
        ).scalar_one_or_none()

    else:
        user = None

    if user is None:
        pytest.skip(
            f"No real user exists for "
            f"{acl.principal_type.value} ACL "
            f"on document {document.document_id}."
        )

    return user


def make_repository_user(
    user: User,
):
    """
    Convert the real SQLAlchemy User into the minimal
    authenticated-user context required by the repository.
    """

    return make_user(
        user_id=user.user_id,
        organization_id=user.organization_id,
        department_id=user.department_id,
        team_id=user.team_id,
        role=user.role,
    )


def find_unauthorized_user(
    db,
    document,
    acl,
):
    """
    Find a real user in the same organization who does NOT
    satisfy the target ACL.

    This is intentionally conservative.

    If we cannot safely identify such a user, the test is skipped
    rather than making an unsafe assumption.
    """

    # --------------------------------------------------------------
    # User ACL
    # --------------------------------------------------------------

    if acl.principal_type == PrincipalType.USER:

        user = db.execute(
            select(User)
            .where(
                User.organization_id
                == document.organization_id,

                User.user_id
                != acl.principal_id,
            )
            .limit(20)
        ).scalars().all()

        for candidate in user:

            if (
                candidate.team_id
                != acl.principal_id
                and candidate.department_id
                != acl.principal_id
            ):
                return candidate

    # --------------------------------------------------------------
    # Team ACL
    # --------------------------------------------------------------

    elif acl.principal_type == PrincipalType.TEAM:

        candidates = db.execute(
            select(User)
            .where(
                User.organization_id
                == document.organization_id,

                User.team_id
                != acl.principal_id,
            )
            .limit(20)
        ).scalars().all()

        for candidate in candidates:

            return candidate

    # --------------------------------------------------------------
    # Department ACL
    # --------------------------------------------------------------

    elif acl.principal_type == PrincipalType.DEPARTMENT:

        candidates = db.execute(
            select(User)
            .where(
                User.organization_id
                == document.organization_id,

                User.department_id
                != acl.principal_id,
            )
            .limit(20)
        ).scalars().all()

        for candidate in candidates:

            return candidate

    # --------------------------------------------------------------
    # ORG_ADMIN ACL
    # --------------------------------------------------------------

    elif acl.principal_type == PrincipalType.ORG_ADMIN:

        candidates = db.execute(
            select(User)
            .where(
                User.organization_id
                == document.organization_id,

                User.role
                != UserRole.ORG_ADMIN,
            )
            .limit(1)
        ).scalars().all()

        if candidates:
            return candidates[0]

    pytest.skip(
        f"Could not safely find an unauthorized "
        f"user for document {document.document_id}."
    )


# ======================================================================
# ORGANIZATION VISIBILITY
# ======================================================================


def test_organization_visibility_allows_same_organization_user(
    db,
    repository,
):
    """
    ORGANIZATION documents are accessible to users
    belonging to the same organization.
    """

    # --------------------------------------------------------------
    # Find real organization-visible embedded document
    # --------------------------------------------------------------

    document = db.execute(
        select(Document)
        .where(
            Document.visibility
            == DocumentVisibility.ORGANIZATION,

            Document.is_deleted.is_(False),
        )
        .order_by(
            Document.document_id.asc()
        )
    ).scalars().first()

    if document is None:
        pytest.skip(
            "No organization-visible document exists."
        )

    chunk = get_embedded_chunk(
        db,
        document.document_id,
    )

    if chunk is None:
        pytest.skip(
            "Organization-visible document has "
            "no embedded chunks."
        )

    # --------------------------------------------------------------
    # Find same-organization user
    # --------------------------------------------------------------

    user = db.execute(
        select(User)
        .where(
            User.organization_id
            == document.organization_id
        )
        .limit(1)
    ).scalar_one_or_none()

    if user is None:
        pytest.skip(
            "No user exists in the document organization."
        )

    current_user = make_repository_user(
        user
    )

    # --------------------------------------------------------------
    # Search using the document's own embedding
    # --------------------------------------------------------------

    results = repository.search(
        db=db,
        query_embedding=list(
            chunk.embedding
        ),
        current_user=current_user,
        top_k=30,
    )

    returned_document_ids = {
        result.document_id
        for result in results
    }

    assert document.document_id in (
        returned_document_ids
    )


# ======================================================================
# CROSS ORGANIZATION ISOLATION
# ======================================================================


def test_cross_organization_document_is_not_visible(
    db,
    repository,
):
    """
    A document from another organization must NEVER
    be returned, even if the user otherwise has matching
    identifiers.
    """

    document = db.execute(
        select(Document)
        .where(
            Document.is_deleted.is_(False)
        )
        .order_by(
            Document.document_id.asc()
        )
    ).scalars().first()

    if document is None:
        pytest.skip(
            "No documents exist."
        )

    chunk = get_embedded_chunk(
        db,
        document.document_id,
    )

    if chunk is None:
        pytest.skip(
            "No embedded document exists."
        )

    # --------------------------------------------------------------
    # Find user from another organization
    # --------------------------------------------------------------

    other_user = db.execute(
        select(User)
        .where(
            User.organization_id
            != document.organization_id
        )
        .limit(1)
    ).scalar_one_or_none()

    if other_user is None:
        pytest.skip(
            "No user from another organization exists."
        )

    current_user = make_repository_user(
        other_user
    )

    # --------------------------------------------------------------
    # Search
    # --------------------------------------------------------------

    results = repository.search(
        db=db,
        query_embedding=list(
            chunk.embedding
        ),
        current_user=current_user,
        top_k=30,
    )

    returned_document_ids = {
        result.document_id
        for result in results
    }

    # --------------------------------------------------------------
    # SECURITY ASSERTION
    # --------------------------------------------------------------

    assert document.document_id not in (
        returned_document_ids
    )


# ======================================================================
# USER ACL
# ======================================================================


def test_user_acl_allows_authorized_user(
    db,
    repository,
):
    """
    USER ACL grants access to the specified user.
    """

    document, acl, chunk = (
        find_restricted_document_with_acl(
            db,
            PrincipalType.USER,
        )
    )

    user = find_user_for_acl(
        db,
        document,
        acl,
    )

    current_user = make_repository_user(
        user
    )

    results = repository.search(
        db=db,
        query_embedding=list(
            chunk.embedding
        ),
        current_user=current_user,
        top_k=30,
    )

    returned_document_ids = {
        result.document_id
        for result in results
    }

    assert document.document_id in (
        returned_document_ids
    )


# ======================================================================
# TEAM ACL
# ======================================================================


def test_team_acl_allows_authorized_team_member(
    db,
    repository,
):
    """
    TEAM ACL grants access to users belonging
    to the specified team.
    """

    document, acl, chunk = (
        find_restricted_document_with_acl(
            db,
            PrincipalType.TEAM,
        )
    )

    user = find_user_for_acl(
        db,
        document,
        acl,
    )

    current_user = make_repository_user(
        user
    )

    results = repository.search(
        db=db,
        query_embedding=list(
            chunk.embedding
        ),
        current_user=current_user,
        top_k=30,
    )

    returned_document_ids = {
        result.document_id
        for result in results
    }

    assert document.document_id in (
        returned_document_ids
    )


# ======================================================================
# DEPARTMENT ACL
# ======================================================================


def test_department_acl_allows_authorized_department_member(
    db,
    repository,
):
    """
    DEPARTMENT ACL grants access to users belonging
    to the specified department.
    """

    document, acl, chunk = (
        find_restricted_document_with_acl(
            db,
            PrincipalType.DEPARTMENT,
        )
    )

    user = find_user_for_acl(
        db,
        document,
        acl,
    )

    current_user = make_repository_user(
        user
    )

    results = repository.search(
        db=db,
        query_embedding=list(
            chunk.embedding
        ),
        current_user=current_user,
        top_k=30,
    )

    returned_document_ids = {
        result.document_id
        for result in results
    }

    assert document.document_id in (
        returned_document_ids
    )


# ======================================================================
# UNAUTHORIZED RESTRICTED DOCUMENT
# ======================================================================


def test_unauthorized_user_cannot_retrieve_restricted_document(
    db,
    repository,
):
    """
    A restricted document must not be returned to a user
    who does not satisfy its ACL.
    """

    # --------------------------------------------------------------
    # Find a restricted document with an ACL
    # --------------------------------------------------------------

    rows = db.execute(
        select(
            Document,
            DocumentACL,
        )
        .join(
            DocumentACL,
            DocumentACL.document_id
            == Document.document_id,
        )
        .where(
            Document.visibility
            == DocumentVisibility.RESTRICTED,

            Document.is_deleted.is_(False),
        )
        .order_by(
            Document.document_id.asc()
        )
    ).all()

    if not rows:
        pytest.skip(
            "No restricted documents with ACLs exist."
        )

    for document, acl in rows:

        chunk = get_embedded_chunk(
            db,
            document.document_id,
        )

        if chunk is None:
            continue

        # ----------------------------------------------------------
        # Find user who should NOT have access
        # ----------------------------------------------------------

        try:

            unauthorized_user = (
                find_unauthorized_user(
                    db,
                    document,
                    acl,
                )
            )

        except pytest.skip.Exception:

            continue

        current_user = make_repository_user(
            unauthorized_user
        )

        # ----------------------------------------------------------
        # Search
        # ----------------------------------------------------------

        results = repository.search(
            db=db,
            query_embedding=list(
                chunk.embedding
            ),
            current_user=current_user,
            top_k=30,
        )

        returned_document_ids = {
            result.document_id
            for result in results
        }

        # ----------------------------------------------------------
        # SECURITY ASSERTION
        # ----------------------------------------------------------

        assert document.document_id not in (
            returned_document_ids
        )

        return

    pytest.skip(
        "Could not find a suitable unauthorized "
        "user/document combination."
    )
    