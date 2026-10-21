"""Small persistent worklist. Writes only to its explicit report directory."""
from __future__ import annotations
import hashlib
import json
import os
from collections import deque
from datetime import datetime, timezone
from pathlib import Path


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".new")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


class Worklist:
    """Caller supplies reference parsing, canonical identity, and scope admission."""
    def __init__(self, directory, seeds=(), *, policy_id, normalize=str, admit=lambda _: True):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "worklist.json"
        self.normalize, self.admit = normalize, admit
        if self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
            if self.state.get("policy_id") != policy_id:
                raise ValueError("Policy changed; preserve old state and use a new report directory")
        else:
            self.state = {
                "schema": 1, "policy_id": policy_id, "pending": [],
                "done": {}, "failed": {}, "excluded": {}, "phase": "READY",
            }
        self.pending = deque(self.state["pending"])
        self.known = set(self.pending) | set(self.state["done"]) | set(self.state["failed"])
        for node in seeds:
            self.enqueue(node)
        self.save()

    def enqueue(self, node):
        node = self.normalize(str(node))
        if node in self.known or node in self.state["excluded"]:
            return
        if not self.admit(node):
            self.state["excluded"][node] = "SCOPE_EXCLUDED"
            return
        self.pending.append(node)
        self.known.add(node)

    def save(self):
        self.state["pending"] = list(self.pending)  # COMPLETE queue, never just its head.
        self.state["saved_at"] = datetime.now(timezone.utc).isoformat()
        atomic_json(self.path, self.state)

    def run(self, process, *, deadline=None, max_items=None):
        """No fixed read cap by default; a batch cap preserves all pending items."""
        if deadline is not None:
            deadline = datetime.fromisoformat(deadline) if isinstance(deadline, str) else deadline
            if deadline.tzinfo is None:
                raise ValueError("deadline must include timezone")
        processed = 0
        while self.pending:
            if deadline is not None and datetime.now(timezone.utc) >= deadline:
                self.state["phase"] = "DEADLINE_CHECKPOINT"
                break
            if max_items is not None and processed >= max_items:
                self.state["phase"] = "BATCH_CHECKPOINT"
                break
            node = self.pending[0]  # Do not consume the item before its result is durable.
            self.state["phase"] = "READING"
            self.state["current"] = node
            self.save()
            try:
                result = process(node)
                if not isinstance(result, dict):
                    raise TypeError("process must return a dict")
                targets = result.get("targets", [])
                if not isinstance(targets, list):
                    raise TypeError("targets must be a list")
            except Exception as error:
                self.state["failed"][node] = {
                    "type": type(error).__name__, "reason": str(error)[:1000]
                }
            else:
                key = hashlib.sha256(node.encode("utf-8")).hexdigest()
                result_path = self.directory / "node_results" / (key + ".json")
                # Failed output writes propagate; pending item is retained in the last state.
                atomic_json(result_path, {"node": node, **result})
                for target in targets:
                    self.enqueue(target)
                self.state["done"][node] = {
                    "result_file": str(result_path),
                    "source_sha256": result.get("source_sha256"),
                    "targets": len(targets),
                }
            self.pending.popleft()
            processed += 1
            self.state.pop("current", None)
            self.save()
        else:
            self.state["phase"] = "WORKLIST_DRAINED"  # Not full system acceptance.
        self.save()
        return {
            "phase": self.state["phase"],
            "processed_this_run": processed,
            "done": len(self.state["done"]), "failed": len(self.state["failed"]),
            "pending": len(self.pending), "excluded": len(self.state["excluded"]),
        }

