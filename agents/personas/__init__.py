#!/usr/bin/env python3
"""
Zen-AI-Pentest Personas Module

This module contains specialized AI personas for different aspects of penetration testing.
Each persona has specific expertise, tools, and methodologies.

Available Personas:
    - WebAppExpertPersona: OWASP Top 10, web vulnerabilities
    - APISecurityExpertPersona: REST/GraphQL API security
    - CloudSecurityExpertPersona: AWS/Azure/GCP security
    - CryptoExpertPersona: SSL/TLS and cryptographic analysis
    - ForensicsExpertPersona: Digital forensics and incident response
    - SocialEngineeringExpertPersona: OSINT and authorized social engineering

Example:
    >>> from agents.personas import WebAppExpertPersona
    >>> persona = WebAppExpertPersona("WebApp Agent")
    >>> results = await persona.execute_task({
    ...     "type": "webapp_scan",
    ...     "context": {"target": "example.com"}
    ... })
"""

from typing import Any, Dict

from .api_security_expert import APISecurityExpertPersona
from .cloud_security_expert import CloudSecurityExpertPersona
from .crypto_expert import CryptoExpertPersona
from .forensics_expert import ForensicsExpertPersona
from .social_engineering_expert import SocialEngineeringExpertPersona
from .webapp_expert import WebAppExpertPersona

__all__ = [
    "WebAppExpertPersona",
    "APISecurityExpertPersona",
    "CloudSecurityExpertPersona",
    "CryptoExpertPersona",
    "ForensicsExpertPersona",
    "SocialEngineeringExpertPersona",
]

__version__ = "1.0.0"
__author__ = "SHAdd0WTAka"

# Persona Registry for easy lookup
PERSONA_REGISTRY = {
    "webapp_expert": {
        "class": WebAppExpertPersona,
        "name": "WebApp Expert",
        "description": "Specialized in web application penetration testing",
        "icon": "🌐",
        "tags": ["web", "owasp", "sqli", "xss", "csrf"],
    },
    "api_security_expert": {
        "class": APISecurityExpertPersona,
        "name": "API Security Expert",
        "description": "Specialized in REST and GraphQL API security",
        "icon": "🔌",
        "tags": ["api", "rest", "graphql", "jwt", "bola"],
    },
    "cloud_security_expert": {
        "class": CloudSecurityExpertPersona,
        "name": "Cloud Security Expert",
        "description": "Specialized in AWS, Azure, and GCP security",
        "icon": "☁️",
        "tags": ["cloud", "aws", "azure", "gcp", "iam", "s3"],
    },
    "crypto_expert": {
        "class": CryptoExpertPersona,
        "name": "Cryptography Expert",
        "description": "Specialized in SSL/TLS and cryptographic analysis",
        "icon": "🔐",
        "tags": ["crypto", "ssl", "tls", "certificates", "ciphers"],
    },
    "forensics_expert": {
        "class": ForensicsExpertPersona,
        "name": "Forensics Expert",
        "description": "Specialized in digital forensics and incident response",
        "icon": "🔍",
        "tags": ["forensics", "memory", "logs", "timeline", "ioc"],
    },
    "social_engineering_expert": {
        "class": SocialEngineeringExpertPersona,
        "name": "Social Engineering Expert",
        "description": "Specialized in OSINT and authorized social engineering",
        "icon": "🎭",
        "tags": ["osint", "phishing", "social", "recon", "breach"],
    },
}


def get_persona(persona_id: str):
    """
    Get a persona class by ID.

    Args:
        persona_id: The persona identifier (e.g., 'webapp_expert')

    Returns:
        The persona class

    Raises:
        KeyError: If persona_id is not found

    Example:
        >>> PersonaClass = get_persona("webapp_expert")
        >>> persona = PersonaClass("My Agent")
    """
    if persona_id not in PERSONA_REGISTRY:
        raise KeyError(f"Persona '{persona_id}' not found. Available: {list(PERSONA_REGISTRY.keys())}")
    return PERSONA_REGISTRY[persona_id]["class"]


def list_personas():
    """
    List all available personas.

    Returns:
        Dictionary of persona IDs and their metadata

    Example:
        >>> personas = list_personas()
        >>> for pid, info in personas.items():
        ...     print(f"{info['icon']} {info['name']}: {info['description']}")
    """
    return {
        pid: {
            "name": info["name"],
            "description": info["description"],
            "icon": info["icon"],
            "tags": info["tags"],
        }
        for pid, info in PERSONA_REGISTRY.items()
    }


def create_persona(persona_id: str, name: str = None, **kwargs):
    """
    Create a persona instance by ID.

    Args:
        persona_id: The persona identifier
        name: Optional custom name for the persona instance
        **kwargs: Additional arguments passed to persona constructor

    Returns:
        Instantiated persona object

    Example:
        >>> persona = create_persona("webapp_expert", "Web Scanner")
        >>> await persona.execute_task({"type": "webapp_scan", "context": {...}})
    """
    persona_class = get_persona(persona_id)
    instance_name = name or PERSONA_REGISTRY[persona_id]["name"]
    return persona_class(instance_name, **kwargs)


def get_personas_by_tag(tag: str):
    """
    Get all personas matching a specific tag.

    Args:
        tag: The tag to search for

    Returns:
        List of persona IDs matching the tag

    Example:
        >>> web_personas = get_personas_by_tag("web")
        >>> print(web_personas)  # ['webapp_expert']
    """
    return [pid for pid, info in PERSONA_REGISTRY.items() if tag.lower() in [t.lower() for t in info["tags"]]]


def get_persona_info(persona_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a persona.

    Args:
        persona_id: The persona identifier

    Returns:
        Dictionary with persona details including expertise and tools
    """
    if persona_id not in PERSONA_REGISTRY:
        raise KeyError(f"Persona '{persona_id}' not found")

    persona_class = PERSONA_REGISTRY[persona_id]["class"]

    return {
        "id": persona_id,
        "name": persona_class.name,
        "description": persona_class.description,
        "icon": PERSONA_REGISTRY[persona_id]["icon"],
        "expertise": persona_class.expertise,
        "tools": persona_class.tools,
        "tags": PERSONA_REGISTRY[persona_id]["tags"],
    }
