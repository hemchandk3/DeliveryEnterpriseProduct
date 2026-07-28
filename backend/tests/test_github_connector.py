from app.connectors.github import GitHubConnector
from tests.fakes import FakeGitHubGateway


def test_fetch_normalizes_prs_and_commits():
    gateway = FakeGitHubGateway(
        pulls=[
            {
                "number": 42,
                "title": "Add login",
                "state": "open",
                "user": {"login": "alice"},
                "created_at": "2026-07-01T10:00:00Z",
                "updated_at": "2026-07-02T10:00:00Z",
                "draft": False,
                "base": {"ref": "main"},
            }
        ],
        commits=[
            {
                "sha": "abc123",
                "author": {"login": "bob"},
                "commit": {
                    "message": "Fix bug\n\ndetails",
                    "author": {"date": "2026-07-01T09:00:00Z"},
                },
            }
        ],
    )

    signals = GitHubConnector(gateway).fetch("hemchandk3/DeliveryEnterpriseProduct")

    assert len(signals) == 2
    pr = next(s for s in signals if s.kind == "pr")
    assert pr.external_id == "42"
    assert pr.actor == "alice"
    assert pr.state == "open"
    commit = next(s for s in signals if s.kind == "commit")
    assert commit.external_id == "abc123"
    assert commit.title == "Fix bug"


def test_fetch_enriches_pr_meta_with_base_ref_reviewers_and_reviews():
    """Fold-in: Workstream #0 §5.2 evidence extension.

    PR #47 in the curated demo dataset is the review-starvation signal:
    open against release/1.4, a reviewer requested, zero approved reviews.
    """
    gateway = FakeGitHubGateway(
        pulls=[
            {
                "number": 47,
                "title": "SCRUM-42: payment retry on transient gateway failure",
                "state": "open",
                "draft": False,
                "user": {"login": "priya-nair"},
                "created_at": "2026-07-17T15:00:00Z",
                "updated_at": "2026-07-18T14:20:00Z",
                "base": {"ref": "release/1.4"},
                "head": {"ref": "feature/SCRUM-42"},
            }
        ],
        commits=[],
        reviews={47: []},
        requested_reviewers={47: [{"login": "dan-ohis"}]},
    )

    signals = GitHubConnector(gateway).fetch("hemchandk3/DeliveryEnterpriseProduct")

    pr = signals[0]
    assert pr.meta["base_ref"] == "release/1.4"
    assert pr.meta["requested_reviewers"] == ["dan-ohis"]
    assert pr.meta["reviews"] == []


def test_fetch_normalizes_approved_reviews():
    gateway = FakeGitHubGateway(
        pulls=[
            {
                "number": 43,
                "title": "SCRUM-41: coupon stacking validation",
                "state": "closed",
                "draft": False,
                "user": {"login": "priya-nair"},
                "created_at": "2026-07-15T10:00:00Z",
                "updated_at": "2026-07-20T10:30:00Z",
                "base": {"ref": "develop"},
            }
        ],
        commits=[],
        reviews={43: [{"user": {"login": "mara-vlad"}, "state": "APPROVED"}]},
        requested_reviewers={43: []},
    )

    signals = GitHubConnector(gateway).fetch("hemchandk3/DeliveryEnterpriseProduct")

    pr = signals[0]
    assert pr.meta["reviews"] == [{"user": "mara-vlad", "state": "APPROVED"}]
    assert pr.meta["requested_reviewers"] == []
