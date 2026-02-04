"""
Rate Limiting für Zen-AI-Pentest API

Schützt API vor:
- Brute Force Angriffen
- DoS Attacken
- API Missbrauch
"""

import os
import time
from typing import Dict, Optional, Callable
from functools import wraps
from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

# Rate limits from environment variables
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
RATE_LIMIT_BURST_SIZE = int(os.getenv("RATE_LIMIT_BURST_SIZE", "10"))

# Stricter limits for auth endpoints
AUTH_RATE_LIMIT = int(os.getenv("AUTH_RATE_LIMIT", "5"))  # 5 attempts per minute


# =============================================================================
# Token Bucket Rate Limiter
# =============================================================================

class TokenBucket:
    """
    Token Bucket Algorithm für Rate Limiting.
    
    Ermöglicht:
    - Bursts von Requests (bis zu burst_size)
    - Gleichmäßige Rate im Durchschnitt
    """
    
    def __init__(self, rate: int, burst_size: int):
        """
        Args:
            rate: Tokens pro Minute
            burst_size: Maximale Token-Anzahl (Burst)
        """
        self.rate = rate
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self.lock = False
    
    def _add_tokens(self):
        """Fügt Tokens basierend auf vergangener Zeit hinzu"""
        now = time.time()
        time_passed = now - self.last_update
        tokens_to_add = (time_passed / 60) * self.rate
        
        self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
        self.last_update = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Versucht Tokens zu verbrauchen.
        
        Returns:
            True wenn erfolgreich, False wenn Rate Limit überschritten
        """
        self._add_tokens()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Berechnet Wartezeit bis genug Tokens verfügbar"""
        if self.tokens >= tokens:
            return 0
        
        tokens_needed = tokens - self.tokens
        return (tokens_needed / self.rate) * 60


# =============================================================================
# Rate Limit Storage
# =============================================================================

class RateLimitStorage:
    """
    Speichert Rate Limit Buckets pro Client.
    
    In Produktion: Redis verwenden für verteilte Systeme!
    """
    
    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        self.last_access: Dict[str, float] = {}
    
    def get_bucket(self, key: str, rate: int, burst_size: int) -> TokenBucket:
        """Holt oder erstellt Bucket für Client"""
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(rate, burst_size)
        
        self.last_access[key] = time.time()
        return self.buckets[key]
    
    def cleanup_old_buckets(self, max_age: float = 3600):
        """Entfernt alte Buckets (Housekeeping)"""
        now = time.time()
        to_remove = [
            key for key, last in self.last_access.items()
            if now - last > max_age
        ]
        for key in to_remove:
            del self.buckets[key]
            del self.last_access[key]


# Global storage
rate_limit_storage = RateLimitStorage()


# =============================================================================
# Rate Limiting Decorator
# =============================================================================

def rate_limit(requests_per_minute: int = None, burst_size: int = None):
    """
    Decorator für Rate Limiting auf Endpoints.
    
    Usage:
        @app.get("/api/data")
        @rate_limit(requests_per_minute=30)
        async def get_data():
            return {"data": "value"}
    """
    rpm = requests_per_minute or RATE_LIMIT_REQUESTS_PER_MINUTE
    burst = burst_size or RATE_LIMIT_BURST_SIZE
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Finde Request Objekt
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Kein Request Objekt gefunden - Rate Limit nicht anwendbar
                return await func(*args, **kwargs)
            
            # Client Identifikation
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "")
            key = f"{client_ip}:{user_agent[:50]}"  # Limit key
            
            # Rate Limit prüfen
            bucket = rate_limit_storage.get_bucket(key, rpm, burst)
            
            if not bucket.consume():
                wait_time = bucket.get_wait_time()
                logger.warning(f"Rate limit exceeded for {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {wait_time:.0f} seconds.",
                    headers={"Retry-After": str(int(wait_time))}
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# =============================================================================
# Middleware für globales Rate Limiting
# =============================================================================

class RateLimitMiddleware:
    """
    ASGI Middleware für globales Rate Limiting.
    
    Usage:
        app.add_middleware(RateLimitMiddleware)
    """
    
    def __init__(self, app, requests_per_minute: int = None, burst_size: int = None):
        self.app = app
        self.rpm = requests_per_minute or RATE_LIMIT_REQUESTS_PER_MINUTE
        self.burst = burst_size or RATE_LIMIT_BURST_SIZE
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Client identifizieren
        client = scope.get("client")
        client_ip = client[0] if client else "unknown"
        
        # Rate Limit prüfen
        bucket = rate_limit_storage.get_bucket(client_ip, self.rpm, self.burst)
        
        if not bucket.consume():
            wait_time = bucket.get_wait_time()
            logger.warning(f"Global rate limit exceeded for {client_ip}")
            
            # 429 Response
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"retry-after", str(int(wait_time)).encode()]
                ]
            })
            await send({
                "type": "http.response.body",
                "body": f'"Rate limit exceeded. Retry after {int(wait_time)} seconds."'.encode()
            })
            return
        
        await self.app(scope, receive, send)


# =============================================================================
# Auth-spezifisches Rate Limiting
# =============================================================================

class AuthRateLimiter:
    """
    Spezielles Rate Limiting für Auth-Endpunkte.
    
    Stricktere Limits gegen Brute Force.
    """
    
    def __init__(self):
        self.failed_attempts: Dict[str, list] = {}  # IP -> list of timestamps
        self.lockout_duration = 300  # 5 Minuten Lockout
        self.max_attempts = 5  # 5 Versuche pro Minute
    
    def is_allowed(self, client_ip: str) -> tuple[bool, Optional[int]]:
        """
        Prüft ob Auth-Versuch erlaubt.
        
        Returns:
            (allowed, lockout_seconds)
        """
        now = time.time()
        
        # Alte Einträge entfernen (älter als 1 Minute)
        if client_ip in self.failed_attempts:
            self.failed_attempts[client_ip] = [
                t for t in self.failed_attempts[client_ip]
                if now - t < 60
            ]
        
        attempts = len(self.failed_attempts.get(client_ip, []))
        
        if attempts >= self.max_attempts:
            # Lockout prüfen
            oldest_attempt = min(self.failed_attempts[client_ip])
            lockout_remaining = self.lockout_duration - (now - oldest_attempt)
            
            if lockout_remaining > 0:
                return False, int(lockout_remaining)
            else:
                # Lockout abgelaufen, zurücksetzen
                self.failed_attempts[client_ip] = []
        
        return True, None
    
    def record_failure(self, client_ip: str):
        """Speichert fehlgeschlagenen Versuch"""
        if client_ip not in self.failed_attempts:
            self.failed_attempts[client_ip] = []
        self.failed_attempts[client_ip].append(time.time())
    
    def record_success(self, client_ip: str):
        """Löscht Failed Attempts bei Erfolg"""
        if client_ip in self.failed_attempts:
            del self.failed_attempts[client_ip]


# Global auth rate limiter
auth_rate_limiter = AuthRateLimiter()


def check_auth_rate_limit(client_ip: str):
    """
    Prüft Auth Rate Limit und wirft Exception falls überschritten.
    """
    allowed, lockout = auth_rate_limiter.is_allowed(client_ip)
    
    if not allowed:
        logger.warning(f"Auth rate limit exceeded for {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please try again in {lockout} seconds.",
            headers={"Retry-After": str(lockout)}
        )


def record_auth_failure(client_ip: str):
    """Record failed auth attempt"""
    auth_rate_limiter.record_failure(client_ip)


def record_auth_success(client_ip: str):
    """Record successful auth"""
    auth_rate_limiter.record_success(client_ip)
