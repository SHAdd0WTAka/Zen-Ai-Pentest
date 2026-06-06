"""
Enhanced Guardrails Validator for AI Pentest Agents
Implements comprehensive security controls with threat intelligence
"""

import asyncio
import hashlib
import ipaddress
import json
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import aiohttp
import redis.asyncio as redis


class RiskLevel(Enum):
    """Risk levels 0-3 as per requirements"""

    INFO = 0  # Passive reconnaissance only
    LOW = 1  # Active scanning, no exploitation
    MEDIUM = 2  # Exploitation with restrictions
    HIGH = 3  # Full exploitation (requires explicit approval)


class ActionType(Enum):
    """Types of actions agents can perform"""

    DNS_LOOKUP = "dns_lookup"
    PORT_SCAN = "port_scan"
    VULNERABILITY_SCAN = "vulnerability_scan"
    EXPLOITATION = "exploitation"
    PAYLOAD_DEPLOYMENT = "payload_deployment"
    DATA_EXFILTRATION = "data_exfiltration"
    LATERAL_MOVEMENT = "lateral_movement"
    PERSISTENCE = "persistence"
    CLEANUP = "cleanup"


class ValidationResult(Enum):
    """Result of guardrail validation"""

    ALLOWED = "allowed"
    DENIED = "denied"
    ESCALATION_REQUIRED = "escalation_required"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"


@dataclass
class GuardrailDecision:
    """Decision from guardrail validation"""

    result: ValidationResult
    action_type: ActionType
    risk_level: RiskLevel
    agent_id: str
    timestamp: datetime
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    escalation_token: Optional[str] = None


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    cooldown_seconds: int = 60


@dataclass
class BudgetConfig:
    """Budget/consumption limits"""

    max_api_calls_per_day: int = 10000
    max_compute_minutes_per_day: int = 480  # 8 hours
    max_storage_mb: int = 1024
    max_network_egress_mb: int = 5120  # 5 GB


@dataclass
class ThreatIntelligenceEntry:
    """Threat intelligence entry for IP/domain"""

    indicator: str  # IP or domain
    indicator_type: str  # "ip", "domain", "url"
    threat_type: str  # "malware", "phishing", "c2", etc.
    confidence: float  # 0-1
    severity: str  # "low", "medium", "high", "critical"
    first_seen: datetime
    last_seen: datetime
    sources: List[str]
    tags: List[str]


