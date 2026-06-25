"""
Checkpoint Management System

LangGraph-inspired checkpoint persistence for crash recovery.
Provides database-backed saving and loading of agent state with
integrity verification, TTL-based pruning, and workflow resumption.
"""

import hashlib
import json
import logging
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestrator.state import StateManager, StateSnapshot

logger = logging.getLogger("ZenAI.Checkpoints")

DEFAULT_DB_DIR = Path.home() / ".zen-ai" / "checkpoints"
DEFAULT_DB_NAME = "checkpoints.db"


@dataclass
class Checkpoint:
    """A persisted checkpoint of orchestrator state stored in the database."""

    checkpoint_id: str
    workflow_id: str
    timestamp: datetime
    state: Dict[str, Any]
    metadata: Dict[str, Any]
    checksum: str
    parent_id: Optional[str] = None


class CheckpointManager:
    """Database-backed checkpoint persistence for crash recovery.

    Wraps ``StateManager`` to provide durable snapshots with integrity
    verification, TTL-based pruning, and workflow resumption helpers.

    All low-level persistence methods are thread-safe via an internal
    ``threading.Lock`` and SQLite's WAL mode.

    Args:
        state_manager: The orchestrator ``StateManager`` instance.
        db_path:       Path to the SQLite database file.  ``None`` uses
                       ``~/.zen-ai/checkpoints/checkpoints.db``.
    """

    def __init__(
        self,
        state_manager: StateManager,
        db_path: Optional[str] = None,
    ) -> None:
        self.state_manager = state_manager
        self._db_path = Path(db_path or str(self._default_db_path()))
        self._lock = threading.Lock()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
        self._init_db()
        logger.info("CheckpointManager initialised at %s", self._db_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _default_db_path() -> Path:
        return DEFAULT_DB_DIR / DEFAULT_DB_NAME

    def _get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False,
            )
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA busy_timeout=5000")
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def _init_db(self) -> None:
        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id            TEXT PRIMARY KEY,
                workflow_id   TEXT NOT NULL,
                timestamp     TEXT NOT NULL,
                state_json    TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                checksum      TEXT NOT NULL,
                parent_id     TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_workflow_id
            ON checkpoints(workflow_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_timestamp
            ON checkpoints(timestamp)
        """)
        conn.commit()
        logger.debug("Checkpoints table and indexes ready")

    @staticmethod
    def _compute_checksum(state: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        raw = json.dumps(
            {"state": state, "metadata": metadata},
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _verify_checksum(checkpoint: Checkpoint) -> None:
        expected = CheckpointManager._compute_checksum(checkpoint.state, checkpoint.metadata)
        if checkpoint.checksum != expected:
            raise ValueError(
                f"Checksum mismatch for checkpoint {checkpoint.checkpoint_id}: "
                f"computed {expected}, stored {checkpoint.checksum}"
            )

    def _row_to_checkpoint(self, row: sqlite3.Row) -> Checkpoint:
        return Checkpoint(
            checkpoint_id=row["id"],
            workflow_id=row["workflow_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            state=json.loads(row["state_json"]),
            metadata=json.loads(row["metadata_json"]),
            checksum=row["checksum"],
            parent_id=row["parent_id"],
        )

    # ------------------------------------------------------------------
    # Low-level persistence  (thread-safe, SQLite-backed)
    # ------------------------------------------------------------------

    def save_checkpoint(
        self,
        workflow_id: str,
        state_dict: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
    ) -> Checkpoint:
        """Persist a full agent-state dict as a checkpoint row."""
        metadata = metadata or {}
        checkpoint_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc)
        checksum = self._compute_checksum(state_dict, metadata)

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            workflow_id=workflow_id,
            timestamp=ts,
            state=state_dict,
            metadata=metadata,
            checksum=checksum,
            parent_id=parent_id,
        )

        with self._lock:
            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO checkpoints
                    (id, workflow_id, timestamp, state_json,
                     metadata_json, checksum, parent_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint_id,
                    workflow_id,
                    ts.isoformat(),
                    json.dumps(state_dict, default=str),
                    json.dumps(metadata, default=str),
                    checksum,
                    parent_id,
                ),
            )
            conn.commit()

        logger.debug("Saved checkpoint %s for workflow %s", checkpoint_id, workflow_id)
        return checkpoint

    def load_checkpoint(self, workflow_id: str) -> Optional[Checkpoint]:
        """Load the latest checkpoint for *workflow_id* (or ``None``)."""
        with self._lock:
            conn = self._get_connection()
            row = conn.execute(
                """
                SELECT * FROM checkpoints
                WHERE workflow_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (workflow_id,),
            ).fetchone()

        if row is None:
            return None

        cp = self._row_to_checkpoint(row)
        self._verify_checksum(cp)
        return cp

    def list_checkpoints(self, workflow_id: str) -> List[Checkpoint]:
        """Return all checkpoints for *workflow_id* (newest first)."""
        with self._lock:
            conn = self._get_connection()
            rows = conn.execute(
                """
                SELECT * FROM checkpoints
                WHERE workflow_id = ?
                ORDER BY timestamp DESC
                """,
                (workflow_id,),
            ).fetchall()

        return [self._row_to_checkpoint(r) for r in rows]

    def load_checkpoint_by_id(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Load a specific checkpoint by its UUID."""
        with self._lock:
            conn = self._get_connection()
            row = conn.execute(
                "SELECT * FROM checkpoints WHERE id = ?",
                (checkpoint_id,),
            ).fetchone()

        if row is None:
            return None

        cp = self._row_to_checkpoint(row)
        self._verify_checksum(cp)
        return cp

    def delete_workflow_checkpoints(self, workflow_id: str) -> int:
        """Remove every checkpoint belonging to *workflow_id*."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(
                "DELETE FROM checkpoints WHERE workflow_id = ?",
                (workflow_id,),
            )
            conn.commit()
            deleted = cursor.rowcount

        logger.info("Deleted %d checkpoints for workflow %s", deleted, workflow_id)
        return deleted

    def prune_old_checkpoints(
        self,
        max_age_days: int = 7,
        max_per_workflow: int = 20,
    ) -> int:
        """Remove checkpoints older than *max_age_days* and cap per workflow.

        1. Delete checkpoints older than *max_age_days*.
        2. For each workflow, keep at most *max_per_workflow* newest rows.

        Returns:
            Total number of pruned checkpoints.
        """
        total_pruned = 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        cutoff_str = cutoff.isoformat()

        with self._lock:
            conn = self._get_connection()

            cursor = conn.execute(
                "DELETE FROM checkpoints WHERE timestamp < ?",
                (cutoff_str,),
            )
            total_pruned += cursor.rowcount

            workflows = conn.execute("SELECT DISTINCT workflow_id FROM checkpoints").fetchall()

            for (wf_id,) in workflows:
                count = conn.execute(
                    "SELECT COUNT(*) FROM checkpoints WHERE workflow_id = ?",
                    (wf_id,),
                ).fetchone()[0]

                if count > max_per_workflow:
                    excess = count - max_per_workflow
                    conn.execute(
                        """
                        DELETE FROM checkpoints WHERE id IN (
                            SELECT id FROM checkpoints
                            WHERE workflow_id = ?
                            ORDER BY timestamp ASC
                            LIMIT ?
                        )
                        """,
                        (wf_id, excess),
                    )
                    total_pruned += excess

            conn.commit()

        if total_pruned:
            logger.info("Pruned %d old / excess checkpoints", total_pruned)
        return total_pruned

    def verify_checkpoint(self, checkpoint_id: str) -> bool:
        """Return ``True`` if the checkpoint exists and its checksum is valid."""
        try:
            return self.load_checkpoint_by_id(checkpoint_id) is not None
        except ValueError:
            return False

    # ------------------------------------------------------------------
    # High-level StateManager integration
    # ------------------------------------------------------------------

    async def create_checkpoint(
        self,
        workflow_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None,
    ) -> Checkpoint:
        """Snapshot current ``StateManager`` state and persist to DB.

        Calls ``StateManager.create_snapshot()``, serialises the
        ``StateSnapshot`` into a state dict, and saves via
        ``save_checkpoint()``.
        """
        snapshot = await self.state_manager.create_snapshot()

        state_dict: Dict[str, Any] = {
            "snapshot_id": snapshot.id,
            "task_states": snapshot.task_states,
            "system_state": snapshot.system_state,
            "system_metadata": snapshot.metadata,
            "checksum": snapshot.checksum,
        }

        checkpoint_metadata: Dict[str, Any] = {
            "workflow_name": workflow_id,
            "step_number": 0,
            "iteration": 0,
            "status": snapshot.system_state,
            "task_count": len(snapshot.task_states),
        }
        if metadata:
            checkpoint_metadata.update(metadata)

        return self.save_checkpoint(
            workflow_id=workflow_id,
            state_dict=state_dict,
            metadata=checkpoint_metadata,
            parent_id=parent_id,
        )

    async def restore_checkpoint(self, workflow_id: str) -> Optional[StateSnapshot]:
        """Restore ``StateManager`` state from the latest checkpoint.

        Loads the newest checkpoint for *workflow_id*, reconstructs a
        ``StateSnapshot``, and applies it directly to the wrapped
        ``StateManager`` under its internal lock.
        """
        checkpoint = self.load_checkpoint(workflow_id)
        if checkpoint is None:
            logger.warning("No checkpoint found for workflow '%s'", workflow_id)
            return None

        state = checkpoint.state
        snapshot = StateSnapshot(
            id=checkpoint.checkpoint_id,
            timestamp=checkpoint.timestamp,
            task_states=state.get("task_states", {}),
            system_state=state.get("system_state", "initializing"),
            metadata=state.get("system_metadata", {}),
        )

        async with self.state_manager._lock:
            from orchestrator.state import SystemState, TaskState

            self.state_manager._task_states = {tid: TaskState(s) for tid, s in snapshot.task_states.items()}
            self.state_manager._system_state = SystemState(snapshot.system_state)
            self.state_manager._system_metadata = snapshot.metadata.copy()

            self.state_manager._snapshots.append(snapshot)
            if len(self.state_manager._snapshots) > self.state_manager._max_snapshots:
                self.state_manager._snapshots = self.state_manager._snapshots[-self.state_manager._max_snapshots :]

        logger.info(
            "Restored checkpoint %s for workflow '%s'",
            checkpoint.checkpoint_id,
            workflow_id,
        )
        return snapshot

    # ------------------------------------------------------------------
    # Resumption helpers
    # ------------------------------------------------------------------

    def get_latest_checkpoint(self, workflow_id: str) -> Optional[Checkpoint]:
        """Alias for ``load_checkpoint()``."""
        return self.load_checkpoint(workflow_id)

    def has_checkpoint(self, workflow_id: str) -> bool:
        """Return ``True`` if *workflow_id* has at least one checkpoint."""
        with self._lock:
            conn = self._get_connection()
            row = conn.execute(
                "SELECT 1 FROM checkpoints WHERE workflow_id = ? LIMIT 1",
                (workflow_id,),
            ).fetchone()
            return row is not None

    def get_workflow_status(self, workflow_id: str) -> Optional[str]:
        """Return the last-known ``status`` from the latest checkpoint."""
        cp = self.load_checkpoint(workflow_id)
        if cp is None:
            return None
        return cp.metadata.get("status")

    def count_checkpoints(self, workflow_id: Optional[str] = None) -> int:
        """Count checkpoints, optionally filtered by workflow."""
        with self._lock:
            conn = self._get_connection()
            if workflow_id is not None:
                row = conn.execute(
                    "SELECT COUNT(*) FROM checkpoints WHERE workflow_id = ?",
                    (workflow_id,),
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) FROM checkpoints").fetchone()
            return row[0] if row else 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None
                logger.debug("CheckpointManager database connection closed")

    def __enter__(self):
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


