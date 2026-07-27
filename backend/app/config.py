from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./delivery.db"
    github_token: str = ""
    jira_base_url: str = ""
    jira_email: str = ""
    jira_token: str = ""
    # Jira custom field id for Story Points. Instance-specific -- resolve via
    # GET /rest/api/3/field at OAuth time rather than assuming this default
    # holds for every Jira site. See docs/mvp workstream #0 §5.1.
    jira_story_points_field: str = "customfield_10016"


@lru_cache
def get_settings() -> Settings:
    return Settings()