class IPDomainFilter:
    """
    IP and domain filtering with threat intelligence integration
    """

    # Default blocked patterns
    BLOCKED_PATTERNS = [
        r"localhost",
        r"127\.\d+\.\d+\.\d+",
        r"10\.\d+\.\d+\.\d+",
        r"172\.(1[6-9]|2[0-9]|3[01])\.\d+\.\d+",
        r"192\.168\.\d+\.\d+",
        r"169\.254\.\d+\.\d+",
        r"0\.0\.0\.0",
        r"::1",
        r"fc00:",
        r"fe80:",
    ]

    # Government TLDs to block
    GOV_TLDS = {".gov", ".mil", ".gov.uk", ".gob", ".gouv", ".gov.au"}

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        threat_intel_api_key: Optional[str] = None,
    ):
        self.redis = None
        self.redis_url = redis_url
        self.threat_intel_api_key = threat_intel_api_key

        # Blocked lists
        self._blocked_ips: Set[str] = set()
        self._blocked_domains: Set[str] = set()
        self._blocked_patterns: List[re.Pattern] = [re.compile(p, re.IGNORECASE) for p in self.BLOCKED_PATTERNS]

        # Allowed lists (whitelist)
        self._allowed_ips: Set[str] = set()
        self._allowed_domains: Set[str] = set()

        # Threat intelligence cache
        self._threat_intel_cache: Dict[str, ThreatIntelligenceEntry] = {}

        # Custom rules
        self._custom_rules: List[Callable] = []

    async def connect(self):
        self.redis = await redis.from_url(self.redis_url)

    def add_blocked_ip(self, ip: str):
        """Add IP to blocklist"""
        self._blocked_ips.add(ip)

    def add_blocked_domain(self, domain: str):
        """Add domain to blocklist"""
        self._blocked_domains.add(domain.lower())

    def add_allowed_ip(self, ip: str):
        """Add IP to whitelist"""
        self._allowed_ips.add(ip)

    def add_allowed_domain(self, domain: str):
        """Add domain to whitelist"""
        self._allowed_domains.add(domain.lower())

    def is_ip_blocked(self, ip: str) -> Tuple[bool, Optional[str]]:
        """Check if IP is blocked"""
        # Check whitelist first
        if ip in self._allowed_ips:
            return False, None

        # Check explicit blocklist
        if ip in self._blocked_ips:
            return True, "IP in blocklist"

        # Check patterns
        for pattern in self._blocked_patterns:
            if pattern.match(ip):
                return True, f"IP matches blocked pattern: {pattern.pattern}"

        # Check if private IP
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
                return True, "Private/reserved IP address"
        except ValueError:
            pass

        return False, None

    def is_domain_blocked(self, domain: str) -> Tuple[bool, Optional[str]]:
        """Check if domain is blocked"""
        domain_lower = domain.lower()

        # Check whitelist first
        if domain_lower in self._allowed_domains:
            return False, None

        # Check explicit blocklist
        if domain_lower in self._blocked_domains:
            return True, "Domain in blocklist"

        # Check government TLDs
        for tld in self.GOV_TLDS:
            if domain_lower.endswith(tld):
                return True, f"Government domain (TLD: {tld})"

        # Check patterns
        for pattern in self._blocked_patterns:
            if pattern.match(domain):
                return True, "Domain matches blocked pattern"

        # Run custom rules
        for rule in self._custom_rules:
            result = rule(domain)
            if result[0]:
                return result

        return False, None

    async def check_threat_intelligence(
        self, indicator: str, indicator_type: str = "auto"
    ) -> Optional[ThreatIntelligenceEntry]:
        """
        Check threat intelligence for indicator

        Args:
            indicator: IP, domain, or URL to check
            indicator_type: "ip", "domain", "url", or "auto"

        Returns:
            ThreatIntelligenceEntry if found, None otherwise
        """
        # Check cache first
        cache_key = f"ti:{indicator}"
        if indicator in self._threat_intel_cache:
            entry = self._threat_intel_cache[indicator]
            # Cache for 1 hour
            if datetime.now(timezone.utc) - entry.last_seen < timedelta(hours=1):
                return entry

        # Check Redis cache
        if self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                return ThreatIntelligenceEntry(**data)

        # Query threat intelligence sources
        entry = await self._query_threat_intel(indicator, indicator_type)

        if entry:
            # Cache result
            self._threat_intel_cache[indicator] = entry
            if self.redis:
                await self.redis.setex(
                    cache_key,
                    3600,  # 1 hour
                    json.dumps(
                        {
                            "indicator": entry.indicator,
                            "indicator_type": entry.indicator_type,
                            "threat_type": entry.threat_type,
                            "confidence": entry.confidence,
                            "severity": entry.severity,
                            "first_seen": entry.first_seen.isoformat(),
                            "last_seen": entry.last_seen.isoformat(),
                            "sources": entry.sources,
                            "tags": entry.tags,
                        }
                    ),
                )

        return entry

    async def _query_threat_intel(self, indicator: str, indicator_type: str) -> Optional[ThreatIntelligenceEntry]:
        """Query external threat intelligence sources"""
        # Auto-detect type
        if indicator_type == "auto":
            try:
                ipaddress.ip_address(indicator)
                indicator_type = "ip"
            except ValueError:
                indicator_type = "domain"

        # Query VirusTotal
        if self.threat_intel_api_key:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"https://www.virustotal.com/api/v3/{indicator_type}s/{indicator}"
                    headers = {"x-apikey": self.threat_intel_api_key}

                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            attrs = data.get("data", {}).get("attributes", {})

                            # Calculate threat score
                            stats = attrs.get("last_analysis_stats", {})
                            malicious = stats.get("malicious", 0)
                            suspicious = stats.get("suspicious", 0)
                            total = sum(stats.values()) if stats else 1

                            confidence = (malicious + suspicious) / total if total > 0 else 0

                            if confidence > 0.1:  # At least 10% detection
                                severity = "low"
                                if confidence > 0.5:
                                    severity = "critical"
                                elif confidence > 0.3:
                                    severity = "high"
                                elif confidence > 0.1:
                                    severity = "medium"

                                return ThreatIntelligenceEntry(
                                    indicator=indicator,
                                    indicator_type=indicator_type,
                                    threat_type="malicious",
                                    confidence=confidence,
                                    severity=severity,
                                    first_seen=datetime.now(timezone.utc),
                                    last_seen=datetime.now(timezone.utc),
                                    sources=["virustotal"],
                                    tags=[],
                                )
            except Exception as e:
                print(f"Threat intel query failed: {e}")

        return None

    def add_custom_rule(self, rule: Callable[[str], Tuple[bool, Optional[str]]]):
        """Add custom validation rule"""
        self._custom_rules.append(rule)

    async def validate_target(
        self, target: str, check_threat_intel: bool = True
    ) -> Tuple[bool, Optional[str], Optional[ThreatIntelligenceEntry]]:
        """
        Validate target (IP or domain)

        Returns:
            Tuple of (is_allowed, reason, threat_intel_entry)
        """
        # Parse target
        parsed = urlparse(target)
        host = parsed.hostname or target

        # Check if IP
        try:
            ipaddress.ip_address(host)
            is_ip = True
        except ValueError:
            is_ip = False

        # Check blocklists
        if is_ip:
            blocked, reason = self.is_ip_blocked(host)
        else:
            blocked, reason = self.is_domain_blocked(host)

        if blocked:
            return False, reason, None

        # Check threat intelligence
        threat_entry = None
        if check_threat_intel:
            threat_entry = await self.check_threat_intelligence(host)
            if threat_entry and threat_entry.severity in ["high", "critical"]:
                return (
                    False,
                    f"Threat intelligence: {threat_entry.threat_type}",
                    threat_entry,
                )

        return True, None, threat_entry


