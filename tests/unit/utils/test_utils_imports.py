"""Test utils imports"""

import pytest


class TestUtilsImports:
    """Test utils can be imported"""

    def test_hash_utils_import(self):
        from utils.helpers import load_config

        assert load_config is not None

    def test_file_utils_import(self):
        from utils.security import mask_secret

        assert mask_secret is not None
