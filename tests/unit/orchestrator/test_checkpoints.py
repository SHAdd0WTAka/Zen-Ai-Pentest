import json
import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orchestrator.checkpoints import Checkpoint, CheckpointManager
from orchestrator.state import StateManager


@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def state_manager():
    return MagicMock(spec=StateManager)


@pytest.fixture
def mgr(state_manager, db_path):
    return CheckpointManager(state_manager=state_manager, db_path=db_path)


class TestCheckpointManager:
    def test_init_creates_db(self, mgr, db_path):
        assert os.path.exists(db_path)
        assert mgr._db_path is not None

    def test_save_checkpoint(self, mgr):
        cp = mgr.save_checkpoint(
            workflow_id="wf-1",
            state_dict={"task": "scan", "status": "running"},
            metadata={"phase": "recon"},
        )
        assert isinstance(cp, Checkpoint)
        assert cp.workflow_id == "wf-1"
        assert cp.state == {"task": "scan", "status": "running"}
        assert cp.metadata == {"phase": "recon"}
        assert cp.checkpoint_id is not None
        assert cp.checksum is not None

    def test_save_checkpoint_with_parent(self, mgr):
        cp1 = mgr.save_checkpoint("wf-1", {"step": 1})
        cp2 = mgr.save_checkpoint("wf-1", {"step": 2}, parent_id=cp1.checkpoint_id)
        assert cp2.parent_id == cp1.checkpoint_id

    def test_load_checkpoint_returns_latest(self, mgr):
        mgr.save_checkpoint("wf-1", {"step": 1}, metadata={"ts": "first"})
        mgr.save_checkpoint("wf-1", {"step": 2}, metadata={"ts": "second"})
        loaded = mgr.load_checkpoint("wf-1")
        assert loaded is not None
        assert loaded.state == {"step": 2}

    def test_load_checkpoint_nonexistent(self, mgr):
        loaded = mgr.load_checkpoint("nonexistent")
        assert loaded is None

    def test_list_checkpoints(self, mgr):
        mgr.save_checkpoint("wf-1", {"step": 1})
        mgr.save_checkpoint("wf-1", {"step": 2})
        mgr.save_checkpoint("wf-2", {"step": 1})
        lst = mgr.list_checkpoints("wf-1")
        assert len(lst) == 2

    def test_list_checkpoints_empty(self, mgr):
        lst = mgr.list_checkpoints("wf-1")
        assert lst == []

    def test_delete_workflow_checkpoints(self, mgr):
        mgr.save_checkpoint("wf-1", {"step": 1})
        mgr.save_checkpoint("wf-1", {"step": 2})
        mgr.save_checkpoint("wf-2", {"step": 1})
        deleted = mgr.delete_workflow_checkpoints("wf-1")
        assert deleted == 2
        assert mgr.count_checkpoints("wf-2") == 1
        assert mgr.count_checkpoints("wf-1") == 0

    def test_delete_workflow_checkpoints_nonexistent(self, mgr):
        deleted = mgr.delete_workflow_checkpoints("nonexistent")
        assert deleted == 0

    def test_checkpoint_exists(self, mgr):
        mgr.save_checkpoint("wf-1", {"step": 1})
        assert mgr.has_checkpoint("wf-1") is True
        assert mgr.has_checkpoint("nope") is False

    def test_verify_checkpoint_valid(self, mgr):
        cp = mgr.save_checkpoint("wf-1", {"step": 1})
        assert mgr.verify_checkpoint(cp.checkpoint_id) is True

    def test_verify_checkpoint_invalid_id(self, mgr):
        assert mgr.verify_checkpoint("not-a-real-id") is False

    def test_corrupted_checkpoint_detected(self, mgr):
        cp = mgr.save_checkpoint("wf-1", {"step": 1})
        with mgr._lock:
            conn = mgr._get_connection()
            conn.execute(
                "UPDATE checkpoints SET state_json = ? WHERE id = ?",
                (json.dumps({"step": 999}), cp.checkpoint_id),
            )
            conn.commit()
        with pytest.raises(ValueError, match="Checksum mismatch"):
            mgr.load_checkpoint("wf-1")

    def test_corrupted_checkpoint_verify_returns_false(self, mgr):
        cp = mgr.save_checkpoint("wf-1", {"step": 1})
        with mgr._lock:
            conn = mgr._get_connection()
            conn.execute(
                "UPDATE checkpoints SET checksum = ? WHERE id = ?",
                ("deadbeef", cp.checkpoint_id),
            )
            conn.commit()
        assert mgr.verify_checkpoint(cp.checkpoint_id) is False

    def test_load_checkpoint_by_id(self, mgr):
        cp = mgr.save_checkpoint("wf-1", {"step": 1})
        loaded = mgr.load_checkpoint_by_id(cp.checkpoint_id)
        assert loaded is not None
        assert loaded.checkpoint_id == cp.checkpoint_id

    def test_load_checkpoint_by_id_missing(self, mgr):
        loaded = mgr.load_checkpoint_by_id("missing")
        assert loaded is None

    def test_prune_old_checkpoints(self, mgr):
        mgr.save_checkpoint("wf-1", {"step": 1})
        mgr.save_checkpoint("wf-1", {"step": 2})
        mgr.save_checkpoint("wf-1", {"step": 3})
        pruned = mgr.prune_old_checkpoints(max_age_days=365, max_per_workflow=1)
        assert pruned >= 2
        assert mgr.count_checkpoints("wf-1") == 1

    def test_count_checkpoints_all(self, mgr):
        mgr.save_checkpoint("wf-1", {"step": 1})
        mgr.save_checkpoint("wf-2", {"step": 1})
        assert mgr.count_checkpoints() == 2

    def test_count_checkpoints_by_workflow(self, mgr):
        mgr.save_checkpoint("wf-1", {"step": 1})
        mgr.save_checkpoint("wf-1", {"step": 2})
        mgr.save_checkpoint("wf-2", {"step": 1})
        assert mgr.count_checkpoints("wf-1") == 2

    def test_get_workflow_status(self, mgr):
        mgr.save_checkpoint("wf-1", {"step": 1}, metadata={"status": "running"})
        assert mgr.get_workflow_status("wf-1") == "running"

    def test_get_workflow_status_none(self, mgr):
        assert mgr.get_workflow_status("nonexistent") is None

    def test_get_latest_checkpoint_alias(self, mgr):
        cp = mgr.save_checkpoint("wf-1", {"step": 1})
        latest = mgr.get_latest_checkpoint("wf-1")
        assert latest is not None
        assert latest.checkpoint_id == cp.checkpoint_id

    def test_context_manager(self, state_manager, db_path):
        with CheckpointManager(state_manager=state_manager, db_path=db_path) as mgr:
            assert mgr._connection is not None
        assert mgr._connection is None

    def test_close(self, mgr):
        mgr.close()
        assert mgr._connection is None

    def test_compute_checksum_deterministic(self, mgr):
        c1 = CheckpointManager._compute_checksum({"a": 1}, {"b": 2})
        c2 = CheckpointManager._compute_checksum({"a": 1}, {"b": 2})
        assert c1 == c2

    def test_compute_checksum_different(self, mgr):
        c1 = CheckpointManager._compute_checksum({"a": 1}, {"b": 2})
        c2 = CheckpointManager._compute_checksum({"a": 2}, {"b": 2})
        assert c1 != c2

    @pytest.mark.asyncio
    async def test_create_checkpoint_calls_state_manager(self, state_manager, db_path):
        snapshot = AsyncMock()
        snapshot.id = "snap-1"
        snapshot.task_states = {"t1": "running"}
        snapshot.system_state = "active"
        snapshot.metadata = {}
        snapshot.checksum = "abc"
        state_manager.create_snapshot = AsyncMock(return_value=snapshot)

        mgr = CheckpointManager(state_manager=state_manager, db_path=db_path)
        cp = await mgr.create_checkpoint("wf-1", metadata={"custom": "val"})
        assert cp.workflow_id == "wf-1"
        assert "custom" in cp.metadata
        state_manager.create_snapshot.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_restore_checkpoint_no_checkpoint(self, state_manager, db_path):
        mgr = CheckpointManager(state_manager=state_manager, db_path=db_path)
        result = await mgr.restore_checkpoint("nonexistent")
        assert result is None

    def test_row_to_checkpoint(self, mgr):
        row = MagicMock()
        row.__getitem__.side_effect = lambda k: {
            "id": "cp-1",
            "workflow_id": "wf-1",
            "timestamp": "2025-01-01T00:00:00+00:00",
            "state_json": '{"a": 1}',
            "metadata_json": '{"b": 2}',
            "checksum": "abc",
            "parent_id": None,
        }[k]
        cp = mgr._row_to_checkpoint(row)
        assert cp.checkpoint_id == "cp-1"
        assert cp.state == {"a": 1}
