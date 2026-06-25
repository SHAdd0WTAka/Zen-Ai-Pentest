"""Smoke tests for core/false_positive_filter.py"""

import pytest

from core.false_positive_filter import FalsePositiveFilter, LLMVote, ValidationResult, VoteVerdict, validate_finding


class TestVoteVerdict:
    def test_values(self):
        assert VoteVerdict.VALID == "valid"
        assert VoteVerdict.FALSE_POSITIVE == "false_positive"
        assert VoteVerdict.UNCERTAIN == "uncertain"


class TestLLMVote:
    def test_creation(self):
        vote = LLMVote(
            provider="openai",
            verdict=VoteVerdict.VALID,
            confidence=0.85,
            reasoning="Looks like a real vulnerability",
        )
        assert vote.provider == "openai"
        assert vote.verdict == VoteVerdict.VALID
        assert vote.confidence == 0.85


class TestValidationResult:
    def test_creation(self):
        result = ValidationResult(
            is_valid=True,
            confidence=0.85,
            votes=[],
            consensus="valid (1/1 votes)",
            recommended_action="accept",
        )
        assert result.is_valid is True
        assert result.confidence == 0.85
        assert result.recommended_action == "accept"


class TestFalsePositiveFilter:
    def test_init_defaults(self):
        fpf = FalsePositiveFilter()
        assert fpf.providers == ["openai", "anthropic", "openrouter"]
        assert fpf.confidence_threshold == 0.7
        assert fpf.min_votes_required == 2

    def test_init_custom(self):
        fpf = FalsePositiveFilter(providers=["openai"], min_votes_required=1)
        assert fpf.providers == ["openai"]
        assert fpf.min_votes_required == 1

    def test_build_validation_prompt(self):
        fpf = FalsePositiveFilter()
        finding = {
            "title": "SQL Injection",
            "severity": "high",
            "description": "SQLi in login form",
            "tool": "sqlmap",
            "target": "http://example.com",
        }
        prompt = fpf._build_validation_prompt(finding)
        assert "SQL Injection" in prompt
        assert "high" in prompt

    def test_determine_consensus_no_votes(self):
        fpf = FalsePositiveFilter()
        assert fpf.determine_consensus([]) == "no_votes"

    def test_calculate_confidence_no_votes(self):
        fpf = FalsePositiveFilter()
        assert fpf.calculate_confidence([]) == 0.0