class CommandValidator:
    """
    Command validation and sanitization
    """

    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"mkfs\.",
        r"dd\s+if=.*of=/dev/",
        r">",
        r">>",
        r"\|\s*sh",
        r"\|\s*bash",
        r"eval\s*\(",
        r"exec\s*\(",
        r"system\s*\(",
        r"`.*`",
        r"\$\(.*\)",
    ]

    # Allowed command prefixes per risk level
    ALLOWED_COMMANDS = {
        RiskLevel.INFO: [
            "nslookup",
            "dig",
            "host",
            "whois",
            "curl",
            "wget",
            "ping",
            "traceroute",
            "nmap -sL",
            "nmap -sn",
        ],
        RiskLevel.LOW: [
            "nmap",
            "nikto",
            "dirb",
            "gobuster",
            "whatweb",
            "sslscan",
            "testssl.sh",
            "wapiti",
        ],
        RiskLevel.MEDIUM: [
            "sqlmap",
            "metasploit",
            "burp",
            "owasp-zap",
            "beef",
            "setoolkit",
        ],
        RiskLevel.HIGH: ["msfvenom", "msfconsole", " Empire", "cobaltstrike"],
    }

    def __init__(self):
        self._dangerous_patterns = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
        self._custom_sanitizers: List[Callable] = []

    def validate_command(self, command: str, risk_level: RiskLevel, agent_id: str) -> Tuple[bool, Optional[str], str]:
        """
        Validate and sanitize command

        Returns:
            Tuple of (is_valid, reason, sanitized_command)
        """

        # Check dangerous patterns
        for pattern in self._dangerous_patterns:
            if pattern.search(command):
                return (
                    False,
                    f"Command contains dangerous pattern: {pattern.pattern}",
                    "",
                )

        # Check allowed commands for risk level
        allowed = self.ALLOWED_COMMANDS.get(risk_level, [])
        command_prefix = command.split()[0] if command.split() else ""

        if risk_level != RiskLevel.HIGH:
            is_allowed = any(command.startswith(cmd) or command_prefix == cmd.split()[0] for cmd in allowed)
            if not is_allowed:
                return (
                    False,
                    f"Command not allowed at risk level {risk_level.name}",
                    "",
                )

        # Sanitize command
        sanitized = self._sanitize_command(command)

        # Run custom sanitizers
        for sanitizer in self._custom_sanitizers:
            sanitized = sanitizer(sanitized)

        return True, None, sanitized

    def _sanitize_command(self, command: str) -> str:
        """Basic command sanitization"""
        # Remove shell injection attempts
        sanitized = command

        # Escape special characters
        dangerous_chars = [
            ";",
            "&",
            "|",
            "`",
            "$",
            "(",
            ")",
            "{",
            "}",
            "<",
            ">",
        ]
        for char in dangerous_chars:
            if char in sanitized:
                # Only escape if not part of valid syntax
                pass  # Implement context-aware escaping

        return sanitized

    def add_custom_sanitizer(self, sanitizer: Callable[[str], str]):
        """Add custom command sanitizer"""
        self._custom_sanitizers.append(sanitizer)


