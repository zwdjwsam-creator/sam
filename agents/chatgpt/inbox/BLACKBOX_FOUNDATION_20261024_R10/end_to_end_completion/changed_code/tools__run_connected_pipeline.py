"""Connected update pipeline over retained real batches, with an isolated publisher.

This is deliverable 3: the *whole* path, not standalone helpers.

    local replay transport  ->  response gate  ->  cleaning + anti-leak
        ->  factor refresh  ->  compiler  ->  candidate checkpoint
        ->  isolated publication (candidate pointer pair)

Design choices, all deliberate:

* The external transport is the only substituted piece: `LocalReplayTransport`
  reads the retained RAW batch + sidecar + adjust-factor increment and returns a
  response object that carries the requested date, the payload date and the batch
  provenance. Nothing is fetched.
* The gate is evaluated *before* any merge. A malformed date, a short batch or an
  unproven coverage declaration raises `PipelineStop`, which propagates out of
  `run_day()` and leaves the published candidate untouched.
* Publication writes a candidate pointer PAIR (pointer + registry) with tmp+replace
  for each file. Two sequential replaces are not a transaction and the report says
  so; what is proven is that a failed run leaves the previous pair readable.
* The checkpoint is per-day and content-addressed, so a resume starts from the last
  committed day and a replay of the same day is a no-op.
* `publish_atomic` (production) is never called, `CURRENT` is never touched.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pyarrow.parquet as pq

TASK_ROOT = r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
RAW_ROOT = r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw"
CACHE_RELEASE_ROOT = (
    r"E:\BLACKBOX\数据\回测缓存\releases"
    r"\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439"
)
PIPE_ROOT = os.path.join(TASK_ROOT, "candidate", "data", "R12_PIPELINE")
PRODUCT = "STOCK_DAILY_PIT_R1"
ACCUM_PART = os.path.join(PIPE_ROOT, PRODUCT, "year=2026", "part_2026.parquet")
POINTER = os.path.join(PIPE_ROOT, "CANDIDATE_POINTER.json")
REGISTRY = os.path.join(PIPE_ROOT, "CANDIDATE_REGISTRY.json")
CHECKPOINT = os.path.join(PIPE_ROOT, "CHECKPOINT.json")
REPORT = os.path.join(TASK_ROOT, "deliverables", "CONNECTED_PIPELINE.json")
RUN_LOG_DIR = os.path.join(TASK_ROOT, "pipeline_runs")

RECOVERY_DAYS = ("2026-08-31", "2026-09-01")
PRICE_COLUMNS = ["date", "code", "open", "high", "low", "close", "volume", "money"]
META_COLUMNS = ["signal_date", "data_date", "asset_type", "price_adj_tag",
                "asof_rule", "pit_status", "source_version", "known_at"]
SOURCE_VERSION = "R12_CONNECTED_PIPELINE_20261025"

# Coverage declaration required by the gate. It is read from the retained sidecar;
# a payload without it is treated as unproven coverage, not as a full batch.
REQUIRED_SIDECAR_KEYS = ("rows", "price_basis", "gap_start", "gap_end")


class PipelineStop(RuntimeError):
    """A gate refused the batch. Nothing downstream may run."""

    def __init__(self, stage: str, code: str, detail: Dict[str, Any]):
        super().__init__(f"{stage}/{code}: {json.dumps(detail, ensure_ascii=False, default=str)[:400]}")
        self.stage = stage
        self.code = code
        self.detail = detail


def sha256(path: Optional[str]) -> Optional[str]:
    if not path or not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- transport
@dataclass
class Response:
    requested_date: str
    payload_date: Optional[str]
    frame: pd.DataFrame
    sidecar: Dict[str, Any]
    provenance: Dict[str, Any]
    factor: Optional[pd.DataFrame] = None
    tamper: Optional[str] = None


class LocalReplayTransport:
    """Reads retained batches. The only substituted component."""

    def __init__(self, raw_root: str = RAW_ROOT) -> None:
        self.domain = os.path.join(raw_root, "P2_stock_daily")
        self.factor_domain = os.path.join(raw_root, "P1_adjust_factor")

    def _find(self, domain: str, token: str) -> str:
        hits = [os.path.join(domain, n) for n in os.listdir(domain)
                if n.endswith(".parquet") and token in n]
        if not hits:
            raise FileNotFoundError(f"no retained batch token={token} under {domain}")
        return sorted(hits)[-1]

    def fetch(self, day: str, tamper: Optional[str] = None) -> Response:
        token = day.replace("-", "")
        path = self._find(self.domain, f"gap_{token}")
        raw = pq.ParquetFile(path).read().to_pandas()
        sidecar_path = path + ".sidecar.json"
        sidecar = json.load(open(sidecar_path, encoding="utf-8")) if os.path.exists(sidecar_path) else {}
        factor_path = self._find(self.factor_domain, f"incremental_{token}")
        factor = pq.ParquetFile(factor_path).read().to_pandas()
        frame = raw.copy()
        if tamper == "short_batch":
            frame = frame.iloc[: max(1, len(frame) // 20)].copy()
        if tamper == "malformed_date":
            frame["time"] = pd.to_datetime(frame["time"]).dt.normalize() + pd.Timedelta(days=1)
        if tamper == "missing_coverage":
            sidecar = {k: v for k, v in sidecar.items() if k not in REQUIRED_SIDECAR_KEYS}
        if tamper == "wrong_index":
            frame["time"] = "not-a-date"
        return Response(
            requested_date=day,
            payload_date=str(pd.to_datetime(raw["time"]).dt.normalize().max().date())
            if len(raw) else None,
            frame=frame,
            sidecar=sidecar,
            provenance={
                "batch": path, "batch_sha256": sha256(path),
                "sidecar": sidecar_path if os.path.exists(sidecar_path) else None,
                "sidecar_sha256": sha256(sidecar_path) if os.path.exists(sidecar_path) else None,
                "factor_batch": factor_path, "factor_sha256": sha256(factor_path),
                "tamper": tamper,
            },
            factor=factor,
            tamper=tamper,
        )


# --------------------------------------------------------------------------- gate
def response_gate(resp: Response, expected_rows_band: Tuple[int, int]) -> Dict[str, Any]:
    rec: Dict[str, Any] = {"requested_date": resp.requested_date,
                           "payload_date": resp.payload_date, "checks": {}}
    if resp.payload_date != resp.requested_date:
        raise PipelineStop("RESPONSE_GATE", "PAYLOAD_DATE_MISMATCH",
                           {"requested": resp.requested_date, "payload": resp.payload_date})
    rec["checks"]["payload_date_matches_request"] = True

    missing = [k for k in REQUIRED_SIDECAR_KEYS if k not in resp.sidecar]
    if missing:
        raise PipelineStop("RESPONSE_GATE", "COVERAGE_UNPROVEN",
                           {"missing_sidecar_keys": missing,
                            "note": "no coverage declaration -> the batch may not be merged"})
    rec["checks"]["coverage_declared"] = True
    if (resp.sidecar.get("gap_start"), resp.sidecar.get("gap_end")) != (
        resp.requested_date, resp.requested_date
    ):
        raise PipelineStop("RESPONSE_GATE", "COVERAGE_INTERVAL_MISMATCH",
                           {"gap_start": resp.sidecar.get("gap_start"),
                            "gap_end": resp.sidecar.get("gap_end"),
                            "requested": resp.requested_date})
    rec["checks"]["coverage_interval_matches_request"] = True
    rec["sidecar_batch_identity"] = {
        "declared_file_sha256": resp.sidecar.get("file_sha256"),
        "actual_batch_sha256": resp.provenance.get("batch_sha256"),
        "sidecar_points_to_same_batch": resp.sidecar.get("file_sha256")
        == resp.provenance.get("batch_sha256"),
        "note": "a retained sidecar may describe an earlier build of the same day; "
                "recorded, not used to rewrite the payload",
    }

    side_rows = resp.sidecar.get("rows")
    if side_rows is not None and int(side_rows) != int(len(resp.frame)):
        raise PipelineStop("RESPONSE_GATE", "SIDECAR_ROW_MISMATCH",
                           {"sidecar_rows": side_rows, "payload_rows": int(len(resp.frame))})
    rec["checks"]["sidecar_rows_match_payload"] = True

    n = int(len(resp.frame))
    lo, hi = expected_rows_band
    if not (lo <= n <= hi):
        raise PipelineStop("RESPONSE_GATE", "SHORT_OR_OVERSIZED_BATCH",
                           {"rows": n, "expected_band": [lo, hi]})
    rec["checks"]["row_band_ok"] = True

    try:
        times = pd.to_datetime(resp.frame["time"]).dt.normalize()
    except Exception as exc:  # noqa: BLE001
        raise PipelineStop("RESPONSE_GATE", "INDEX_DATE_UNPARSEABLE", {"error": str(exc)}) from exc
    distinct = sorted({str(d.date()) for d in times.dropna().unique()})
    if distinct != [resp.requested_date]:
        raise PipelineStop("RESPONSE_GATE", "INDEX_DATE_NOT_PRESERVED",
                           {"distinct_dates": distinct[:5], "requested": resp.requested_date})
    rec["checks"]["index_date_survives_serialization"] = True
    rec["rows"] = n
    return rec


# --------------------------------------------------------------------------- cleaning
def clean_and_antileak(resp: Response) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    df = resp.frame.copy()
    checks: Dict[str, Any] = {"input_rows": int(len(df)),
                              "input_columns": list(df.columns)}
    try:
        df["date"] = pd.to_datetime(df["time"]).dt.normalize()
    except Exception as exc:  # noqa: BLE001
        raise PipelineStop("CLEANING", "DATE_COERCE_FAILED", {"error": str(exc)}) from exc
    df["code"] = df["code"].astype(str)
    for col in ("open", "high", "low", "close", "volume", "money"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    checks["anti_leak_max_date"] = str(df["date"].max().date())
    checks["rows_outside_batch_day"] = int((df["date"] != pd.Timestamp(resp.requested_date)).sum())
    if checks["rows_outside_batch_day"]:
        raise PipelineStop("ANTI_LEAK", "FUTURE_OR_FOREIGN_DATE_IN_BATCH",
                           {"rows": checks["rows_outside_batch_day"],
                            "max_date": checks["anti_leak_max_date"]})
    checks["anti_leak_ok"] = True

    checks["duplicate_rows"] = int(df.duplicated(["date", "code"]).sum())
    df = df.drop_duplicates(["date", "code"], keep="last")

    ohlc_bad = ((df["high"] < df[["open", "close"]].max(axis=1))
                | (df["low"] > df[["open", "close"]].min(axis=1))
                | (df["low"] > df["high"]))
    checks["ohlc_inconsistent_rows"] = int(ohlc_bad.sum())
    df = df[~ohlc_bad]

    checks["null_price_rows"] = int(df[["open", "high", "low", "close"]].isna().any(axis=1).sum())
    df = df[~df[["open", "high", "low", "close"]].isna().any(axis=1)]

    checks["nonpositive_price_rows"] = int((df[["open", "high", "low", "close"]] <= 0).any(axis=1).sum())
    df = df[~((df[["open", "high", "low", "close"]] <= 0).any(axis=1))]

    checks["clean_rows"] = int(len(df))
    checks["clean_codes"] = int(df["code"].nunique())

    # factor contract: the factor plane must carry code+factor. A physical `fq`
    # column is NOT required by this contract, so its absence is not a violation.
    factor = resp.factor if resp.factor is not None else pd.DataFrame()
    required = ["code", "factor"]
    missing_required = [c for c in required if c not in factor.columns]
    if missing_required:
        raise PipelineStop("FACTOR_REFRESH", "FACTOR_CONTRACT_COLUMNS_MISSING",
                           {"missing": missing_required, "present": list(factor.columns)[:12]})
    checks["factor_contract"] = {
        "required_columns": required,
        "missing": [],
        "fq_column_required": False,
        "fq_column_present": "fq" in factor.columns,
        "note": "physical fq-column absence is not a contract violation",
        "factor_rows": int(len(factor)),
    }

    df["signal_date"] = df["date"]
    df["data_date"] = df["date"]
    df["asset_type"] = "STOCK"
    df["price_adj_tag"] = "RAW_NONE"
    df["asof_rule"] = "SAME_DAY_KNOWN_EOD"
    df["pit_status"] = "OK"
    df["source_version"] = SOURCE_VERSION
    df["known_at"] = pd.NaT
    return df[PRICE_COLUMNS + META_COLUMNS], checks


# --------------------------------------------------------------------------- accumulator
def _load_current_year() -> pd.DataFrame:
    files = []
    for dp, _dn, fn in os.walk(os.path.join(CACHE_RELEASE_ROOT, PRODUCT)):
        if "year=2026" in dp:
            files += [os.path.join(dp, f) for f in fn if f.endswith(".parquet")]
    if not files:
        raise SystemExit("no CURRENT year=2026 partition")
    df = pd.concat([pq.ParquetFile(f).read().to_pandas() for f in sorted(files)], ignore_index=True)
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    for col in META_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NaT if col == "known_at" else ""
    return df[PRICE_COLUMNS + META_COLUMNS]


def _ensure_seeded() -> Dict[str, Any]:
    """Seed the candidate accumulator from CURRENT once (never re-seeded)."""
    if os.path.exists(CHECKPOINT):
        return json.load(open(CHECKPOINT, encoding="utf-8"))
    os.makedirs(os.path.dirname(ACCUM_PART), exist_ok=True)
    base = _load_current_year()
    # The two recovery days are the *gap*; drop whatever placeholder CURRENT has so
    # the pipeline is the only source of those days.
    base = base[~base["date"].isin([pd.Timestamp(d) for d in RECOVERY_DAYS])]
    base = base.sort_values(["date", "code"]).reset_index(drop=True)
    base.to_parquet(ACCUM_PART, index=False)
    cp = {
        "schema": "R12_CANDIDATE_CHECKPOINT_1",
        "product": PRODUCT,
        "seed": {
            "from": os.path.join(CACHE_RELEASE_ROOT, PRODUCT),
            "rows": int(len(base)),
            "date_min": str(base["date"].min().date()),
            "date_max": str(base["date"].max().date()),
            "sha256": sha256(ACCUM_PART),
        },
        "committed_days": [],
        "updated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    _write_json(CHECKPOINT, cp)
    return cp


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _publish_pair(cp: Dict[str, Any]) -> Dict[str, Any]:
    """Candidate-only publication. Two sequential replaces are not a transaction."""
    pointer = {
        "schema": "R12_CANDIDATE_POINTER_1",
        "product": PRODUCT,
        "partition": ACCUM_PART,
        "partition_sha256": sha256(ACCUM_PART),
        "rows": cp["seed"]["rows"] + sum(d["rows_added"] for d in cp["committed_days"]),
        "committed_days": [d["day"] for d in cp["committed_days"]],
        "is_candidate": True,
        "CURRENT_SWITCH_ALLOWED": False,
        "published_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    registry = {
        "schema": "R12_CANDIDATE_REGISTRY_1",
        "products": {PRODUCT: {"pointer": POINTER, "partition_sha256": pointer["partition_sha256"]}},
    }
    _write_json(POINTER, pointer)
    _write_json(REGISTRY, registry)

    # paired-registry consistency check (read back both, compare the hash)
    p = json.load(open(POINTER, encoding="utf-8"))
    r = json.load(open(REGISTRY, encoding="utf-8"))
    consistent = (
        r["products"][PRODUCT]["partition_sha256"] == p["partition_sha256"]
        == sha256(ACCUM_PART)
    )
    return {"pointer": POINTER, "registry": REGISTRY, "paired_registry_consistent": bool(consistent),
            "atomicity_note": "two sequential os.replace calls; not a multi-file transaction",
            "current_pointer_touched": False}


# --------------------------------------------------------------------------- one day
def run_day(day: str, tamper: Optional[str] = None,
            expected_band: Tuple[int, int] = (4000, 7000)) -> Dict[str, Any]:
    log: Dict[str, Any] = {"day": day, "tamper": tamper, "stages": {}}
    transport = LocalReplayTransport()
    resp = transport.fetch(day, tamper=tamper)
    log["provenance"] = resp.provenance

    log["stages"]["response_gate"] = response_gate(resp, expected_band)
    cleaned, checks = clean_and_antileak(resp)
    log["stages"]["cleaning_antileak"] = checks
    log["stages"]["factor_refresh"] = checks["factor_contract"]

    cp = json.load(open(CHECKPOINT, encoding="utf-8")) if os.path.exists(CHECKPOINT) else _ensure_seeded()
    already = [d for d in cp["committed_days"] if d["day"] == day]
    before_sha = sha256(ACCUM_PART)
    before_rows = int(pq.ParquetFile(ACCUM_PART).metadata.num_rows)

    accum = pq.ParquetFile(ACCUM_PART).read().to_pandas()
    accum["date"] = pd.to_datetime(accum["date"]).dt.normalize()
    had_day_rows = int((accum["date"] == pd.Timestamp(day)).sum())
    accum = accum[accum["date"] != pd.Timestamp(day)]
    merged = pd.concat([accum, cleaned], ignore_index=True)
    merged = merged.sort_values(["date", "code"]).reset_index(drop=True)

    dup = int(merged.duplicated(["date", "code"]).sum())
    if dup:
        raise PipelineStop("COMPILER", "DUPLICATE_KEYS_AFTER_MERGE", {"duplicates": dup})

    merged.to_parquet(ACCUM_PART, index=False)
    after_sha = sha256(ACCUM_PART)
    after_rows = int(len(merged))

    log["stages"]["compiler"] = {
        "rows_before": before_rows, "rows_after": after_rows,
        "rows_added": after_rows - before_rows,
        "partial_day_rows_replaced": had_day_rows,
        "partial_day_was_replaced_not_skipped": bool(had_day_rows > 0),
        "duplicate_keys_after_merge": dup,
        "sha_before": before_sha, "sha_after": after_sha,
        "idempotent_noop": bool(after_sha == before_sha and already),
    }

    if not already:
        cp["committed_days"] = [d for d in cp["committed_days"] if d["day"] != day]
        cp["committed_days"].append({
            "day": day,
            "rows_added": after_rows - before_rows,
            "rows_in_day": int((merged["date"] == pd.Timestamp(day)).sum()),
            "partition_sha256": after_sha,
            "batch_sha256": resp.provenance["batch_sha256"],
            "committed_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        })
        cp["committed_days"] = sorted(cp["committed_days"], key=lambda d: d["day"])
        cp["updated_at"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        _write_json(CHECKPOINT, cp)

    log["stages"]["publication"] = _publish_pair(cp)
    log["checkpoint"] = {
        "committed_days": [d["day"] for d in cp["committed_days"]],
        "resume_point": cp["committed_days"][-1]["day"] if cp["committed_days"] else None,
        "checkpoint_path": CHECKPOINT,
        "checkpoint_sha256": sha256(CHECKPOINT),
    }
    log["status"] = "COMMITTED" if not already else "IDEMPOTENT_REPLAY"
    return log


def _reset_pipeline() -> None:
    if os.path.isdir(PIPE_ROOT):
        shutil.rmtree(PIPE_ROOT)


def main() -> int:
    run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(RUN_LOG_DIR, run_id)
    os.makedirs(out_dir, exist_ok=True)
    _reset_pipeline()
    _ensure_seeded()

    receipts: Dict[str, Any] = {"run_id": run_id, "fresh_sequence": [], "idempotent_replay": [],
                               "negative_controls": [], "verdict": "UNKNOWN"}
    try:
        # 1) fresh sequence: 08-31, then checkpoint, then 09-01 (resume)
        for day in RECOVERY_DAYS:
            receipts["fresh_sequence"].append(run_day(day))
        cp1 = json.load(open(CHECKPOINT, encoding="utf-8"))
        sha_after_first_pass = sha256(ACCUM_PART)

        # 2) idempotent replay of the same retained inputs
        for day in RECOVERY_DAYS:
            receipts["idempotent_replay"].append(run_day(day))
        sha_after_replay = sha256(ACCUM_PART)

        # 3) negative controls; each must stop before merge and leave the candidate intact
        for tamper, expected in (
            ("short_batch", {"SHORT_OR_OVERSIZED_BATCH", "SIDECAR_ROW_MISMATCH"}),
            ("malformed_date", {"PAYLOAD_DATE_MISMATCH", "INDEX_DATE_NOT_PRESERVED"}),
            ("missing_coverage", {"COVERAGE_UNPROVEN"}),
            ("wrong_index", {"INDEX_DATE_UNPARSEABLE"}),
        ):
            sha_before = sha256(ACCUM_PART)
            entry = {"tamper": tamper, "expected_stop": sorted(expected)}
            try:
                run_day("2026-09-01", tamper=tamper)
                entry.update({"stopped": False, "result": "NOT_STOPPED"})
            except PipelineStop as stop:
                entry.update({
                    "stopped": True,
                    "stage": stop.stage,
                    "code": stop.code,
                    "code_matches_expected": stop.code in expected,
                    "partition_unchanged": sha256(ACCUM_PART) == sha_before,
                    "detail": stop.detail,
                })
            receipts["negative_controls"].append(entry)

        # 3b) an existing PARTIAL day must be replaced, not silently skipped
        receipts["partial_day_control"] = _partial_day_control()

        cp2 = json.load(open(CHECKPOINT, encoding="utf-8"))
        validator = _validate(receipts, cp1, cp2, sha_after_first_pass, sha_after_replay)
        receipts.update(validator)
        with open(os.path.join(out_dir, "pipeline_receipts.json"), "w", encoding="utf-8") as fh:
            json.dump(receipts, fh, ensure_ascii=False, indent=2, default=str)
        with open(REPORT, "w", encoding="utf-8") as fh:
            json.dump({
                "artifact": "CONNECTED_PIPELINE",
                "deliverable": "D3_CONNECTED_UPDATE_CLEANING_CANDIDATE",
                "run_id": run_id,
                "transport": "LocalReplayTransport over retained RAW batch + sidecar + factor increment",
                "stages": ["response_gate", "cleaning_antileak", "factor_refresh", "compiler",
                           "candidate_checkpoint", "isolated_publication"],
                "receipts": receipts,
                "outputs": {"partition": ACCUM_PART, "pointer": POINTER,
                            "registry": REGISTRY, "checkpoint": CHECKPOINT},
                "flags": {
                    "NEW_DATA_ACQUISITION_AUTHORIZED": False,
                    "CURRENT_SWITCH_ALLOWED": False,
                    "ORDER_ALLOWED": False,
                    "PRODUCTION_PUBLISH_CALLED": False,
                    "CURRENT_POINTER_TOUCHED": False,
                },
                "limitations": [
                    "external transport replaced by a local replay reader (declared)",
                    "two os.replace calls are not a multi-file transaction",
                    "no supplier call, so supplier-side completeness remains unproven",
                ],
            }, fh, ensure_ascii=False, indent=2, default=str)
        print(json.dumps({k: receipts[k] for k in ("verdict", "all_controls_passed",
                                                   "idempotent", "resume_evidence")}, ensure_ascii=False))
        return 0 if receipts["verdict"] == "PASS" else 1
    except PipelineStop as stop:
        receipts["verdict"] = f"BLOCKED_{stop.stage}_{stop.code}"
        with open(os.path.join(out_dir, "pipeline_receipts.json"), "w", encoding="utf-8") as fh:
            json.dump(receipts, fh, ensure_ascii=False, indent=2, default=str)
        print(json.dumps({"verdict": receipts["verdict"], "detail": stop.detail}, ensure_ascii=False))
        return 1


def _partial_day_control() -> Dict[str, Any]:
    """An existing partial day must be replaced by the full batch, not skipped."""
    day = "2026-09-01"
    cp = json.load(open(CHECKPOINT, encoding="utf-8"))
    accum = pq.ParquetFile(ACCUM_PART).read().to_pandas()
    accum["date"] = pd.to_datetime(accum["date"]).dt.normalize()
    keep = accum[accum["date"] != pd.Timestamp(day)]
    full_day = accum[accum["date"] == pd.Timestamp(day)]
    partial = full_day.head(200)
    injected = pd.concat([keep, partial], ignore_index=True)
    injected.to_parquet(ACCUM_PART, index=False)
    cp["committed_days"] = [d for d in cp["committed_days"] if d["day"] != day]
    _write_json(CHECKPOINT, cp)

    row = run_day(day)
    after = pq.ParquetFile(ACCUM_PART).read().to_pandas()
    after["date"] = pd.to_datetime(after["date"]).dt.normalize()
    day_rows = int((after["date"] == pd.Timestamp(day)).sum())
    return {
        "injected_rows": int(len(partial)),
        "rows_after_rerun": day_rows,
        "expected_full_rows": int(len(full_day)),
        "replaced_not_skipped": bool(
            day_rows == len(full_day) and row["stages"]["compiler"]["partial_day_rows_replaced"] == len(partial)
        ),
        "compiler": row["stages"]["compiler"],
        "duplicate_keys": int(after.duplicated(["date", "code"]).sum()),
    }


def _validate(receipts, cp1, cp2, sha_first, sha_replay) -> Dict[str, Any]:
    seq = receipts["fresh_sequence"]
    controls = receipts["negative_controls"]
    all_controls = all(c.get("stopped") and c.get("code_matches_expected")
                       and c.get("partition_unchanged") for c in controls)
    partial_ok = bool((receipts.get("partial_day_control") or {}).get("replaced_not_skipped"))
    idempotent = sha_first == sha_replay and all(
        r["stages"]["compiler"]["idempotent_noop"] for r in receipts["idempotent_replay"]
    )
    no_dup = all(r["stages"]["compiler"]["duplicate_keys_after_merge"] == 0 for r in seq)
    resume = {
        "committed_after_first_pass": [d["day"] for d in cp1["committed_days"]],
        "committed_after_replay": [d["day"] for d in cp2["committed_days"]],
        "no_duplicate_commit_entries": len(cp2["committed_days"]) == len(cp1["committed_days"]),
    }
    ok = bool(all_controls and idempotent and no_dup and resume["no_duplicate_commit_entries"]
              and partial_ok and len(cp2["committed_days"]) == len(RECOVERY_DAYS))
    return {
        "verdict": "PASS" if ok else "FAIL",
        "all_controls_passed": all_controls,
        "partial_day_replaced_not_skipped": partial_ok,
        "idempotent": idempotent,
        "no_duplicate_keys": no_dup,
        "resume_evidence": resume,
        "partition_sha_after_first_pass": sha_first,
        "partition_sha_after_replay": sha_replay,
    }


if __name__ == "__main__":
    raise SystemExit(main())
