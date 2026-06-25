"""Smoke tests for scripts/coverage_achiever.py"""

import pytest


class TestCoverageAchieverImports:
    def test_import(self):
        from scripts.coverage_achiever import COVERAGE_PHASES, CoverageAchiever

        assert CoverageAchiever is not None
        assert len(COVERAGE_PHASES) == 4

    def test_initialization(self, tmp_path):
        from scripts.coverage_achiever import CoverageAchiever

        achiever = CoverageAchiever(repo_path=str(tmp_path))
        assert achiever.current_phase == 1
        assert achiever.current_coverage == 35
        assert achiever.state_file == tmp_path / ".coverage_state.json"

    def test_phases_defined(self):
        from scripts.coverage_achiever import COVERAGE_PHASES

        assert COVERAGE_PHASES[0]["phase"] == 1
        assert COVERAGE_PHASES[0]["name"] == "API Layer"
        assert COVERAGE_PHASES[-1]["phase"] == 4
        assert COVERAGE_PHASES[-1]["target"] == 80

    def test_save_and_load_state(self, tmp_path):
        from scripts.coverage_achiever import CoverageAchiever

        achiever = CoverageAchiever(repo_path=str(tmp_path))
        achiever.current_coverage = 55
        achiever.current_phase = 2
        achiever.save_state()

        assert achiever.state_file.exists()

        achiever2 = CoverageAchiever(repo_path=str(tmp_path))
        assert achiever2.current_coverage == 55
        assert achiever2.current_phase == 2
