"""
Comprehensive Tests for Wordlist Generator Module

This module tests the WordlistGenerator class which provides
targeted wordlist generation for penetration testing.

Target Coverage: 70%+
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from modules.wordlist_generator import (
    WordlistConfig,
    WordlistGenerator,
    generate_company_wordlist,
    generate_password_mutations,
    generate_target_wordlist,
)


class TestWordlistConfig:
    """Test WordlistConfig dataclass"""

    def test_default_config(self):
        """Test default configuration"""
        config = WordlistConfig()
        assert config.min_length == 4
        assert config.max_length == 20
        assert config.include_numbers is True
        assert config.include_special is False
        assert config.include_years is True
        assert config.years_range == [2020, 2021, 2022, 2023, 2024, 2025]
        assert config.mutations is True
        assert config.mutation_level == "medium"

    def test_custom_config(self):
        """Test custom configuration"""
        config = WordlistConfig(
            min_length=8,
            max_length=30,
            include_numbers=False,
            include_special=True,
            include_years=False,
            years_range=[2020],
            mutations=False,
            mutation_level="high",
        )
        assert config.min_length == 8
        assert config.max_length == 30
        assert config.include_numbers is False
        assert config.include_special is True
        assert config.include_years is False


class TestWordlistGeneratorInit:
    """Test WordlistGenerator initialization"""

    def test_default_init(self):
        """Test default initialization"""
        gen = WordlistGenerator()
        assert isinstance(gen.config, WordlistConfig)
        assert gen.generated_words == set()

    def test_custom_config_init(self):
        """Test initialization with custom config"""
        config = WordlistConfig(min_length=6, max_length=15)
        gen = WordlistGenerator(config=config)
        assert gen.config.min_length == 6
        assert gen.config.max_length == 15


class TestCompanyWordlist:
    """Test company wordlist generation"""

    @pytest.fixture
    def generator(self):
        return WordlistGenerator()

    def test_basic_company_wordlist(self, generator):
        """Test basic company wordlist generation"""
        words = generator.generate_company_wordlist("Acme Corp")
        assert len(words) > 0
        # Should include base variations
        assert any("acme" in w.lower() for w in words)
        assert any("corp" in w.lower() for w in words)

    def test_company_with_industry(self, generator):
        """Test company wordlist with industry"""
        words = generator.generate_company_wordlist("TechCorp", industry="tech")
        # Should include tech-related terms
        assert any("tech" in w.lower() for w in words)

    def test_company_with_locations(self, generator):
        """Test company wordlist with locations"""
        words = generator.generate_company_wordlist("GlobalCorp", locations=["NY", "London"])
        # Check for NY (may be upper or mixed case)
        assert any("ny" in w.lower() for w in words)
        assert any("london" in w.lower() for w in words)

    def test_company_with_extras(self, generator):
        """Test company wordlist with extra keywords"""
        words = generator.generate_company_wordlist("TestCorp", extras=["secret", "admin"])
        assert "secret" in words
        assert "admin" in words

    def test_company_wordlist_with_numbers(self, generator):
        """Test that numbers are added to company wordlist"""
        words = generator.generate_company_wordlist("Acme")
        # Should have number suffixes
        assert any(w.startswith("acme") and any(c.isdigit() for c in w) for w in words)

    def test_company_wordlist_length_filtering(self, generator):
        """Test that words are filtered by length"""
        config = WordlistConfig(min_length=8, max_length=12)
        gen = WordlistGenerator(config=config)
        words = gen.generate_company_wordlist("Acme")

        # All words should be within length bounds
        for word in words:
            assert len(word) >= 8
            assert len(word) <= 12

    def test_company_wordlist_industries(self, generator):
        """Test different industries"""
        industries = ["tech", "finance", "healthcare", "education", "retail"]

        for industry in industries:
            words = generator.generate_company_wordlist("TestCorp", industry=industry)
            assert len(words) > 0

    def test_company_wordlist_permutations(self, generator):
        """Test that permutations are generated"""
        words = generator.generate_company_wordlist("TestCorp")

        # Should have case variations
        case_variations = [w for w in words if "testcorp" in w.lower()]
        assert len(case_variations) > 1


class TestTargetedWordlist:
    """Test targeted wordlist generation"""

    @pytest.fixture
    def generator(self):
        return WordlistGenerator()

    def test_targeted_with_names(self, generator):
        """Test targeted wordlist with first and last name"""
        info = {
            "first_name": "John",
            "last_name": "Doe",
        }
        words = generator.generate_targeted_wordlist(info)

        assert "John" in words
        assert "john" in words
        assert "Doe" in words
        assert "doe" in words
        assert "JohnDoe" in words or "johndoe" in words

    def test_targeted_with_birthdate(self, generator):
        """Test targeted wordlist with birthdate"""
        info = {
            "first_name": "John",
            "birthdate": "1990-05-15",
        }
        words = generator.generate_targeted_wordlist(info)

        # Should include date parts
        assert "19900515" in words or any("1990" in w for w in words)
        assert "90" in words or any(w.endswith("90") for w in words)

    def test_targeted_with_pet_names(self, generator):
        """Test targeted wordlist with pet names"""
        info = {
            "first_name": "John",
            "pet_names": ["Fluffy", "Buddy"],
        }
        words = generator.generate_targeted_wordlist(info)

        assert "Fluffy" in words
        assert "Buddy" in words

    def test_targeted_with_hobbies(self, generator):
        """Test targeted wordlist with hobbies"""
        info = {
            "first_name": "John",
            "hobbies": ["football", "gaming"],
        }
        words = generator.generate_targeted_wordlist(info)

        assert "football" in words
        assert "gaming" in words

    def test_targeted_name_combinations(self, generator):
        """Test various name combinations"""
        info = {
            "first_name": "John",
            "last_name": "Doe",
        }
        words = generator.generate_targeted_wordlist(info)

        # Check for name combinations
        combinations = [
            "JohnDoe", "John.Doe", "John_Doe",
            "JDoe", "JohnD", "DoeJohn",
        ]
        for combo in combinations:
            assert combo in words or combo.lower() in words or combo.upper() in words


class TestPatternWordlist:
    """Test pattern-based wordlist generation"""

    @pytest.fixture
    def generator(self):
        return WordlistGenerator()

    def test_simple_pattern(self, generator):
        """Test simple pattern generation"""
        pattern = "{word}{number}"
        values = {
            "word": ["Pass", "Secret"],
            "number": ["1", "2"],
        }
        words = generator.generate_pattern_wordlist(pattern, values)

        assert "Pass1" in words
        assert "Pass2" in words
        assert "Secret1" in words
        assert "Secret2" in words

    def test_complex_pattern(self, generator):
        """Test complex pattern with multiple placeholders"""
        pattern = "{word}{number}{special}"
        values = {
            "word": ["Pass"],
            "number": ["1", "2"],
            "special": ["!", "@"],
        }
        words = generator.generate_pattern_wordlist(pattern, values)

        assert "Pass1!" in words
        assert "Pass1@" in words
        assert "Pass2!" in words
        assert "Pass2@" in words

    def test_pattern_with_missing_placeholder(self, generator):
        """Test pattern with missing placeholder values"""
        pattern = "{word}{missing}"
        values = {
            "word": ["Pass"],
        }
        words = generator.generate_pattern_wordlist(pattern, values)

        # Missing placeholder should be kept as-is
        assert any("{missing}" in w for w in words)


class TestPasswordMutation:
    """Test password mutation"""

    @pytest.fixture
    def generator(self):
        return WordlistGenerator()

    def test_basic_mutation(self, generator):
        """Test basic password mutation"""
        mutations = generator.mutate_password("password")

        assert "password" in mutations
        assert "PASSWORD" in mutations
        assert "Password" in mutations

    def test_leet_speak(self, generator):
        """Test leet speak transformations"""
        mutations = generator.mutate_password("password")

        # Check leet variants
        assert any("p@ssword" in m for m in mutations)
        assert any("p4ssword" in m for m in mutations)
        assert any("passw0rd" in m for m in mutations)

    def test_reversal(self, generator):
        """Test password reversal"""
        mutations = generator.mutate_password("abc123")

        assert "321cba" in mutations

    def test_duplication(self, generator):
        """Test password duplication"""
        mutations = generator.mutate_password("pass")

        assert "passpass" in mutations
        assert "passpasspass" in mutations

    def test_common_substitutions(self, generator):
        """Test common character substitutions"""
        mutations = generator.mutate_password("password")

        assert any("p@ssword" in m for m in mutations)
        assert any("p4ssword" in m for m in mutations)
        assert any("passw0rd" in m for m in mutations)

    def test_mutation_with_special_chars(self, generator):
        """Test mutation with special characters enabled"""
        config = WordlistConfig(include_special=True)
        gen = WordlistGenerator(config=config)
        mutations = gen.mutate_password("password")

        # Should have special character variants
        assert any("!" in m for m in mutations)

    def test_mutation_empty_password(self, generator):
        """Test mutation with empty password"""
        mutations = generator.mutate_password("")
        # Should handle gracefully
        assert "" in mutations


class TestCommonPasswords:
    """Test common password generation"""

    @pytest.fixture
    def generator(self):
        return WordlistGenerator()

    def test_common_passwords_generated(self, generator):
        """Test that common passwords are generated"""
        passwords = generator.generate_common_passwords(count=100)

        assert len(passwords) <= 100
        # Should include base passwords (may have mutations applied)
        assert any("password" in p.lower() for p in passwords)
        assert any("123456" in p for p in passwords)

    def test_common_passwords_with_mutations(self, generator):
        """Test that mutations are applied"""
        passwords = generator.generate_common_passwords(count=1000)

        # Should have mutated versions
        assert any("password" in p.lower() and any(c.isdigit() for c in p) for p in passwords)

    def test_common_passwords_count_limit(self, generator):
        """Test that count limit is respected"""
        passwords = generator.generate_common_passwords(count=50)

        assert len(passwords) <= 50


class TestSaveWordlist:
    """Test wordlist saving functionality"""

    @pytest.fixture
    def generator(self):
        return WordlistGenerator()

    def test_save_wordlist(self, generator):
        """Test saving wordlist to file"""
        words = ["password1", "password2", "password3"]
        filepath = "test_wordlist_temp.txt"

        try:
            result = generator.save_wordlist(words, filepath)

            assert os.path.exists(result)
            with open(result, "r") as f:
                content = f.read().strip().split("\n")
                assert content == words
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_save_wordlist_creates_dirs(self, generator):
        """Test that save_wordlist creates directories"""
        words = ["test"]
        import tempfile
        temp_dir = tempfile.mkdtemp()
        filepath = os.path.join(temp_dir, "subdir", "wordlist.txt")

        try:
            result = generator.save_wordlist(words, filepath)
            assert os.path.exists(result)
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_save_empty_wordlist(self, generator):
        """Test saving empty wordlist"""
        words = []
        filepath = "empty_wordlist_temp.txt"

        try:
            result = generator.save_wordlist(words, filepath)

            assert os.path.exists(result)
            with open(result, "r") as f:
                content = f.read().strip()
                assert content == ""
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)


class TestPrivateMethods:
    """Test private helper methods"""

    @pytest.fixture
    def generator(self):
        return WordlistGenerator()

    def test_extract_base_words(self, generator):
        """Test base word extraction"""
        words = generator._extract_base_words("Acme Corp")

        assert "Acme Corp" in words
        assert "acme corp" in words
        assert any("corp" in w.lower() for w in words)
        assert any("acme" in w.lower() for w in words)

    def test_extract_base_words_acronym(self, generator):
        """Test acronym extraction"""
        words = generator._extract_base_words("Acme Corporation")

        assert "AC" in words  # Acronym

    def test_get_industry_words(self, generator):
        """Test industry word retrieval"""
        tech_words = generator._get_industry_words("tech")
        assert "tech" in tech_words
        assert "software" in tech_words

        finance_words = generator._get_industry_words("finance")
        assert "finance" in finance_words
        assert "bank" in finance_words

        unknown_words = generator._get_industry_words("unknown")
        assert unknown_words == set()

    def test_generate_permutations(self, generator):
        """Test permutation generation"""
        perms = generator._generate_permutations("Test")

        assert "Test" in perms
        assert "test" in perms
        assert "TEST" in perms
        assert "tEST" in perms

    def test_generate_permutations_with_space(self, generator):
        """Test permutation generation with space"""
        perms = generator._generate_permutations("Hello World")

        assert "HelloWorld" in perms
        assert "helloworld" in perms

    def test_add_numbers(self, generator):
        """Test adding number suffixes"""
        results = generator._add_numbers("test")

        assert "test1" in results
        assert "test123" in results
        assert "1test" in results
        assert "123test" in results

    def test_add_special(self, generator):
        """Test adding special characters"""
        results = generator._add_special("test")

        assert "test!" in results
        assert "!test" in results
        assert "test!!" in results

    def test_mutate_word(self, generator):
        """Test word mutation"""
        mutations = generator._mutate_word("test")

        # Should have year suffixes
        assert any("test2024" in m for m in mutations)
        # Should have season suffixes
        assert any("testSummer" in m for m in mutations)
        # Should have month suffixes
        assert any("testJan" in m for m in mutations)

    def test_apply_leet_speak(self, generator):
        """Test leet speak application"""
        results = generator._apply_leet_speak("password")

        # Check various leet transformations
        assert any("p@ssword" in r for r in results)
        assert any("passw0rd" in r for r in results)
        assert any("p4ssword" in r for r in results)


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_generate_company_wordlist(self):
        """Test generate_company_wordlist convenience function"""
        words = generate_company_wordlist("TestCorp")
        assert len(words) > 0
        assert any("test" in w.lower() for w in words)

    def test_generate_password_mutations(self):
        """Test generate_password_mutations convenience function"""
        mutations = generate_password_mutations("password")
        assert len(mutations) > 0
        assert "password" in mutations
        assert "PASSWORD" in mutations

    def test_generate_target_wordlist(self):
        """Test generate_target_wordlist convenience function"""
        info = {"first_name": "John", "last_name": "Doe"}
        words = generate_target_wordlist(info)
        assert len(words) > 0
        assert "John" in words or "john" in words


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def generator(self):
        return WordlistGenerator()

    def test_empty_company_name(self, generator):
        """Test with empty company name"""
        words = generator.generate_company_wordlist("")
        # Should handle gracefully
        assert isinstance(words, list)

    def test_special_characters_in_company(self, generator):
        """Test with special characters in company name"""
        words = generator.generate_company_wordlist("Acme & Co.")
        # Should handle special characters
        assert len(words) > 0

    def test_very_long_company_name(self, generator):
        """Test with very long company name"""
        long_name = "A" * 100
        words = generator.generate_company_wordlist(long_name)
        # Should handle long names
        assert isinstance(words, list)

    def test_unicode_characters(self, generator):
        """Test with unicode characters"""
        words = generator.generate_company_wordlist("Müller & Söhne")
        # Should handle unicode
        assert len(words) > 0


class TestWordlistGeneratorIntegration:
    """Integration-style tests"""

    def test_full_company_wordlist_workflow(self):
        """Test complete company wordlist workflow"""
        gen = WordlistGenerator()

        words = gen.generate_company_wordlist(
            company_name="TechCorp",
            industry="tech",
            locations=["NY", "London"],
            extras=["secret", "admin"],
        )

        # Save and reload
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            filepath = f.name

        try:
            gen.save_wordlist(words, filepath)

            with open(filepath, "r") as f:
                loaded_words = f.read().strip().split("\n")

            assert len(loaded_words) == len(words)
        finally:
            os.unlink(filepath)

    def test_password_variations_consistency(self):
        """Test that password mutations are consistent"""
        gen = WordlistGenerator()

        mutations1 = gen.mutate_password("password")
        mutations2 = gen.mutate_password("password")

        assert mutations1 == mutations2

    def test_wordlist_uniqueness(self):
        """Test that generated wordlists have unique entries"""
        gen = WordlistGenerator()

        words = gen.generate_company_wordlist("TestCorp")
        assert len(words) == len(set(words))
