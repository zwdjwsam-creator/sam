# -*- coding: utf-8 -*-
"""One-shot readonly source latency probe. Does not modify the runtime modules."""
import hashlib
import json
import os
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
import r9_pilot_common_r9fix as common
import r9_plan_reader as reader
import r9_source_contract as source_contract
from r9_winio import Win32Syscalls

EXPECTED_DIGEST = "b54de9124166eb489ce56d30b14e28d614f82d28299cf35c9b879cef9fc9b7ab"
SUBSET = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_COMPLETE_TIMING_AND_FREEZE_REBENCH_20261014\subset\BENCH_SUBSET.sqlite")
OUT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_SOURCE_LATENCY_READONLY_20261014\SOURCE_LATENCY.json")
LIMIT = 24
PREFIX = 64 * 1024
BYTE_CAP = 8 * 1024 * 1024
WORKERS = 4

_local = threading.local()
_basic = common.GetFileInformationByHandle
_extended = common.GetFileInformationByHandleEx
_handle_lock = threading.Lock()
_handles = {"open": 0, "peak": 0}
_bytes_lock = threading.Lock()
_bytes = {"read": 0}


def _timed(original, slot):
    def wrapped(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - started
            current = getattr(_local, slot, None)
            if current is None:
                current = []
                setattr(_local, slot, current)
            current.append(elapsed)
    return wrapped


common.GetFileInformationByHandle = _timed(_basic, "basic")
common.GetFileInformationByHandleEx = _timed(_extended, "alloc")


def _take(slot):
    values = getattr(_local, slot, None) or []
    setattr(_local, slot, [])
    return values


def _enter_handle():
    with _handle_lock:
        _handles["open"] += 1
        _handles["peak"] = max(_handles["peak"], _handles["open"])


def _leave_handle():
    with _handle_lock:
        _handles["open"] -= 1


def _select():
    conn = sqlite3.connect(f"file:{SUBSET.resolve().as_posix()}?mode=ro", uri=True)
    rows = conn.execute(
        """
        SELECT path, volume_serial, file_id, logical_size
        FROM paths
        WHERE is_dir=0 AND is_reparse=0
        ORDER BY path
        """
    ).fetchall()
    conn.close()
    forced = []
    rest = []
    for path, volume, file_id, size in rows:
        text = str(path)
        long_zh = len(text) >= 240 and any(ord(ch) > 127 for ch in text)
        is_d = str(volume) == "3187598165"
        if is_d or long_zh:
            forced.append((text, str(volume), str(file_id), int(size or 0), "d_source" if is_d else "long_zh"))
        else:
            rest.append((text, str(volume), str(file_id), int(size or 0), "spread"))
    chosen = []
    seen = set()
    parents = set()

    def add(row):
        key = (row[1], row[2])
        parent = str(Path(row[0]).parent).casefold()
        if key in seen or len(chosen) >= LIMIT:
            return
        if row[4] == "spread" and parent in parents:
            return
        mapped = reader.map_inventory_path(row[0])
        source = mapped["source_path"]
        if not (source.startswith("\\\\192.168.100.2\\E_DRIVE\\BLACKBOX") or source.startswith("\\\\192.168.100.2\\D_DRIVE")):
            return
        seen.add(key)
        parents.add(parent)
        chosen.append({
            "dest_path": row[0],
            "source_path": source,
            "volume_serial": row[1],
            "file_id": row[2],
            "logical_size": row[3],
            "sample_class": row[4],
        })

    for row in forced:
        add(row)
    for row in rest:
        if len(chosen) >= LIMIT:
            break
        add(row)
    return chosen


def _work(item):
    sc = Win32Syscalls()
    handle = None
    row = {
        "source_path": item["source_path"],
        "dest_path": item["dest_path"],
        "plan_volume": item["volume_serial"],
        "plan_file_id": item["file_id"],
        "plan_size": item["logical_size"],
        "sample_class": item["sample_class"],
    }
    try:
        started = time.perf_counter()
        handle = sc.open_source(item["source_path"])
        _enter_handle()
        row["open_seconds"] = time.perf_counter() - started
        _take("basic")
        _take("alloc")
        started = time.perf_counter()
        before = sc.identity(handle)
        row["identity_before_seconds"] = time.perf_counter() - started
        row["basic_before_seconds"] = sum(_take("basic"))
        row["alloc_before_seconds"] = sum(_take("alloc"))
        if str(before.get("file_id")) != item["file_id"] or str(before.get("volume_serial")) != item["volume_serial"]:
            raise RuntimeError("SOURCE_IDENTITY_MISMATCH")
        if int(before.get("size")) != int(item["logical_size"]):
            raise RuntimeError("SOURCE_SIZE_MISMATCH")
        requested = min(PREFIX, int(before.get("size")))
        with _bytes_lock:
            if _bytes["read"] + requested > BYTE_CAP:
                raise RuntimeError("BYTE_CAP")
        started = time.perf_counter()
        payload = sc.read(handle, requested) if requested else b""
        row["read_seconds"] = time.perf_counter() - started
        row["bytes_read"] = len(payload)
        row["prefix_sha256"] = hashlib.sha256(payload).hexdigest()
        with _bytes_lock:
            _bytes["read"] += len(payload)
        del payload
        _take("basic")
        _take("alloc")
        started = time.perf_counter()
        after = sc.identity(handle)
        row["identity_after_seconds"] = time.perf_counter() - started
        row["basic_after_seconds"] = sum(_take("basic"))
        row["alloc_after_seconds"] = sum(_take("alloc"))
        row["identity_stable"] = (
            str(after.get("file_id")) == str(before.get("file_id"))
            and str(after.get("volume_serial")) == str(before.get("volume_serial"))
            and int(after.get("size")) == int(before.get("size"))
            and str(after.get("mtime_ft")) == str(before.get("mtime_ft"))
        )
        if not row["identity_stable"]:
            raise RuntimeError("SOURCE_CHANGED_DURING_READ")
        row["error"] = None
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if handle is not None:
            started = time.perf_counter()
            try:
                sc.close(handle)
                row["close_seconds"] = time.perf_counter() - started
            except Exception as exc:
                row["close_seconds"] = time.perf_counter() - started
                row["close_error"] = f"{type(exc).__name__}: {exc}"
            _leave_handle()
    return row


def _run_serial(items):
    rows = []
    for item in items:
        row = _work(item)
        rows.append(row)
        if row.get("error"):
            break
    return rows


def _run_parallel(items):
    stop = threading.Event()
    rows = [None] * len(items)

    def wrapped(index, item):
        if stop.is_set():
            return {"source_path": item["source_path"], "error": None, "not_started": True}
        row = _work(item)
        if row.get("error"):
            stop.set()
        return row

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(wrapped, index, item) for index, item in enumerate(items)]
        for index, future in enumerate(futures):
            rows[index] = future.result()
    return [row for row in rows if row and not row.get("not_started")]


