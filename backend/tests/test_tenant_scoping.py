"""DB-enforced tenant-isolation invariants (SCRUM-19 AC: "one organization's
connections and ingested data are never visible to another").

True cross-tenant *query* isolation is enforced by Postgres RLS (migration
0008), which cannot run against SQLite -- these tests instead prove the
piece SQLite *can* enforce: uniqueness is scoped per-organization, not
global, so two organizations legitimately re-using the same identifiers
(e.g. both naming a Jira project "SCRUM") do not collide. `security`
should add an RLS-specific negative test against a real Postgres instance
(a session with org A's `app.current_org_id` must get zero rows for org
B's data even with a matching WHERE-less SELECT) -- see
docs/db/schema.md "Reconciliation".
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Organization, Project


def _org(session, slug: str) -> Organization:
    org = Organization(slug=slug, name=slug.title())
    session.add(org)
    session.commit()
    return org


def test_same_project_key_allowed_across_organizations(session):
    org_a = _org(session, "org-a")
    org_b = _org(session, "org-b")

    session.add(Project(organization_id=org_a.id, key="SCRUM", name="Org A's SCRUM"))
    session.add(Project(organization_id=org_b.id, key="SCRUM", name="Org B's SCRUM"))
    session.commit()  # must not raise -- CHANGED from PR #1's global-unique key

    keys = {p.organization_id: p.key for p in session.query(Project).all()}
    assert keys == {org_a.id: "SCRUM", org_b.id: "SCRUM"}


def test_duplicate_project_key_within_same_organization_rejected(session):
    org = _org(session, "org-c")

    session.add(Project(organization_id=org.id, key="SCRUM", name="First"))
    session.commit()
    session.add(Project(organization_id=org.id, key="SCRUM", name="Duplicate"))
    with pytest.raises(IntegrityError):
        session.commit()
