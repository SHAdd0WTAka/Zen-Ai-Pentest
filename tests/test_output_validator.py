"""
Tests for Output Validator Module
Phase 8.2: Enhanced Safety - Output Validation
"""

import json
import tempfile
from pathlib import Path

import pytest

from core.output_validator import (
    OutputValidator,
    ValidatedToolOutput,
    validate_and_report,
    validate_tool_output,
)


class TestOutputValidatorInitialization:
    """Tests for OutputValidator initialization"""

    def test_default_initialization(self):
        """Test initialization with defaults"""
        validator = OutputValidator()

        assert len(validator.schemas) == 7  # Default schemas
        assert validator.strict_mode is False
        assert "nmap" in validator.schemas
        assert "sqlmap" in validator.schemas

    def test_custom_schema_dir(self):
        """Test initialization with custom schema directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a custom schema
            schema_file = Path(tmpdir) / "custom_tool.json"
            schema_file.write_text(
                json.dumps(
                    {
                        "type": "object",
                        "required": ["result"],
                        "properties": {"result": {"type": "string"}},
                    }
                )
            )

            validator = OutputValidator(schema_dir=tmpdir)

            assert "custom_tool" in validator.schemas
            assert validator.schemas["custom_tool"]["required"] == ["result"]

    def test_strict_mode(self):
        """Test initialization with strict mode"""
        validator = OutputValidator(strict_mode=True)

        assert validator.strict_mode is True


class TestOutputValidatorValidation:
    """Tests for validation functionality"""

    @pytest.fixture
    def validator(self):
        """Create an OutputValidator instance"""
        return OutputValidator()

    def test_validate_nmap_valid(self, validator):
        """Test validating valid nmap output"""
        output = {
            "target": "example.com",
            "ports": [
                {"port": 80, "state": "open", "service": "http"},
                {"port": 443, "state": "open", "service": "https"},
            ],
            "scan_time": 10.5,
        }

        result = validator.validate("nmap", output)

        assert result is True

    def test_validate_nmap_invalid(self, validator):
        """Test validating invalid nmap output"""
        output = {
            "target": "example.com",
            # Missing required "ports" field
        }

        result = validator.validate("nmap", output)

        assert result is False

    def test_validate_nmap_invalid_port(self, validator):
        """Test validating nmap output with invalid port number"""
        output = {
            "target": "example.com",
            "ports": [
                {"port": 99999, "state": "open"},  # Invalid port number
            ],
        }

        result = validator.validate("nmap", output)

        assert result is False

    def test_validate_sqlmap_valid(self, validator):
        """Test validating valid sqlmap output"""
        output = {
            "target": "http://example.com/search",
            "vulnerable": True,
            "injection_points": [
                {
                    "parameter": "q",
                    "type": "boolean-based",
                    "title": "MySQL OR",
                },
            ],
            "dbms": "MySQL",
        }

        result = validator.validate("sqlmap", output)

        assert result is True

    def test_validate_sqlmap_invalid(self, validator):
        """Test validating invalid sqlmap output"""
        output = {
            "target": "http://example.com/search",
            # Missing required "vulnerable" field
        }

        result = validator.validate("sqlmap", output)

        assert result is False

    def test_validate_nuclei_valid(self, validator):
        """Test validating valid nuclei output"""
        output = {
            "template": "cve-2023-1234.yaml",
            "template_id": "CVE-2023-1234",
            "host": "example.com",
            "severity": "high",
            "info": {
                "name": "Test Vulnerability",
                "author": "test",
            },
        }

        result = validator.validate("nuclei", output)

        assert result is True

    def test_validate_nuclei_invalid_severity(self, validator):
        """Test validating nuclei output with invalid severity"""
        output = {
            "template": "test.yaml",
            "host": "example.com",
            "severity": "invalid_severity",  # Not in enum
        }

        result = validator.validate("nuclei", output)

        assert result is False

    def test_validate_json_string(self, validator):
        """Test validating JSON string input"""
        output = '{"target": "example.com", "ports": []}'

        result = validator.validate("nmap", output)

        assert result is True

    def test_validate_invalid_json_string(self, validator):
        """Test validating invalid JSON string"""
        output = "{invalid json}"

        result = validator.validate("nmap", output)

        assert result is False

    def test_validate_no_schema(self, validator):
        """Test validating tool with no schema defined"""
        output = {"any": "data"}

        result = validator.validate("unknown_tool", output)

        # Should pass when no schema exists
        assert result is True

    def test_validate_list_output(self, validator):
        """Test validating list output"""
        output = [{"host": "sub1.example.com"}, {"host": "sub2.example.com"}]

        result = validator.validate("subfinder", output[0])  # Validate single item

        assert result is True


class TestOutputValidatorWithErrors:
    """Tests for validation with error details"""

    @pytest.fixture
    def validator(self):
        """Create an OutputValidator instance"""
        return OutputValidator()

    def test_validate_with_errors_valid(self, validator):
        """Test validate_with_errors with valid output"""
        output = {
            "target": "example.com",
            "ports": [{"port": 80, "state": "open"}],
        }

        is_valid, errors = validator.validate_with_errors("nmap", output)

        assert is_valid is True
        assert errors == []

    def test_validate_with_errors_invalid(self, validator):
        """Test validate_with_errors with invalid output"""
        output = {
            "target": "example.com",
            # Missing required fields
        }

        is_valid, errors = validator.validate_with_errors("nmap", output)

        assert is_valid is False
        assert len(errors) > 0

    def test_validate_with_errors_invalid_json(self, validator):
        """Test validate_with_errors with invalid JSON"""
        output = "{not valid json}"

        is_valid, errors = validator.validate_with_errors("nmap", output)

        assert is_valid is False
        assert any("Invalid JSON" in e for e in errors)


class TestOutputValidatorSanitization:
    """Tests for output sanitization"""

    @pytest.fixture
    def validator(self):
        """Create an OutputValidator instance"""
        return OutputValidator()

    def test_sanitize_output(self, validator):
        """Test sanitizing output to schema fields"""
        output = {
            "target": "example.com",
            "ports": [],
            "unknown_field": "should be removed",
            "another_unknown": 123,
        }

        sanitized = validator.sanitize_output("nmap", output)

        assert "target" in sanitized
        assert "ports" in sanitized
        assert "unknown_field" not in sanitized
        assert "another_unknown" not in sanitized

    def test_sanitize_no_schema(self, validator):
        """Test sanitizing when no schema exists"""
        output = {"any": "data", "extra": "field"}

        sanitized = validator.sanitize_output("unknown_tool", output)

        # Should return unchanged when no schema
        assert sanitized == output


class TestOutputValidatorSchemaManagement:
    """Tests for schema management"""

    @pytest.fixture
    def validator(self):
        """Create an OutputValidator instance"""
        return OutputValidator()

    def test_add_schema(self, validator):
        """Test adding a new schema"""
        new_schema = {
            "type": "object",
            "required": ["test_field"],
            "properties": {
                "test_field": {"type": "string"},
            },
        }

        validator.add_schema("test_tool", new_schema)

        assert "test_tool" in validator.schemas
        assert validator.schemas["test_tool"] == new_schema

    def test_remove_schema(self, validator):
        """Test removing a schema"""
        result = validator.remove_schema("nmap")

        assert result is True
        assert "nmap" not in validator.schemas

    def test_remove_nonexistent_schema(self, validator):
        """Test removing a schema that doesn't exist"""
        result = validator.remove_schema("nonexistent")

        assert result is False

    def test_list_schemas(self, validator):
        """Test listing all schemas"""
        schemas = validator.list_schemas()

        assert isinstance(schemas, list)
        assert "nmap" in schemas
        assert "sqlmap" in schemas
        assert "nuclei" in schemas

    def test_get_schema(self, validator):
        """Test getting a specific schema"""
        schema = validator.get_schema("nmap")

        assert schema is not None
        assert schema["type"] == "object"
        assert "properties" in schema

    def test_get_nonexistent_schema(self, validator):
        """Test getting a schema that doesn't exist"""
        schema = validator.get_schema("nonexistent")

        assert schema is None