def _mode(name, items, runner):
    with _handle_lock:
        _handles["open"] = 0
        _handles["peak"] = 0
    started = time.perf_counter()
    rows = runner(items)
    wall = time.perf_counter() - started
    failed = [row for row in rows if row.get("error")]
    return {
        "mode": name,
        "wall_seconds": wall,
        "completed": sum(1 for row in rows if not row.get("error")),
        "failed": len(failed),
        "bytes_read": sum(int(row.get("bytes_read") or 0) for row in rows),
        "handle_peak": _handles["peak"],
        "item_seconds_sum_not_wall": sum(
            float(row.get("open_seconds") or 0)
            + float(row.get("identity_before_seconds") or 0)
            + float(row.get("read_seconds") or 0)
            + float(row.get("identity_after_seconds") or 0)
            + float(row.get("close_seconds") or 0)
            for row in rows
        ),
        "items": rows,
    }


def _consistent(rounds):
    seen = {}
    for rnd in rounds:
        for mode in (rnd.get("first"), rnd.get("second")):
            if not mode:
                continue
            for row in mode["items"]:
                if row.get("error"):
                    return False
                key = (row["plan_volume"], row["plan_file_id"])
                marker = (row.get("prefix_sha256"), row.get("bytes_read"), row.get("identity_stable"))
                if key in seen and seen[key] != marker:
                    return False
                seen[key] = marker
    return True


def main():
    digest = source_contract.code_digest()
    if digest != EXPECTED_DIGEST:
        raise SystemExit("CODE_DIGEST_CHANGED")
    items = _select()
    classes = {}
    for item in items:
        classes[item["sample_class"]] = classes.get(item["sample_class"], 0) + 1
    rounds = []
    for label, order in (("serial_then_4", (_run_serial, _run_parallel)), ("4_then_serial", (_run_parallel, _run_serial))):
        first_runner, second_runner = order
        first = _mode("serial" if first_runner is _run_serial else "workers_4", items, first_runner)
        if first["failed"]:
            rounds.append({"round": label, "first": first, "second": None, "stopped": True})
            break
        second = _mode("workers_4" if second_runner is _run_parallel else "serial", items, second_runner)
        rounds.append({"round": label, "first": first, "second": second, "stopped": bool(second["failed"])})
        if second["failed"]:
            break
    payload = {
        "task_id": "R9_DESKTOP_SOURCE_LATENCY_READONLY_20261014_2018",
        "pid": os.getpid(),
        "code_digest": digest,
        "samples": len(items),
        "sample_classes": classes,
        "byte_cap": BYTE_CAP,
        "bytes_read_total": _bytes["read"],
        "rounds": rounds,
        "results_consistent": _consistent(rounds),
        "copy_authorized": False,
        "e_root_exists_after": Path(r"E:\R9_FORMAL_BENCH_RECHECK_20261014").exists(),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SAMPLES", len(items), classes)
    print("BYTES", _bytes["read"], "CONSISTENT", payload["results_consistent"])
    for rnd in rounds:
        for key in ("first", "second"):
            mode = rnd.get(key)
            if not mode:
                continue
            print(rnd["round"], mode["mode"], "wall", round(mode["wall_seconds"], 4), "ok", mode["completed"], "fail", mode["failed"], "peak", mode["handle_peak"])


if __name__ == "__main__":
    main()
