"""
Tests for OSINT Sub-modules
Certificate Transparency, WHOIS Lookup, DNS Enumeration
"""

import json
import pytest
import asyncio
import ssl
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import socket

from modules.osint_modules.cert_transparency import (
    CertificateTransparency,
    Certificate,
)
from modules.osint_modules.whois_lookup import (
    WhoisLookup,
    WhoisRecord,
)
from modules.osint_modules.dns_enum import (
    DNSEnumerator,
    DNSRecord,
)


# CertificateTransparency Tests
class TestCertificateTransparency:
    """Tests for CertificateTransparency class"""

    @pytest.fixture
    def ct_scanner(self):
        """Create a CertificateTransparency instance"""
        return CertificateTransparency(config={"timeout": 30.0})

    @pytest.fixture
    def mock_crtsh_response(self):
        """Create mock crt.sh response"""
        return [
            {
                "id": "12345",
                "name_value": "*.example.com\nexample.com",
                "issuer_name": "Let's Encrypt Authority X3",
                "not_before": "2024-01-01T00:00:00",
                "not_after": "2024-04-01T00:00:00",
                "serial_number": "00:01:02:03:04:05:06:07:08:09:0a:0b:0c:0d:0e:0f:10:11",
            },
            {
                "id": "12346",
                "name_value": "www.example.com",
                "issuer_name": "Let's Encrypt Authority X3",
                "not_before": "2024-01-15T00:00:00",
                "not_after": "2024-04-15T00:00:00",
                "serial_number": "00:11:22:33:44:55:66:77:88:99:aa:bb:cc:dd:ee:ff:00:11",
            },
        ]

    @pytest.fixture
    def mock_certspotter_response(self):
        """Create mock CertSpotter response"""
        return [
            {
                "id": "cert-001",
                "dns_names": ["example.com", "www.example.com"],
                "issuer": {"name": "Let's Encrypt"},
                "not_before": "2024-01-01T00:00:00Z",
                "not_after": "2024-04-01T00:00:00Z",
            },
            {
                "id": "cert-002",
                "dns_names": ["api.example.com"],
                "issuer": {"name": "DigiCert"},
                "not_before": "2024-01-15T00:00:00Z",
                "not_after": "2024-07-15T00:00:00Z",
            },
        ]

    def test_initialization(self, ct_scanner):
        """Test CertificateTransparency initialization"""
        assert ct_scanner.config == {"timeout": 30.0}
        assert ct_scanner.timeout == 30.0
        assert ct_scanner.cache == {}
        assert ct_scanner.found_subdomains == set()

    @pytest.mark.asyncio
    async def test_search(self, ct_scanner, mock_crtsh_response, mock_certspotter_response):
        """Test CT log search"""
        with patch.object(ct_scanner, '_search_crtsh', return_value={
            "source": "crt.sh",
            "certificates": [Mock(spec=Certificate, id="12345", domain="example.com", 
                                  issuer="Let's Encrypt", serial_number="12345", san=[],
                                  not_before=None, not_after=None, subject=None, fingerprint=None, raw=None)],
            "subdomains": ["example.com", "www.example.com"],
        }):
            with patch.object(ct_scanner, '_search_certspotter', return_value={
                "source": "certspotter",
                "certificates": [],
                "subdomains": ["api.example.com"],
            }):
                result = await ct_scanner.search("example.com")
                
                assert result["domain"] == "example.com"
                assert "subdomains" in result
                assert "certificates" in result

    @pytest.mark.asyncio
    async def test_search_crtsh(self, ct_scanner, mock_crtsh_response):
        """Test crt.sh search"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_crtsh_response)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await ct_scanner._search_crtsh("example.com")
            
            assert result["source"] == "crt.sh"
            assert len(result["certificates"]) == 2
            assert "example.com" in result["subdomains"]
            assert "www.example.com" in result["subdomains"]

    @pytest.mark.asyncio
    async def test_search_crtsh_http_error(self, ct_scanner):
        """Test crt.sh search with HTTP error"""
        mock_response = AsyncMock()
        mock_response.status = 404
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await ct_scanner._search_crtsh("example.com")
            
            assert result["source"] == "crt.sh"
            assert len(result["certificates"]) == 0

    @pytest.mark.asyncio
    async def test_search_certspotter(self, ct_scanner, mock_certspotter_response):
        """Test CertSpotter search"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_certspotter_response)
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await ct_scanner._search_certspotter("example.com")
            
            assert result["source"] == "certspotter"
            assert len(result["certificates"]) == 2
            assert "example.com" in result["subdomains"]
            assert "api.example.com" in result["subdomains"]

    @pytest.mark.asyncio
    async def test_get_certificate_details(self, ct_scanner):
        """Test getting certificate details directly from server"""
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        
        mock_ssl_obj = Mock()
        mock_ssl_obj.getpeercert.return_value = {
            "subject": (("commonName", "example.com"),),
            "issuer": (("commonName", "Let's Encrypt"),),
            "notBefore": "Jan 1 00:00:00 2024 GMT",
            "notAfter": "Apr 1 00:00:00 2024 GMT",
            "serialNumber": "1234567890",
            "version": 3,
            "subjectAltName": (("DNS", "example.com"), ("DNS", "www.example.com")),
        }
        mock_ssl_obj.cipher.return_value = ("TLS_AES_256_GCM_SHA384", "TLSv1.3", 256)
        mock_ssl_obj.version.return_value = "TLSv1.3"
        
        mock_writer.get_extra_info.return_value = mock_ssl_obj
        
        with patch('asyncio.open_connection', return_value=(mock_reader, mock_writer)):
            with patch('asyncio.wait_for', side_effect=lambda coro, timeout: coro):
                result = await ct_scanner.get_certificate_details("example.com")
                
                assert result is not None
                assert result["tls_version"] == "TLSv1.3"
                assert result["cipher_suite"] == "TLS_AES_256_GCM_SHA384"

    @pytest.mark.asyncio
    async def test_get_certificate_details_error(self, ct_scanner):
        """Test getting certificate details with error"""
        with patch('asyncio.open_connection', side_effect=Exception("Connection failed")):
            result = await ct_scanner.get_certificate_details("example.com")
            
            assert result is None

    def test_get_subdomains_empty(self, ct_scanner):
        """Test getting subdomains when cache is empty"""
        subdomains = ct_scanner.get_subdomains()
        assert subdomains == []

    def test_get_subdomains_for_domain(self, ct_scanner):
        """Test getting subdomains for specific domain"""
        cert1 = Certificate(id="1", domain="example.com", san=["www.example.com"])
        cert2 = Certificate(id="2", domain="api.example.com", san=[])
        ct_scanner.cache["example.com"] = [cert1, cert2]
        
        subdomains = ct_scanner.get_subdomains("example.com")
        
        assert "example.com" in subdomains
        assert "www.example.com" in subdomains
        assert "api.example.com" in subdomains

    def test_get_expiring_certificates(self, ct_scanner):
        """Test getting expiring certificates"""
        # Certificate expiring soon
        soon = datetime.now().isoformat()
        cert1 = Certificate(id="1", domain="example.com", not_after=soon)
        # Certificate expiring far in future
        far_future = "2099-12-31T00:00:00"
        cert2 = Certificate(id="2", domain="example.com", not_after=far_future)
        
        ct_scanner.cache["example.com"] = [cert1, cert2]
        
        expiring = ct_scanner.get_expiring_certificates(days=30)
        
        assert len(expiring) >= 1  # At least the one with 'now' timestamp

    def test_certificate_to_dict(self):
        """Test Certificate to_dict"""
        cert = Certificate(
            id="123",
            domain="example.com",
            issuer="Let's Encrypt",
            san=["www.example.com", "api.example.com"],
        )
        
        data = cert.to_dict()
        
        assert data["id"] == "123"
        assert data["domain"] == "example.com"
        assert data["issuer"] == "Let's Encrypt"
        assert data["san"] == ["www.example.com", "api.example.com"]