# ======================================================================
if __name__ == "__main__":
    import asyncio
    import os
    import tempfile

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    async def demo() -> None:
        from orchestrator.state import TaskState

        state_mgr = StateManager()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        cp_mgr = CheckpointManager(state_manager=state_mgr, db_path=db_path)
        wf = "pentest-demo"

        logger.info("=" * 60)
        logger.info("  CheckpointManager Demo — Save / Load Cycle")
        logger.info("=" * 60)

        await state_mgr.set_task_state("recon-1", TaskState.RUNNING)
        await state_mgr.set_task_state("scan-1", TaskState.QUEUED)
        await state_mgr.set_task_state("exploit-1", TaskState.PENDING)

        logger.info("[1] Checkpoint A — phase=reconnaissance, step=1")
        cp_a = await cp_mgr.create_checkpoint(
            wf,
            metadata={"step_number": 1, "phase": "reconnaissance"},
        )
        logger.info(
            "    id=%s…  checksum=%s…  tasks=%d", cp_a.checkpoint_id[:8], cp_a.checksum[:12], cp_a.metadata["task_count"]
        )

        await state_mgr.set_task_state("recon-1", TaskState.COMPLETED)
        await state_mgr.set_task_state("scan-1", TaskState.RUNNING)

        logger.info("[2] Checkpoint B — phase=scanning, step=2 (parent=A)")
        cp_b = await cp_mgr.create_checkpoint(
            wf,
            metadata={"step_number": 2, "phase": "scanning"},
            parent_id=cp_a.checkpoint_id,
        )
        logger.info("    id=%s…  parent_id=%s…", cp_b.checkpoint_id[:8], cp_b.parent_id[:8])

        logger.info("[3] Listing checkpoints for '%s':", wf)
        for c in cp_mgr.list_checkpoints(wf):
            logger.info(
                "    [%s…] step=%d phase=%s tasks=%d",
                c.checkpoint_id[:8],
                c.metadata["step_number"],
                c.metadata["phase"],
                c.metadata["task_count"],
            )

        logger.info(
            "[4] has_checkpoint=%s  count=%d  status=%s",
            cp_mgr.has_checkpoint(wf),
            cp_mgr.count_checkpoints(wf),
            cp_mgr.get_workflow_status(wf),
        )

        logger.info("[5] Restore latest → state matches B's snapshot:")
        await cp_mgr.restore_checkpoint(wf)
        current = await state_mgr.get_all_task_states()
        for tid, st in sorted(current.items()):
            logger.info("      %s: %s", tid, st.value)

        logger.info(
            "[6] Integrity:  A=%s  B=%s",
            cp_mgr.verify_checkpoint(cp_a.checkpoint_id),
            cp_mgr.verify_checkpoint(cp_b.checkpoint_id),
        )

        logger.info("[7] Pruning (max_age_days=0, max_per_workflow=1):")
        pruned = cp_mgr.prune_old_checkpoints(max_age_days=0, max_per_workflow=1)
        logger.info("    pruned=%d, remaining=%d", pruned, cp_mgr.count_checkpoints(wf))

        cp_mgr.close()
        os.unlink(db_path)
        logger.info("[*] Demo complete.  All checks passed.")

    asyncio.run(demo())
