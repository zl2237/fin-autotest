import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RunRecord:
    run_id: str
    marker: str
    env: dict
    status: str = "running"
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: Optional[str] = None
    result: Optional[dict] = None
    logs: list = field(default_factory=list)


class RunStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._runs: dict[str, RunRecord] = {}

    def create(self, marker: str, env: dict) -> RunRecord:
        run_id = uuid.uuid4().hex[:8]
        record = RunRecord(run_id=run_id, marker=marker, env=env)
        with self._lock:
            self._runs[run_id] = record
        return record

    def get(self, run_id: str) -> Optional[RunRecord]:
        with self._lock:
            return self._runs.get(run_id)

    def append_log(self, run_id: str, line: str):
        with self._lock:
            record = self._runs.get(run_id)
            if record:
                record.logs.append(line)

    def complete(self, run_id: str, result: dict):
        with self._lock:
            record = self._runs.get(run_id)
            if record:
                record.status = "completed"
                record.finished_at = datetime.now().isoformat()
                record.result = result

    def fail(self, run_id: str, error: str):
        with self._lock:
            record = self._runs.get(run_id)
            if record:
                record.status = "failed"
                record.finished_at = datetime.now().isoformat()
                record.result = {"error": error}


store = RunStore()
