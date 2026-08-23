from types import SimpleNamespace

from app.enums.enums import UserRole

from app.services.observability import (
    agent_execution_queries,
)


def make_user(
    *,
    role=UserRole.ORG_ADMIN,
    organization_id=2,
):

    return SimpleNamespace(
        user_id=9,
        organization_id=organization_id,
        role=role,
    )


def test_org_admin_query_is_scoped_to_organization(
    monkeypatch,
):

    captured = {}

    class DummyResult:

        def scalars(self):
            return self

        def all(self):
            return []

    class DummyDB:

        def execute(self, stmt):

            captured["statement"] = stmt

            return DummyResult()

    agent_execution_queries.get_chat_execution_trace(
        db=DummyDB(),
        chat_id=100,
        current_user=make_user(
            role=UserRole.ORG_ADMIN,
            organization_id=2,
        ),
    )

    sql_text = str(
        captured["statement"]
    )

    assert "organization_id" in sql_text


def test_super_admin_does_not_need_org_scope(
    monkeypatch,
):

    captured = {}

    class DummyResult:

        def scalars(self):
            return self

        def all(self):
            return []

    class DummyDB:

        def execute(self, stmt):

            captured["statement"] = stmt

            return DummyResult()

    agent_execution_queries.get_chat_execution_trace(
        db=DummyDB(),
        chat_id=100,
        current_user=make_user(
            role=UserRole.SUPER_ADMIN,
            organization_id=999,
        ),
    )

    # Basic sanity check that the query was built.
    assert "agent_execution" in str(
        captured["statement"]
    )