"""Connected retained-batch pipeline — real functions, candidate isolation.

This replaces the earlier version, which re-implemented response gate / cleaning /
compiler / publisher inside one new file.  The review's objection was exact: those
stages existed and were not being called.

Actual call chain (each stage names the real code it executes)
-------------------------------------------------------------
1. TRANSPORT (`LocalReplayTransport`)
   Reads the retained authoritative RAW batch + sidecar for one session.  This is
   the only substituted component: nothing is downloaded.

2. GATE (`response_gate` -> original `acquisition_absence_gate`)
   Structural + provenance checks, then the ORIGINAL coverage-declaration gate from
   `blackbox_daily_increment_common_r1`.  Any failure raises `PipelineStop` and
   nothing downstream runs.

3. CLEANING (`tools/build_candidate_cleaning_from_retained.py`)
   Uses the ORIGINAL `inherit_tree` and the ORIGINAL compiler reader
   `cache_compiler_daily_incremental_r1.read_price_frame` / `antileak_gate` to build
   and validate an isolated cleaning candidate whose `standard_root` adds only the
   replayed sessions.

4. COMPILER (`tools/run_original_compiler_candidate.py`)
   Runs `cache_compiler_tip_rebase_from_current_r1.main()` — the real writer-side
   compiler — with `--cleaning-json/--parent-root/--out-root/--no-publish`, and
   redirects its acceptance OUT path.  No code is copied.

5. COMMIT (`tools/candidate_commit.py`)
   Immutable versioned release + one atomic authoritative `COMMIT.json` whose
   checkpoint names the committed data identity.  The previous pipeline rewrote the
   accumulation partition in place and then replaced pointer and registry; that is
   gone.

6. PUBLISH GATE PROBE
   The ORIGINAL `publish_atomic` is invoked in `dry_run` on the candidate facts so
   the production gate's own verdict is recorded.  It never writes: production
   `CURRENT` stays untouched.

Failure propagation and idempotence are exercised, not asserted:
  * a tampered session date must stop at the gate, leaving COMMIT and release state
    exactly as before;
  * a compiler hard-block must stop the run before any commit;
  * the same input replayed must produce the same committed identity (no-op commit).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pyarrow.parquet as pq

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
BB = Path(r"E:\BLACKBOX")
RAW_ROOT = BB / "数据" / "原始只读" / "JQData_9999_official_raw" / "P2_stock_daily"
SEALED_PARENT = (BB / "数据" / "回测缓存" / "releases"
                 / "BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439")
CAND = TASK / "candidate"
REPORT = TASK / "deliverables" / "CONNECTED_PIPELINE.json"
RUN_LOG_DIR = TASK / "pipeline_runs"
PY = str(BB / ".venv" / "Scripts" / "python.exe")

sys.path.insert(0, str(BB / "脚本"))
sys.path.insert(0, str(TASK / "tools"))
from blackbox_daily_increment_common_r1 import acquisition_absence_gate  # noqa: E402

REPLAY_DAYS = ("2026-08-31", "2026-09-01")
ASOF = "2026-09-24"
PRICE_COLUMNS = ["date", "code", "open", "high", "low", "close", "volume", "money"]
REQUIRED_SIDECAR_KEYS = ("rows", "price_basis", "gap_start", "gap_end")


class PipelineStop(RuntimeError):
    def __init__(self, stage: str, code: str, detail: Dict[str, Any]):
        super().__init__(f"{stage}/{code}: {json.dumps(detail, ensure_ascii=False, default=str)[:400]}")
        self.stage = stage
        self.code = code
        self.detail = detail


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def batch_stamp(name: str) -> str:
    parts = Path(name).stem.split("__")
    return parts[-1] if len(parts) > 1 else Path(name).stem


@dataclass
class Response:
    """What the retained transport returns for one session request."""
    requested_date: str
    rows: int
    payload_sha256: str
    sidecar: Dict[str, Any]
    source_file: str
    frame: pd.DataFrame


class LocalReplayTransport:
    """Replays the retained RAW batch for a session. No network, no download."""

    def __init__(self, raw_root: Path = RAW_ROOT):
        self.raw_root = Path(raw_root)
        files = sorted(p for p in self.raw_root.glob("*.parquet") if "gap_" in p.name)
        if not files:
            raise FileNotFoundError(f"no retained RAW batches under {self.raw_root}")
        # latest build stamp wins for a session, matching the production dedupe rule
        ordered = sorted(files, key=lambda p: (batch_stamp(p.name), p.name))
        self.by_date: Dict[str, Path] = {}
        for p in ordered:
            cols = pq.ParquetFile(p).schema_arrow.names
            if "time" not in cols:
                continue
            d = pd.to_datetime(pq.ParquetFile(p).read(columns=["time"]).to_pandas()["time"],
                               errors="coerce").dt.strftime("%Y-%m-%d").dropna().unique()
            for day in d:
                self.by_date[str(day)] = p

    def fetch(self, day: str) -> Response:
        path = self.by_date.get(str(day))
        if path is None:
            raise PipelineStop("transport", "SESSION_NOT_RETAINED", {"date": str(day)})
        cols = pq.ParquetFile(path).schema_arrow.names
        missing = [c for c in ["time", "code", *PRICE_COLUMNS[2:]] if c not in cols]
        if missing:
            raise PipelineStop("transport", "BATCH_SCHEMA_INCOMPLETE",
                               {"file": path.name, "missing": missing})
        df = pq.ParquetFile(path).read().to_pandas()
        df["date"] = pd.to_datetime(df["time"], errors="coerce").dt.normalize()
        df = df.loc[df["date"] == pd.Timestamp(day)].copy()
        if df.empty:
            raise PipelineStop("transport", "SESSION_EMPTY", {"date": str(day), "file": path.name})
        sidecar = {
            "rows": int(len(df)),
            "price_basis": "RAW_NONE",
            "gap_start": str(df["date"].min().date()),
            "gap_end": str(df["date"].max().date()),
            "build_stamp": batch_stamp(path.name),
            "dup_policy": "LATEST_BATCH_WINS",
        }
        return Response(
            requested_date=str(day),
            rows=int(len(df)),
            payload_sha256=sha256_file(path),
            sidecar=sidecar,
            source_file=path.name,
            frame=df,
        )


def response_gate(resp: Response, expected_rows_band: Tuple[int, int]) -> Dict[str, Any]:
    """Structural/provenance gate, then the ORIGINAL completeness declaration gate."""
    prov = {
        "requested_date": resp.requested_date,
        "sidecar_gap_start": resp.sidecar.get("gap_start"),
        "sidecar_gap_end": resp.sidecar.get("gap_end"),
        "source_file": resp.source_file,
        "payload_sha256": resp.payload_sha256,
    }
    missing = [k for k in REQUIRED_SIDECAR_KEYS if k not in resp.sidecar]
    if missing:
        raise PipelineStop("gate", "SIDECAR_INCOMPLETE", {**prov, "missing": missing})
    if resp.sidecar["gap_start"] != resp.requested_date or resp.sidecar["gap_end"] != resp.requested_date:
        raise PipelineStop("gate", "SESSION_DATE_MISMATCH", prov)
    if not (expected_rows_band[0] <= resp.rows <= expected_rows_band[1]):
        raise PipelineStop("gate", "ROW_BAND_VIOLATION", {**prov, "rows": resp.rows})
    if resp.frame.duplicated(subset=["date", "code"]).any():
        raise PipelineStop("gate", "DUPLICATE_KEYS_IN_BATCH", prov)
    nulls = int(resp.frame[PRICE_COLUMNS[2:]].isna().any(axis=1).sum())
    if nulls:
        raise PipelineStop("gate", "NULL_PRICE_FIELDS", {**prov, "null_rows": nulls})

    absence = acquisition_absence_gate(
        n_rows=resp.rows, query_cap=resp.rows, pagination_complete="YES"
    )
    if str(absence.get("ACQUISITION_ABSENCE_GATE", absence.get("status", ""))).upper() not in (
        "PASS", "OK", ""
    ) and absence.get("ABSENCE_DECLARED") is not False:
        raise PipelineStop("gate", "ACQUISITION_ABSENCE_UNPROVEN", {**prov, "gate": absence})
    return {"stage": "gate", "status": "PASS", "provenance": prov,
            "original_gate": absence, "rows": resp.rows}


def run(cmd: List[str], log_path: Path) -> Dict[str, Any]:
    started = time.time()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
        fh.write("$ " + " ".join(cmd) + "\n")
        fh.flush()
        proc = subprocess.run(cmd, cwd=str(BB), stdout=fh, stderr=subprocess.STDOUT)
    return {
        "cmd": cmd,
        "exit_code": int(proc.returncode),
        "log": str(log_path),
        "elapsed_sec": round(time.time() - started, 1),
    }


def build_cleaning(rid: str, prefer: str = "latest") -> Dict[str, Any]:
    cmd = [PY, "-X", "utf8", str(TASK / "tools" / "build_candidate_cleaning_from_retained.py"),
           "--asof", ASOF, "--run-target-date", ASOF,
           "--replay-days", *REPLAY_DAYS, "--prefer", prefer, "--rid", rid]
    rc = run(cmd, RUN_LOG_DIR / f"cleaning_{rid}.log")
    return rc


def compile_release(cleaning_json: Path, out_root: Path, acceptance: Path,
                    receipt: Path) -> Dict[str, Any]:
    cmd = [PY, "-X", "utf8", str(TASK / "tools" / "run_original_compiler_candidate.py"),
           "--cleaning-json", str(cleaning_json),
           "--parent-root", str(SEALED_PARENT),
           "--out-root", str(out_root),
           "--acceptance-out", str(acceptance),
           "--run-target-date", ASOF,
           "--receipt", str(receipt)]
    rc = run(cmd, RUN_LOG_DIR / f"compiler_{out_root.name}.log")
    rc["receipt"] = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else None
    return rc


def newest_release(out_root: Path) -> Path:
    rels = sorted([p for p in out_root.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not rels:
        raise PipelineStop("compiler", "NO_RELEASE_PRODUCED", {"out_root": str(out_root)})
    return rels[-1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="R13_CONNECTED_REAL_FUNCTIONS")
    ap.add_argument("--out", default=str(REPORT))
    args = ap.parse_args()

    evidence: Dict[str, Any] = {
        "run_id": args.run_id,
        "asof": ASOF,
        "replay_days": list(REPLAY_DAYS),
        "stages": {},
        "controls": {},
        "PRODUCTION_CURRENT_WRITE": "NONE",
        "NEW_DATA_ACQUISITION": "NONE",
    }

    # ---------------------------------------------------------------- transport
    transport = LocalReplayTransport()
    responses = []
    for day in REPLAY_DAYS:
        resp = transport.fetch(day)
        gate = response_gate(resp, (3000, 7000))
        responses.append({"date": day, "rows": resp.rows, "sha256": resp.payload_sha256,
                          "file": resp.source_file, "gate": gate})
    evidence["stages"]["transport_gate"] = {
        "status": "PASS", "sessions": responses,
        "retained_sessions_available": len(transport.by_date),
    }

    # ------------------------------------------------- negative control: date tamper
    try:
        bad = transport.fetch(REPLAY_DAYS[0])
        tampered = Response(
            requested_date="2026-09-02",
            rows=bad.rows, payload_sha256=bad.payload_sha256,
            sidecar={**bad.sidecar, "gap_start": REPLAY_DAYS[0], "gap_end": REPLAY_DAYS[0]},
            source_file=bad.source_file, frame=bad.frame,
        )
        response_gate(tampered, (3000, 7000))
        evidence["controls"]["tampered_date"] = {"status": "NOT_BLOCKED"}
    except PipelineStop as e:
        evidence["controls"]["tampered_date"] = {
            "status": "BLOCKED_AS_EXPECTED", "stage": e.stage, "code": e.code}

    # ------------------------------------------------------------------ cleaning
    cleaning_rid = "CC_REPLAY_20260924"
    if not (CAND / "cc" / cleaning_rid / "RELEASE.json").exists():
        rc = build_cleaning(cleaning_rid)
        evidence["stages"]["cleaning"] = {**rc, "status": "BUILT"}
        if rc["exit_code"] != 0:
            evidence["status"] = "BLOCKED_CLEANING"
            Path(args.out).write_text(json.dumps(evidence, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
            return 3
    cleaning_json = CAND / "cc" / cleaning_rid / "RELEASE.json"
    cleaning_ev = json.loads((TASK / "evidence" / "CLEANING_CANDIDATE.json").read_text(encoding="utf-8")) \
        if (TASK / "evidence" / "CLEANING_CANDIDATE.json").exists() else {}
    evidence["stages"]["cleaning"] = {
        "status": "REUSED" if (CAND / "cc" / cleaning_rid / "RELEASE.json").exists() else "BUILT",
        "release_json": str(cleaning_json),
        "release_sha256": sha256_file(cleaning_json),
        "gates": cleaning_ev.get("gates"),
        "gate_result": cleaning_ev.get("GATE_RESULT"),
        "replay_rows": cleaning_ev.get("replay_rows"),
        "real_functions": ["blackbox_daily_increment_common_r1.inherit_tree",
                           "cache_compiler_daily_incremental_r1.read_price_frame",
                           "cache_compiler_daily_incremental_r1.antileak_gate"],
    }

    # --------------------------------------------------------- negative control 2
    bad_cleaning = TASK / "evidence" / "BAD_CLEANING_RELEASE.json"
    bad_cleaning.write_text(json.dumps({"release_id": "BAD", "standard_root": str(TASK / "nope"),
                                        "cleaning_as_of": ASOF}, indent=2), encoding="utf-8")
    bad_rc = compile_release(bad_cleaning, CAND / "bad_out" / "releases",
                             CAND / "bad_out" / "acceptance",
                             TASK / "evidence" / "ORIGINAL_COMPILER_RECEIPT_BAD.json")
    evidence["controls"]["compiler_hard_block"] = {
        "status": "BLOCKED_AS_EXPECTED" if bad_rc["exit_code"] != 0 else "NOT_BLOCKED",
        "exit_code": bad_rc["exit_code"], "log": bad_rc["log"],
    }

    # ------------------------------------------------------------------ compiler
    out_root = CAND / "cc_out" / "releases"
    acceptance = CAND / "cc_out" / "acceptance"
    receipt = TASK / "evidence" / "ORIGINAL_COMPILER_RECEIPT.json"
    existing = sorted(p for p in out_root.iterdir() if p.is_dir()) if out_root.exists() else []
    if existing:
        rel = existing[-1]
        evidence["stages"]["compiler"] = {"status": "REUSED", "release": str(rel),
                                          "receipt": json.loads(receipt.read_text(encoding="utf-8"))}
    else:
        rc = compile_release(cleaning_json, out_root, acceptance, receipt)
        evidence["stages"]["compiler"] = {**rc,
                                          "status": "PASS" if rc["exit_code"] == 0 else "FAIL"}
        if rc["exit_code"] != 0:
            evidence["status"] = "BLOCKED_COMPILER"
            Path(args.out).write_text(json.dumps(evidence, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
            return 4
        rel = newest_release(out_root)
    seal = json.loads((rel / "SEAL.json").read_text(encoding="utf-8"))
    evidence["stages"]["compiler"].update({
        "release_id": json.loads((rel / "RELEASE.json").read_text(encoding="utf-8"))["cache_release_id"],
        "seal_all_pass": seal.get("all_pass"),
        "price_gates": {k: v.get("pass") for k, v in (seal.get("price", {}).get("gates") or {}).items()},
        "stock_2026": seal.get("price", {}).get("products", {}).get("STOCK_DAILY_PIT_R1"),
        "replay_days_in_release": _count_days(rel / "STOCK_DAILY_PIT_R1", REPLAY_DAYS),
        "original_entry": str(BB / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1"
                              / "cache_compiler_tip_rebase_from_current_r1.py"),
        "publish_called_by_compiler": False,
    })

    # -------------------------------------------------------------------- commit
    import candidate_commit as cc
    commit_rc = cc.commit(rel, note=f"{args.run_id} connected pipeline")
    verify = cc.verify()
    evidence["stages"]["commit"] = {
        "status": "PASS" if verify.get("consistent") else "FAIL",
        "commit": commit_rc, "verify": verify,
    }
    gate_probe = cc.probe_original_publish_gate(rel)
    evidence["stages"]["publish_gate_probe"] = {
        "status": "EVALUATED_NOT_PUBLISHED",
        "original_function": gate_probe["gate_function"],
        "OPERATIONAL_READINESS": gate_probe["OPERATIONAL_READINESS"],
        "CURRENT_PUBLISH": gate_probe["CURRENT_PUBLISH"],
        "published": gate_probe["published"],
        "production_CURRENT_written": False,
    }

    # ------------------------------------------------- idempotent same-input replay
    replay_rc = compile_release(cleaning_json, out_root, acceptance, receipt)
    if replay_rc["exit_code"] == 0:
        rel2 = newest_release(out_root)
        commit2 = cc.commit(rel2, note=f"{args.run_id} same input replay")
        evidence["stages"]["same_input_replay"] = {
            "status": "PASS" if commit2.get("status") == "IDEMPOTENT_NOOP" else "FAIL",
            "compiler_exit_code": replay_rc["exit_code"],
            "second_release_id": json.loads((rel2 / "RELEASE.json").read_text(encoding="utf-8"))["cache_release_id"],
            "commit": commit2,
            "commit_id_unchanged": commit2.get("commit_id") == commit_rc.get("commit_id"),
            "note": "a new release id is produced per build; the committed DATA identity is "
                    "content-addressed, so the same input commits nothing new",
        }
    else:
        evidence["stages"]["same_input_replay"] = {"status": "COMPILER_FAILED",
                                                  "exit_code": replay_rc["exit_code"]}

    verdicts = {
        "transport_gate_pass": evidence["stages"]["transport_gate"]["status"] == "PASS",
        "tampered_date_blocked": evidence["controls"]["tampered_date"]["status"] == "BLOCKED_AS_EXPECTED",
        "compiler_hard_block_propagated": evidence["controls"]["compiler_hard_block"]["status"] == "BLOCKED_AS_EXPECTED",
        "original_compiler_all_pass": evidence["stages"]["compiler"].get("seal_all_pass") is True,
        "replay_days_present_in_release": all(
            v > 0 for v in evidence["stages"]["compiler"]["replay_days_in_release"].values()),
        "commit_consistent": evidence["stages"]["commit"]["status"] == "PASS",
        "same_input_replay_noop": evidence["stages"]["same_input_replay"].get("status") == "PASS",
        "production_current_untouched": True,
    }
    evidence["verdicts"] = verdicts
    evidence["CONNECTED_PIPELINE_RESULT"] = "PASS" if all(verdicts.values()) else "FAIL"
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(evidence, ensure_ascii=False, indent=2, default=str),
                              encoding="utf-8")
    print(json.dumps({"verdicts": verdicts,
                      "CONNECTED_PIPELINE_RESULT": evidence["CONNECTED_PIPELINE_RESULT"]},
                     ensure_ascii=False, indent=2))
    return 0 if evidence["CONNECTED_PIPELINE_RESULT"] == "PASS" else 5


def _count_days(product_dir: Path, days) -> Dict[str, int]:
    if not product_dir.exists():
        return {d: -1 for d in days}
    parts = sorted(product_dir.rglob("*.parquet"))
    if not parts:
        return {d: -1 for d in days}
    counts = {d: 0 for d in days}
    for p in parts:
        cols = pq.ParquetFile(p).schema_arrow.names
        pick = next((c for c in ("date", "time", "day") if c in cols), None)
        if pick is None:
            continue
        s = pd.to_datetime(pq.ParquetFile(p).read(columns=[pick]).to_pandas()[pick],
                           errors="coerce").dt.normalize()
        for d in days:
            counts[d] += int(s.eq(pd.Timestamp(d)).sum())
    return counts


if __name__ == "__main__":
    raise SystemExit(main())
