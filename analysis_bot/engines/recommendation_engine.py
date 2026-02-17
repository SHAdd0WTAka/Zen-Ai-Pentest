"""
Zen-Ai-Pentest AnalysisBot - Recommendation Engine Module
=========================================================
Empfehlungs-Engine fÃ¼r das Zen-Ai-Pentest Framework.

Autor: AnalysisBot
Version: 1.0.0 (2026)
"""

import json
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class RemediationPriority(Enum):
    """PrioritÃ¤t von Remediation-MaÃŸnahmen"""
    IMMEDIATE = "immediate"      # Sofort (0-24 Stunden)
    URGENT = "urgent"            # Dringend (1-3 Tage)
    HIGH = "high"                # Hoch (1 Woche)
    MEDIUM = "medium"            # Mittel (1 Monat)
    LOW = "low"                  # Niedrig (3 Monate)
    PLANNING = "planning"        # Planung (6+ Monate)


class RemediationEffort(Enum):
    """Aufwand fÃ¼r Remediation"""
    TRIVIAL = "trivial"          # < 1 Stunde
    LOW = "low"                  # 1-4 Stunden
    MEDIUM = "medium"            # 4-16 Stunden
    HIGH = "high"                # 16-40 Stunden
    MAJOR = "major"              # 40+ Stunden
    ARCHITECTURAL = "architectural"  # Erfordert Architektur-Ã„nderung


class RemediationType(Enum):
    """Art der Remediation"""
    PATCH = "patch"                      # Software-Patch anwenden
    CONFIGURATION = "configuration"      # Konfiguration Ã¤ndern
    CODE_FIX = "code_fix"                # Code-Ã„nderung
    WORKAROUND = "workaround"            # TemporÃ¤re LÃ¶sung
    COMPENSATING_CONTROL = "compensating_control"  # Kompensierende Kontrolle
    ACCEPT_RISK = "accept_risk"          # Risiko akzeptieren
    TRANSFER_RISK = "transfer_risk"      # Risiko transferieren
    AVOID_RISK = "avoid_risk"            # Risiko vermeiden
    MONITOR = "monitor"                  # Ãœberwachen


class ComplianceFramework(Enum):
    """Compliance-Frameworks"""
    ISO27001 = "ISO27001"
    NIST_CSF = "NIST_CSF"
    NIST_800_53 = "NIST_800_53"
    CIS_CONTROLS = "CIS_CONTROLS"
    PCI_DSS = "PCI_DSS"
    HIPAA = "HIPAA"
    GDPR = "GDPR"
    SOC2 = "SOC2"
    COBIT = "COBIT"
    OWASP_ASVS = "OWASP_ASVS"