class RateLimiter:
    """
    Rate limiting per agent with burst handling
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = None
        self.redis_url = redis_url
        self._local_counters: Dict[str, Dict] = {}
        self._configs: Dict[str, RateLimitConfig] = {}

    async def connect(self):
        self.redis = await redis.from_url(self.redis_url)

    def set_agent_config(self, agent_id: str, config: RateLimitConfig):
        """Set rate limit config for agent"""
        self._configs[agent_id] = config

    async def check_rate_limit(self, agent_id: str, action_type: ActionType) -> Tuple[bool, Optional[str], Dict]:
        """
        Check if action is within rate limits

        Returns:
            Tuple of (allowed, reason, rate_limit_info)
        """
        config = self._configs.get(agent_id, RateLimitConfig())

        # Redis-based rate limiting
        if self.redis:
            minute_key = f"ratelimit:{agent_id}:{action_type.value}:minute"
            hour_key = f"ratelimit:{agent_id}:{action_type.value}:hour"

            # Increment counters
            minute_count = await self.redis.incr(minute_key)
            if minute_count == 1:
                await self.redis.expire(minute_key, 60)

            hour_count = await self.redis.incr(hour_key)
            if hour_count == 1:
                await self.redis.expire(hour_key, 3600)

            # Check limits
            if minute_count > config.requests_per_minute:
                return (
                    False,
                    "Rate limit exceeded (per minute)",
                    {
                        "minute_count": minute_count,
                        "minute_limit": config.requests_per_minute,
                        "retry_after": 60,
                    },
                )

            if hour_count > config.requests_per_hour:
                return (
                    False,
                    "Rate limit exceeded (per hour)",
                    {
                        "hour_count": hour_count,
                        "hour_limit": config.requests_per_hour,
                        "retry_after": 3600,
                    },
                )

            return (
                True,
                None,
                {
                    "minute_count": minute_count,
                    "minute_limit": config.requests_per_minute,
                    "hour_count": hour_count,
                    "hour_limit": config.requests_per_hour,
                    "remaining": config.requests_per_minute - minute_count,
                },
            )

        # Local rate limiting fallback
        return await self._local_rate_limit(agent_id, action_type, config)

    async def _local_rate_limit(
        self, agent_id: str, action_type: ActionType, config: RateLimitConfig
    ) -> Tuple[bool, Optional[str], Dict]:
        """Local in-memory rate limiting"""
        key = f"{agent_id}:{action_type.value}"
        now = datetime.now(timezone.utc)

        if key not in self._local_counters:
            self._local_counters[key] = {
                "minute_start": now,
                "minute_count": 0,
                "hour_start": now,
                "hour_count": 0,
            }

        counter = self._local_counters[key]

        # Reset minute counter
        if (now - counter["minute_start"]).seconds >= 60:
            counter["minute_start"] = now
            counter["minute_count"] = 0

        # Reset hour counter
        if (now - counter["hour_start"]).seconds >= 3600:
            counter["hour_start"] = now
            counter["hour_count"] = 0

        counter["minute_count"] += 1
        counter["hour_count"] += 1

        if counter["minute_count"] > config.requests_per_minute:
            return (
                False,
                "Rate limit exceeded (per minute)",
                {
                    "minute_count": counter["minute_count"],
                    "minute_limit": config.requests_per_minute,
                },
            )

        if counter["hour_count"] > config.requests_per_hour:
            return (
                False,
                "Rate limit exceeded (per hour)",
                {
                    "hour_count": counter["hour_count"],
                    "hour_limit": config.requests_per_hour,
                },
            )

        return (
            True,
            None,
            {
                "minute_count": counter["minute_count"],
                "minute_remaining": config.requests_per_minute - counter["minute_count"],
                "hour_count": counter["hour_count"],
                "hour_remaining": config.requests_per_hour - counter["hour_count"],
            },
        )


class BudgetManager:
    """
    Budget and consumption limits per agent
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = None
        self.redis_url = redis_url
        self._configs: Dict[str, BudgetConfig] = {}
        self._usage: Dict[str, Dict] = {}

    async def connect(self):
        self.redis = await redis.from_url(self.redis_url)

    def set_agent_budget(self, agent_id: str, config: BudgetConfig):
        """Set budget for agent"""
        self._configs[agent_id] = config

    async def check_budget(
        self,
        agent_id: str,
        operation_type: str,
        estimated_cost: Dict[str, float],
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Check if operation is within budget

        Args:
            agent_id: Agent identifier
            operation_type: Type of operation
            estimated_cost: Estimated resource consumption

        Returns:
            Tuple of (allowed, reason, budget_info)
        """
        config = self._configs.get(agent_id, BudgetConfig())

        # Get current usage
        usage = await self._get_usage(agent_id)

        # Check API calls
        api_calls = usage.get("api_calls", 0) + estimated_cost.get("api_calls", 0)
        if api_calls > config.max_api_calls_per_day:
            return (
                False,
                "API call budget exceeded",
                {
                    "used": usage.get("api_calls", 0),
                    "estimated": api_calls,
                    "limit": config.max_api_calls_per_day,
                },
            )

        # Check compute time
        compute = usage.get("compute_minutes", 0) + estimated_cost.get("compute_minutes", 0)
        if compute > config.max_compute_minutes_per_day:
            return (
                False,
                "Compute budget exceeded",
                {
                    "used": usage.get("compute_minutes", 0),
                    "estimated": compute,
                    "limit": config.max_compute_minutes_per_day,
                },
            )

        return (
            True,
            None,
            {
                "api_calls": {
                    "used": usage.get("api_calls", 0),
                    "remaining": config.max_api_calls_per_day - api_calls,
                },
                "compute_minutes": {
                    "used": usage.get("compute_minutes", 0),
                    "remaining": config.max_compute_minutes_per_day - compute,
                },
            },
        )

    async def record_usage(self, agent_id: str, usage: Dict[str, float]):
        """Record actual resource usage"""
        if self.redis:
            key = f"budget:{agent_id}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"

            for metric, value in usage.items():
                await self.redis.hincrbyfloat(key, metric, value)

            await self.redis.expire(key, 86400 * 7)  # Keep for 7 days
        else:
            if agent_id not in self._usage:
                self._usage[agent_id] = {}

            for metric, value in usage.items():
                self._usage[agent_id][metric] = self._usage[agent_id].get(metric, 0) + value

    async def _get_usage(self, agent_id: str) -> Dict[str, float]:
        """Get current usage for agent"""
        if self.redis:
            key = f"budget:{agent_id}:{datetime.now(timezone.utc).strftime('%Y%m%d')}"
            data = await self.redis.hgetall(key)
            return {k: float(v) for k, v in data.items()}

        return self._usage.get(agent_id, {})


class EnhancedGuardrailsValidator:
    """
    Main guardrails validator combining all security controls
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        threat_intel_api_key: Optional[str] = None,
    ):
        self.ip_filter = IPDomainFilter(redis_url, threat_intel_api_key)
        self.command_validator = CommandValidator()
        self.rate_limiter = RateLimiter(redis_url)
        self.budget_manager = BudgetManager(redis_url)

        # Risk escalation handlers
        self._escalation_handlers: List[Callable] = []

        # Audit callback
        self._audit_callback: Optional[Callable] = None

    async def initialize(self):
        """Initialize all components"""
        await self.ip_filter.connect()
        await self.rate_limiter.connect()
        await self.budget_manager.connect()

    async def validate_action(
        self,
        agent_id: str,
        action_type: ActionType,
        target: Optional[str],
        command: Optional[str],
        risk_level: RiskLevel,
        estimated_cost: Optional[Dict[str, float]] = None,
    ) -> GuardrailDecision:
        """
        Validate agent action against all guardrails

        Args:
            agent_id: Agent identifier
            action_type: Type of action
            target: Target IP/domain (if applicable)
            command: Command to execute (if applicable)
            risk_level: Current risk level
            estimated_cost: Estimated resource cost

        Returns:
            GuardrailDecision with result and metadata
        """
        timestamp = datetime.now(timezone.utc)

        # 1. Validate target if provided
        if target:
            allowed, reason, threat_intel = await self.ip_filter.validate_target(target)
            if not allowed:
                decision = GuardrailDecision(
                    result=ValidationResult.DENIED,
                    action_type=action_type,
                    risk_level=risk_level,
                    agent_id=agent_id,
                    timestamp=timestamp,
                    reason=reason,
                    metadata={"target": target, "threat_intel": threat_intel},
                )
                await self._audit(decision)
                return decision

        # 2. Validate command if provided
        if command:
            valid, reason, sanitized = self.command_validator.validate_command(command, risk_level, agent_id)
            if not valid:
                decision = GuardrailDecision(
                    result=ValidationResult.DENIED,
                    action_type=action_type,
                    risk_level=risk_level,
                    agent_id=agent_id,
                    timestamp=timestamp,
                    reason=reason or "Command validation failed",
                    metadata={"command": command},
                )
                await self._audit(decision)
                return decision

        # 3. Check rate limits
        allowed, reason, rate_info = await self.rate_limiter.check_rate_limit(agent_id, action_type)
        if not allowed:
            decision = GuardrailDecision(
                result=ValidationResult.RATE_LIMITED,
                action_type=action_type,
                risk_level=risk_level,
                agent_id=agent_id,
                timestamp=timestamp,
                reason=reason,
                metadata=rate_info,
            )
            await self._audit(decision)
            return decision

        # 4. Check budget
        if estimated_cost:
            allowed, reason, budget_info = await self.budget_manager.check_budget(agent_id, action_type.value, estimated_cost)
            if not allowed:
                decision = GuardrailDecision(
                    result=ValidationResult.QUOTA_EXCEEDED,
                    action_type=action_type,
                    risk_level=risk_level,
                    agent_id=agent_id,
                    timestamp=timestamp,
                    reason=reason,
                    metadata=budget_info,
                )
                await self._audit(decision)
                return decision

        # 5. Check risk level escalation
        required_level = self._get_required_risk_level(action_type)
        if risk_level.value < required_level.value:
            # Requires escalation
            escalation_token = self._generate_escalation_token()

            decision = GuardrailDecision(
                result=ValidationResult.ESCALATION_REQUIRED,
                action_type=action_type,
                risk_level=risk_level,
                agent_id=agent_id,
                timestamp=timestamp,
                reason=f"Action requires risk level {required_level.name}, current: {risk_level.name}",
                metadata={
                    "required_level": required_level.name,
                    "current_level": risk_level.name,
                    "target": target,
                    "command": command,
                },
                escalation_token=escalation_token,
            )

            # Notify escalation handlers
            for handler in self._escalation_handlers:
                asyncio.create_task(handler(decision))

            await self._audit(decision)
            return decision

        # All checks passed
        decision = GuardrailDecision(
            result=ValidationResult.ALLOWED,
            action_type=action_type,
            risk_level=risk_level,
            agent_id=agent_id,
            timestamp=timestamp,
            reason="All guardrail checks passed",
            metadata={
                "rate_limit_info": rate_info,
                "budget_info": budget_info if estimated_cost else None,
            },
        )

        await self._audit(decision)
        return decision

    def _get_required_risk_level(self, action_type: ActionType) -> RiskLevel:
        """Get minimum required risk level for action"""
        requirements = {
            ActionType.DNS_LOOKUP: RiskLevel.INFO,
            ActionType.PORT_SCAN: RiskLevel.LOW,
            ActionType.VULNERABILITY_SCAN: RiskLevel.LOW,
            ActionType.EXPLOITATION: RiskLevel.MEDIUM,
            ActionType.PAYLOAD_DEPLOYMENT: RiskLevel.HIGH,
            ActionType.DATA_EXFILTRATION: RiskLevel.HIGH,
            ActionType.LATERAL_MOVEMENT: RiskLevel.HIGH,
            ActionType.PERSISTENCE: RiskLevel.HIGH,
            ActionType.CLEANUP: RiskLevel.MEDIUM,
        }
        return requirements.get(action_type, RiskLevel.LOW)

    def _generate_escalation_token(self) -> str:
        """Generate unique escalation token"""
        return hashlib.sha256(f"{datetime.now(timezone.utc).isoformat()}:{secrets.token_hex(16)}".encode()).hexdigest()[:32]

    async def _audit(self, decision: GuardrailDecision):
        """Audit guardrail decision"""
        if self._audit_callback:
            await self._audit_callback(decision)

    def on_escalation(self, handler: Callable):
        """Register escalation handler"""
        self._escalation_handlers.append(handler)

    def set_audit_callback(self, callback: Callable):
        """Set audit callback"""
        self._audit_callback = callback