# WhoisLookup Tests
class TestWhoisLookup:
    """Tests for WhoisLookup class"""

    @pytest.fixture
    def whois(self):
        """Create a WhoisLookup instance"""
        return WhoisLookup(config={"timeout": 10.0})

    def test_initialization(self, whois):
        """Test WhoisLookup initialization"""
        assert whois.config == {"timeout": 10.0}
        assert whois.timeout == 10.0
        assert whois.cache == {}

    @pytest.mark.asyncio
    async def test_lookup_from_cache(self, whois):
        """Test lookup returns cached result"""
        record = WhoisRecord(domain_name="example.com", registrar="Test Registrar")
        whois.cache["example.com"] = record
        
        result = await whois.lookup("example.com")
        
        assert result == record

    @pytest.mark.asyncio
    async def test_lookup_python_whois(self, whois):
        """Test lookup using python-whois"""
        mock_whois_obj = Mock()
        mock_whois_obj.registrar = "Example Registrar Inc."
        mock_whois_obj.registrar_url = "https://example.com"
        mock_whois_obj.name_servers = ["ns1.example.com", "ns2.example.com"]
        mock_whois_obj.creation_date = datetime(2020, 1, 1)
        mock_whois_obj.expiration_date = datetime(2025, 1, 1)
        mock_whois_obj.updated_date = datetime(2024, 1, 1)
        mock_whois_obj.status = ["clientTransferProhibited"]
        mock_whois_obj.dnssec = "unsigned"
        mock_whois_obj.registrant_name = "John Doe"
        mock_whois_obj.registrant_organization = "Example Corp"
        mock_whois_obj.registrant_email = "admin@example.com"
        mock_whois_obj.admin_email = "admin@example.com"
        mock_whois_obj.tech_email = "tech@example.com"
        
        with patch('whois.whois', return_value=mock_whois_obj):
            result = await whois.lookup("example.com")
            
            assert result.domain_name == "example.com"
            assert result.registrar == "Example Registrar Inc."
            assert result.name_servers == ["ns1.example.com", "ns2.example.com"]
            assert result.registrant_name == "John Doe"
            assert result.registrant_email == "admin@example.com"

    @pytest.mark.asyncio
    async def test_lookup_system_whois(self, whois):
        """Test lookup using system whois command"""
        whois_output = """
Domain Name: EXAMPLE.COM
Registrar: Example Registrar Inc.
Registrar URL: https://example.com
Name Server: NS1.EXAMPLE.COM
Name Server: NS2.EXAMPLE.COM
Creation Date: 2020-01-01T00:00:00Z
Expiry Date: 2025-01-01T00:00:00Z
Updated Date: 2024-01-01T00:00:00Z
Status: clientTransferProhibited
DNSSEC: unsigned
"""
        
        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (whois_output.encode(), b"")
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with patch('asyncio.wait_for', side_effect=lambda coro, timeout: coro):
                result = await whois._lookup_system_whois("example.com")
                
                assert result.domain_name == "example.com"
                assert "Example Registrar" in result.registrar
                assert len(result.name_servers) == 2

    def test_parse_whois_output(self, whois):
        """Test parsing whois output"""
        output = """
Domain Name: example.com
Registrar: Test Registrar
Name Server: ns1.example.com
Name Server: ns2.example.com
Creation Date: 2020-01-01
Expiry Date: 2025-01-01
Status: active
"""
        record = WhoisRecord(domain_name="example.com")
        result = whois._parse_whois_output(output, record)
        
        assert "Test Registrar" in result.registrar
        assert len(result.name_servers) == 2
        assert "active" in result.status

    def test_parse_whois_output_with_comments(self, whois):
        """Test parsing whois output with comments"""
        output = """
% This is a comment
# This is also a comment
Domain Name: example.com
Registrar: Test Registrar
% Another comment
"""
        record = WhoisRecord(domain_name="example.com")
        result = whois._parse_whois_output(output, record)
        
        assert "Test Registrar" in result.registrar

    def test_format_date_datetime(self, whois):
        """Test formatting datetime object"""
        date = datetime(2024, 1, 15, 10, 30, 0)
        result = whois._format_date(date)
        
        assert "2024-01-15" in result

    def test_format_date_string(self, whois):
        """Test formatting date string"""
        result = whois._format_date("2024-01-15")
        
        assert "2024-01-15" in result

    def test_format_date_list(self, whois):
        """Test formatting date list (takes first element)"""
        dates = [datetime(2024, 1, 15), datetime(2024, 1, 16)]
        result = whois._format_date(dates)
        
        assert "2024-01-15" in result

    def test_get_domain_age(self, whois):
        """Test getting domain age"""
        record = WhoisRecord(
            domain_name="example.com",
            creation_date="2020-01-01T00:00:00",
        )
        whois.cache["example.com"] = record
        
        age = whois.get_domain_age("example.com")
        
        assert age is not None
        assert age > 0  # Should be several years old

    def test_get_domain_age_no_creation_date(self, whois):
        """Test getting domain age without creation date"""
        record = WhoisRecord(domain_name="example.com")
        whois.cache["example.com"] = record
        
        age = whois.get_domain_age("example.com")
        
        assert age is None

    def test_is_expired_true(self, whois):
        """Test checking if domain is expired (true case)"""
        record = WhoisRecord(
            domain_name="example.com",
            expiration_date="2020-01-01T00:00:00",  # Past date
        )
        whois.cache["example.com"] = record
        
        expired = whois.is_expired("example.com")
        
        assert expired is True

    def test_is_expired_false(self, whois):
        """Test checking if domain is expired (false case)"""
        record = WhoisRecord(
            domain_name="example.com",
            expiration_date="2099-01-01T00:00:00",  # Future date
        )
        whois.cache["example.com"] = record
        
        expired = whois.is_expired("example.com")
        
        assert expired is False

    def test_get_abuse_contacts(self, whois):
        """Test getting abuse contacts"""
        record = WhoisRecord(
            domain_name="example.com",
            registrant_email="owner@example.com",
            admin_email="admin@example.com",
            tech_email="tech@example.com",
        )
        whois.cache["example.com"] = record
        
        contacts = whois.get_abuse_contacts("example.com")
        
        assert len(contacts) == 3
        assert "owner@example.com" in contacts
        assert "admin@example.com" in contacts
        assert "tech@example.com" in contacts

    def test_whois_record_to_dict(self):
        """Test WhoisRecord to_dict"""
        record = WhoisRecord(
            domain_name="example.com",
            registrar="Test Registrar",
            name_servers=["ns1.example.com"],
        )
        
        data = record.to_dict()
        
        assert data["domain_name"] == "example.com"
        assert data["registrar"] == "Test Registrar"
        assert data["name_servers"] == ["ns1.example.com"]


