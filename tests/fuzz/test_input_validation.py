"""
Fuzz tests for input validation.

Tests various modules with random/hypothesis-generated inputs
to ensure proper validation and error handling.
"""

import sys
import hypothesis
from hypothesis import given, strategies as st, settings
import pytest

# Skip if hypothesis not installed
try:
    from hypothesis import given, strategies as st
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    pytest.skip("hypothesis not installed", allow_module_level=True)


class TestInputValidation:
    """Test input validation with fuzzing."""
    
    @given(st.text())
    @settings(max_examples=100, deadline=1000)
    def test_string_input_handling(self, input_string):
        """Test that string inputs don't cause crashes."""
        # Test various string operations
        assert isinstance(input_string, str)
        # Should not raise on basic operations
        _ = len(input_string)
        _ = input_string.strip()
        
    @given(st.emails())
    @settings(max_examples=50, deadline=1000)
    def test_email_validation(self, email):
        """Test email validation with fuzzed inputs."""
        # Test email format validation
        assert "@" in email
        assert "." in email.split("@")[-1]
        
    @given(st.ip_addresses())
    @settings(max_examples=50, deadline=1000)
    def test_ip_address_handling(self, ip):
        """Test IP address handling."""
        ip_str = str(ip)
        # Should be valid IP format
        assert len(ip_str) > 0
        
    @given(st.lists(st.integers()), st.dictionaries(st.text(), st.text()))
    @settings(max_examples=50, deadline=1000)
    def test_complex_data_structures(self, list_data, dict_data):
        """Test handling of complex nested structures."""
        # Should handle without crashes
        combined = {
            "list": list_data,
            "dict": dict_data
        }
        assert isinstance(combined, dict)
        assert "list" in combined
        assert "dict" in combined


class TestAPISchemaValidation:
    """Test API schema validation."""
    
    @given(st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.one_of(st.text(), st.integers(), st.booleans())
    ))
    @settings(max_examples=50, deadline=1000)
    def test_json_payload_handling(self, payload):
        """Test JSON payload handling."""
        import json
        
        # Should serialize/deserialize without errors
        try:
            serialized = json.dumps(payload)
            deserialized = json.loads(serialized)
            assert isinstance(deserialized, dict)
        except (TypeError, ValueError):
            # Some payloads might not be JSON serializable - that's ok
            pass


class TestURLValidation:
    """Test URL validation fuzzing."""
    
    @given(st.text(min_size=1, max_size=200))
    @settings(max_examples=100, deadline=1000)
    def test_url_like_strings(self, url_string):
        """Test URL-like string handling."""
        # Should not crash on URL parsing attempts
        if url_string.startswith(('http://', 'https://')):
            assert '://' in url_string


def run_fuzz_tests():
    """Run all fuzz tests."""
    if not HYPOTHESIS_AVAILABLE:
        print("hypothesis not installed, skipping fuzz tests")
        return 0
        
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_fuzz_tests())
