# -*- coding: utf-8 -*-
"""Bounded source-handle prefetch. Workers only open and take the first identity."""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor


class SourcePrefetch:
    def __init__(self, backend, workers: int, run_id):
        if workers != 4:
            raise RuntimeError("PREFETCH_WORKERS")
        self.backend = backend
        self.workers = workers
        self.run_id = run_id
        self._slots = threading.Semaphore(workers)
        self._pool = ThreadPoolExecutor(max_workers=workers)
        self._lock = threading.Lock()
        self._futures = {}
        self._stop = threading.Event()
        self._shutdown = False
        self.wait_seconds = 0.0
        self.worker_seconds = 0.0
        self.peak_slots = 0
        self._held = 0

    def submit(self, entity):
        if self._stop.is_set():
            raise RuntimeError("PREFETCH_STOPPED")
        self._slots.acquire()
        with self._lock:
            self._held += 1
            self.peak_slots = max(self.peak_slots, self._held)
            if entity["entity_key"] in self._futures:
                self._held -= 1
                self._slots.release()
                raise RuntimeError("PREFETCH_DUPLICATE")
        future = self._pool.submit(self._prepare, entity)
        with self._lock:
            self._futures[entity["entity_key"]] = future

    def _release_unopened(self):
        self._slots.release()
        with self._lock:
            self._held -= 1

    def _prepare(self, entity):
        started = time.perf_counter()
        handle = None
        try:
            if self._stop.is_set():
                self._release_unopened()
                return {"cancelled": True, "entity_key": entity["entity_key"]}
            with self.backend._phase("source_open"):
                handle = self.backend.sc.open_source(entity["source_path"])
            if self._stop.is_set():
                self.backend.sc.close(handle)
                handle = None
                self._release_unopened()
                return {"cancelled": True, "entity_key": entity["entity_key"]}
            with self.backend._phase("source_identity"):
                ident = self.backend.sc.identity(handle)
            if str(ident.get("file_id")) != str(entity["file_id"]) or str(ident.get("volume_serial")) != str(entity["volume_serial"]):
                raise RuntimeError("SOURCE_CHANGED")
            if int(ident.get("size")) != int(entity["logical_size"]):
                raise RuntimeError("SOURCE_SIZE")
            return {
                "handle": handle,
                "identity": ident,
                "source_path": entity["source_path"],
                "entity_key": entity["entity_key"],
                "file_id": entity["file_id"],
                "volume_serial": entity["volume_serial"],
                "logical_size": entity["logical_size"],
                "run_id": self.run_id,
            }
        except Exception:
            if handle is not None:
                self.backend.sc.close(handle)
            self._release_unopened()
            raise
        finally:
            with self._lock:
                self.worker_seconds += time.perf_counter() - started

    def take(self, entity):
        with self._lock:
            future = self._futures.pop(entity["entity_key"])
        started = time.perf_counter()
        try:
            prepared = future.result()
        except Exception:
            self.shutdown()
            raise
        finally:
            with self._lock:
                self.wait_seconds += time.perf_counter() - started
        if prepared.get("cancelled") or prepared.get("entity_key") != entity["entity_key"]:
            self.shutdown()
            raise RuntimeError("PREFETCH_ENTITY_MISMATCH")
        if prepared.get("source_path") != entity["source_path"] or prepared.get("run_id") != self.run_id:
            handle = prepared.pop("handle", None)
            if handle is not None:
                self.backend.sc.close(handle)
            self._release_unopened()
            self.shutdown()
            raise RuntimeError("PREFETCH_ENTITY_MISMATCH")
        return prepared

    def release_slot(self):
        """The caller already closed the consumed handle."""
        self._release_unopened()

    def shutdown(self):
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True
            futures = list(self._futures.items())
            self._futures.clear()
        self._stop.set()
        for _key, future in futures:
            try:
                prepared = future.result()
            except Exception:
                continue
            if not isinstance(prepared, dict) or prepared.get("cancelled"):
                continue
            handle = prepared.pop("handle", None)
            if handle is not None:
                self.backend.sc.close(handle)
                self._release_unopened()
        self._pool.shutdown(wait=True, cancel_futures=False)

    def stats(self) -> dict:
        return {
            "source_prefetch_wait_seconds": self.wait_seconds,
            "source_prefetch_worker_seconds_sum": self.worker_seconds,
            "source_prefetch_handle_peak": self.peak_slots,
            "prefetch_timing_note": (
                "source_prefetch_worker_seconds_sum adds overlapping worker time. "
                "It is not wall-clock time and is not included in copy_seconds."
            ),
        }
