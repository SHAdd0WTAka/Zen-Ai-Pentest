"""GitHub webhook event models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GitHubUser(BaseModel):
    """GitHub user model."""

    login: str
    id: int
    avatar_url: Optional[str] = None
    html_url: Optional[str] = None


class GitHubRepository(BaseModel):
    """GitHub repository model."""

    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    clone_url: str
    default_branch: str
    owner: GitHubUser


class GitHubInstallation(BaseModel):
    """GitHub installation model."""

    id: int
    account: GitHubUser
    repository_selection: str
    target_type: str


class PullRequest(BaseModel):
    """Pull request model."""

    number: int
    title: str
    body: Optional[str] = None
    state: str
    html_url: str
    user: GitHubUser
    head: Dict[str, Any]
    base: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    draft: bool = False


class PREvent(BaseModel):
    """Pull request webhook event."""

    action: str
    number: int
    pull_request: PullRequest
    repository: GitHubRepository
    installation: GitHubInstallation
    sender: GitHubUser


class PushCommit(BaseModel):
    """Push commit model."""

    id: str = Field(alias="sha")
    message: str
    author: Dict[str, str]
    committer: Dict[str, str]
    url: str
    added: List[str] = []
    removed: List[str] = []
    modified: List[str] = []


class PushEvent(BaseModel):
    """Push webhook event."""

    ref: str
    before: str
    after: str
    repository: GitHubRepository
    pusher: Dict[str, str]
    sender: GitHubUser
    installation: GitHubInstallation
    commits: List[PushCommit] = []
    head_commit: Optional[PushCommit] = None


class ReleaseAsset(BaseModel):
    """Release asset model."""

    id: int
    name: str
    browser_download_url: str
    size: int


class Release(BaseModel):
    """Release model."""

    id: int
    tag_name: str
    name: Optional[str] = None
    body: Optional[str] = None
    draft: bool
    prerelease: bool
    html_url: str
    author: GitHubUser
    created_at: datetime
    published_at: Optional[datetime] = None
    assets: List[ReleaseAsset] = []


class ReleaseEvent(BaseModel):
    """Release webhook event."""

    action: str
    release: Release
    repository: GitHubRepository
    sender: GitHubUser
    installation: GitHubInstallation


class InstallationEvent(BaseModel):
    """Installation webhook event."""

    action: str
    installation: GitHubInstallation
    repositories: List[Dict[str, Any]] = []
    sender: GitHubUser
