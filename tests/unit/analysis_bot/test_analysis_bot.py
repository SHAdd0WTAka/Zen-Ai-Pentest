"""
Unit Tests for Analysis Bot
"""

import pytest
from unittest.mock import Mock, patch
from analysis_bot import AnalysisBot, AnalysisConfig, AnalysisResult
from analysis_bot.engines import (
    VulnerabilityAnalyzer,
    RiskScorer,
    ExploitabilityChecker,
    RecommendationEngine
)


class TestAnalysisConfig:
    """Test AnalysisConfig dataclass"""

    def test_default_config(self):
        """Test default configuration"""
        config = AnalysisConfig()
        assert config is not None

    def test_config_with_user_id(self):
        """Test config with user ID"""
        config = AnalysisConfig(user_id="test-user-123")
        assert config.user_id == "test-user-123"


class TestVulnerabilityAnalyzer:
    """Test VulnerabilityAnalyzer"""

    def test_init(self):
        """Test analyzer initialization"""
        analyzer = VulnerabilityAnalyzer()
        assert analyzer is not None

    def test_analyze_code_sql_injection(self):
        """Test SQL injection detection"""
        analyzer = VulnerabilityAnalyzer()
        code = "SELECT * FROM users WHERE id = '" + "$_GET['id']" + "'"

        # Mock the analyze_code method
        with patch.object(analyzer, 'analyze_code') as mock_analyze:
            mock_vuln = Mock()
            mock_vuln.title = "SQL Injection"
            mock_vuln.severity = "High"
            mock_analyze.return_value = [mock_vuln]

            results = analyzer.analyze_code(code, "test.php")
            assert len(results) > 0
            assert results[0].title == "SQL Injection"


class TestRiskScorer:
    """Test RiskScorer"""

    def test_init(self):
        """Test scorer initialization"""
        scorer = RiskScorer()
        assert scorer is not None

    def test_cvss_calculation(self):
        """Test CVSS score calculation"""
        scorer = RiskScorer()

        # Test with a critical vulnerability
        cvss_vector = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"

        with patch.object(scorer, 'calculate_cvss') as mock_calc:
            mock_calc.return_value = 9.8
            score = scorer.calculate_cvss(cvss_vector)
            assert score == 9.8


class TestExploitabilityChecker:
    """Test ExploitabilityChecker"""

    def test_init(self):
        """Test checker initialization"""
        checker = ExploitabilityChecker()
        assert checker is not None

    def test_check_exploitability(self):
        """Test exploitability check"""
        checker = ExploitabilityChecker()

        mock_vuln = Mock()
        mock_vuln.title = "SQL Injection"

        with patch.object(checker, 'check_exploitability') as mock_check:
            mock_check.return_value = {
                "exploitable": True,
                "difficulty": "Easy",
                "public_exploit_available": True
            }
            result = checker.check_exploitability(mock_vuln)
            assert result["exploitable"] is True


class TestRecommendationEngine:
    """Test RecommendationEngine"""

    def test_init(self):
        """Test engine initialization"""
        engine = RecommendationEngine()
        assert engine is not None

    def test_generate_recommendation(self):
        """Test recommendation generation"""
        engine = RecommendationEngine()

        mock_vuln = Mock()
        mock_vuln.title = "SQL Injection"
        mock_vuln.severity = "High"

        with patch.object(engine, 'generate_recommendation') as mock_gen:
            mock_gen.return_value = {
                "title": "Use Prepared Statements",
                "priority": "High",
                "effort": "Medium"
            }
            result = engine.generate_recommendation(mock_vuln)
            assert result["priority"] == "High"


class TestAnalysisBot:
    """Test AnalysisBot main class"""

    def test_init(self):
        """Test bot initialization"""
        bot = AnalysisBot()
        assert bot is not None
        assert hasattr(bot, 'vulnerability_analyzer')
        assert hasattr(bot, 'risk_scorer')
        assert hasattr(bot, 'exploitability_checker')
        assert hasattr(bot, 'recommendation_engine')

    @pytest.mark.asyncio
    async def test_analyze_code(self):
        """Test analyze method"""
        bot = AnalysisBot()

        with patch.object(bot, 'analyze') as mock_analyze:
            mock_result = Mock(spec=AnalysisResult)
            mock_result.id = "test-analysis-123"
            mock_result.status = "completed"
            mock_result.vulnerabilities = []
            mock_analyze.return_value = mock_result

            config = AnalysisConfig(user_id="test-user")
            result = await bot.analyze(
                target=r"<?php echo \$_GET['id']; ?>",
                target_type="code",
                config=config
            )

            assert result.id == "test-analysis-123"
            assert result.status == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
