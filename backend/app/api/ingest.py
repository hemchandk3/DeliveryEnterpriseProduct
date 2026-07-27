from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.connectors.base import Connector
from app.connectors.github import GitHubConnector, GitHubGateway, GitHubHttpGateway
from app.connectors.jira import JiraConnector, JiraGateway, JiraHttpGateway
from app.db import get_session
from app.ingest.service import IngestService
from app.models import Project

router = APIRouter()


class IngestRequest(BaseModel):
    source: str
    project_ref: str


def build_github_gateway() -> GitHubGateway:
    return GitHubHttpGateway(token=get_settings().github_token)


def build_jira_gateway() -> JiraGateway:
    s = get_settings()
    return JiraHttpGateway(base_url=s.jira_base_url, email=s.jira_email, token=s.jira_token)


def _build_connector(source: str) -> Connector:
    if source == "github":
        return GitHubConnector(build_github_gateway())
    if source == "jira":
        return JiraConnector(
            build_jira_gateway(), story_points_field=get_settings().jira_story_points_field
        )
    raise HTTPException(status_code=400, detail=f"Unknown source: {source}")


@router.post("/projects/{project_id}/ingest")
def ingest(
    project_id: int,
    body: IngestRequest,
    session: Session = Depends(get_session),  # noqa: B008 -- standard FastAPI DI idiom
) -> dict[str, int]:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    connector = _build_connector(body.source)
    written = IngestService(session).run(project, connector, body.project_ref)
    return {"written": written}