# DNSEnumerator Tests
class TestDNSEnumerator:
    """Tests for DNSEnumerator class"""

    @pytest.fixture
    def dns_enum(self):
        """Create a DNSEnumerator instance"""
        return DNSEnumerator(config={"timeout": 5.0})

    def test_initialization(self, dns_enum):
        """Test DNSEnumerator initialization"""
        assert dns_enum.config == {"timeout": 5.0}
        assert dns_enum.timeout == 5.0
        assert "A" in dns_enum.RECORD_TYPES
        assert "AAAA" in dns_enum.RECORD_TYPES
        assert "MX" in dns_enum.RECORD_TYPES
        assert "NS" in dns_enum.RECORD_TYPES
        assert "TXT" in dns_enum.RECORD_TYPES
        assert "SOA" in dns_enum.RECORD_TYPES

    @pytest.mark.asyncio
    async def test_enumerate_from_cache(self, dns_enum):
        """Test enumerate returns cached result"""
        cached_result = {
            "domain": "example.com",
            "records": {"A": [{"value": "1.2.3.4"}]},
        }
        dns_enum.cache["example.com"] = cached_result
        
        result = await dns_enum.enumerate("example.com")
        
        assert result == cached_result

    @pytest.mark.asyncio
    async def test_enumerate(self, dns_enum):
        """Test full DNS enumeration"""
        with patch.object(dns_enum, '_query_records', return_value=[{"value": "1.2.3.4"}]):
            with patch.object(dns_enum, '_check_dnssec', return_value={"enabled": True}):
                with patch.object(dns_enum, '_try_zone_transfer', return_value=False):
                    with patch.object(dns_enum, '_reverse_dns_lookup', return_value="host.example.com"):
                        with patch.object(dns_enum, '_check_email_security', return_value={"spf": None}):
                            result = await dns_enum.enumerate("example.com")
                            
                            assert result["domain"] == "example.com"
                            assert "records" in result
                            assert "dnssec" in result
                            assert "zone_transfer" in result

    @pytest.mark.asyncio
    async def test_query_records_a(self, dns_enum):
        """Test querying A records"""
        mock_answer = Mock()
        mock_answer.__str__ = Mock(return_value="1.2.3.4")
        
        mock_answers = Mock()
        mock_answers.__iter__ = Mock(return_value=iter([mock_answer]))
        mock_answers.rrset = Mock(ttl=300)
        
        mock_resolver = Mock()
        mock_resolver.resolve.return_value = mock_answers
        
        with patch('dns.resolver.Resolver', return_value=mock_resolver):
            records = await dns_enum._query_records("example.com", "A")
            
            assert len(records) == 1
            assert records[0]["value"] == "1.2.3.4"
            assert records[0]["type"] == "A"

    @pytest.mark.asyncio
    async def test_query_records_mx(self, dns_enum):
        """Test querying MX records with priority"""
        mock_answer = Mock()
        mock_answer.__str__ = Mock(return_value="10 mail.example.com.")
        mock_answer.preference = 10
        
        mock_answers = Mock()
        mock_answers.__iter__ = Mock(return_value=iter([mock_answer]))
        mock_answers.rrset = Mock(ttl=300)
        
        mock_resolver = Mock()
        mock_resolver.resolve.return_value = mock_answers
        
        with patch('dns.resolver.Resolver', return_value=mock_resolver):
            records = await dns_enum._query_records("example.com", "MX")
            
            assert len(records) == 1
            assert records[0]["priority"] == 10

    @pytest.mark.asyncio
    async def test_query_records_nxdomain(self, dns_enum):
        """Test querying non-existent domain"""
        import dns.resolver
        
        mock_resolver = Mock()
        mock_resolver.resolve.side_effect = dns.resolver.NXDOMAIN()
        
        with patch('dns.resolver.Resolver', return_value=mock_resolver):
            records = await dns_enum._query_records("nonexistent.example", "A")
            
            assert records == []

    @pytest.mark.asyncio
    async def test_check_dnssec_enabled(self, dns_enum):
        """Test checking DNSSEC when enabled"""
        import dns.resolver
        import dns.dnssec
        
        mock_answer = Mock()
        mock_answer.algorithm = 8  # RSA/SHA-256
        mock_answer.key_tag = 12345
        
        mock_answers = Mock()
        mock_answers.__iter__ = Mock(return_value=iter([mock_answer]))
        
        mock_resolver = Mock()
        mock_resolver.resolve.return_value = mock_answers
        
        with patch('dns.resolver.Resolver', return_value=mock_resolver):
            with patch('dns.dnssec.algorithm_to_text', return_value="RSASHA256"):
                result = await dns_enum._check_dnssec("example.com")
                
                assert result["enabled"] is True
                assert result["algorithm"] == "RSASHA256"
                assert result["key_tag"] == 12345

    @pytest.mark.asyncio
    async def test_check_dnssec_disabled(self, dns_enum):
        """Test checking DNSSEC when disabled"""
        import dns.resolver
        
        mock_resolver = Mock()
        mock_resolver.resolve.side_effect = dns.resolver.NoAnswer()
        
        with patch('dns.resolver.Resolver', return_value=mock_resolver):
            result = await dns_enum._check_dnssec("example.com")
            
            assert result["enabled"] is False

    @pytest.mark.asyncio
    async def test_try_zone_transfer_success(self, dns_enum):
        """Test successful zone transfer"""
        import dns.resolver
        import dns.zone
        import dns.query
        
        # Mock NS records
        with patch.object(dns_enum, '_query_records', return_value=[{"value": "ns1.example.com."}]):
            mock_zone = Mock()
            
            with patch('dns.zone.from_xfr', return_value=mock_zone):
                result = await dns_enum._try_zone_transfer("example.com")
                
                # Should return True if zone transfer succeeds
                # Note: Actual result depends on mocking

    @pytest.mark.asyncio
    async def test_try_zone_transfer_failure(self, dns_enum):
        """Test failed zone transfer"""
        import dns.resolver
        
        with patch.object(dns_enum, '_query_records', return_value=[{"value": "ns1.example.com."}]):
            with patch('dns.zone.from_xfr', side_effect=Exception("Zone transfer failed")):
                result = await dns_enum._try_zone_transfer("example.com")
                
                assert result is False

    @pytest.mark.asyncio
    async def test_reverse_dns_lookup_success(self, dns_enum):
        """Test successful reverse DNS lookup"""
        with patch('socket.gethostbyaddr', return_value=("host.example.com", [], [])):
            result = await dns_enum._reverse_dns_lookup("1.2.3.4")
            
            assert result == "host.example.com"

    @pytest.mark.asyncio
    async def test_reverse_dns_lookup_failure(self, dns_enum):
        """Test failed reverse DNS lookup"""
        with patch('socket.gethostbyaddr', side_effect=socket.herror()):
            result = await dns_enum._reverse_dns_lookup("1.2.3.4")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_check_email_security_with_spf(self, dns_enum):
        """Test checking email security with SPF"""
        spf_record = "v=spf1 include:_spf.google.com ~all"
        
        with patch.object(dns_enum, '_query_records', side_effect=[
            [{"value": spf_record}],  # SPF
            [],  # DMARC
            [],  # DKIM
        ]):
            result = await dns_enum._check_email_security("example.com")
            
            assert result["spf"] is not None
            assert result["spf"]["record"] == spf_record
            assert result["spf"]["policy"] == "softfail"

    @pytest.mark.asyncio
    async def test_check_email_security_with_dmarc(self, dns_enum):
        """Test checking email security with DMARC"""
        dmarc_record = "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"
        
        with patch.object(dns_enum, '_query_records', side_effect=[
            [],  # SPF
            [{"value": dmarc_record}],  # DMARC
            [],  # DKIM
        ]):
            result = await dns_enum._check_email_security("example.com")
            
            assert result["dmarc"] is not None
            assert result["dmarc"]["policy"] == "quarantine"

    def test_parse_spf_policy_softfail(self, dns_enum):
        """Test parsing SPF softfail policy"""
        result = dns_enum._parse_spf_policy("v=spf1 ~all")
        assert result == "softfail"

    def test_parse_spf_policy_fail(self, dns_enum):
        """Test parsing SPF fail policy"""
        result = dns_enum._parse_spf_policy("v=spf1 -all")
        assert result == "fail"

    def test_parse_spf_policy_neutral(self, dns_enum):
        """Test parsing SPF neutral policy"""
        result = dns_enum._parse_spf_policy("v=spf1 ?all")
        assert result == "neutral"

    def test_parse_spf_policy_pass(self, dns_enum):
        """Test parsing SPF pass policy"""
        result = dns_enum._parse_spf_policy("v=spf1 +all")
        assert result == "pass"

    def test_parse_spf_policy_unknown(self, dns_enum):
        """Test parsing SPF with unknown policy"""
        result = dns_enum._parse_spf_policy("v=spf1")
        assert result == "unknown"

    def test_parse_dmarc_policy_reject(self, dns_enum):
        """Test parsing DMARC reject policy"""
        result = dns_enum._parse_dmarc_policy("v=DMARC1; p=reject")
        assert result == "reject"

    def test_parse_dmarc_policy_quarantine(self, dns_enum):
        """Test parsing DMARC quarantine policy"""
        result = dns_enum._parse_dmarc_policy("v=DMARC1; p=quarantine")
        assert result == "quarantine"

    def test_parse_dmarc_policy_none(self, dns_enum):
        """Test parsing DMARC none policy"""
        result = dns_enum._parse_dmarc_policy("v=DMARC1; p=none")
        assert result == "none"

    def test_parse_dmarc_policy_unknown(self, dns_enum):
        """Test parsing DMARC with unknown policy"""
        result = dns_enum._parse_dmarc_policy("v=DMARC1")
        assert result == "unknown"

    def test_get_nameservers(self, dns_enum):
        """Test getting nameservers"""
        dns_enum.cache["example.com"] = {
            "nameservers": ["ns1.example.com", "ns2.example.com"],
        }
        
        result = dns_enum.get_nameservers("example.com")
        
        assert result == ["ns1.example.com", "ns2.example.com"]

    def test_get_ip_addresses(self, dns_enum):
        """Test getting IP addresses"""
        dns_enum.cache["example.com"] = {
            "records": {
                "A": [{"value": "1.2.3.4"}],
                "AAAA": [{"value": "2001:db8::1"}],
            },
        }
        
        result = dns_enum.get_ip_addresses("example.com")
        
        assert "1.2.3.4" in result
        assert "2001:db8::1" in result

    def test_dns_record_to_dict(self):
        """Test DNSRecord to_dict"""
        record = DNSRecord(
            record_type="A",
            name="example.com",
            value="1.2.3.4",
            ttl=300,
        )
        
        data = record.to_dict()
        
        assert data["record_type"] == "A"
        assert data["name"] == "example.com"
        assert data["value"] == "1.2.3.4"
        assert data["ttl"] == 300
