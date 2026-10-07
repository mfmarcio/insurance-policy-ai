from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.config.settings import get_settings
from app.models.policy import PolicyComparison, PolicyData


class PolicyRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self.settings = get_settings()
        self.db_path = db_path or self.settings.database_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS policies (
                    policy_id TEXT PRIMARY KEY,
                    document_name TEXT NOT NULL,
                    insurer TEXT,
                    policy_number TEXT,
                    product TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_a_id TEXT NOT NULL,
                    policy_b_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def save_policy(self, policy: PolicyData) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO policies(policy_id, document_name, insurer, policy_number, product, payload_json, created_at)
                VALUES(?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(policy_id) DO UPDATE SET
                    document_name=excluded.document_name,
                    insurer=excluded.insurer,
                    policy_number=excluded.policy_number,
                    product=excluded.product,
                    payload_json=excluded.payload_json,
                    created_at=excluded.created_at
                """,
                (
                    policy.policy_id,
                    policy.document_name,
                    policy.insurer,
                    policy.policy_number,
                    policy.product,
                    policy.model_dump_json(),
                    policy.created_at.isoformat(),
                ),
            )

    def list_policies(self) -> list[PolicyData]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload_json FROM policies ORDER BY created_at DESC").fetchall()
        return [PolicyData.model_validate(json.loads(row["payload_json"])) for row in rows]

    def get_policy(self, policy_id: str) -> PolicyData | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload_json FROM policies WHERE policy_id = ?", (policy_id,)).fetchone()
        return PolicyData.model_validate(json.loads(row["payload_json"])) if row else None

    def save_comparison(self, comparison: PolicyComparison) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO comparisons(policy_a_id, policy_b_id, payload_json) VALUES(?, ?, ?)",
                (comparison.policy_a_id, comparison.policy_b_id, comparison.model_dump_json()),
            )
