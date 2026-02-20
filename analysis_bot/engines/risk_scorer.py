"""
Zen-Ai-Pentest AnalysisBot - Risk Scorer Module
===============================================
Risiko-Bewertungs-Modul fÃ¼r das Zen-Ai-Pentest Framework.

Autor: AnalysisBot
Version: 1.0.0 (2026)
"""

import json
import logging
import math
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risiko-Level nach ISO 27005"""

    CRITICAL = "critical"  # Sofortige MaÃŸnahmen erforderlich
    HIGH = "high"  # Kurzfristige MaÃŸnahmen erforderlich
    MEDIUM = "medium"  # MaÃŸnahmen planen
    LOW = "low"  # Akzeptabel, Monitoring empfohlen
    NEGLIGIBLE = "negligible"  # Keine MaÃŸnahmen erforderlich


class AssetCriticality(Enum):
    """KritikalitÃ¤t von Assets"""

    CRITICAL = 5  # GeschÃ¤ftskritisch, Ausfall nicht tolerierbar
    HIGH = 4  # Wichtig, Ausfall nur kurz tolerierbar
    MEDIUM = 3  # Normal, Ausfall begrenzt tolerierbar
    LOW = 2  # Weniger wichtig, Ausfall tolerierbar
    MINIMAL = 1  # Nicht kritisch


class ThreatActor(Enum):
    """Threat Actor Profile nach MITRE ATT&CK"""

    SCRIPT_KIDDIE = "script_kiddie"  # Wenig FÃ¤higkeiten, Ã¶ffentliche Tools
    HACKTIVIST = "hacktivist"  # Ideologisch motiviert
    CYBERCRIMINAL = "cybercriminal"  # Finanziell motiviert
    INSIDER = "insider"  # Interner Angreifer
    STATE_SPONSORED = "state_sponsored"  # APT, Nation State
    COMPETITOR = "competitor"  # Wirtschaftsspionage


@dataclass
class RiskFactors:
    """Risikofaktoren fÃ¼r die Bewertung"""

    # Technische Faktoren (0-10)
    exploitability: float = 5.0  # Wie einfach ist die Ausnutzung
    prevalence: float = 5.0  # Wie verbreitet ist die Schwachstelle
    detection_difficulty: float = 5.0  # Wie schwer ist die Erkennung

    # GeschÃ¤ftliche Faktoren (0-10)
    data_sensitivity: float = 5.0  # SensitivitÃ¤t der betroffenen Daten
    business_impact: float = 5.0  # GeschÃ¤ftlicher Impact
    compliance_relevance: float = 5.0  # Relevanz fÃ¼r Compliance

    # Kontext-Faktoren (0-10)
    exposure: float = 5.0  # Exposition (Internet, intern, etc.)
    asset_value: float = 5.0  # Wert des betroffenen Assets
    user_interaction: float = 5.0  # Benutzerinteraktion erforderlich

    # Zeitliche Faktoren
    time_to_exploit: float = 1.0  # Zeit bis zur Ausnutzung (Stunden)
    patch_availability: float = 0.0  # Patch verfÃ¼gbar (0=nein, 1=ja)

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class RiskScore:
    """Risiko-Score mit Metadaten"""

    base_score: float = 0.0  # Basis-Score (0-10)
    temporal_score: float = 0.0  # Temporaler Score (0-10)
    environmental_score: float = 0.0  # Umwelt-Score (0-10)
    final_score: float = 0.0  # Finaler Score (0-10)
    risk_level: RiskLevel = RiskLevel.LOW

    # Komponenten
    likelihood: float = 0.0  # Eintrittswahrscheinlichkeit (0-1)
    impact: float = 0.0  # Auswirkung (0-1)

    # Bewertungsdetails
    calculation_method: str = ""
    factors_applied: List[str] = field(default_factory=list)
    confidence: float = 1.0  # Konfidenz der Bewertung (0-1)

    # Metadaten
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    calculated_by: str = "RiskScorer"
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        data["calculated_at"] = self.calculated_at.isoformat()
        return data


class RiskScorer:
    """
    Risiko-Bewertungs-Engine fÃ¼r Schwachstellen.

    Implementiert:
    - CVSS-basierte Scoring
    - FAIR-Methodologie (Factor Analysis of Information Risk)
    - DREAD-Modell
    - OWASP Risk Rating
    - Kontext-basierte Anpassung
    """

    # Gewichtungen fÃ¼r verschiedene Scoring-Methoden
    DEFAULT_WEIGHTS = {"cvss": 0.30, "fair": 0.25, "dread": 0.20, "owasp": 0.15, "context": 0.10}

    # Threat Actor Capability Scores
    THREAT_ACTOR_CAPABILITIES = {
        ThreatActor.SCRIPT_KIDDIE: 0.2,
        ThreatActor.HACKTIVIST: 0.4,
        ThreatActor.CYBERCRIMINAL: 0.6,
        ThreatActor.INSIDER: 0.7,
        ThreatActor.COMPETITOR: 0.8,
        ThreatActor.STATE_SPONSORED: 1.0,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.scoring_history: List[Dict] = []
        self.risk_thresholds = {
            RiskLevel.CRITICAL: (9.0, 10.0),
            RiskLevel.HIGH: (7.0, 9.0),
            RiskLevel.MEDIUM: (4.0, 7.0),
            RiskLevel.LOW: (1.0, 4.0),
            RiskLevel.NEGLIGIBLE: (0.0, 1.0),
        }

    def calculate_cvss_score(self, cvss_vector: str) -> Dict[str, float]:
        """
        Berechnet CVSS 3.1 Score aus Vector String.

        Args:
            cvss_vector: CVSS 3.1 Vector String

        Returns:
            Dictionary mit Base, Temporal und Environmental Score
        """
        # CVSS 3.1 Metric Values
        metric_values = {
            "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2},
            "AC": {"L": 0.77, "H": 0.44},
            "PR": {"N": 0.85, "L": 0.62, "H": 0.27},
            "PR_SCOPE": {"N": 0.85, "L": 0.68, "H": 0.5},
            "UI": {"N": 0.85, "R": 0.62},
            "C": {"H": 0.56, "L": 0.22, "N": 0},
            "I": {"H": 0.56, "L": 0.22, "N": 0},
            "A": {"H": 0.56, "L": 0.22, "N": 0},
            "E": {"X": 1.0, "U": 0.91, "P": 0.94, "F": 0.97, "H": 1.0},
            "RL": {"X": 1.0, "O": 0.95, "T": 0.96, "W": 0.97, "U": 1.0},
            "RC": {"X": 1.0, "U": 0.92, "R": 0.96, "C": 1.0},
        }

        try:
            # Parse Vector
            metrics = {}
            for part in cvss_vector.replace("CVSS:3.1/", "").split("/"):
                if ":" in part:
                    key, value = part.split(":")
                    metrics[key] = value

            # Base Score Calculation
            iss = 1 - (
                (1 - metric_values["C"].get(metrics.get("C", "N"), 0))
                * (1 - metric_values["I"].get(metrics.get("I", "N"), 0))
                * (1 - metric_values["A"].get(metrics.get("A", "N"), 0))
            )

            scope_changed = metrics.get("S", "U") == "C"

            if scope_changed:
                impact = 7.52 * (iss - 0.029) - 3.25 * pow(iss - 0.02, 15)
            else:
                impact = 6.42 * iss

            exploitability = (
                8.22
                * metric_values["AV"].get(metrics.get("AV", "N"), 0.85)
                * metric_values["AC"].get(metrics.get("AC", "L"), 0.77)
                * (
                    metric_values["PR_SCOPE"].get(metrics.get("PR", "N"), 0.85)
                    if scope_changed
                    else metric_values["PR"].get(metrics.get("PR", "N"), 0.85)
                )
                * metric_values["UI"].get(metrics.get("UI", "N"), 0.85)
            )

            if impact <= 0:
                base_score = 0
            elif scope_changed:
                base_score = min(1.08 * (impact + exploitability), 10)
            else:
                base_score = min(impact + exploitability, 10)

            # Temporal Score
            e = metric_values["E"].get(metrics.get("E", "X"), 1.0)
            rl = metric_values["RL"].get(metrics.get("RL", "X"), 1.0)
            rc = metric_values["RC"].get(metrics.get("RC", "X"), 1.0)
            temporal_score = base_score * e * rl * rc

            return {
                "base_score": round(base_score, 1),
                "temporal_score": round(temporal_score, 1),
                "impact": round(impact, 1),
                "exploitability": round(exploitability, 1),
            }

        except Exception as e:
            logger.error(f"CVSS Berechnungsfehler: {e}")
            return {"base_score": 0, "temporal_score": 0, "impact": 0, "exploitability": 0}

    def calculate_fair_score(self, factors: RiskFactors) -> Dict[str, float]:
        """
        Berechnet FAIR-basierten Risk Score.

        FAIR: Factor Analysis of Information Risk
        Loss Event Frequency (LEF) = Threat Event Frequency (TEF) * Vulnerability (Threat Capability - Control Strength)
        Loss Magnitude (LM) = Primary Loss + Secondary Loss
        """
        # Threat Event Frequency (geschÃ¤tzt aus Exposure und Prevalence)
        tef = (factors.exposure / 10) * (factors.prevalence / 10)

        # Vulnerability (1 - Control Strength)
        control_strength = (10 - factors.exploitability) / 10
        threat_capability = factors.exploitability / 10
        vulnerability = max(0, threat_capability - control_strength)

        # Loss Event Frequency
        lef = tef * vulnerability

        # Loss Magnitude
        primary_loss = (factors.data_sensitivity + factors.business_impact) / 20
        secondary_loss = (factors.compliance_relevance + factors.asset_value) / 20
        lm = primary_loss + secondary_loss

        # Risk
        risk = lef * lm

        return {
            "threat_event_frequency": round(tef, 2),
            "vulnerability": round(vulnerability, 2),
            "loss_event_frequency": round(lef, 2),
            "loss_magnitude": round(lm, 2),
            "fair_risk": round(risk * 10, 1),  # Skaliert auf 0-10
        }

    def calculate_dread_score(
        self, damage: float, reproducibility: float, exploitability: float, affected_users: float, discoverability: float
    ) -> Dict[str, float]:
        """
        Berechnet DREAD Score.

        DREAD: Damage, Reproducibility, Exploitability, Affected Users, Discoverability
        Score = (D + R + E + A + D) / 5
        """
        # Alle Werte sollten 0-10 sein
        dread_score = (damage + reproducibility + exploitability + affected_users + discoverability) / 5

        return {
            "damage": damage,
            "reproducibility": reproducibility,
            "exploitability": exploitability,
            "affected_users": affected_users,
            "discoverability": discoverability,
            "dread_score": round(dread_score, 1),
        }

    def calculate_owasp_risk(
        self, threat_agent: float, vulnerability: float, technical_impact: float, business_impact: float
    ) -> Dict[str, float]:
        """
        Berechnet OWASP Risk Rating.

        Likelihood = Threat Agent * Vulnerability
        Impact = Technical Impact * Business Impact
        Risk = Likelihood * Impact
        """
        likelihood = (threat_agent / 10) * (vulnerability / 10)
        impact = (technical_impact / 10) * (business_impact / 10)
        risk = likelihood * impact

        return {
            "likelihood": round(likelihood, 2),
            "impact": round(impact, 2),
            "owasp_risk": round(risk * 10, 1),
        }

    def calculate_context_score(
        self, factors: RiskFactors, asset_criticality: AssetCriticality, threat_actor: ThreatActor
    ) -> Dict[str, float]:
        """
        Berechnet kontext-basierten Risk Score.

        BerÃ¼cksichtigt:
        - Asset KritikalitÃ¤t
        - Threat Actor Profil
        - Umgebungsfaktoren
        """
        # Asset Criticality Multiplier
        ac_multiplier = asset_criticality.value / 3  # 0.33 - 1.67

        # Threat Actor Capability
        ta_capability = self.THREAT_ACTOR_CAPABILITIES.get(threat_actor, 0.5)

        # Exposure Factor
        exposure_factor = factors.exposure / 10

        # Patch Factor (inverse - wenn Patch verfÃ¼gbar, sinkt Risiko)
        patch_factor = 1 - factors.patch_availability

        # Time Factor (schnellere Ausnutzung = hÃ¶heres Risiko)
        time_factor = min(1, 24 / max(factors.time_to_exploit, 1))

        context_score = (
            (
                factors.exploitability * 0.3
                + factors.data_sensitivity * 0.2
                + factors.business_impact * 0.2
                + factors.compliance_relevance * 0.1
                + factors.asset_value * 0.2
            )
            * ac_multiplier
            * ta_capability
            * exposure_factor
            * patch_factor
            * time_factor
        )

        return {
            "context_score": round(min(context_score, 10), 1),
            "asset_multiplier": round(ac_multiplier, 2),
            "threat_capability": round(ta_capability, 2),
            "exposure_factor": round(exposure_factor, 2),
            "patch_factor": round(patch_factor, 2),
            "time_factor": round(time_factor, 2),
        }

    def calculate_comprehensive_risk(
        self,
        cvss_vector: Optional[str] = None,
        cvss_score: Optional[float] = None,
        factors: Optional[RiskFactors] = None,
        asset_criticality: AssetCriticality = AssetCriticality.MEDIUM,
        threat_actor: ThreatActor = ThreatActor.CYBERCRIMINAL,
        dread_values: Optional[Dict[str, float]] = None,
        owasp_values: Optional[Dict[str, float]] = None,
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> RiskScore:
        """
        Berechnet einen umfassenden Risk Score unter Verwendung mehrerer Methoden.

        Args:
            cvss_vector: CVSS 3.1 Vector String
            cvss_score: Direkter CVSS Score (wenn kein Vector)
            factors: RiskFactors fÃ¼r FAIR und Kontext
            asset_criticality: KritikalitÃ¤t des Assets
            threat_actor: Threat Actor Profil
            dread_values: DREAD-Komponenten
            owasp_values: OWASP Risk-Komponenten
            custom_weights: Benutzerdefinierte Gewichtungen

        Returns:
            RiskScore mit allen Berechnungen
        """
        weights = custom_weights or self.weights
        scores = {}
        factors_applied = []

        # CVSS Score
        if cvss_vector:
            cvss_result = self.calculate_cvss_score(cvss_vector)
            scores["cvss"] = cvss_result["base_score"]
            factors_applied.append("cvss_vector")
        elif cvss_score is not None:
            scores["cvss"] = cvss_score
            factors_applied.append("cvss_score")
        else:
            scores["cvss"] = 5.0

        # FAIR Score
        if factors:
            fair_result = self.calculate_fair_score(factors)
            scores["fair"] = fair_result["fair_risk"]
            factors_applied.append("fair_factors")
        else:
            scores["fair"] = scores["cvss"] * 0.9

        # DREAD Score
        if dread_values:
            dread_result = self.calculate_dread_score(**dread_values)
            scores["dread"] = dread_result["dread_score"]
            factors_applied.append("dread")
        else:
            scores["dread"] = scores["cvss"] * 0.95

        # OWASP Score
        if owasp_values:
            owasp_result = self.calculate_owasp_risk(**owasp_values)
            scores["owasp"] = owasp_result["owasp_risk"]
            factors_applied.append("owasp")
        else:
            scores["owasp"] = scores["cvss"] * 0.85

        # Context Score
        if factors:
            context_result = self.calculate_context_score(factors, asset_criticality, threat_actor)
            scores["context"] = context_result["context_score"]
            factors_applied.append("context")
        else:
            scores["context"] = scores["cvss"] * 1.1

        # Gewichteter Durchschnitt
        final_score = sum(scores[method] * weights.get(method, 0.2) for method in scores.keys())

        # Normalisierung auf 0-10
        final_score = min(10, max(0, final_score))

        # Risk Level bestimmen
        risk_level = self._score_to_level(final_score)

        # Likelihood und Impact berechnen
        likelihood = self._calculate_likelihood(scores, factors)
        impact = self._calculate_impact(scores, factors)

        risk_score = RiskScore(
            base_score=round(scores["cvss"], 1),
            temporal_score=round(scores["cvss"] * 0.95, 1),  # Vereinfacht
            environmental_score=round(scores["context"], 1),
            final_score=round(final_score, 1),
            risk_level=risk_level,
            likelihood=round(likelihood, 2),
            impact=round(impact, 2),
            calculation_method="comprehensive_weighted",
            factors_applied=factors_applied,
            confidence=self._calculate_confidence(factors_applied),
        )

        # Historie speichern
        self.scoring_history.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "scores": scores,
                "final_score": final_score,
                "risk_level": risk_level.value,
            }
        )

        return risk_score

    def calculate_risk_trend(self, vulnerability_id: str, scores: List[Tuple[datetime, float]]) -> Dict[str, Any]:
        """
        Analysiert den Risiko-Trend Ã¼ber Zeit.

        Args:
            vulnerability_id: ID der Schwachstelle
            scores: Liste von (Timestamp, Score) Tupeln

        Returns:
            Trend-Analyse
        """
        if len(scores) < 2:
            return {"trend": "insufficient_data", "change_rate": 0}

        # Sortiere nach Zeit
        sorted_scores = sorted(scores, key=lambda x: x[0])

        # Berechne Ã„nderungsrate
        first_score = sorted_scores[0][1]
        last_score = sorted_scores[-1][1]
        change = last_score - first_score
        change_rate = change / len(scores)

        # Trend bestimmen
        if change > 1:
            trend = "increasing"
        elif change < -1:
            trend = "decreasing"
        else:
            trend = "stable"

        # VolatilitÃ¤t
        score_values = [s[1] for s in sorted_scores]
        mean = sum(score_values) / len(score_values)
        variance = sum((x - mean) ** 2 for x in score_values) / len(score_values)
        volatility = math.sqrt(variance)

        return {
            "vulnerability_id": vulnerability_id,
            "trend": trend,
            "change": round(change, 2),
            "change_rate": round(change_rate, 3),
            "volatility": round(volatility, 2),
            "first_score": first_score,
            "last_score": last_score,
            "data_points": len(scores),
        }

    def prioritize_vulnerabilities(
        self, vulnerabilities: List[Dict[str, Any]], asset_criticalities: Optional[Dict[str, AssetCriticality]] = None
    ) -> List[Dict[str, Any]]:
        """
        Priorisiert eine Liste von Schwachstellen.

        Args:
            vulnerabilities: Liste von Schwachstellen-Dictionaries
            asset_criticalities: Mapping von Asset zu Criticality

        Returns:
            Priorisierte Liste mit Risk Scores
        """
        prioritized = []
        asset_criticalities = asset_criticalities or {}

        for vuln in vulnerabilities:
            asset = vuln.get("target", "unknown")
            criticality = asset_criticalities.get(asset, AssetCriticality.MEDIUM)

            # Berechne Risk Score
            risk_score = self.calculate_comprehensive_risk(
                cvss_vector=vuln.get("cvss_vector"),
                cvss_score=vuln.get("cvss_score"),
                asset_criticality=criticality,
            )

            prioritized.append(
                {
                    **vuln,
                    "risk_score": risk_score.to_dict(),
                    "priority_score": self._calculate_priority_score(risk_score, vuln),
                }
            )

        # Sortiere nach Priority Score (absteigend)
        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)

        return prioritized

    def get_risk_matrix(self) -> Dict[str, List[str]]:
        """
        Generiert eine Risk Matrix nach ISO 27005.

        Returns:
            Risk Matrix als Dictionary
        """
        likelihood_levels = ["Sehr unwahrscheinlich", "Unwahrscheinlich", "MÃ¶glich", "Wahrscheinlich", "Sehr wahrscheinlich"]
        impact_levels = ["Sehr gering", "Gering", "Mittel", "Hoch", "Sehr hoch"]

        matrix = {}
        for i, likelihood in enumerate(likelihood_levels):
            matrix[likelihood] = []
            for j, impact in enumerate(impact_levels):
                risk_value = (i + 1) * (j + 1)
                if risk_value >= 20:
                    level = "KRITISCH"
                elif risk_value >= 12:
                    level = "HOCH"
                elif risk_value >= 6:
                    level = "MITTEL"
                else:
                    level = "NIEDRIG"
                matrix[likelihood].append(f"{impact}: {level} ({risk_value})")

        return matrix

    def generate_risk_report(self) -> Dict[str, Any]:
        """Generiert einen Risk Report basierend auf der Scoring-Historie"""
        if not self.scoring_history:
            return {"error": "Keine Scoring-Historie verfÃ¼gbar"}

        scores = [entry["final_score"] for entry in self.scoring_history]

        return {
            "report_generated": datetime.utcnow().isoformat(),
            "total_assessments": len(self.scoring_history),
            "average_score": round(sum(scores) / len(scores), 2),
            "max_score": max(scores),
            "min_score": min(scores),
            "score_distribution": self._calculate_distribution(scores),
            "risk_level_distribution": self._calculate_level_distribution(),
            "scoring_methods_used": list(
                set(method for entry in self.scoring_history for method in entry.get("scores", {}).keys())
            ),
        }

    def _score_to_level(self, score: float) -> RiskLevel:
        """Konvertiert Score zu Risk Level"""
        for level, (min_val, max_val) in self.risk_thresholds.items():
            if min_val <= score <= max_val:
                return level
        return RiskLevel.LOW

    def _calculate_likelihood(self, scores: Dict[str, float], factors: Optional[RiskFactors]) -> float:
        """Berechnet die Eintrittswahrscheinlichkeit"""
        base_likelihood = scores.get("cvss", 5) / 10

        if factors:
            exploitability_factor = factors.exploitability / 10
            prevalence_factor = factors.prevalence / 10
            return base_likelihood * 0.4 + exploitability_factor * 0.4 + prevalence_factor * 0.2

        return base_likelihood

    def _calculate_impact(self, scores: Dict[str, float], factors: Optional[RiskFactors]) -> float:
        """Berechnet den Impact"""
        base_impact = scores.get("cvss", 5) / 10

        if factors:
            data_impact = factors.data_sensitivity / 10
            business_impact = factors.business_impact / 10
            return base_impact * 0.3 + data_impact * 0.35 + business_impact * 0.35

        return base_impact

    def _calculate_confidence(self, factors_applied: List[str]) -> float:
        """Berechnet die Konfidenz basierend auf angewendeten Faktoren"""
        base_confidence = 0.5
        confidence_boost = len(factors_applied) * 0.1
        return min(1.0, base_confidence + confidence_boost)

    def _calculate_priority_score(self, risk_score: RiskScore, vuln: Dict) -> float:
        """Berechnet einen PrioritÃ¤ts-Score fÃ¼r die Sortierung"""
        base_priority = risk_score.final_score

        # Boost fÃ¼r kritische Schwachstellen
        if vuln.get("category") in ["sql_injection", "code_execution", "insecure_deserialization"]:
            base_priority *= 1.2

        # Boost fÃ¼r Ã¶ffentlich bekannte CVEs
        if vuln.get("cve_id"):
            base_priority *= 1.1

        # Boost fÃ¼r einfache Ausnutzbarkeit
        if vuln.get("exploit_available"):
            base_priority *= 1.15

        return round(base_priority, 2)

    def _calculate_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Berechnet die Verteilung der Scores"""
        distribution = {"0-2": 0, "2-4": 0, "4-6": 0, "6-8": 0, "8-10": 0}
        for score in scores:
            if score < 2:
                distribution["0-2"] += 1
            elif score < 4:
                distribution["2-4"] += 1
            elif score < 6:
                distribution["4-6"] += 1
            elif score < 8:
                distribution["6-8"] += 1
            else:
                distribution["8-10"] += 1
        return distribution

    def _calculate_level_distribution(self) -> Dict[str, int]:
        """Berechnet die Verteilung der Risk Levels"""
        distribution = defaultdict(int)
        for entry in self.scoring_history:
            distribution[entry.get("risk_level", "unknown")] += 1
        return dict(distribution)


# Singleton-Instanz
_scorer = None


def get_risk_scorer() -> RiskScorer:
    """Gibt die Singleton-Instanz des RiskScorers zurÃ¼ck"""
    global _scorer
    if _scorer is None:
        _scorer = RiskScorer()
    return _scorer


if __name__ == "__main__":
    # Demo/Test
    scorer = RiskScorer()

    # Test CVSS
    cvss_vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    cvss_result = scorer.calculate_cvss_score(cvss_vector)
    print("CVSS Result:", cvss_result)

    # Test Comprehensive Risk
    factors = RiskFactors(
        exploitability=8.0,
        prevalence=7.0,
        data_sensitivity=9.0,
        business_impact=8.0,
        exposure=9.0,
        asset_value=8.0,
    )

    risk_score = scorer.calculate_comprehensive_risk(
        cvss_vector=cvss_vector,
        factors=factors,
        asset_criticality=AssetCriticality.HIGH,
        threat_actor=ThreatActor.CYBERCRIMINAL,
    )

    print("\nComprehensive Risk Score:")
    print(json.dumps(risk_score.to_dict(), indent=2))

    # Test Risk Matrix
    print("\nRisk Matrix:")
    print(json.dumps(scorer.get_risk_matrix(), indent=2))
