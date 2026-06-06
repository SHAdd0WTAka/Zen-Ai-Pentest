"""GitHub App FastAPI main application."""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from .handlers.pr_scan import PRScanHandler
from .handlers.push_scan import PushScanHandler
from .handlers.release_scan import ReleaseScanHandler
from .models.events import InstallationEvent, PREvent, PushEvent, ReleaseEvent
from .utils.auth import GitHubAuth
from .utils.config_loader import ConfigLoader
from .utils.github_api import GitHubAPI

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class GitHubAppConfig(BaseModel):
    """GitHub App configuration."""

    app_id: str
    private_key: str
    webhook_secret: Optional[str] = None

    model_config = ConfigDict(env_prefix="GITHUB_APP_")


# Global state
app_state: Dict[str, Any] = {}


def get_config() -> GitHubAppConfig:
    """Get GitHub App configuration from environment."""
    return GitHubAppConfig(
        app_id=os.getenv("GITHUB_APP_ID", ""),
        private_key=os.getenv("GITHUB_APP_PRIVATE_KEY", ""),
        webhook_secret=os.getenv("GITHUB_APP_WEBHOOK_SECRET"),
    )


def get_auth(config: GitHubAppConfig = Depends(get_config)) -> GitHubAuth:
    """Get GitHubAuth instance."""
    return GitHubAuth(config.app_id, config.private_key)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting GitHub App for Zen-AI-Pentest")
    config = get_config()

    if not config.app_id or not config.private_key:
        logger.warning("GitHub App credentials not configured!")

    app_state["config"] = config
    app_state["auth"] = GitHubAuth(config.app_id, config.private_key)

    yield

    # Shutdown
    logger.info("Shutting down GitHub App")


app = FastAPI(
    title="Zen-AI-Pentest GitHub App",
    description="CI/CD Security Integration for Zen-AI-Pentest",
    version="1.0.0",
    lifespan=lifespan,
)


async def verify_webhook(
    request: Request, x_hub_signature_256: Optional[str] = Header(None), config: GitHubAppConfig = Depends(get_config)
) -> bytes:
    """Verify GitHub webhook signature."""
    body = await request.body()

    if config.webhook_secret and x_hub_signature_256:
        auth = GitHubAuth(config.app_id, config.private_key)
        is_valid = await auth.verify_webhook_signature(body, x_hub_signature_256, config.webhook_secret)

        if not is_valid:
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

    return body


@app.get("/")
async def root():
    """Root endpoint."""
    return {"name": "Zen-AI-Pentest GitHub App", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0", "timestamp": datetime.now().isoformat()}


@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(...),
    body: bytes = Depends(verify_webhook),
):
    """Handle GitHub webhook events."""
    logger.info(f"Received webhook event: {x_github_event}")

    try:
        import json

        payload = json.loads(body)

        if x_github_event == "pull_request":
            event = PREvent(**payload)
            background_tasks.add_task(handle_pr_event, event)
            return {"status": "processing", "event": "pull_request"}

        elif x_github_event == "push":
            event = PushEvent(**payload)
            background_tasks.add_task(handle_push_event, event)
            return {"status": "processing", "event": "push"}

        elif x_github_event == "release":
            event = ReleaseEvent(**payload)
            background_tasks.add_task(handle_release_event, event)
            return {"status": "processing", "event": "release"}

        elif x_github_event == "installation":
            event = InstallationEvent(**payload)
            background_tasks.add_task(handle_installation_event, event)
            return {"status": "processed", "event": "installation"}

        else:
            logger.debug(f"Unhandled event type: {x_github_event}")
            return {"status": "ignored", "event": x_github_event}

    except Exception as e:
        logger.exception("Webhook processing error")
        raise HTTPException(status_code=400, detail=str(e))


