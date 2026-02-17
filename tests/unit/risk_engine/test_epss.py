"""
Unit Tests für risk_engine/epss.py

Tests EPSS client with mocked HTTP requests.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from risk_engine.epss import EPSSClient

pytestmark = pytest.mark.unit


class TestEPSSClientInit:
    """Test EPSSClient initialization"""
    
    def test_default_init(self):
        """Test default initialization"""
        client = EPSSClient()
        assert client.cache == {}
        assert client.cache_duration == timedelta(hours=24)
        assert hasattr(client, 'logger')
    
    def test_custom_cache_duration(self):
        """Test custom cache duration"""
        client = EPSSClient(cache_duration=48)
        assert client.cache_duration == timedelta(hours=48)
    
    def test_api_url_constant(self):
        """Test API URL is correct"""
        assert EPSSClient.API_URL == "https://api.first.org/data/v1/epss"


class TestEPSSGetScore:
    """Test get_score method"""
    
    def test_get_score_from_api(self):
        """Test fetching score from API"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"cve": "CVE-2021-44228", "epss": "0.95"}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            score = client.get_score("CVE-2021-44228")
            assert score == 0.95
    
    def test_get_score_caching(self):
        """Test score is cached"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"cve": "CVE-2021-44228", "epss": "0.95"}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            # First call - should hit API
            score1 = client.get_score("CVE-2021-44228")
            # Second call - should use cache
            score2 = client.get_score("CVE-2021-44228")
            
            # API should only be called once
            assert mock_get.call_count == 1
            assert score1 == score2
    
    def test_get_score_cache_expired(self):
        """Test cache expiration"""
        client = EPSSClient(cache_duration=0)  # Immediate expiration
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"cve": "CVE-2021-44228", "epss": "0.95"}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            # First call
            client.get_score("CVE-2021-44228")
            # Second call - cache expired, should hit API again
            client.get_score("CVE-2021-44228")
            
            assert mock_get.call_count == 2
    
    def test_get_score_api_error(self):
        """Test handling API error"""
        client = EPSSClient()
        
        with patch('requests.get', side_effect=Exception("API Error")):
            score = client.get_score("CVE-2021-44228")
            assert score == 0.0
    
    def test_get_score_empty_response(self):
        """Test empty API response"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            score = client.get_score("CVE-2021-44228")
            assert score == 0.0
    
    def test_get_score_missing_epss(self):
        """Test response without epss field"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"cve": "CVE-2021-44228"}]}
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            score = client.get_score("CVE-2021-44228")
            assert score == 0.0
    
    def test_get_score_case_insensitive(self):
        """Test CVE ID case handling"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"cve": "CVE-2021-44228", "epss": "0.95"}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            score = client.get_score("cve-2021-44228")  # lowercase
            assert score == 0.95


