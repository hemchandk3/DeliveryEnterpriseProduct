"""Constraint-level tests for the new MVP governance tables: roles/RBAC
(SCRUM-14), actions/approvals (SCRUM-12/13), and connections (SCRUM-19).

SQLite enforces CHECK constraints natively (unlike foreign keys, which
need `PRAGMA foreign_keys=ON` -- not set by the shared `session` fixture,
see tests/conftest.py), so the negative cases below exercise the real DB
constraint, not just application logic.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Action, Approval, Connection, Organization, Project, Role, User, UserRole


def _org(session) -> Organization:
    org = Organization(slug="acme", name="Acme")
    session.add(org)
    session.commit()
    return org


def _project(session, org: Organization) -> Project:
    project = Project(organization_id=org.id, key="SCRUM", name="Acme Delivery")
    session.add(project)
    session.commit()
    return project


# ---------------------------------------------------------------- roles ---


def test_user_can_be_granted_a_role(session):
    org = _org(session)
    role = Role(name="approver")
    user = User(
        organization_id=org.id,
        email="pm@acme.example",
        display_name="PM Approver",
        hashed_password="not-a-real-hash",
    )
    session.add_all([role, user])
    session.commit()

    session.add(UserRole(user_id=user.id, role_id=role.id))
    session.commit()

    stored = session.query(User).one()
    assert [ur.role_id for ur in stored.roles] == [role.id]


def test_duplicate_email_within_organization_rejected(session):
    org = _org(session)
    session.add(
        User(
            organization_id=org.id,
            email="dup@acme.example",
            display_name="First",
            hashed_password="hash-a",
        )
    )
    session.commit()
    session.add(
        User(
            organization_id=org.id,
            email="dup@acme.example",
            display_name="Second",
            hashed_password="hash-b",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


# ------------------------------------------------------------- actions ---


def _action(session, org: Organization, project: Project) -> Action:
    action = Action(
        organization_id=org.id,
        project_id=project.id,
        agent_name="governance-agent-v1",
        operation="jira.transition_issue",
        target_ref="SCRUM-42",
        proposed_steps=[{"op": "transition", "to": "In Review"}],
        evidence_signal_ids=[101, 102],
    )
    session.add(action)
    session.commit()
    return action


def test_action_defaults_to_pending_approval(session):
    org = _org(session)
    project = _project(session, org)

    action = _action(session, org, project)

    assert action.status == "PENDING_APPROVAL"


def test_action_status_outside_allowed_set_rejected(session):
    org = _org(session)
    project = _project(session, org)

    session.add(
        Action(
            organization_id=org.id,
            project_id=project.id,
            agent_name="governance-agent-v1",
            operation="jira.transition_issue",
            target_ref="SCRUM-42",
            status="MADE_UP_STATUS",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_approval_requires_reason_when_rejected(session):
    org = _org(session)
    project = _project(session, org)
    action = _action(session, org, project)

    session.add(
        Approval(
            organization_id=org.id,
            action_id=action.id,
            approver_label="pm-approver@acme.example",
            decision="REJECTED",
            reason=None,
            original_steps=action.proposed_steps,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_approval_records_original_and_edited_steps(session):
    org = _org(session)
    project = _project(session, org)
    action = _action(session, org, project)

    approval = Approval(
        organization_id=org.id,
        action_id=action.id,
        approver_label="pm-approver@acme.example",
        decision="APPROVED",
        original_steps=action.proposed_steps,
        edited_steps=[{"op": "transition", "to": "Done"}],
        decided_at=datetime(2026, 7, 27, tzinfo=UTC),
    )
    session.add(approval)
    session.commit()

    stored = session.query(Approval).one()
    assert stored.original_steps == [{"op": "transition", "to": "In Review"}]
    assert stored.edited_steps == [{"op": "transition", "to": "Done"}]
    assert stored.approver_id is None  # identity carried via approver_label, not FK-only


# --------------------------------------------------------- connections ---


def test_connection_credential_ref_is_stored_not_a_secret_value(session):
    org = _org(session)
    connection = Connection(
        organization_id=org.id,
        source_type="github",
        instance_url="https://github.com",
        target_ref="hemchandk3/DeliveryEnterpriseProduct",
        credential_ref="secretsmanager://acme/github-connection-1",
        status="active",
    )
    session.add(connection)
    session.commit()

    stored = session.query(Connection).one()
    assert stored.credential_ref.startswith("secretsmanager://")
    assert stored.status == "active"


def test_connection_source_type_outside_allowed_set_rejected(session):
    org = _org(session)
    session.add(
        Connection(
            organization_id=org.id,
            source_type="slack",  # not github/jira
            instance_url="https://slack.example",
            target_ref="whatever",
            credential_ref="secretsmanager://acme/x",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_duplicate_connection_identity_within_org_rejected(session):
    org = _org(session)
    kwargs = {
        "organization_id": org.id,
        "source_type": "github",
        "instance_url": "https://github.com",
        "target_ref": "hemchandk3/DeliveryEnterpriseProduct",
    }
    session.add(Connection(credential_ref="secretsmanager://acme/1", **kwargs))
    session.commit()
    session.add(Connection(credential_ref="secretsmanager://acme/2", **kwargs))
    with pytest.raises(IntegrityError):
        session.commit()