async def handle_pr_event(event: PREvent) -> None:
    """Handle pull request events."""
    # Only process relevant actions
    if event.action not in ["opened", "synchronize", "reopened"]:
        return

    owner = event.repository.owner.login
    repo = event.repository.name

    logger.info(f"Processing PR #{event.number} in {owner}/{repo}")

    try:
        # Get installation token
        auth = app_state["auth"]
        token = await auth.get_installation_token(event.installation.id, [repo])

        # Initialize GitHub API client
        github_api = GitHubAPI(token)

        # Load repository configuration
        config = await ConfigLoader.load_config(github_api, owner, repo, event.pull_request.head["sha"])

        # Check if PR scanning is enabled
        pr_config = config.get_pr_config()
        if not pr_config.enabled:
            logger.info(f"PR scanning disabled for {owner}/{repo}")
            return

        # Run scan
        handler = PRScanHandler(github_api, pr_config)
        result = await handler.handle(event)

        logger.info(f"PR scan complete: {len(result.findings)} findings")

    except Exception as e:
        logger.exception(f"Failed to process PR event: {e}")


async def handle_push_event(event: PushEvent) -> None:
    """Handle push events."""
    owner = event.repository.owner.login
    repo = event.repository.name
    branch = event.ref.replace("refs/heads/", "")

    logger.info(f"Processing push to {owner}/{repo}@{branch}")

    try:
        # Get installation token
        auth = app_state["auth"]
        token = await auth.get_installation_token(event.installation.id, [repo])

        # Initialize GitHub API client
        github_api = GitHubAPI(token)

        # Load repository configuration
        config = await ConfigLoader.load_config(github_api, owner, repo, event.after)

        # Check if push scanning is enabled
        push_config = config.get_push_config()
        if not push_config.enabled:
            logger.info(f"Push scanning disabled for {owner}/{repo}")
            return

        # Run scan
        handler = PushScanHandler(github_api, push_config)
        result = await handler.handle(event)

        logger.info(f"Push scan complete: {len(result.findings)} findings")

    except Exception as e:
        logger.exception(f"Failed to process push event: {e}")


async def handle_release_event(event: ReleaseEvent) -> None:
    """Handle release events."""
    owner = event.repository.owner.login
    repo = event.repository.name

    logger.info(f"Processing release {event.release.tag_name} in {owner}/{repo}")

    try:
        # Get installation token
        auth = app_state["auth"]
        token = await auth.get_installation_token(event.installation.id, [repo])

        # Initialize GitHub API client
        github_api = GitHubAPI(token)

        # Run release scan
        handler = ReleaseScanHandler(github_api)
        result = await handler.handle(event)

        logger.info(f"Release scan complete: passed={result.passed}")

    except Exception as e:
        logger.exception(f"Failed to process release event: {e}")


async def handle_installation_event(event: InstallationEvent) -> None:
    """Handle installation events."""
    action = event.action
    account = event.installation.account.login

    logger.info(f"Installation {action} by {account}")

    if action == "created":
        logger.info(f"New installation for {account}")
        # Could send welcome message or setup default config

    elif action == "deleted":
        logger.info(f"Installation removed for {account}")
        # Cleanup any stored data


# API Endpoints for direct access


@app.get("/repos/{owner}/{repo}/config")
async def get_repo_config(owner: str, repo: str, ref: Optional[str] = None, auth: GitHubAuth = Depends(get_auth)):
    """Get repository configuration."""
    # This would need proper authentication in production
    raise HTTPException(status_code=501, detail="Not implemented")


@app.post("/repos/{owner}/{repo}/scan")
async def trigger_scan(owner: str, repo: str, scan_type: str = "full", auth: GitHubAuth = Depends(get_auth)):
    """Manually trigger a security scan."""
    # This would need proper authentication in production
    raise HTTPException(status_code=501, detail="Not implemented")


@app.get("/installations")
async def list_installations(auth: GitHubAuth = Depends(get_auth)):
    """List GitHub App installations."""
    try:
        jwt_token = auth.generate_jwt()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/app/installations",
                headers={"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github.v3+json"},
            )
            response.raise_for_status()
            return response.json()

    except Exception as e:
        logger.exception("Failed to list installations")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__:":
    import uvicorn

    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=8000)
