#!/usr/bin/env python3
"""
Kimi Personas API für Zen-Ai-Pentest
REST API für alle 11 Pentest-Personas
"""

import logging
import sys
from datetime import datetime
from functools import wraps
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, Response, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from flask_sock import Sock

from config_loader import load_config

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
sock = Sock(app)

# Request Logging
from logging.handlers import RotatingFileHandler

# Setup request logger
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

request_logger = logging.getLogger("kimi_api_requests")
request_logger.setLevel(logging.INFO)
handler = RotatingFileHandler(log_dir / "api_requests.log", maxBytes=10 * 1024 * 1024, backupCount=5)  # 10MB
handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
request_logger.addHandler(handler)

# Request stats
request_stats = {"total_requests": 0, "requests_by_persona": {}, "requests_by_endpoint": {}, "start_time": datetime.utcnow()}

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Persona Registry
PERSONAS = {
    "recon": {
        "name": "🔍 Recon/OSINT Specialist",
        "description": "Subdomain枚举, Port扫描, Technologie-Erkennung",
        "category": "core",
        "skills": ["subdomain_enum", "port_scanning", "osint", "tech_detection"],
    },
    "exploit": {
        "name": "💣 Exploit Developer",
        "description": "Python-Exploits, POC-Entwicklung, Automation",
        "category": "core",
        "skills": ["python_coding", "poc_development", "automation", "tooling"],
    },
    "report": {
        "name": "📝 Technical Writer",
        "description": "CVSS-Scoring, Remediation, Executive Summary",
        "category": "core",
        "skills": ["cvss_scoring", "remediation", "executive_summary", "documentation"],
    },
    "audit": {
        "name": "🔐 Code Auditor",
        "description": "Sicherheits-Review, Bug-Bounty Pattern",
        "category": "core",
        "skills": ["static_analysis", "owasp", "cwe", "code_review"],
    },
    "social": {
        "name": "🎭 Social Engineering Specialist",
        "description": "Phishing, Pretexting, OSINT auf Personen",
        "category": "extended",
        "skills": ["phishing_analysis", "email_security", "awareness_training", "pretexting"],
    },
    "network": {
        "name": "🌐 Network Pentester",
        "description": "Infrastruktur, Active Directory, Lateral Movement",
        "category": "extended",
        "skills": ["active_directory", "lateral_movement", "pivoting", "network_enum"],
    },
    "mobile": {
        "name": "📱 Mobile Security Expert",
        "description": "Android/iOS, App-Analyse, API-Testing",
        "category": "extended",
        "skills": ["android", "ios", "frida", "api_testing", "mobsf"],
    },
    "redteam": {
        "name": "🕵️ Red Team Operator",
        "description": "Adversary Simulation, APT TTPs, C2 Operations",
        "category": "extended",
        "skills": ["apt_ttps", "c2_operations", "lolbas", "opsec", "kill_chain"],
    },
    "ics": {
        "name": "🧪 ICS/SCADA Specialist",
        "description": "Industrial Control Systems, Modbus, S7, Safety",
        "category": "extended",
        "skills": ["modbus", "scada", "safety_systems", " Purdue_model", "iec_62443"],
    },
    "cloud": {
        "name": "☁️ Cloud Security Expert",
        "description": "AWS, Azure, GCP, Container, K8s Pentesting",
        "category": "extended",
        "skills": ["aws", "azure", "gcp", "kubernetes", "container_escape"],
    },
    "crypto": {
        "name": "🔬 Cryptography Analyst",
        "description": "Kryptographie, Hash-Analyse, JWT, TLS",
        "category": "extended",
        "skills": ["jwt", "tls", "hash_analysis", "libsodium", "crypto_review"],
    },
}


def get_persona_dir():
    """Gibt Persona-Verzeichnis zurück"""
    return Path.home() / ".config" / "kimi" / "personas"


def load_persona_content(persona_name):
    """Lädt den vollständigen System Prompt"""
    persona_file = get_persona_dir() / f"{persona_name}.md"
    if persona_file.exists():
        return persona_file.read_text()
    return None


def require_api_key(f):
    """API Key Authentication Decorator"""

    @wraps(f)
    def decorated(*args, **kwargs):
        config = load_config()
        expected_key = config.get("api", {}).get("api_key") or config.get("backends", {}).get("kimi_api_key")

        # Optional: Allow local requests without key
        if request.remote_addr in ["127.0.0.1", "localhost", "::1"]:
            if not expected_key:
                return f(*args, **kwargs)

        api_key = request.headers.get("X-API-Key") or request.args.get("api_key")

        if not expected_key:
            return jsonify({"error": "API key not configured on server"}), 500

        if not api_key or api_key != expected_key:
            logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
            return jsonify({"error": "Unauthorized"}), 401

        return f(*args, **kwargs)

    return decorated