class TestEPSSBatchScores:
    """Test get_batch_scores method"""
    
    def test_batch_scores_success(self):
        """Test successful batch fetch"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"cve": "CVE-2021-44228", "epss": "0.95"},
                {"cve": "CVE-2017-0144", "epss": "0.85"},
            ]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            results = client.get_batch_scores(["CVE-2021-44228", "CVE-2017-0144"])
            
            assert results["CVE-2021-44228"] == 0.95
            assert results["CVE-2017-0144"] == 0.85
    
    def test_batch_scores_empty_list(self):
        """Test with empty list"""
        client = EPSSClient()
        results = client.get_batch_scores([])
        assert results == {}
    
    def test_batch_scores_api_limit(self):
        """Test API limit of 100 CVEs"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            cves = [f"CVE-2021-{i:05d}" for i in range(150)]
            client.get_batch_scores(cves)
            
            # Check that only first 100 were passed
            call_args = mock_get.call_args
            params = call_args[1].get('params', {})
            cve_param = params.get('cve', '')
            assert len(cve_param.split(',')) == 100
    
    def test_batch_scores_missing_cves(self):
        """Test batch with missing CVEs"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"cve": "CVE-2021-44228", "epss": "0.95"}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            results = client.get_batch_scores(["CVE-2021-44228", "CVE-9999-99999"])
            
            assert results["CVE-2021-44228"] == 0.95
            assert results["CVE-9999-99999"] == 0.0  # Missing CVE gets 0
    
    def test_batch_scores_api_error(self):
        """Test batch with API error"""
        client = EPSSClient()
        
        with patch('requests.get', side_effect=Exception("API Error")):
            results = client.get_batch_scores(["CVE-2021-44228"])
            
            assert results["CVE-2021-44228"] == 0.0


class TestEPSSGetPercentile:
    """Test get_percentile method"""
    
    def test_get_percentile_success(self):
        """Test successful percentile fetch"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"cve": "CVE-2021-44228", "epss": "0.95", "percentile": "0.99"}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            percentile = client.get_percentile("CVE-2021-44228")
            assert percentile == 0.99
    
    def test_get_percentile_no_data(self):
        """Test percentile with no data"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            percentile = client.get_percentile("CVE-2021-44228")
            assert percentile is None
    
    def test_get_percentile_api_error(self):
        """Test percentile with API error"""
        client = EPSSClient()
        
        with patch('requests.get', side_effect=Exception("API Error")):
            percentile = client.get_percentile("CVE-2021-44228")
            assert percentile is None
    
    def test_get_percentile_missing_field(self):
        """Test percentile when field is missing"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"cve": "CVE-2021-44228", "epss": "0.95"}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            percentile = client.get_percentile("CVE-2021-44228")
            assert percentile is None


class TestEPSSInterpretScore:
    """Test interpret_score method"""
    
    def test_interpret_very_high(self):
        """Test very high score interpretation"""
        client = EPSSClient()
        text = client.interpret_score(0.5)
        assert "Very High" in text
        assert "likely" in text
    
    def test_interpret_high(self):
        """Test high score interpretation"""
        client = EPSSClient()
        text = client.interpret_score(0.3)
        assert "High" in text
        assert "probable" in text
    
    def test_interpret_medium(self):
        """Test medium score interpretation"""
        client = EPSSClient()
        text = client.interpret_score(0.1)
        assert "Medium" in text
        assert "risk" in text
    
    def test_interpret_low(self):
        """Test low score interpretation"""
        client = EPSSClient()
        text = client.interpret_score(0.05)
        assert "Low" in text
    
    def test_interpret_very_low(self):
        """Test very low score interpretation"""
        client = EPSSClient()
        text = client.interpret_score(0.01)
        assert "Very Low" in text
        assert "Unlikely" in text  # Case sensitive in implementation
    
    def test_interpret_boundary(self):
        """Test boundary values"""
        client = EPSSClient()
        
        # Exactly 0.5
        assert "Very High" in client.interpret_score(0.5)
        # Exactly 0.3
        assert "High" in client.interpret_score(0.3)
        # Zero
        assert "Very Low" in client.interpret_score(0.0)


class TestEPSSShouldPrioritize:
    """Test should_prioritize method"""
    
    def test_should_prioritize_high_score(self):
        """Test prioritization for high EPSS"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"cve": "CVE-2021-44228", "epss": "0.5"}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            assert client.should_prioritize("CVE-2021-44228") is True
    
    def test_should_not_prioritize_low_score(self):
        """Test no prioritization for low EPSS"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"cve": "CVE-2021-44228", "epss": "0.05"}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            assert client.should_prioritize("CVE-2021-44228") is False
    
    def test_should_prioritize_custom_threshold(self):
        """Test prioritization with custom threshold"""
        client = EPSSClient()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"cve": "CVE-2021-44228", "epss": "0.15"}]
        }
        mock_response.raise_for_status = Mock()
        
        with patch('requests.get', return_value=mock_response):
            # Default threshold 0.2
            assert client.should_prioritize("CVE-2021-44228") is False
            # Custom threshold 0.1
            assert client.should_prioritize("CVE-2021-44228", threshold=0.1) is True
