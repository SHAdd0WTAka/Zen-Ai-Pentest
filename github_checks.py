#!/usr/bin/env python3
"""
GitHub Actions Workflow Checker
"""

import time

import jwt
import requests

CONFIG = {
    "app_id": "2872904",
    "key_path": "/root/.ssh/github-app-zenai.pem",
    "owner": "SHAdd0WTAka",
    "repo": "Zen-Ai-Pentest",
}


def generate_jwt(app_id, key_path):
    with open(key_path, "r") as f:
        private_key = f.read()
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
        "iss": app_id,
    }
    return jwt.encode(payload, private_key, algorithm="RS256")


def get_installation_token(jwt_token, owner, repo):
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = requests.get(f"https://api.github.com/repos/{owner}/{repo}/installation", headers=headers, timeout=30)
    if resp.status_code != 200:
        return None
    installation_id = resp.json()["id"]
    resp = requests.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens", headers=headers, timeout=30
    )
    return resp.json()["token"] if resp.status_code == 201 else None


def get_workflow_runs(token, owner, repo):
    """Holt aktuelle Workflow Runs"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = requests.get(f"https://api.github.com/repos/{owner}/{repo}/actions/runs", headers=headers, timeout=30)
    return resp.json() if resp.status_code == 200 else None


def get_workflow_run_logs(token, owner, repo, run_id):
    """Holt Logs eines Workflow Runs"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = requests.get(f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/logs", headers=headers, timeout=30)
    return resp


if __name__ == "__main__":
    jwt_token = generate_jwt(CONFIG["app_id"], CONFIG["key_path"])
    token = get_installation_token(jwt_token, CONFIG["owner"], CONFIG["repo"])

    if not token:
        print("❌ Kein Token")
        exit(1)

    runs = get_workflow_runs(token, CONFIG["owner"], CONFIG["repo"])

    if runs:
        print("=" * 60)
        print("📊 WORKFLOW RUNS STATUS")
        print("=" * 60)
        print(f"Total: {runs['total_count']} runs\n")

        # Gruppiere nach Status
        status_counts = {}
        for run in runs["workflow_runs"][:10]:
            status = run["conclusion"] if run["conclusion"] else run["status"]
            if status not in status_counts:
                status_counts[status] = []
            status_counts[status].append(
                {
                    "id": run["id"],
                    "name": run["name"],
                    "head_branch": run["head_branch"],
                    "status": run["status"],
                    "conclusion": run["conclusion"],
                    "created_at": run["created_at"],
                    "html_url": run["html_url"],
                }
            )

        # Zeige Zusammenfassung
        for status, runs_list in status_counts.items():
            print(f"\n{status.upper()}: {len(runs_list)} runs")
            for run in runs_list[:3]:  # Zeige max 3 pro Status
                print(f"  • {run['name']} ({run['head_branch']}) - {run['html_url']}")

        # Zeige fehlende
        if "failure" in status_counts or "action_required" in status_counts:
            print("\n" + "=" * 60)
            print("⚠️ FAILING WORKFLOWS")
            print("=" * 60)
            for run in status_counts.get("failure", []) + status_counts.get("action_required", []):
                print(f"\n❌ {run['name']}")
                print(f"   Branch: {run['head_branch']}")
                print(f"   URL: {run['html_url']}")

    else:
        print("❌ Konnte Workflow Runs nicht laden")