@dataclass
class RemediationStep:
    """Einzelner Remediation-Schritt"""
    order: int
    description: str
    detailed_instructions: str = ""
    estimated_time: str = ""  # z.B. "30 minutes"
    required_tools: List[str] = field(default_factory=list)
    required_access: List[str] = field(default_factory=list)
    verification_method: str = ""
    rollback_procedure: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RemediationOption:
    """Remediation-Option fÃ¼r eine Schwachstelle"""
    id: str = field(default_factory=lambda: f"REM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    type: RemediationType = RemediationType.PATCH
    priority: RemediationPriority = RemediationPriority.MEDIUM
    effort: RemediationEffort = RemediationEffort.MEDIUM
    
    # Beschreibung
    title: str = ""
    description: str = ""
    justification: str = ""
    
    # Schritte
    steps: List[RemediationStep] = field(default_factory=list)
    
    # Ressourcen
    estimated_cost: str = ""  # z.B. "$500-$1000"
    required_skills: List[str] = field(default_factory=list)
    required_resources: List[str] = field(default_factory=list)
    
    # Impact
    downtime_required: bool = False
    estimated_downtime: str = ""  # z.B. "2 hours"
    user_impact: str = ""  # z.B. "minimal", "moderate", "high"
    
    # Compliance
    compliance_mappings: Dict[str, List[str]] = field(default_factory=dict)
    
    # Metadaten
    created_at: datetime = field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['type'] = self.type.value
        data['priority'] = self.priority.value
        data['effort'] = self.effort.value
        data['created_at'] = self.created_at.isoformat()
        data['valid_until'] = self.valid_until.isoformat() if self.valid_until else None
        return data


@dataclass
class Recommendation:
    """Empfehlung fÃ¼r eine Schwachstelle"""
    id: str = field(default_factory=lambda: f"REC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}")
    vulnerability_id: str = ""
    
    # Priorisierung
    priority_score: float = 0.0  # 0-100
    risk_based_priority: int = 0  # 1-n
    
    # Empfohlene Option
    recommended_option: Optional[RemediationOption] = None
    
    # Alternative Optionen
    alternative_options: List[RemediationOption] = field(default_factory=list)
    
    # ZusÃ¤tzliche Informationen
    timeline: str = ""  # Empfohlener Zeitplan
    responsible_roles: List[str] = field(default_factory=list)
    
    # Tracking
    status: str = "open"  # open, in_progress, implemented, verified, rejected
    implementation_notes: str = ""
    implemented_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    
    # Metadaten
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "RecommendationEngine"
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['recommended_option'] = self.recommended_option.to_dict() if self.recommended_option else None
        data['alternative_options'] = [opt.to_dict() for opt in self.alternative_options]
        data['created_at'] = self.created_at.isoformat()
        data['implemented_at'] = self.implemented_at.isoformat() if self.implemented_at else None
        data['verified_at'] = self.verified_at.isoformat() if self.verified_at else None
        return data


class RemediationDatabase:
    """Datenbank von Remediation-MaÃŸnahmen"""
    
    # Remediation-MaÃŸnahmen nach Schwachstellen-Kategorie
    REMEDIATIONS = {
        "sql_injection": {
            "title": "SQL Injection Remediation",
            "description": "Implement parameterized queries and input validation",
            "options": [
                {
                    "type": RemediationType.CODE_FIX,
                    "priority": RemediationPriority.IMMEDIATE,
                    "effort": RemediationEffort.MEDIUM,
                    "title": "Implement Parameterized Queries",
                    "description": "Replace all dynamic SQL with parameterized queries",
                    "steps": [
                        RemediationStep(
                            order=1,
                            description="Identify all SQL query locations",
                            detailed_instructions="Search codebase for execute(), query(), raw() methods",
                            estimated_time="1 hour",
                        ),
                        RemediationStep(
                            order=2,
                            description="Replace dynamic SQL with prepared statements",
                            detailed_instructions="Use parameterized queries with placeholders",
                            estimated_time="4 hours",
                        ),
                        RemediationStep(
                            order=3,
                            description="Test all modified queries",
                            detailed_instructions="Run unit tests and integration tests",
                            estimated_time="2 hours",
                        ),
                    ],
                    "compliance_mappings": {
                        "OWASP_ASVS": ["V5.3.4", "V5.3.5"],
                        "PCI_DSS": ["6.5.1"],
                        "CIS_CONTROLS": ["18.1"],
                    },
                },
                {
                    "type": RemediationType.COMPENSATING_CONTROL,
                    "priority": RemediationPriority.URGENT,
                    "effort": RemediationEffort.LOW,
                    "title": "Deploy Web Application Firewall",
                    "description": "Deploy WAF with SQL injection rules as temporary protection",
                    "steps": [
                        RemediationStep(
                            order=1,
                            description="Configure WAF SQL injection rules",
                            estimated_time="2 hours",
                        ),
                        RemediationStep(
                            order=2,
                            description="Test WAF blocking behavior",
                            estimated_time="1 hour",
                        ),
                    ],
                    "compliance_mappings": {
                        "PCI_DSS": ["6.6"],
                    },
                },
            ],
        },
        
        "xss": {
            "title": "Cross-Site Scripting Remediation",
            "description": "Implement output encoding and Content Security Policy",
            "options": [
                {
                    "type": RemediationType.CODE_FIX,
                    "priority": RemediationPriority.HIGH,
                    "effort": RemediationEffort.MEDIUM,
                    "title": "Implement Output Encoding",
                    "description": "Encode all output based on context",
                    "steps": [
                        RemediationStep(
                            order=1,
                            description="Identify all output locations",
                            estimated_time="2 hours",
                        ),
                        RemediationStep(
                            order=2,
                            description="Implement context-aware encoding",
                            estimated_time="4 hours",
                        ),
                        RemediationStep(
                            order=3,
                            description="Add CSP header",
                            estimated_time="1 hour",
                        ),
                    ],
                    "compliance_mappings": {
                        "OWASP_ASVS": ["V5.3.6", "V5.3.7"],
                        "PCI_DSS": ["6.5.7"],
                    },
                },
            ],
        },
        
        "command_injection": {
            "title": "Command Injection Remediation",
            "description": "Remove OS command execution with user input",
            "options": [
                {
                    "type": RemediationType.CODE_FIX,
                    "priority": RemediationPriority.IMMEDIATE,
                    "effort": RemediationEffort.MEDIUM,
                    "title": "Replace OS Commands with Safe APIs",
                    "description": "Use language-specific safe APIs instead of shell commands",
                    "steps": [
                        RemediationStep(
                            order=1,
                            description="Identify all OS command executions",
                            estimated_time="1 hour",
                        ),
                        RemediationStep(
                            order=2,
                            description="Replace with safe alternatives",
                            estimated_time="4 hours",
                        ),
                        RemediationStep(
                            order=3,
                            description="Implement strict input validation",
                            estimated_time="2 hours",
                        ),
                    ],
                    "compliance_mappings": {
                        "OWASP_ASVS": ["V5.2.4"],
                        "PCI_DSS": ["6.5.1"],
                    },
                },
            ],
        },
        
        "path_traversal": {
            "title": "Path Traversal Remediation",
            "description": "Validate and sanitize file paths",
            "options": [
                {
                    "type": RemediationType.CODE_FIX,
                    "priority": RemediationPriority.HIGH,
                    "effort": RemediationEffort.LOW,
                    "title": "Implement Path Validation",
                    "description": "Validate file paths against whitelist",
                    "steps": [
                        RemediationStep(
                            order=1,
                            description="Identify all file access points",
                            estimated_time="1 hour",
                        ),
                        RemediationStep(
                            order=2,
                            description="Implement path canonicalization",
                            estimated_time="2 hours",
                        ),
                        RemediationStep(
                            order=3,
                            description="Add whitelist validation",
                            estimated_time="1 hour",
                        ),
                    ],
                    "compliance_mappings": {
                        "OWASP_ASVS": ["V12.3.2"],
                    },
                },
            ],
        },
        
        "insecure_deserialization": {
            "title": "Insecure Deserialization Remediation",
            "description": "Use safe serialization methods",
            "options": [
                {
                    "type": RemediationType.CODE_FIX,
                    "priority": RemediationPriority.IMMEDIATE,
                    "effort": RemediationEffort.HIGH,
                    "title": "Replace Insecure Deserialization",
                    "description": "Use JSON or safe serialization libraries",
                    "steps": [
                        RemediationStep(
                            order=1,
                            description="Identify all deserialization points",
                            estimated_time="2 hours",
                        ),
                        RemediationStep(
                            order=2,
                            description="Replace with JSON serialization",
                            estimated_time="8 hours",
                        ),
                        RemediationStep(
                            order=3,
                            description="Implement integrity checks",
                            estimated_time="4 hours",
                        ),
                    ],
                    "compliance_mappings": {
                        "OWASP_ASVS": ["V5.5.1", "V5.5.2"],
                    },
                },
            ],
        },
        
        "hardcoded_secrets": {
            "title": "Hardcoded Secrets Remediation",
            "description": "Remove hardcoded credentials from code",
            "options": [
                {
                    "type": RemediationType.CODE_FIX,
                    "priority": RemediationPriority.URGENT,
                    "effort": RemediationEffort.LOW,
                    "title": "Move Secrets to Secure Storage",
                    "description": "Use environment variables or secrets manager",
                    "steps": [
                        RemediationStep(
                            order=1,
                            description="Identify all hardcoded secrets",
                            estimated_time="1 hour",
                        ),
                        RemediationStep(
                            order=2,
                            description="Move to environment variables",
                            estimated_time="2 hours",
                        ),
                        RemediationStep(
                            order=3,
                            description="Rotate exposed credentials",
                            estimated_time="1 hour",
                        ),
                    ],
                    "compliance_mappings": {
                        "OWASP_ASVS": ["V2.10.4"],
                        "PCI_DSS": ["8.2.1"],
                    },
                },
            ],
        },
        
        "missing_security_headers": {
            "title": "Security Headers Remediation",
            "description": "Add missing security headers",
            "options": [
                {
                    "type": RemediationType.CONFIGURATION,
                    "priority": RemediationPriority.MEDIUM,
                    "effort": RemediationEffort.TRIVIAL,
                    "title": "Add Security Headers",
                    "description": "Configure web server to add security headers",
                    "steps": [
                        RemediationStep(
                            order=1,
                            description="Add HSTS header",
                            estimated_time="15 minutes",
                        ),
                        RemediationStep(
                            order=2,
                            description="Add X-Frame-Options header",
                            estimated_time="15 minutes",
                        ),
                        RemediationStep(
                            order=3,
                            description="Add X-Content-Type-Options header",
                            estimated_time="15 minutes",
                        ),
                        RemediationStep(
                            order=4,
                            description="Add CSP header",
                            estimated_time="30 minutes",
                        ),
                    ],
                    "compliance_mappings": {
                        "OWASP_ASVS": ["V7.2.1", "V7.2.2"],
                    },
                },
            ],
        },
    }
    
    @classmethod
    def get_remediation(cls, category: str) -> Optional[Dict]:
        """Gibt Remediation fÃ¼r eine Kategorie zurÃ¼ck"""
        return cls.REMEDIATIONS.get(category.lower())
    
    @classmethod
    def get_all_remediations(cls) -> Dict[str, Dict]:
        """Gibt alle Remediations zurÃ¼ck"""
        return cls.REMEDIATIONS.copy()


class RecommendationEngine:
    """
    Empfehlungs-Engine fÃ¼r Schwachstellen-Remediation.
    
    Features:
    - Automatische Empfehlungsgenerierung
    - Priorisierung basierend auf Risiko
    - Compliance-Mapping
    - Aufwand-SchÃ¤tzung
    - Alternative Optionen
    """
    
    def __init__(self):
        self.recommendation_history: List[Dict] = []
        self.remediation_db = RemediationDatabase()
        
    def generate_recommendation(self, vulnerability: Dict[str, Any],
                               risk_score: Dict[str, Any],
                               exploitability: Dict[str, Any],
                               context: Optional[Dict[str, Any]] = None) -> Recommendation:
        """
        Generiert eine Empfehlung fÃ¼r eine Schwachstelle.
        
        Args:
            vulnerability: Schwachstellen-Daten
            risk_score: Risk Score Daten
            exploitability: Exploitability Assessment Daten
            context: ZusÃ¤tzlicher Kontext
            
        Returns:
            Recommendation
        """
        context = context or {}
        
        # Hole Remediation-Optionen
        category = vulnerability.get("category", "unknown")
        remediation_data = self.remediation_db.get_remediation(category)
        
        options = []
        if remediation_data:
            for opt_data in remediation_data.get("options", []):
                option = self._create_remediation_option(opt_data)
                options.append(option)
        
        # Generiere generische Option falls keine spezifische gefunden
        if not options:
            options.append(self._generate_generic_option(vulnerability))
        
        # Priorisiere Optionen
        prioritized_options = self._prioritize_options(options, risk_score, exploitability)
        
        # WÃ¤hle empfohlene Option
        recommended = prioritized_options[0] if prioritized_options else None
        alternatives = prioritized_options[1:] if len(prioritized_options) > 1 else []
        
        # Berechne PrioritÃ¤ts-Score
        priority_score = self._calculate_priority_score(
            vulnerability, risk_score, exploitability
        )
        
        # Erstelle Empfehlung
        recommendation = Recommendation(
            vulnerability_id=vulnerability.get("id", ""),
            priority_score=priority_score,
            recommended_option=recommended,
            alternative_options=alternatives,
            timeline=self._generate_timeline(recommended, risk_score),
            responsible_roles=self._determine_responsible_roles(recommended, vulnerability),
        )
        
        # Historie speichern
        self.recommendation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "vulnerability_id": vulnerability.get("id"),
            "recommendation_id": recommendation.id,
            "priority_score": priority_score,
        })
        
        return recommendation
    
    def generate_remediation_plan(self, vulnerabilities: List[Dict[str, Any]],
                                  risk_scores: List[Dict[str, Any]],
                                  team_capacity: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generiert einen umfassenden Remediation-Plan.
        
        Args:
            vulnerabilities: Liste von Schwachstellen
            risk_scores: Liste von Risk Scores
            team_capacity: Team-KapazitÃ¤t (Stunden pro Woche)
            
        Returns:
            Remediation-Plan
        """
        team_capacity = team_capacity or {"hours_per_week": 40}
        
        # Generiere Empfehlungen fÃ¼r alle Schwachstellen
        recommendations = []
        for vuln, risk in zip(vulnerabilities, risk_scores):
            rec = self.generate_recommendation(vuln, risk, {})
            recommendations.append(rec)
        
        # Sortiere nach PrioritÃ¤t
        recommendations.sort(key=lambda r: r.priority_score, reverse=True)
        
        # Weise PrioritÃ¤ten zu
        for i, rec in enumerate(recommendations):
            rec.risk_based_priority = i + 1
        
        # Gruppiere nach Zeithorizont
        immediate = [r for r in recommendations if r.recommended_option and 
                    r.recommended_option.priority == RemediationPriority.IMMEDIATE]
        urgent = [r for r in recommendations if r.recommended_option and 
                 r.recommended_option.priority == RemediationPriority.URGENT]
        high = [r for r in recommendations if r.recommended_option and 
               r.recommended_option.priority == RemediationPriority.HIGH]
        
        # SchÃ¤tze Gesamtaufwand
        total_effort = self._estimate_total_effort(recommendations)
        
        # Berechne Timeline
        weeks_needed = self._calculate_timeline(total_effort, team_capacity)
        
        return {
            "plan_id": f"PLAN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "created_at": datetime.utcnow().isoformat(),
            "total_vulnerabilities": len(vulnerabilities),
            "total_effort_hours": total_effort,
            "estimated_weeks": weeks_needed,
            "team_capacity": team_capacity,
            "phases": {
                "immediate": {
                    "count": len(immediate),
                    "timeframe": "0-24 hours",
                    "recommendations": [r.to_dict() for r in immediate],
                },
                "urgent": {
                    "count": len(urgent),
                    "timeframe": "1-3 days",
                    "recommendations": [r.to_dict() for r in urgent],
                },
                "high": {
                    "count": len(high),
                    "timeframe": "1 week",
                    "recommendations": [r.to_dict() for r in high],
                },
            },
            "all_recommendations": [r.to_dict() for r in recommendations],
        }
    
    def get_compliance_mapping(self, vulnerability_category: str,
                               framework: ComplianceFramework) -> List[str]:
        """
        Gibt Compliance-Mapping fÃ¼r eine Schwachstelle zurÃ¼ck.
        
        Args:
            vulnerability_category: Kategorie der Schwachstelle
            framework: Compliance-Framework
            
        Returns:
            Liste von Control-IDs
        """
        remediation = self.remediation_db.get_remediation(vulnerability_category)
        if not remediation:
            return []
        
        # Sammle alle Mappings aus allen Optionen
        all_mappings = []
        for opt in remediation.get("options", []):
            mappings = opt.get("compliance_mappings", {})
            framework_mappings = mappings.get(framework.value, [])
            all_mappings.extend(framework_mappings)
        
        return list(set(all_mappings))
    
    def estimate_remediation_cost(self, recommendation: Recommendation) -> Dict[str, Any]:
        """
        SchÃ¤tzt die Kosten fÃ¼r eine Remediation.
        
        Args:
            recommendation: Empfehlung
            
        Returns:
            KostenschÃ¤tzung
        """
        option = recommendation.recommended_option
        if not option:
            return {"error": "No recommended option"}
        
        # StundensÃ¤tze (Beispiel)
        hourly_rates = {
            "developer": 100,
            "security_engineer": 150,
            "system_admin": 80,
        }
        
        # SchÃ¤tze Stunden basierend auf Effort
        effort_hours = {
            RemediationEffort.TRIVIAL: 1,
            RemediationEffort.LOW: 4,
            RemediationEffort.MEDIUM: 16,
            RemediationEffort.HIGH: 40,
            RemediationEffort.MAJOR: 80,
            RemediationEffort.ARCHITECTURAL: 160,
        }
        
        hours = effort_hours.get(option.effort, 16)
        
        # Bestimme primÃ¤re Rolle
        primary_role = "developer"
        if "security" in option.required_skills:
            primary_role = "security_engineer"
        elif "admin" in option.required_skills:
            primary_role = "system_admin"
        
        labor_cost = hours * hourly_rates[primary_role]
        
        # ZusÃ¤tzliche Kosten (Tools, etc.)
        additional_costs = 0
        if option.required_resources:
            additional_costs = len(option.required_resources) * 500
        
        return {
            "labor_hours": hours,
            "hourly_rate": hourly_rates[primary_role],
            "labor_cost": labor_cost,
            "additional_costs": additional_costs,
            "total_cost": labor_cost + additional_costs,
            "primary_role": primary_role,
        }
    
    def _create_remediation_option(self, data: Dict) -> RemediationOption:
        """Erstellt RemediationOption aus Dictionary"""
        raw_steps = data.get("steps", [])
        steps = []
        for step in raw_steps:
            if isinstance(step, RemediationStep):
                steps.append(step)
            elif isinstance(step, dict):
                steps.append(RemediationStep(**step))
        
        return RemediationOption(
            type=data.get("type", RemediationType.PATCH),
            priority=data.get("priority", RemediationPriority.MEDIUM),
            effort=data.get("effort", RemediationEffort.MEDIUM),
            title=data.get("title", ""),
            description=data.get("description", ""),
            steps=steps,
            compliance_mappings=data.get("compliance_mappings", {}),
            required_skills=data.get("required_skills", []),
            required_resources=data.get("required_resources", []),
        )
    
    def _generate_generic_option(self, vulnerability: Dict) -> RemediationOption:
        """Generiert eine generische Remediation-Option"""
        return RemediationOption(
            type=RemediationType.CODE_FIX,
            priority=RemediationPriority.HIGH,
            effort=RemediationEffort.MEDIUM,
            title=f"Fix {vulnerability.get('name', 'Vulnerability')}",
            description="Review and fix the identified vulnerability",
            steps=[
                RemediationStep(
                    order=1,
                    description="Analyze the vulnerability",
                    estimated_time="2 hours",
                ),
                RemediationStep(
                    order=2,
                    description="Implement fix",
                    estimated_time="4 hours",
                ),
                RemediationStep(
                    order=3,
                    description="Test the fix",
                    estimated_time="2 hours",
                ),
            ],
        )
    
    def _prioritize_options(self, options: List[RemediationOption],
                           risk_score: Dict, exploitability: Dict) -> List[RemediationOption]:
        """Priorisiert Remediation-Optionen"""
        # Sortiere nach PrioritÃ¤t und Effort
        priority_order = {
            RemediationPriority.IMMEDIATE: 0,
            RemediationPriority.URGENT: 1,
            RemediationPriority.HIGH: 2,
            RemediationPriority.MEDIUM: 3,
            RemediationPriority.LOW: 4,
            RemediationPriority.PLANNING: 5,
        }
        
        effort_order = {
            RemediationEffort.TRIVIAL: 0,
            RemediationEffort.LOW: 1,
            RemediationEffort.MEDIUM: 2,
            RemediationEffort.HIGH: 3,
            RemediationEffort.MAJOR: 4,
            RemediationEffort.ARCHITECTURAL: 5,
        }
        
        return sorted(options, key=lambda o: (
            priority_order.get(o.priority, 3),
            effort_order.get(o.effort, 2)
        ))
    
    def _calculate_priority_score(self, vulnerability: Dict,
                                  risk_score: Dict, exploitability: Dict) -> float:
        """Berechnet PrioritÃ¤ts-Score (0-100)"""
        score = 0.0
        
        # Risk Score (0-40 Punkte)
        risk_value = risk_score.get("final_score", 0)
        score += min(40, risk_value * 4)
        
        # Exploitability (0-30 Punkte)
        exploit_score = exploitability.get("score", 0)
        score += min(30, exploit_score * 3)
        
        # Schwachstellen-Kategorie (0-20 Punkte)
        critical_categories = ["sql_injection", "code_execution", "insecure_deserialization"]
        high_categories = ["command_injection", "authentication_bypass", "path_traversal"]
        
        category = vulnerability.get("category", "").lower()
        if category in critical_categories:
            score += 20
        elif category in high_categories:
            score += 15
        else:
            score += 10
        
        # CVE vorhanden (0-10 Punkte)
        if vulnerability.get("cve_id"):
            score += 10
        
        return min(100, score)
    
    def _generate_timeline(self, option: Optional[RemediationOption],
                          risk_score: Dict) -> str:
        """Generiert empfohlenen Zeitplan"""
        if not option:
            return "As soon as possible"
        
        priority_timeline = {
            RemediationPriority.IMMEDIATE: "Within 24 hours",
            RemediationPriority.URGENT: "Within 3 days",
            RemediationPriority.HIGH: "Within 1 week",
            RemediationPriority.MEDIUM: "Within 1 month",
            RemediationPriority.LOW: "Within 3 months",
            RemediationPriority.PLANNING: "As part of next planning cycle",
        }
        
        return priority_timeline.get(option.priority, "As soon as possible")
    
    def _determine_responsible_roles(self, option: Optional[RemediationOption],
                                    vulnerability: Dict) -> List[str]:
        """Bestimmt verantwortliche Rollen"""
        if option and option.required_skills:
            return option.required_skills
        
        # Default basierend auf Kategorie
        category = vulnerability.get("category", "").lower()
        
        if "configuration" in category:
            return ["System Administrator", "Security Engineer"]
        elif "code" in category or "injection" in category:
            return ["Developer", "Security Engineer"]
        else:
            return ["Security Engineer", "Development Team"]
    
    def _estimate_total_effort(self, recommendations: List[Recommendation]) -> int:
        """SchÃ¤tzt Gesamtaufwand in Stunden"""
        effort_hours = {
            RemediationEffort.TRIVIAL: 1,
            RemediationEffort.LOW: 4,
            RemediationEffort.MEDIUM: 16,
            RemediationEffort.HIGH: 40,
            RemediationEffort.MAJOR: 80,
            RemediationEffort.ARCHITECTURAL: 160,
        }
        
        total = 0
        for rec in recommendations:
            if rec.recommended_option:
                total += effort_hours.get(rec.recommended_option.effort, 16)
        
        return total
    
    def _calculate_timeline(self, total_hours: int,
                           team_capacity: Dict) -> int:
        """Berechnet benÃ¶tigte Wochen"""
        hours_per_week = team_capacity.get("hours_per_week", 40)
        return max(1, (total_hours // hours_per_week) + 1)


# Singleton-Instanz
_engine = None

def get_recommendation_engine() -> RecommendationEngine:
    """Gibt die Singleton-Instanz zurÃ¼ck"""
    global _engine
    if _engine is None:
        _engine = RecommendationEngine()
    return _engine


if __name__ == "__main__":
    # Demo/Test
    engine = RecommendationEngine()
    
    test_vuln = {
        "id": "VULN-001",
        "name": "SQL Injection in Login Form",
        "category": "sql_injection",
        "severity": "critical",
        "cve_id": "CVE-2021-1234",
    }
    
    test_risk = {
        "final_score": 9.2,
        "risk_level": "critical",
    }
    
    test_exploit = {
        "score": 9.0,
        "exploit_available": True,
    }
    
    recommendation = engine.generate_recommendation(test_vuln, test_risk, test_exploit)
    print("Recommendation:")
    print(json.dumps(recommendation.to_dict(), indent=2, default=str))
    
    # Compliance Mapping
    print("\nPCI DSS Mapping:")
    print(engine.get_compliance_mapping("sql_injection", ComplianceFramework.PCI_DSS))

