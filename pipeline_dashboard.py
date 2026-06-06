#!/usr/bin/env python3
"""
Zen-AI-Pentest Pipeline Dashboard
Simple FastAPI app to visualize CI/CD pipeline reports.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Zen Pipeline Dashboard")

REPORT_PATH = Path("/home/atakan/Zen-Ai-Pentest/reports/n8n_full_report.json")

# Simple inline HTML template (no external templates directory needed)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zen Pipeline Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 2rem;
        }
        h1 { color: #38bdf8; margin-bottom: 0.5rem; }
        .subtitle { color: #94a3b8; margin-bottom: 2rem; }
        .meta { display: flex; gap: 2rem; margin-bottom: 2rem; flex-wrap: wrap; }
        .meta-box {
            background: #1e293b;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            border: 1px solid #334155;
        }
        .meta-box label { display: block; font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; }
        .meta-box value { display: block; font-size: 1.1rem; font-weight: 600; color: #f8fafc; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
        }
        .card {
            background: #1e293b;
            border-radius: 0.75rem;
            padding: 1.25rem;
            border: 1px solid #334155;
            transition: transform 0.1s;
        }
        .card:hover { transform: translateY(-2px); }
        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.75rem;
        }
        .card-title { font-weight: 600; font-size: 1rem; }
        .badge {
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge-ok { background: #064e3b; color: #34d399; }
        .badge-fail { background: #450a0a; color: #f87171; }
        .badge-warn { background: #422006; color: #fbbf24; }
        .output {
            background: #0f172a;
            border-radius: 0.5rem;
            padding: 0.75rem;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            color: #cbd5e1;
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .summary-bar {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: #1e293b;
            border-radius: 0.5rem;
            border: 1px solid #334155;
        }
        .summary-item { flex: 1; text-align: center; }
        .summary-item .number { font-size: 2rem; font-weight: 700; }
        .summary-item .label { font-size: 0.8rem; color: #94a3b8; }
        .green { color: #34d399; }
        .red { color: #f87171; }
        .yellow { color: #fbbf24; }
        a { color: #38bdf8; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .refresh {
            display: inline-block;
            margin-top: 1rem;
            padding: 0.5rem 1rem;
            background: #2563eb;
            color: white;
            border-radius: 0.375rem;
            font-size: 0.875rem;
        }
    </style>
</head>
<body>
    <h1>🛡️ Zen-AI-Pentest Pipeline Dashboard</h1>
    <p class="subtitle">Real-time CI/CD pipeline health & reports</p>

    <div class="meta">
        <div class="meta-box">
            <label>Last Run</label>
            <value>{{ timestamp }}</value>
        </div>
        <div class="meta-box">
            <label>Repository</label>
            <value>{{ repo }}</value>
        </div>
        <div class="meta-box">
            <label>Overall Status</label>
            <value style="color: {{ ' #34d399' if overall_ok else '#f87171' }}">{{ overall_status }}</value>
        </div>
    </div>

    <div class="summary-bar">
        <div class="summary-item">
            <div class="number green">{{ ok_count }}</div>
            <div class="label">Passing</div>
        </div>
        <div class="summary-item">
            <div class="number red">{{ fail_count }}</div>
            <div class="label">Failing</div>
        </div>
        <div class="summary-item">
            <div class="number yellow">{{ warn_count }}</div>
            <div class="label">Warnings</div>
        </div>
    </div>

    <div class="grid">
        {% for name, check in checks.items() %}
        <div class="card">
            <div class="card-header">
                <span class="card-title">{{ name }}</span>
                {% if check.ok %}
                <span class="badge badge-ok">Pass</span>
                {% else %}
                <span class="badge badge-fail">Fail</span>
                {% endif %}
            </div>
            {% if check.output %}
            <div class="output">{{ check.output[:500] }}{% if check.output|length > 500 %}...{% endif %}</div>
            {% else %}
            <div class="output" style="color:#64748b">No output available</div>
            {% endif %}
        </div>
        {% endfor %}
    </div>

    <a class="refresh" href="/">🔄 Refresh</a>
    <a class="refresh" href="/json">📄 View JSON</a>
    <a class="refresh" href="/trigger">🚀 Trigger Pipeline</a>
</body>
</html>
"""


def load_report():
    if REPORT_PATH.exists():
        with open(REPORT_PATH) as f:
            return json.load(f)
    return {
        "timestamp": datetime.now().isoformat(),
        "repo": "SHAd0WTAka/Zen-Ai-Pentest",
        "overallStatus": "no report",
        "checks": {},
    }


