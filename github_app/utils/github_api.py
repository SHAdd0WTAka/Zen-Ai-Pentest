"""GitHub API wrapper for GitHub App."""

import base64
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class GitHubAPI:
    """GitHub API client for GitHub App operations."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        """Initialize GitHub API client.

        Args:
            token: Installation access token
        """
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to GitHub API."""
        url = f"{self.BASE_URL}{endpoint}"

        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=self.headers, **kwargs)

            if response.status_code >= 400:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                response.raise_for_status()

            if response.status_code == 204:
                return {}

            return response.json()

    async def get_file_content(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> Optional[str]:
        """Get file content from repository.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Git reference (branch/commit)

        Returns:
            File content as string or None
        """
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref} if ref else {}

        try:
            data = await self._request("GET", endpoint, params=params)

            if "content" in data:
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content

            return None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def create_pr_comment(self, owner: str, repo: str, pr_number: int, body: str) -> Dict[str, Any]:
        """Create a comment on a pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            body: Comment body (Markdown)

        Returns:
            Created comment data
        """
        endpoint = f"/repos/{owner}/{repo}/issues/{pr_number}/comments"
        return await self._request("POST", endpoint, json={"body": body})

    async def create_inline_comment(
        self, owner: str, repo: str, pr_number: int, body: str, commit_id: str, path: str, line: int, side: str = "RIGHT"
    ) -> Dict[str, Any]:
        """Create an inline comment on a pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            body: Comment body
            commit_id: Commit SHA
            path: File path
            line: Line number
            side: Side of diff (LEFT/RIGHT)

        Returns:
            Created review comment data
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        data = {"body": body, "commit_id": commit_id, "path": path, "line": line, "side": side}
        return await self._request("POST", endpoint, json=data)

    async def create_check_run(
        self,
        owner: str,
        repo: str,
        name: str,
        head_sha: str,
        status: str = "queued",
        conclusion: Optional[str] = None,
        output: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Create a check run.

        Args:
            owner: Repository owner
            repo: Repository name
            name: Check run name
            head_sha: Commit SHA
            status: Check status (queued, in_progress, completed)
            conclusion: Conclusion if completed
            output: Check output details
            actions: Possible actions

        Returns:
            Created check run data
        """
        endpoint = f"/repos/{owner}/{repo}/check-runs"
        data: Dict[str, Any] = {"name": name, "head_sha": head_sha, "status": status}

        if conclusion:
            data["conclusion"] = conclusion

        if output:
            data["output"] = output

        if actions:
            data["actions"] = actions

        headers = {**self.headers, "Accept": "application/vnd.github.antiope-preview+json"}

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.BASE_URL}{endpoint}", headers=headers, json=data)
            response.raise_for_status()
            return response.json()

    async def update_check_run(
        self,
        owner: str,
        repo: str,
        check_run_id: int,
        status: Optional[str] = None,
        conclusion: Optional[str] = None,
        output: Optional[Dict[str, Any]] = None,
        completed_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing check run.

        Args:
            owner: Repository owner
            repo: Repository name
            check_run_id: Check run ID
            status: New status
            conclusion: Conclusion
            output: Updated output
            completed_at: ISO timestamp

        Returns:
            Updated check run data
        """
        endpoint = f"/repos/{owner}/{repo}/check-runs/{check_run_id}"
        data: Dict[str, Any] = {}

        if status:
            data["status"] = status
        if conclusion:
            data["conclusion"] = conclusion
        if output:
            data["output"] = output
        if completed_at:
            data["completed_at"] = completed_at

        headers = {**self.headers, "Accept": "application/vnd.github.antiope-preview+json"}

        async with httpx.AsyncClient() as client:
            response = await client.patch(f"{self.BASE_URL}{endpoint}", headers=headers, json=data)
            response.raise_for_status()
            return response.json()

    async def upload_sarif(self, owner: str, repo: str, sarif_data: str, commit_sha: str, ref: str) -> Dict[str, Any]:
        """Upload SARIF data to GitHub Security tab.

        Args:
            owner: Repository owner
            repo: Repository name
            sarif_data: SARIF JSON string
            commit_sha: Commit SHA
            ref: Git reference

        Returns:
            Upload result
        """
        import base64
        import zlib

        # Compress SARIF data
        compressed = base64.b64encode(zlib.compress(sarif_data.encode())).decode()

        endpoint = f"/repos/{owner}/{repo}/code-scanning/sarifs"
        data = {"commit_sha": commit_sha, "ref": ref, "sarif": compressed}

        return await self._request("POST", endpoint, json=data)

    async def list_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """List files changed in a pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            List of changed files
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/files"
        files = []
        page = 1

        async with httpx.AsyncClient() as client:
            while True:
                params = {"page": page, "per_page": 100}
                response = await client.get(f"{self.BASE_URL}{endpoint}", headers=self.headers, params=params)
                response.raise_for_status()

                page_files = response.json()
                if not page_files:
                    break

                files.extend(page_files)
                page += 1

        return files

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Get pull request diff.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            Diff as string
        """
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.BASE_URL}{endpoint}", headers=headers)
            response.raise_for_status()
            return response.text