class TestValidatedToolOutput:
    """Tests for ValidatedToolOutput wrapper"""

    @pytest.fixture
    def validator(self):
        """Create an OutputValidator instance"""
        return OutputValidator()

    def test_validated_output_valid(self, validator):
        """Test wrapper with valid output"""
        output = {
            "target": "example.com",
            "ports": [{"port": 80, "state": "open"}],
        }

        wrapped = ValidatedToolOutput("nmap", output, validator)

        assert wrapped.is_valid is True
        assert wrapped.errors == []
        assert wrapped.tool_name == "nmap"
        assert wrapped.raw_output == output

    def test_validated_output_invalid(self, validator):
        """Test wrapper with invalid output"""
        output = {
            "target": "example.com",
            # Missing required fields
        }

        wrapped = ValidatedToolOutput("nmap", output, validator)

        assert wrapped.is_valid is False
        assert len(wrapped.errors) > 0

    def test_get_sanitized(self, validator):
        """Test getting sanitized output"""
        output = {
            "target": "example.com",
            "ports": [],
            "extra_field": "should be removed",
        }

        wrapped = ValidatedToolOutput("nmap", output, validator)
        sanitized = wrapped.get_sanitized()

        assert "target" in sanitized
        assert "ports" in sanitized
        assert "extra_field" not in sanitized


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    def test_validate_tool_output(self):
        """Test validate_tool_output convenience function"""
        output = {
            "target": "example.com",
            "ports": [{"port": 80, "state": "open"}],
        }

        result = validate_tool_output("nmap", output)

        assert result is True

    def test_validate_and_report_valid(self):
        """Test validate_and_report with valid output"""
        output = {
            "target": "example.com",
            "ports": [{"port": 80, "state": "open"}],
        }

        is_valid, errors = validate_and_report("nmap", output)

        assert is_valid is True
        assert errors == []

    def test_validate_and_report_invalid(self):
        """Test validate_and_report with invalid output"""
        output = {
            "target": "example.com",
            # Missing required fields
        }

        is_valid, errors = validate_and_report("nmap", output)

        assert is_valid is False
        assert len(errors) > 0


class TestBasicValidationFallback:
    """Tests for basic validation when jsonschema is not available"""

    def test_basic_validate_object_type(self):
        """Test basic validation with type checking"""
        validator = OutputValidator()

        # Override to simulate no jsonschema
        result = validator._basic_validate("nmap", {"target": "example.com"})
        assert result is True

    def test_basic_validate_wrong_type(self):
        """Test basic validation with wrong type"""
        validator = OutputValidator()

        result = validator._basic_validate("nmap", ["not", "an", "object"])
        assert result is False

    def test_basic_validate_missing_required(self):
        """Test basic validation with missing required fields"""
        validator = OutputValidator()

        result = validator._basic_validate("nmap", {})  # Missing "target" and "ports"
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