# ═════════════════════════════════════════════════════════════════════════════
# REQUEST LOGGING MIDDLEWARE
# ═════════════════════════════════════════════════════════════════════════════


@app.before_request
def log_request():
    """Log every request"""
    request.start_time = datetime.utcnow()


@app.after_request
def after_request(response):
    """Log request completion"""
    if hasattr(request, "start_time"):
        duration = (datetime.utcnow() - request.start_time).total_seconds()

        # Update stats
        request_stats["total_requests"] += 1
        endpoint = request.endpoint or "unknown"
        request_stats["requests_by_endpoint"][endpoint] = request_stats["requests_by_endpoint"].get(endpoint, 0) + 1

        # Log to file
        log_entry = (
            f"{request.remote_addr} | "
            f"{request.method} {request.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration:.3f}s | "
            f"UA: {request.user_agent.string[:50] if request.user_agent else 'Unknown'}"
        )
        request_logger.info(log_entry)

    return response


# ═════════════════════════════════════════════════════════════════════════════
# WEB UI
# ═════════════════════════════════════════════════════════════════════════════


@app.route("/")
def index():
    """Web UI"""
    return render_template("index.html")


@app.route("/static/screenshots/<path:filename>")
def serve_screenshot(filename):
    """Serve screenshot files"""
    screenshot_dir = Path.home() / "Zen-Ai-Pentest" / "screenshots"
    if screenshot_dir.exists():
        return send_from_directory(screenshot_dir, filename)
    return jsonify({"error": "Screenshot not found"}), 404


@app.route("/api/v1/screenshots", methods=["GET"])
def list_screenshots():
    """List available screenshots"""
    screenshot_dir = Path.home() / "Zen-Ai-Pentest" / "screenshots"
    if not screenshot_dir.exists():
        return jsonify({"screenshots": [], "count": 0})

    screenshots = []
    for ext in ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp"]:
        screenshots.extend(screenshot_dir.glob(ext))

    return jsonify({"screenshots": [s.name for s in screenshots], "count": len(screenshots), "directory": str(screenshot_dir)})


@app.route("/api/v1/screenshots", methods=["POST"])
@require_api_key
def upload_screenshot():
    """Upload a screenshot for analysis"""
    from werkzeug.utils import secure_filename

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    screenshot_dir = Path.home() / "Zen-Ai-Pentest" / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{filename}"

    filepath = screenshot_dir / filename
    file.save(filepath)

    return jsonify(
        {"status": "success", "filename": filename, "path": str(filepath), "url": f"/static/screenshots/{filename}"}
    )