def render_dashboard():
    report = load_report()
    checks = report.get("checks", {})
    ok_count = sum(1 for c in checks.values() if c.get("ok"))
    fail_count = sum(1 for c in checks.values() if not c.get("ok"))
    warn_count = sum(1 for c in checks.values() if c.get("issuesFound") or c.get("output", "").lower().find("warning") != -1)
    overall_ok = fail_count == 0

    # Simple template substitution (no Jinja2 needed for this inline template)
    from string import Template

    Template(HTML_TEMPLATE)
    # We'll use basic string formatting instead since the template has loops
    # Actually, let me use a simple approach - generate the grid HTML dynamically

    grid_html = ""
    for name, check in checks.items():
        status_badge = (
            '<span class="badge badge-ok">Pass</span>' if check.get("ok") else '<span class="badge badge-fail">Fail</span>'
        )
        output = check.get("output", "")
        if not output:
            output_text = '<div class="output" style="color:#64748b">No output available</div>'
        else:
            display = output[:500] + ("..." if len(output) > 500 else "")
            # Escape HTML
            display = display.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            output_text = f'<div class="output">{display}</div>'

        grid_html += f"""
        <div class="card">
            <div class="card-header">
                <span class="card-title">{name}</span>
                {status_badge}
            </div>
            {output_text}
        </div>
        """

    overall_color = "#34d399" if overall_ok else "#f87171"
    overall_status = report.get("overallStatus", "unknown").upper()

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zen Pipeline Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 2rem;
        }}
        h1 {{ color: #38bdf8; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #94a3b8; margin-bottom: 2rem; }}
        .meta {{ display: flex; gap: 2rem; margin-bottom: 2rem; flex-wrap: wrap; }}
        .meta-box {{
            background: #1e293b;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            border: 1px solid #334155;
        }}
        .meta-box label {{ display: block; font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; }}
        .meta-box value {{ display: block; font-size: 1.1rem; font-weight: 600; color: #f8fafc; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1rem;
        }}
        .card {{
            background: #1e293b;
            border-radius: 0.75rem;
            padding: 1.25rem;
            border: 1px solid #334155;
            transition: transform 0.1s;
        }}
        .card:hover {{ transform: translateY(-2px); }}
        .card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.75rem;
        }}
        .card-title {{ font-weight: 600; font-size: 1rem; }}
        .badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge-ok {{ background: #064e3b; color: #34d399; }}
        .badge-fail {{ background: #450a0a; color: #f87171; }}
        .output {{
            background: #0f172a;
            border-radius: 0.5rem;
            padding: 0.75rem;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            color: #cbd5e1;
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .summary-bar {{
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: #1e293b;
            border-radius: 0.5rem;
            border: 1px solid #334155;
        }}
        .summary-item {{ flex: 1; text-align: center; }}
        .summary-item .number {{ font-size: 2rem; font-weight: 700; }}
        .summary-item .label {{ font-size: 0.8rem; color: #94a3b8; }}
        .green {{ color: #34d399; }}
        .red {{ color: #f87171; }}
        .yellow {{ color: #fbbf24; }}
        a {{ color: #38bdf8; text-decoration: none; margin-right: 1rem; }}
        a:hover {{ text-decoration: underline; }}
        .refresh {{
            display: inline-block;
            margin-top: 1.5rem;
            margin-right: 0.75rem;
            padding: 0.5rem 1rem;
            background: #2563eb;
            color: white;
            border-radius: 0.375rem;
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <h1>🛡️ Zen-AI-Pentest Pipeline Dashboard</h1>
    <p class="subtitle">Real-time CI/CD pipeline health & reports</p>

    <div class="meta">
        <div class="meta-box">
            <label>Last Run</label>
            <value>{report.get("timestamp", "N/A")}</value>
        </div>
        <div class="meta-box">
            <label>Repository</label>
            <value>{report.get("repo", "N/A")}</value>
        </div>
        <div class="meta-box">
            <label>Overall Status</label>
            <value style="color: {overall_color}">{overall_status}</value>
        </div>
    </div>

    <div class="summary-bar">
        <div class="summary-item">
            <div class="number green">{ok_count}</div>
            <div class="label">Passing</div>
        </div>
        <div class="summary-item">
            <div class="number red">{fail_count}</div>
            <div class="label">Failing</div>
        </div>
        <div class="summary-item">
            <div class="number yellow">{warn_count}</div>
            <div class="label">Warnings</div>
        </div>
    </div>

    <div class="grid">
        {grid_html}
    </div>

    <a class="refresh" href="/">🔄 Refresh</a>
    <a class="refresh" href="/json">📄 View JSON</a>
    <a class="refresh" href="/trigger">🚀 Trigger Pipeline</a>
</body>
</html>
"""
    return html


@app.get("/", response_class=HTMLResponse)
def index():
    return render_dashboard()


@app.get("/json")
def json_report():
    return load_report()


@app.get("/trigger")
def trigger_pipeline():
    import urllib.request

    try:
        req = urllib.request.Request("http://127.0.0.1:9876/run-full-orchestrator", method="POST")
        # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
        # nosemgrep
        with urllib.request.urlopen(req, timeout=5) as resp:  # nosec B310
            return {"triggered": True, "status": resp.status}
    except Exception:  # nosec B112
        # Security: Do not expose internal error details
        return {"triggered": False, "error": "Failed to trigger pipeline"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("dashboard:app", host=os.getenv("HOST", "127.0.0.1"), port=8080, reload=False)
