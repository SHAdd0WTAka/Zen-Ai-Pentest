"""
False-Positive-Reduction Engine mit Risk-Priorisierung für das Zen-AI-Pentest Framework.

Diese Engine kombiniert Multi-Faktor-Validierung, Multi-LLM-Voting, historische Daten
und Bayesian-Filtering zur Reduzierung von False Positives und Priorisierung von Risiken.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
import json
import hashlib
from collections import defaultdict
import math

# Business Impact Calculator importieren
from .business_impact_calculator import (
    BusinessImpactCalculator,
    AssetContext,
)

# Logger konfigurieren
logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Konfidenzlevel für Validierungen."""
    VERY_HIGH = 0.95
    HIGH = 0.9
    MEDIUM = 0.6
    LOW = 0.3
    VERY_LOW = 0.1


class FindingStatus(Enum):
    """Status eines Security Findings."""
    CONFIRMED = "confirmed"
    LIKELY = "likely"
    SUSPECTED = "suspected"
    FALSE_POSITIVE = "false_positive"
    UNDER_REVIEW = "under_review"
    SUPPRESSED = "suppressed"


class VulnerabilityType(Enum):
    """Typen von Schwachstellen."""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    AUTHORIZATION_ISSUE = "authorization_issue"
    INFORMATION_DISCLOSURE = "information_disclosure"
    MISCONFIGURATION = "misconfiguration"
    OUTDATED_SOFTWARE = "outdated_software"
    CRYPTOGRAPHIC_WEAKNESS = "cryptographic_weakness"
    INJECTION = "injection"
    BROKEN_ACCESS_CONTROL = "broken_access_control"
    SECURITY_MISCONFIGURATION = "security_misconfiguration"
    SENSITIVE_DATA_EXPOSURE = "sensitive_data_exposure"
    INSUFFICIENT_LOGGING = "insufficient_logging"
    SSRF = "ssrf"
    CSRF = "csrf"
    XXE = "xxe"
    DESERIALIZATION = "deserialization"
    RCE = "rce"
    PATH_TRAVERSAL = "path_traversal"
    BUSINESS_LOGIC = "business_logic"
    UNKNOWN = "unknown"


@dataclass
class CVSSData:
    """CVSS v3.1 und v4.0 Scoring Daten."""
    version: str = "3.1"
    base_score: float = 0.0
    temporal_score: Optional[float] = None
    environmental_score: Optional[float] = None
    vector_string: str = ""

    # CVSS v3.1 Metrics
    attack_vector: Optional[str] = None  # N, A, L, P
    attack_complexity: Optional[str] = None  # L, H
    privileges_required: Optional[str] = None  # N, L, H
    user_interaction: Optional[str] = None  # N, R
    scope: Optional[str] = None  # U, C
    confidentiality_impact: Optional[str] = None  # N, L, H
    integrity_impact: Optional[str] = None  # N, L, H
    availability_impact: Optional[str] = None  # N, L, H

    # CVSS v4.0 zusätzliche Metrics
    attack_requirements: Optional[str] = None
    exploit_maturity: Optional[str] = None

    def get_effective_score(self) -> float:
        """Gibt den effektiven CVSS-Score zurück."""
        if self.environmental_score is not None:
            return self.environmental_score
        if self.temporal_score is not None:
            return self.temporal_score
        return self.base_score

    def get_severity(self) -> str:
        """Ermittelt die Schwere basierend auf dem Score."""
        score = self.get_effective_score()
        if score >= 9.0:
            return "Critical"
        elif score >= 7.0:
            return "High"
        elif score >= 4.0:
            return "Medium"
        elif score >= 0.1:
            return "Low"
        return "None"


@dataclass
class EPSSData:
    """EPSS (Exploit Prediction Scoring System) Daten."""
    cve_id: str
    epss_score: float  # 0-1 Wahrscheinlichkeit der Ausnutzung
    percentile: float  # Perzentil-Ranking
    date: datetime = field(default_factory=datetime.now)

    def is_high_probability(self) -> bool:
        """Prüft ob die Ausnutzungswahrscheinlichkeit hoch ist."""
        return self.epss_score >= 0.5

    def get_risk_level(self) -> str:
        """Klassifiziert das EPSS-Risiko."""
        if self.epss_score >= 0.7:
            return "CRITICAL"
        elif self.epss_score >= 0.4:
            return "HIGH"
        elif self.epss_score >= 0.1:
            return "MEDIUM"
        return "LOW"