@app.route("/admin")
def admin_dashboard():
    """Admin Dashboard (JSON)"""
    uptime = datetime.utcnow() - request_stats["start_time"]

    return jsonify(
        {
            "status": "running",
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_formatted": str(uptime).split(".")[0],
            "stats": {
                "total_requests": request_stats["total_requests"],
                "requests_by_endpoint": request_stats["requests_by_endpoint"],
                "requests_by_persona": request_stats["requests_by_persona"],
            },
            "personas_loaded": len(PERSONAS),
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.route("/admin/logs")
def admin_logs():
    """View recent logs"""
    try:
        log_file = log_dir / "api_requests.log"
        if not log_file.exists():
            return jsonify({"logs": [], "count": 0})

        # Read last 100 lines
        with open(log_file, "r") as f:
            lines = f.readlines()

        # Get last 100 entries
        recent_logs = [line.strip() for line in lines[-100:]]

        return jsonify({"logs": recent_logs, "count": len(recent_logs), "total_lines": len(lines)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════


@app.route("/api/v1/health", methods=["GET"])
def health_check():
    """Health Check Endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "personas_available": len(PERSONAS),
        }
    )


@app.route("/api/v1/personas", methods=["GET"])
def list_personas():
    """Liste alle verfügbaren Personas"""
    category = request.args.get("category")

    personas = PERSONAS
    if category:
        personas = {k: v for k, v in personas.items() if v["category"] == category}

    return jsonify({"count": len(personas), "personas": personas})


@app.route("/api/v1/personas/<persona_id>", methods=["GET"])
def get_persona(persona_id):
    """Details einer Persona abrufen"""
    if persona_id not in PERSONAS:
        return jsonify({"error": f"Persona '{persona_id}' not found"}), 404

    include_prompt = request.args.get("include_prompt", "false").lower() == "true"

    response = PERSONAS[persona_id].copy()

    if include_prompt:
        prompt = load_persona_content(persona_id)
        if prompt:
            response["system_prompt"] = prompt
        else:
            response["system_prompt"] = None

    return jsonify(response)


@app.route("/api/v1/personas/<persona_id>/prompt", methods=["GET"])
def get_persona_prompt(persona_id):
    """System Prompt einer Persona abrufen"""
    if persona_id not in PERSONAS:
        return jsonify({"error": f"Persona '{persona_id}' not found"}), 404

    prompt = load_persona_content(persona_id)
    if not prompt:
        return jsonify({"error": f"Prompt file for '{persona_id}' not found"}), 404

    # Plain text response
    return Response(prompt, mimetype="text/plain")


@app.route("/api/v1/personas/categories", methods=["GET"])
def list_categories():
    """Liste alle Kategorien"""
    categories = {}
    for key, data in PERSONAS.items():
        cat = data["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(key)

    return jsonify(
        {
            "categories": categories,
            "core_count": len([p for p in PERSONAS.values() if p["category"] == "core"]),
            "extended_count": len([p for p in PERSONAS.values() if p["category"] == "extended"]),
        }
    )


@app.route("/api/v1/chat", methods=["POST"])
@require_api_key
def chat():
    """
    Chat mit einer Persona

    Request Body:
    {
        "persona": "exploit",
        "message": "Schreibe SQLi Scanner",
        "context": "optional context",
        "temperature": 0.7,
        "max_tokens": 4096
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    persona_id = data.get("persona", "recon")
    message = data.get("message")

    if not message:
        return jsonify({"error": "'message' is required"}), 400

    if persona_id not in PERSONAS:
        return jsonify({"error": f"Unknown persona: {persona_id}"}), 400

    # Load system prompt
    system_prompt = load_persona_content(persona_id)
    if not system_prompt:
        return jsonify({"error": f"Could not load persona '{persona_id}'"}), 500

    # Build full prompt with context
    context = data.get("context", "")
    if context:
        full_prompt = f"Context:\n{context}\n\nUser Request:\n{message}"
    else:
        full_prompt = message

    # Log request
    logger.info(f"Chat request: persona={persona_id}, message_length={len(message)}")

    # Update persona stats
    request_stats["requests_by_persona"][persona_id] = request_stats["requests_by_persona"].get(persona_id, 0) + 1

    # Return structured response (actual Kimi API call would happen here)
    # For now, return the prompt structure
    return jsonify(
        {
            "status": "success",
            "persona": persona_id,
            "persona_name": PERSONAS[persona_id]["name"],
            "request": {
                "message": message,
                "context": context,
                "temperature": data.get("temperature", 0.7),
                "max_tokens": data.get("max_tokens", 4096),
            },
            "system_prompt_length": len(system_prompt),
            "full_prompt_length": len(full_prompt),
            "note": "To get actual AI response, forward this to Kimi API",
        }
    )


@app.route("/api/v1/chat/complete", methods=["POST"])
@require_api_key
def chat_complete():
    """
    Chat mit direkter Kimi API Integration

    Benötigt KIMI_API_KEY in config.json
    """
    import requests

    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    persona_id = data.get("persona", "recon")
    message = data.get("message")

    if not message:
        return jsonify({"error": "'message' is required"}), 400

    if persona_id not in PERSONAS:
        return jsonify({"error": f"Unknown persona: {persona_id}"}), 400

    # Load config for API key
    config = load_config()
    api_key = config.get("backends", {}).get("kimi_api_key")

    if not api_key:
        return jsonify({"error": "KIMI_API_KEY not configured"}), 500

    # Load system prompt
    system_prompt = load_persona_content(persona_id)
    if not system_prompt:
        return jsonify({"error": f"Could not load persona '{persona_id}'"}), 500

    # Build messages
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]

    # Add context if provided
    context = data.get("context")
    if context:
        messages.insert(1, {"role": "user", "content": f"Context: {context}"})

    # Kimi API request
    kimi_payload = {
        "model": data.get("model", "kimi-k2.5"),
        "messages": messages,
        "temperature": data.get("temperature", 0.7),
        "max_tokens": data.get("max_tokens", 4096),
    }

    try:
        logger.info(f"Forwarding to Kimi API: persona={persona_id}")

        response = requests.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=kimi_payload,
            timeout=120,
        )
        response.raise_for_status()

        result = response.json()

        return jsonify(
            {
                "status": "success",
                "persona": persona_id,
                "persona_name": PERSONAS[persona_id]["name"],
                "response": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "model": result.get("model", "unknown"),
            }
        )

    except requests.exceptions.Timeout:
        logger.error("Kimi API timeout")
        return jsonify({"error": "Request timeout"}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Kimi API error: {e}")
        return jsonify({"error": f"Kimi API error: {str(e)}"}), 502


@app.route("/api/v1/batch", methods=["POST"])
@require_api_key
def batch_process():
    """
    Batch-Verarbeitung mehrerer Anfragen

    Request Body:
    {
        "requests": [
            {"persona": "recon", "message": "..."},
            {"persona": "exploit", "message": "..."}
        ]
    }
    """
    data = request.get_json()

    if not data or "requests" not in data:
        return jsonify({"error": "'requests' array required"}), 400

    requests_list = data["requests"]
    if not isinstance(requests_list, list):
        return jsonify({"error": "'requests' must be an array"}), 400

    if len(requests_list) > 10:
        return jsonify({"error": "Maximum 10 requests per batch"}), 400

    results = []
    for idx, req in enumerate(requests_list):
        persona_id = req.get("persona", "recon")
        message = req.get("message", "")

        if persona_id not in PERSONAS:
            results.append({"index": idx, "status": "error", "error": f"Unknown persona: {persona_id}"})
        else:
            system_prompt = load_persona_content(persona_id)
            results.append(
                {
                    "index": idx,
                    "status": "ready",
                    "persona": persona_id,
                    "persona_name": PERSONAS[persona_id]["name"],
                    "system_prompt_loaded": system_prompt is not None,
                    "message_length": len(message),
                }
            )

    return jsonify({"batch_size": len(requests_list), "results": results})


# ═════════════════════════════════════════════════════════════════════════════
# WEBSOCKET ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════


@sock.route("/ws/chat")
def ws_chat(ws):
    """WebSocket für Streaming Chat"""
    import json

    ws.send(json.dumps({"type": "system", "message": "WebSocket verbunden. Sende JSON: {persona: 'recon', message: '...'}"}))

    while True:
        try:
            data = ws.receive()
            if not data:
                break

            msg = json.loads(data)
            persona_id = msg.get("persona", "recon")
            message = msg.get("message", "")

            if persona_id not in PERSONAS:
                ws.send(json.dumps({"type": "error", "message": f"Unknown persona: {persona_id}"}))
                continue

            # Load system prompt
            system_prompt = load_persona_content(persona_id)
            if not system_prompt:
                ws.send(json.dumps({"type": "error", "message": f"Could not load persona '{persona_id}'"}))
                continue

            # Send acknowledgment
            ws.send(json.dumps({"type": "status", "persona": persona_id, "status": "processing"}))

            # Check if we should call Kimi API
            config = load_config()
            api_key = config.get("backends", {}).get("kimi_api_key")

            if api_key and msg.get("stream", False):
                # Stream from Kimi API
                ws.send(json.dumps({"type": "chunk", "content": "🤖 Denke nach..."}))

                # Note: Actual streaming would require SSE or chunked response
                # For now, send complete response
                ws.send(
                    json.dumps(
                        {
                            "type": "complete",
                            "persona": persona_id,
                            "content": (
                                f"[Simulierte Antwort von {PERSONAS[persona_id]['name']}]\n" f"\nAnfrage: {message[:100]}..."
                            ),
                        }
                    )
                )
            else:
                # Mock response for testing
                ws.send(
                    json.dumps(
                        {
                            "type": "complete",
                            "persona": persona_id,
                            "persona_name": PERSONAS[persona_id]["name"],
                            "content": (
                                f"✅ Anfrage empfangen!\n\nPersona: {PERSONAS[persona_id]['name']}\n"
                                f"Nachricht: {message[:200]}...\n\n"
                                "Für echte Antwort: API Key in config.json "
                                "hinterlegen und stream=true setzen."
                            ),
                        }
                    )
                )

        except json.JSONDecodeError:
            ws.send(json.dumps({"type": "error", "message": "Invalid JSON"}))
        except Exception as e:
            ws.send(json.dumps({"type": "error", "message": str(e)}))
            break


# ═════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═════════════════════════════════════════════════════════════════════════════


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found", "available": "/api/v1/health, /api/v1/personas, /api/v1/chat"}), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal error: {e}")
    return jsonify({"error": "Internal server error"}), 500


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Kimi Personas API Server")
    parser.add_argument("-H", "--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("-p", "--port", type=int, default=5000, help="Port to bind (default: 5000)")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    parser.add_argument("--no-auth", action="store_true", help="Disable API key auth (dev only!)")

    args = parser.parse_args()

    if args.no_auth:
        logger.warning("⚠️ API key authentication disabled!")
        app.config["DISABLE_AUTH"] = True

    print(f"""
🚀 Kimi Personas API Server
═══════════════════════════════════════════════════════════════
Host:       {args.host}
Port:       {args.port}
Debug:      {args.debug}
Auth:       {'disabled' if args.no_auth else 'enabled'}
Personas:   {len(PERSONAS)}

Endpoints:
  GET  /api/v1/health          - Health check
  GET  /api/v1/personas        - List all personas
  GET  /api/v1/personas/<id>   - Get persona details
  POST /api/v1/chat            - Chat with persona
  POST /api/v1/chat/complete   - Chat with Kimi API integration

Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
═══════════════════════════════════════════════════════════════
""")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
