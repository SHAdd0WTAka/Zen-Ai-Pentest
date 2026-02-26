"""Tests for risk/epss.py - EPSS Client."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from risk.epss import (
    EPSSClient,
    EPSSScore,
)


class TestEPSSScore:
    """Test EPSSScore dataclass."""

    def test_creation(self):
        """Test creating EPSSScore."""
        score = EPSSScore(
            cve_id="CVE-2021-44228",
            epss_score=0.95,
            epss_percentile=0.99,
            date="2024-01-01",
        )

        assert score.cve_id == "CVE-2021-44228"
        assert score.epss_score == 0.95
        assert score.epss_percentile == 0.99

    def test_probability_percentage(self):
        """Test probability percentage property."""
        score = EPSSScore(
            cve_id="CVE-2021-44228",
            epss_score=0.5,
            epss_percentile=0.8,
            date="2024-01-01",
        )

        assert score.probability_percentage == 50.0

    def test_risk_level_critical(self):
        """Test risk level categorization - Critical."""
        score = EPSSScore(
            cve_id="CVE-2021-44228",
            epss_score=0.5,
            epss_percentile=0.8,
            date="2024-01-01",
        )

        assert score.risk_level == "Critical"

    def test_risk_level_high(self):
        """Test risk level categorization - High."""
        score = EPSSScore(
            cve_id="CVE-2021-44228",
            epss_score=0.25,
            epss_percentile=0.8,
            date="2024-01-01",
        )

        assert score.risk_level == "High"

    def test_risk_level_medium(self):
        """Test risk level categorization - Medium."""
        score = EPSSScore(
            cve_id="CVE-2021-44228",
            epss_score=0.1,
            epss_percentile=0.8,
            date="2024-01-01",
        )

        assert score.risk_level == "Medium"

    def test_risk_level_low(self):
        """Test risk level categorization - Low."""
        score = EPSSScore(
            cve_id="CVE-2021-44228",
            epss_score=0.01,
            epss_percentile=0.8,
            date="2024-01-01",
        )

        assert score.risk_level == "Low"


class TestEPSSClientInit:
    """Test EPSSClient initialization."""

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        client = EPSSClient()

        assert client.api_key is None
        assert client.cache == {}
        assert client.last_update is None

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = EPSSClient(api_key="test-key")

        assert client.api_key == "test-key"


class TestEPSSClientGetScore:
    """Test EPSSClient.get_score method."""

    def test_get_score_from_cache(self):
        """Test getting score from cache."""
        client = EPSSClient()
        cached_score = EPSSScore(
            cve_id="CVE-2021-44228",
            epss_score=0.95,
            epss_percentile=0.99,
            date="2024-01-01",
        )
        client.cache["CVE-2021-44228"] = cached_score

        result = client.get_score("CVE-2021-44228")

        assert result == cached_score

    @patch("risk.epss.requests.Session")
    def test_get_score_api_success(self, mock_session_class):
        """Test getting score from API - success."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "cve": "CVE-2021-44228",
                    "epss": "0.95",
                    "percentile": "0.99",
                    "date": "2024-01-01",
                }
            ]
        }
        mock_session.get.return_value = mock_response

        client = EPSSClient()
        result = client.get_score("CVE-2021-44228")

        assert result is not None
        assert result.cve_id == "CVE-2021-44228"
        assert result.epss_score == 0.95
        assert result.epss_percentile == 0.99
        assert "CVE-2021-44228" in client.cache

    @patch("risk.epss.requests.Session")
    def test_get_score_api_with_auth(self, mock_session_class):
        """Test getting score with API key."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_session.get.return_value = mock_response

        client = EPSSClient(api_key="secret-key")
        client.get_score("CVE-2021-44228")

        call_args = mock_session.get.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer secret-key"

    @patch("risk.epss.requests.Session")
    def test_get_score_api_empty_data(self, mock_session_class):
        """Test getting score - empty API response."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_session.get.return_value = mock_response

        client = EPSSClient()
        result = client.get_score("CVE-2021-44228")

        assert result is None

    @patch("risk.epss.requests.Session")
    def test_get_score_api_error(self, mock_session_class):
        """Test getting score - API error."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 500
        mock_session.get.return_value = mock_response

        client = EPSSClient()
        result = client.get_score("CVE-2021-44228")

        assert result is None

    @patch("risk.epss.requests.Session")
    def test_get_score_api_exception(self, mock_session_class):
        """Test getting score - API exception."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = Exception("Network error")

        client = EPSSClient()
        result = client.get_score("CVE-2021-44228")

        assert result is None