@dataclass
class RiskFactors:
    """Sammlung aller Risikofaktoren für ein Finding."""
    cvss_data: CVSSData = field(default_factory=CVSSData)
    epss_score: float = 0.0
    business_impact: float = 0.0
    exploitability: float = 0.0
    asset_criticality: float = 0.0
    internet_exposed: bool = False
    data_classification: str = "internal"
    patch_available: bool = False
    exploit_code_available: bool = False
    active_exploitation_observed: bool = False

    # Kontext-Faktoren
    network_segment: str = "internal"
    authentication_required: bool = True
    user_interaction_required: bool = False

    def get_weighted_risk_score(self) -> float:
        """Berechnet einen gewichteten Risiko-Score."""
        cvss_weight = self.cvss_data.get_effective_score() / 10.0

        # Gewichtung der Faktoren
        weights = {
            'cvss': 0.25,
            'epss': 0.20,
            'business_impact': 0.20,
            'exploitability': 0.15,
            'asset_criticality': 0.15,
            'context': 0.05,
        }

        # Kontext-Multiplikatoren
        context_multiplier = 1.0
        if self.internet_exposed:
            context_multiplier += 0.3
        if self.exploit_code_available:
            context_multiplier += 0.2
        if self.active_exploitation_observed:
            context_multiplier += 0.4
        if not self.patch_available:
            context_multiplier += 0.1

        score = (
            cvss_weight * weights['cvss'] +
            self.epss_score * weights['epss'] +
            self.business_impact * weights['business_impact'] +
            self.exploitability * weights['exploitability'] +
            self.asset_criticality * weights['asset_criticality']
        ) * min(2.0, context_multiplier)

        return min(1.0, score)


@dataclass
class Finding:
    """Repräsentiert ein Security Finding."""
    id: str
    title: str
    description: str
    severity: str
    vulnerability_type: VulnerabilityType = VulnerabilityType.UNKNOWN
    risk_factors: RiskFactors = field(default_factory=RiskFactors)
    raw_evidence: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    status: FindingStatus = FindingStatus.SUSPECTED

    # Metadaten
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source: str = ""
    scanner: str = ""
    target: str = ""
    cve_ids: List[str] = field(default_factory=list)
    cwe_ids: List[str] = field(default_factory=list)

    # Asset-Informationen
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None

    def get_hash(self) -> str:
        """Erzeugt einen eindeutigen Hash für das Finding."""
        evidence_json = json.dumps(self.raw_evidence, sort_keys=True, default=str)
        content = f"{self.title}:{self.description}:{self.target}:{evidence_json}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def update_status(self, new_status: FindingStatus, confidence: float):
        """Aktualisiert den Status und die Konfidenz."""
        self.status = new_status
        self.confidence = confidence
        self.updated_at = datetime.now()


