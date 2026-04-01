"""Cache sharded lock tests"""

import pytest


class TestShardedLock:
    """Test sharded lock"""

    def test_sharded_lock_import(self):
        from core.cache import ShardedLock

        assert ShardedLock is not None

    def test_sharded_lock_has_acquire(self):
        from core.cache import ShardedLock

        assert hasattr(ShardedLock, "acquire_all")

    def test_sharded_lock_has_release(self):
        from core.cache import ShardedLock

        assert hasattr(ShardedLock, "release_all")