class TestEPSSClientGetScoresBatch:
    """Test EPSSClient.get_scores_batch method."""

    def test_get_scores_batch_all_cached(self):
        """Test batch - all items cached."""
        client = EPSSClient()
        cached_score = EPSSScore(
            cve_id="CVE-2021-44228",
            epss_score=0.95,
            epss_percentile=0.99,
            date="2024-01-01",
        )
        client.cache["CVE-2021-44228"] = cached_score

        results = client.get_scores_batch(["CVE-2021-44228"])

        assert "CVE-2021-44228" in results
        assert results["CVE-2021-44228"] == cached_score

    @patch("risk.epss.requests.Session")
    def test_get_scores_batch_partial_cache(self, mock_session_class):
        """Test batch - partial cache hit."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "cve": "CVE-2021-45046",
                    "epss": "0.85",
                    "percentile": "0.95",
                    "date": "2024-01-01",
                }
            ]
        }
        mock_session.get.return_value = mock_response

        client = EPSSClient()
        cached_score = EPSSScore(
            cve_id="CVE-2021-44228",
            epss_score=0.95,
            epss_percentile=0.99,
            date="2024-01-01",
        )
        client.cache["CVE-2021-44228"] = cached_score

        results = client.get_scores_batch(["CVE-2021-44228", "CVE-2021-45046"])

        assert "CVE-2021-44228" in results
        assert "CVE-2021-45046" in results

    @patch("risk.epss.requests.Session")
    def test_get_scores_batch_limit(self, mock_session_class):
        """Test batch - API limit of 100 CVEs."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_session.get.return_value = mock_response

        client = EPSSClient()
        cve_ids = [f"CVE-2021-{i:05d}" for i in range(150)]
        client.get_scores_batch(cve_ids)

        # Should only request first 100
        call_args = mock_session.get.call_args
        cve_param = call_args[1]["params"]["cve"]
        assert len(cve_param.split(",")) <= 100

    @patch("risk.epss.requests.Session")
    def test_get_scores_batch_api_error(self, mock_session_class):
        """Test batch - API error handling."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = Exception("Network error")

        client = EPSSClient()
        results = client.get_scores_batch(["CVE-2021-44228"])

        assert results == {}


class TestEPSSClientEstimateScore:
    """Test EPSSClient.estimate_score method."""

    def test_estimate_score_cvss_only(self):
        """Test estimation from CVSS score only."""
        client = EPSSClient()

        # CVSS 10.0 should give ~30%
        score = client.estimate_score(10.0)
        assert score == 0.3

        # CVSS 5.0 should give ~15%
        score = client.estimate_score(5.0)
        assert score == 0.15

    def test_estimate_score_with_exploit(self):
        """Test estimation with exploit available."""
        client = EPSSClient()

        # CVSS 10.0 + exploit
        score = client.estimate_score(10.0, has_exploit=True)
        assert score == 0.7  # 0.3 + 0.4

    def test_estimate_score_max_cap(self):
        """Test estimation capped at 95%."""
        client = EPSSClient()

        # Very high CVSS + exploit should not exceed 95%
        score = client.estimate_score(10.0, has_exploit=True)
        score = client.estimate_score(10.0, has_exploit=True)
        assert score <= 0.95

    def test_estimate_score_zero(self):
        """Test estimation for zero CVSS."""
        client = EPSSClient()

        score = client.estimate_score(0.0)
        assert score == 0.0


class TestIntegration:
    """Integration tests."""

    def test_cache_populated_on_get(self):
        """Test cache is populated after get_score."""
        with patch("risk.epss.requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": [
                    {
                        "cve": "CVE-2021-44228",
                        "epss": "0.95",
                        "percentile": "0.99",
                        "date": "2024-01-01",
                    }
                ]
            }
            mock_session.get.return_value = mock_response

            client = EPSSClient()
            assert "CVE-2021-44228" not in client.cache

            client.get_score("CVE-2021-44228")

            assert "CVE-2021-44228" in client.cache