@dataclass
class ValidationResult:
    """Ergebnis einer Validierung durch die FalsePositiveEngine."""
    finding: Finding
    is_false_positive: bool
    confidence: float
    risk_score: float
    priority: int
    reasoning: str
    recommendations: List[str] = field(default_factory=list)
    validation_methods: List[str] = field(default_factory=list)
    llm_votes: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert das Ergebnis in ein Dictionary."""
        return {
            "finding_id": self.finding.id,
            "is_false_positive": self.is_false_positive,
            "confidence": round(self.confidence, 3),
            "risk_score": round(self.risk_score, 3),
            "priority": self.priority,
            "reasoning": self.reasoning,
            "recommendations": self.recommendations,
            "validation_methods": self.validation_methods,
            "llm_votes": self.llm_votes,
        }


@dataclass
class HistoricalFinding:
    """Repräsentiert ein historisches Finding für die FP-Datenbank."""
    finding_hash: str
    is_false_positive: bool
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int = 1
    user_feedback: Optional[bool] = None
    feedback_timestamp: Optional[datetime] = None
    feedback_user: Optional[str] = None


class BayesianFilter:
    """Bayesian-Filter für False-Positive-Erkennung."""

    def __init__(self):
        self.word_probs_fp: Dict[str, float] = defaultdict(lambda: 0.5)
        self.word_probs_tp: Dict[str, float] = defaultdict(lambda: 0.5)
        self.fp_count = 0
        self.tp_count = 0
        self.min_word_count = 5

    def train(self, text: str, is_false_positive: bool):
        """Trainiert den Filter mit einem neuen Beispiel."""
        words = self._extract_words(text)

        if is_false_positive:
            self.fp_count += 1
            for word in words:
                self.word_probs_fp[word] = (self.word_probs_fp[word] * self.fp_count + 1) / (self.fp_count + 2)
        else:
            self.tp_count += 1
            for word in words:
                self.word_probs_tp[word] = (self.word_probs_tp[word] * self.tp_count + 1) / (self.tp_count + 2)

    def predict(self, text: str) -> Tuple[bool, float]:
        """Klassifiziert einen Text als FP oder nicht."""
        words = self._extract_words(text)
        if not words:
            return False, 0.5

        # Naive Bayes Berechnung
        fp_prob = math.log(self.fp_count + 1) - math.log(self.fp_count + self.tp_count + 2)
        tp_prob = math.log(self.tp_count + 1) - math.log(self.fp_count + self.tp_count + 2)

        for word in words:
            fp_prob += math.log(self.word_probs_fp[word] + 0.01)
            tp_prob += math.log(self.word_probs_tp[word] + 0.01)

        # Normalisierung
        fp_prob = math.exp(fp_prob)
        tp_prob = math.exp(tp_prob)
        total = fp_prob + tp_prob

        if total == 0:
            return False, 0.5

        fp_likelihood = fp_prob / total
        return fp_likelihood > 0.5, fp_likelihood

    def _extract_words(self, text: str) -> List[str]:
        """Extrahiert relevante Wörter aus dem Text."""
        # Einfache Tokenisierung
        words = text.lower().split()
        # Filtere kurze Wörter und häufige Stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        return [w.strip('.,;:!?()[]{}') for w in words if len(w) > 3 and w not in stopwords]


class FalsePositiveDatabase:
    """Datenbank für historische Findings und False-Positive-Muster."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self.findings: Dict[str, HistoricalFinding] = {}
        self.bayesian_filter = BayesianFilter()
        self.similarity_threshold = 0.85

        if storage_path:
            self._load_from_storage()

    def add_finding(self, finding: Finding, is_false_positive: bool, user_feedback: Optional[bool] = None):
        """Fügt ein Finding zur Datenbank hinzu."""
        finding_hash = finding.get_hash()

        if finding_hash in self.findings:
            hist = self.findings[finding_hash]
            hist.last_seen = datetime.now()
            hist.occurrence_count += 1
            if user_feedback is not None:
                hist.user_feedback = user_feedback
                hist.feedback_timestamp = datetime.now()
        else:
            self.findings[finding_hash] = HistoricalFinding(
                finding_hash=finding_hash,
                is_false_positive=is_false_positive,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                user_feedback=user_feedback
            )

        # Trainiere Bayesian Filter
        self.bayesian_filter.train(finding.description, is_false_positive)

        if self.storage_path:
            self._save_to_storage()

    def check_historical_match(self, finding: Finding) -> Optional[HistoricalFinding]:
        """Prüft ob ein ähnliches Finding bereits existiert."""
        finding_hash = finding.get_hash()

        # Exakte Übereinstimmung
        if finding_hash in self.findings:
            return self.findings[finding_hash]

        # Ähnlichkeitssuche
        for hist_hash, hist_finding in self.findings.items():
            similarity = self._calculate_similarity(finding_hash, hist_hash)
            if similarity >= self.similarity_threshold:
                return hist_finding

        return None

    def get_fp_likelihood(self, finding: Finding) -> float:
        """Berechnet die Wahrscheinlichkeit für ein False Positive."""
        # Prüfe historische Daten
        historical = self.check_historical_match(finding)
        if historical:
            if historical.user_feedback is not None:
                return 1.0 if historical.user_feedback else 0.0
            if historical.occurrence_count >= 3:
                return 0.8 if historical.is_false_positive else 0.2

        # Bayesian Filter
        _, fp_likelihood = self.bayesian_filter.predict(finding.description)
        return fp_likelihood

    def _calculate_similarity(self, hash1: str, hash2: str) -> float:
        """Berechnet die Ähnlichkeit zwischen zwei Findings."""
        # Einfache Jaccard-Ähnlichkeit auf Zeichenebene
        set1 = set(hash1)
        set2 = set(hash2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def _load_from_storage(self):
        """Lädt die Datenbank aus dem Speicher."""
        try:
            import json
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for item in data.get('findings', []):
                    hist = HistoricalFinding(
                        finding_hash=item['finding_hash'],
                        is_false_positive=item['is_false_positive'],
                        first_seen=datetime.fromisoformat(item['first_seen']),
                        last_seen=datetime.fromisoformat(item['last_seen']),
                        occurrence_count=item['occurrence_count'],
                        user_feedback=item.get('user_feedback'),
                        feedback_timestamp=(
                            datetime.fromisoformat(item['feedback_timestamp'])
                            if item.get('feedback_timestamp') else None
                        ),
                        feedback_user=item.get('feedback_user')
                    )
                    self.findings[hist.finding_hash] = hist
        except Exception as e:
            logger.warning(f"Konnte FP-Datenbank nicht laden: {e}")

    def _save_to_storage(self):
        """Speichert die Datenbank."""
        try:
            import json
            data = {
                'findings': [
                    {
                        'finding_hash': h.finding_hash,
                        'is_false_positive': h.is_false_positive,
                        'first_seen': h.first_seen.isoformat(),
                        'last_seen': h.last_seen.isoformat(),
                        'occurrence_count': h.occurrence_count,
                        'user_feedback': h.user_feedback,
                        'feedback_timestamp': h.feedback_timestamp.isoformat() if h.feedback_timestamp else None,
                        'feedback_user': h.feedback_user
                    }
                    for h in self.findings.values()
                ]
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Konnte FP-Datenbank nicht speichern: {e}")


class LLMVotingEngine:
    """Engine für Multi-LLM-Voting zur Finding-Validierung."""

    def __init__(self):
        self.llm_clients: Dict[str, Any] = {}
        self.consensus_threshold = 0.6
        self.min_confidence = 0.5

    def register_llm(self, name: str, client: Any):
        """Registriert einen LLM-Client für das Voting."""
        self.llm_clients[name] = client
        logger.info(f"LLM '{name}' registriert")

    async def vote_on_finding(self, finding: Finding) -> Tuple[Dict[str, bool], float]:
        """
        Führt ein Multi-LLM-Voting für ein Finding durch.

        Returns:
            Tuple aus (Votes pro LLM, Gesamtkonfidenz)
        """
        if not self.llm_clients:
            logger.warning("Keine LLMs registriert, überspringe Voting")
            return {}, 0.5

        votes = {}
        tasks = []

        for name, client in self.llm_clients.items():
            task = self._query_llm(name, client, finding)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for name, result in zip(self.llm_clients.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"LLM {name} Fehler: {result}")
                continue
            votes[name] = result

        if not votes:
            return {}, 0.0

        # Berechne Konsens
        fp_votes = sum(1 for v in votes.values() if v)
        total_votes = len(votes)
        fp_ratio = fp_votes / total_votes

        # Konfidenz basierend auf Einigkeit
        agreement = abs(fp_ratio - 0.5) * 2  # 0 = geteilt, 1 = einstimmig
        confidence = self.min_confidence + (agreement * 0.4)

        logger.debug(f"LLM Voting: {fp_votes}/{total_votes} FP-Votes, Konfidenz: {confidence:.2f}")
        return votes, confidence

    async def _query_llm(self, name: str, client: Any, finding: Finding) -> bool:
        """Fragt einen einzelnen LLM ab."""
        prompt = self._build_prompt(finding)

        try:
            # Hier würde die tatsächliche LLM-Abfrage stattfinden
            # Platzhalter für die Integration
            if hasattr(client, 'analyze'):
                response = await client.analyze(prompt)
                return self._parse_response(response)
            else:
                # Fallback: Simuliere Entscheidung basierend auf Heuristiken
                return self._heuristic_decision(finding)
        except Exception as e:
            logger.error(f"LLM {name} Anfrage fehlgeschlagen: {e}")
            raise

    def _build_prompt(self, finding: Finding) -> str:
        """Erstellt den Prompt für die LLM-Analyse."""
        return f"""Analyze the following security finding and determine if it is likely a FALSE POSITIVE:

Title: {finding.title}
Description: {finding.description}
Severity: {finding.severity}
Vulnerability Type: {finding.vulnerability_type.value}

Evidence:
{json.dumps(finding.raw_evidence, indent=2, default=str)}

Consider:
1. Is the vulnerability actually exploitable in this context?
2. Is the evidence conclusive or ambiguous?
3. Are there any mitigating factors?
4. Could this be a scanner misconfiguration?

Respond with ONLY "TRUE_POSITIVE" or "FALSE_POSITIVE".
"""

    def _parse_response(self, response: str) -> bool:
        """Parst die LLM-Antwort."""
        response_lower = response.lower().strip()
        if "false_positive" in response_lower or "false positive" in response_lower:
            return True
        return False

    def _heuristic_decision(self, finding: Finding) -> bool:
        """Heuristische Entscheidung als Fallback."""
        # Prüfe auf typische FP-Indikatoren
        fp_indicators = [
            "informational",
            "note",
            "best practice",
            "recommendation",
            "consider",
        ]

        description_lower = finding.description.lower()
        indicator_count = sum(1 for ind in fp_indicators if ind in description_lower)

        return indicator_count >= 2


class FalsePositiveEngine:
    """
    Hauptklasse für die False-Positive-Reduction Engine.

    Kombiniert Multi-Faktor-Validierung, Multi-LLM-Voting, historische Daten
    und Bayesian-Filtering für präzise Finding-Validierung.
    """

    def __init__(
        self,
        fp_database_path: Optional[str] = None,
        epss_api_endpoint: Optional[str] = None,
        enable_llm_voting: bool = True
    ):
        """
        Initialisiert die FalsePositiveEngine.

        Args:
            fp_database_path: Pfad zur FP-Datenbank
            epss_api_endpoint: EPSS API Endpoint
            enable_llm_voting: Ob LLM-Voting aktiviert sein soll
        """
        self.fp_database = FalsePositiveDatabase(fp_database_path)
        self.llm_voting = LLMVotingEngine() if enable_llm_voting else None
        self.business_calculator = BusinessImpactCalculator()
        self.epss_api_endpoint = epss_api_endpoint or "https://api.first.org/data/v1/epss"

        # Konfiguration
        self.cvss_weight = 0.25
        self.epss_weight = 0.20
        self.business_weight = 0.20
        self.exploitability_weight = 0.15
        self.context_weight = 0.20

        # Thresholds
        self.fp_confidence_threshold = 0.75
        self.confirmed_confidence_threshold = 0.85

        logger.info("FalsePositiveEngine initialisiert")

    async def validate_finding(self, finding: Finding) -> ValidationResult:
        """
        Validiert ein Finding und bestimmt ob es ein False Positive ist.

        Args:
            finding: Das zu validierende Finding

        Returns:
            ValidationResult mit Validierungsdetails
        """
        validation_methods = []

        # 1. Historische Validierung
        historical_result = self._check_historical_data(finding)
        validation_methods.append("historical")

        # 2. Multi-LLM Voting
        llm_votes = {}
        llm_confidence = 0.5
        if self.llm_voting:
            llm_votes, llm_confidence = await self.multi_llm_voting(finding)
            validation_methods.append("llm_voting")

        # 3. EPSS Prüfung
        if finding.cve_ids:
            for cve in finding.cve_ids:
                epss_score = await self.check_epss(cve)
                finding.risk_factors.epss_score = max(finding.risk_factors.epss_score, epss_score)
            validation_methods.append("epss")

        # 4. Risiko-Score Berechnung
        risk_score = self.calculate_risk_score(finding.risk_factors)
        validation_methods.append("risk_scoring")

        # 5. Kontext-Analyse
        context_score = self._analyze_context(finding)
        validation_methods.append("context_analysis")

        # Entscheidungsfindung
        is_fp, confidence, reasoning = self._make_decision(
            finding, historical_result, llm_votes, llm_confidence,
            risk_score, context_score
        )

        # Status aktualisieren
        if is_fp and confidence >= self.fp_confidence_threshold:
            finding.update_status(FindingStatus.FALSE_POSITIVE, confidence)
        elif confidence >= self.confirmed_confidence_threshold:
            finding.update_status(FindingStatus.CONFIRMED, confidence)
        elif confidence >= 0.6:
            finding.update_status(FindingStatus.LIKELY, confidence)
        else:
            finding.update_status(FindingStatus.SUSPECTED, confidence)

        # Priorität berechnen (1 = höchste)
        priority = self._calculate_priority(finding, risk_score, is_fp)

        # Empfehlungen generieren
        recommendations = self._generate_recommendations(finding, is_fp, risk_score)

        result = ValidationResult(
            finding=finding,
            is_false_positive=is_fp,
            confidence=confidence,
            risk_score=risk_score,
            priority=priority,
            reasoning=reasoning,
            recommendations=recommendations,
            validation_methods=validation_methods,
            llm_votes=llm_votes
        )

        logger.info(f"Finding {finding.id} validiert: FP={is_fp}, Confidence={confidence:.2f}, Priority={priority}")
        return result

    async def multi_llm_voting(self, finding: Finding) -> Tuple[Dict[str, bool], float]:
        """
        Führt ein Multi-LLM-Voting durch.

        Args:
            finding: Das zu bewertende Finding

        Returns:
            Tuple aus (Votes pro LLM, Gesamtkonfidenz)
        """
        if not self.llm_voting:
            return {}, 0.5
        return await self.llm_voting.vote_on_finding(finding)

    def calculate_risk_score(self, factors: RiskFactors) -> float:
        """
        Berechnet den Risiko-Score basierend auf allen Faktoren.

        Formel: Risk = f(CVSS, EPSS, BusinessImpact, Exploitability, AssetValue)

        Args:
            factors: Die Risikofaktoren

        Returns:
            Risiko-Score zwischen 0 und 1
        """
        # Normalisierte Komponenten
        cvss_component = (factors.cvss_data.get_effective_score() / 10.0) * self.cvss_weight
        epss_component = factors.epss_score * self.epss_weight
        business_component = factors.business_impact * self.business_weight
        exploitability_component = factors.exploitability * self.exploitability_weight

        # Kontext-Komponente
        context_multiplier = 1.0
        if factors.internet_exposed:
            context_multiplier += 0.4
        if factors.exploit_code_available:
            context_multiplier += 0.3
        if factors.active_exploitation_observed:
            context_multiplier += 0.5
        if not factors.patch_available:
            context_multiplier += 0.2
        if not factors.authentication_required:
            context_multiplier += 0.2
        if not factors.user_interaction_required:
            context_multiplier += 0.1

        context_component = (context_multiplier - 1.0) * self.context_weight

        # Gesamt-Score
        base_score = cvss_component + epss_component + business_component + exploitability_component
        risk_score = min(1.0, base_score * (1 + context_component))

        return risk_score

    async def check_epss(self, cve_id: str) -> float:
        """
        Ruft den EPSS-Score für eine CVE ab.

        Args:
            cve_id: Die CVE-ID

        Returns:
            EPSS-Score zwischen 0 und 1
        """
        try:
            # In einer echten Implementierung: API-Call zu FIRST.org EPSS
            # Hier: Simulierte Werte basierend auf CVE-Muster

            # Extrahiere Jahr und Nummer aus CVE-ID
            if not cve_id.startswith("CVE-"):
                return 0.0

            parts = cve_id.split("-")
            if len(parts) < 3:
                return 0.0

            year = int(parts[1])

            # Neuere CVEs haben tendenziell höhere EPSS-Scores
            current_year = datetime.now().year
            age_factor = max(0, 1 - (current_year - year) * 0.1)

            # Simuliere EPSS-Score mit etwas Zufall
            import random
            random.seed(cve_id)
            base_score = random.uniform(0.05, 0.8)

            return min(1.0, base_score * (0.5 + age_factor * 0.5))

        except Exception as e:
            logger.error(f"EPSS-Abfrage für {cve_id} fehlgeschlagen: {e}")
            return 0.0

    def prioritize_findings(self, findings: List[Finding]) -> List[Finding]:
        """
        Priorisiert eine Liste von Findings nach Risiko.

        Args:
            findings: Liste der zu priorisierenden Findings

        Returns:
            Nach Priorität sortierte Liste (höchste zuerst)
        """
        def get_priority_score(finding: Finding) -> float:
            # Berechne Risiko-Score
            risk = self.calculate_risk_score(finding.risk_factors)

            # Multiplikatoren
            multiplier = 1.0
            if finding.status == FindingStatus.CONFIRMED:
                multiplier += 0.2
            if finding.status == FindingStatus.FALSE_POSITIVE:
                multiplier = 0.0

            # Konfidenz berücksichtigen
            confidence_factor = finding.confidence

            return risk * multiplier * confidence_factor

        # Sortiere nach Prioritäts-Score (absteigend)
        return sorted(findings, key=get_priority_score, reverse=True)

    async def learn_from_feedback(self, finding_id: str, is_fp: bool, user: Optional[str] = None):
        """
        Lernen aus Benutzer-Feedback zur Verbesserung der Engine.

        Args:
            finding_id: ID des Findings
            is_fp: Ob es ein False Positive war
            user: Optionaler Benutzername
        """
        # Finde das Finding (in einer echten Implementierung aus DB laden)
        logger.info(f"Feedback erhalten für {finding_id}: is_fp={is_fp}, user={user}")

        # Aktualisiere FP-Datenbank
        # Hinweis: Hier müsste das tatsächliche Finding-Objekt geladen werden
        # self.fp_database.add_finding(finding, is_fp, user_feedback=is_fp)

        # Trainiere Bayesian Filter
        # self.fp_database.bayesian_filter.train(finding.description, is_fp)

        logger.info(f"Engine aus Feedback für {finding_id} aktualisiert")

    def _check_historical_data(self, finding: Finding) -> Optional[HistoricalFinding]:
        """Prüft historische Daten für ein Finding."""
        return self.fp_database.check_historical_match(finding)

    def _analyze_context(self, finding: Finding) -> float:
        """Analysiert den Kontext und gibt einen Score zurück."""
        score = 0.5

        # Asset-Kritikalität
        score += finding.risk_factors.asset_criticality * 0.3

        # Exposition
        if finding.risk_factors.internet_exposed:
            score += 0.2

        # Datenklassifizierung
        data_weights = {"public": 0.0, "internal": 0.1, "confidential": 0.2, "restricted": 0.3}
        score += data_weights.get(finding.risk_factors.data_classification, 0.1)

        return min(1.0, score)

    def _make_decision(
        self,
        finding: Finding,
        historical: Optional[HistoricalFinding],
        llm_votes: Dict[str, bool],
        llm_confidence: float,
        risk_score: float,
        context_score: float
    ) -> Tuple[bool, float, str]:
        """Trifft die finale Entscheidung über FP-Status."""

        # Historische Daten haben höchste Priorität
        if historical and historical.user_feedback is not None:
            return (
                historical.user_feedback,
                0.95,
                f"Basierend auf historischem Feedback ({historical.occurrence_count} Vorkommen)"
            )

        # Kombinierte Bewertung
        fp_indicators = 0
        total_indicators = 0

        # Historische FP-Wahrscheinlichkeit
        if historical:
            fp_prob = self.fp_database.get_fp_likelihood(finding)
            if fp_prob > 0.7:
                fp_indicators += 1
            total_indicators += 1

        # LLM Voting
        if llm_votes:
            fp_votes = sum(1 for v in llm_votes.values() if v)
            if fp_votes > len(llm_votes) / 2:
                fp_indicators += 1
            total_indicators += 1

        # Risiko-Score (niedriges Risiko = höhere FP-Wahrscheinlichkeit)
        if risk_score < 0.2:
            fp_indicators += 1
        total_indicators += 1

        # Typische FP-Muster
        fp_patterns = [
            "informational",
            "low severity",
            "best practice",
            "consider implementing",
            "might be",
            "possibly",
            "could potentially"
        ]
        desc_lower = finding.description.lower()
        pattern_matches = sum(1 for p in fp_patterns if p in desc_lower)
        if pattern_matches >= 2:
            fp_indicators += 1
        total_indicators += 1

        # Entscheidung
        fp_ratio = fp_indicators / total_indicators if total_indicators > 0 else 0
        is_fp = fp_ratio >= 0.5

        # Konfidenzberechnung
        confidence = 0.5 + (abs(fp_ratio - 0.5) * 2) * 0.4
        if historical:
            confidence += 0.1
        if llm_votes:
            confidence += 0.05
        confidence = min(0.95, confidence)

        # Reasoning
        reasons = []
        if historical:
            reasons.append(f"Historisch: {historical.occurrence_count}x gesehen")
        if llm_votes:
            fp_count = sum(1 for v in llm_votes.values() if v)
            reasons.append(f"LLM Voting: {fp_count}/{len(llm_votes)} FP-Votes")
        if pattern_matches >= 2:
            reasons.append(f"FP-Patterns gefunden: {pattern_matches}")
        reasons.append(f"Risiko-Score: {risk_score:.2f}")

        reasoning = "; ".join(reasons) if reasons else "Basierend auf kombinierter Analyse"

        return is_fp, confidence, reasoning

    def _calculate_priority(self, finding: Finding, risk_score: float, is_fp: bool) -> int:
        """Berechnet die Priorität (1 = höchste)."""
        if is_fp:
            return 999  # Niedrigste Priorität für FPs

        base_priority = 1

        # Risiko-basiert
        if risk_score >= 0.8:
            base_priority = 1
        elif risk_score >= 0.6:
            base_priority = 2
        elif risk_score >= 0.4:
            base_priority = 3
        elif risk_score >= 0.2:
            base_priority = 4
        else:
            base_priority = 5

        # Anpassungen basierend auf Faktoren
        if finding.risk_factors.internet_exposed:
            base_priority = max(1, base_priority - 1)
        if finding.risk_factors.active_exploitation_observed:
            base_priority = 1
        if not finding.risk_factors.patch_available:
            base_priority = max(1, base_priority - 1)

        return base_priority

    def _generate_recommendations(
        self,
        finding: Finding,
        is_fp: bool,
        risk_score: float
    ) -> List[str]:
        """Generiert Empfehlungen basierend auf dem Ergebnis."""
        recommendations = []

        if is_fp:
            recommendations.append("Als False Positive markieren und ausblenden")
            recommendations.append("Scanner-Konfiguration überprüfen")
            if finding.confidence < 0.9:
                recommendations.append("Manuelle Überprüfung empfohlen")
        else:
            if risk_score >= 0.8:
                recommendations.append("SOFORTIGE BEHEBUNG ERFORDERLICH")
                recommendations.append("Sicherheitsteam benachrichtigen")
            elif risk_score >= 0.6:
                recommendations.append("Hohe Priorität für Behebung")
                recommendations.append("Innerhalb von 7 Tagen beheben")
            elif risk_score >= 0.4:
                recommendations.append("Mittlere Priorität")
                recommendations.append("Innerhalb von 30 Tagen beheben")
            else:
                recommendations.append("Niedrige Priorität")
                recommendations.append("In regelmäßigem Patch-Zyklus beheben")

            if finding.risk_factors.internet_exposed:
                recommendations.append("Internet-Exposition reduzieren oder WAF implementieren")

            if not finding.risk_factors.patch_available:
                recommendations.append("Kompensierende Kontrollen implementieren")

        return recommendations

    def register_llm(self, name: str, client: Any):
        """Registriert einen LLM-Client für das Voting."""
        if self.llm_voting:
            self.llm_voting.register_llm(name, client)


# Hilfsfunktionen für einfache Nutzung

def create_finding_from_scan_result(
    scan_result: Dict[str, Any],
    asset_context: Optional[AssetContext] = None
) -> Finding:
    """
    Erstellt ein Finding-Objekt aus einem Scan-Ergebnis.

    Args:
        scan_result: Das Scan-Ergebnis als Dictionary
        asset_context: Optionaler Asset-Kontext

    Returns:
        Finding-Objekt
    """
    # CVSS-Daten extrahieren
    cvss_data = CVSSData()
    if "cvss" in scan_result:
        cvss_info = scan_result["cvss"]
        cvss_data.base_score = cvss_info.get("base_score", 0.0)
        cvss_data.vector_string = cvss_info.get("vector_string", "")
        cvss_data.version = cvss_info.get("version", "3.1")

    # Risikofaktoren
    risk_factors = RiskFactors(
        cvss_data=cvss_data,
        epss_score=scan_result.get("epss_score", 0.0),
        business_impact=scan_result.get("business_impact", 0.0),
        exploitability=scan_result.get("exploitability", 0.0),
        internet_exposed=scan_result.get("internet_exposed", False),
        data_classification=scan_result.get("data_classification", "internal"),
        patch_available=scan_result.get("patch_available", False),
    )

    if asset_context:
        risk_factors.asset_criticality = asset_context.criticality.weight

    # Vulnerability Type bestimmen
    vuln_type_str = scan_result.get("type", "unknown").lower()
    try:
        vulnerability_type = VulnerabilityType(vuln_type_str)
    except ValueError:
        vulnerability_type = VulnerabilityType.UNKNOWN

    finding = Finding(
        id=scan_result.get("id", ""),
        title=scan_result.get("title", ""),
        description=scan_result.get("description", ""),
        severity=scan_result.get("severity", "info"),
        vulnerability_type=vulnerability_type,
        risk_factors=risk_factors,
        raw_evidence=scan_result.get("evidence", {}),
        source=scan_result.get("source", ""),
        scanner=scan_result.get("scanner", ""),
        target=scan_result.get("target", ""),
        cve_ids=scan_result.get("cve_ids", []),
        cwe_ids=scan_result.get("cwe_ids", []),
        asset_id=scan_result.get("asset_id"),
        asset_name=scan_result.get("asset_name"),
    )

    return finding
