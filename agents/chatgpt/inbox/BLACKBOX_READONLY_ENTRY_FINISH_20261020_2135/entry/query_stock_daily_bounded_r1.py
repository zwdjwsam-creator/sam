# -*- coding: utf-8 -*-
"""Independent bounded STOCK_DAILY_PIT_R1 readonly query entry (V4 + 2135 finish).

Uses ONLY runtime_v4 under this READONLY_QUERY tree.
Filter pushes code+date into pyarrow dataset before DataFrame materialization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

ENTRY_ROOT = Path(__file__).resolve().parent
RUNTIME = ENTRY_ROOT / "runtime_v4"
EXPECTED_SHA = {
    "blackbox_data_coverage_common_r1.py": "0c018fb5f4cd31fc6fc05d783bf66f7bc54503e5464825259c462682fb980769",
    "blackbox_cache_coverage_non_regression_gate_r1.py": "98faa2945ff9b056936ac87b5e39be87a1adf618120805c2f96e269169798fd3",
    "blackbox_data_access_resolver_r1.py": "5d232abbded4043426a51b57b45afa3d799152c368f7b235a4fff2d9cb26c8d6",
}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _configure_stdio_utf8() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="strict")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8", errors="strict")  # type: ignore[attr-defined]
    except Exception:
        pass


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _emit(obj: dict, code: int) -> int:
    text = json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n"
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.flush()
    return code


def _parse_iso_date(s: str, field: str) -> date:
    if not s or not ISO_DATE.match(s):
        raise ValueError(f"INVALID_ISO_DATE:{field}:{s!r}")
    try:
        return date.fromisoformat(s)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"INVALID_ISO_DATE:{field}:{s!r}:{exc}") from exc


def _verify_runtime(*, require_packages: bool) -> dict:
    files = {}
    for name, exp in EXPECTED_SHA.items():
        fp = RUNTIME / name
        if not fp.is_file():
            raise RuntimeError(f"MISSING_RUNTIME:{name}")
        got = _sha(fp)
        files[name] = {"path": str(fp.resolve()), "sha256": got, "match": got == exp}
        if got != exp:
            raise RuntimeError(f"RUNTIME_SHA_MISMATCH:{name}")

    sys.path = [str(RUNTIME)] + [
        p for p in sys.path if Path(p).resolve() != Path(r"E:\BLACKBOX\脚本").resolve()
    ]
    import blackbox_data_access_resolver_r1 as resolver
    import blackbox_data_coverage_common_r1 as common

    resolver_path = Path(resolver.__file__).resolve()
    common_path = Path(common.__file__).resolve()
    runtime_res = RUNTIME.resolve()
    if resolver_path.parent != runtime_res or common_path.parent != runtime_res:
        raise RuntimeError(
            f"MODULE_PATH_NOT_RUNTIME_V4:resolver={resolver_path};common={common_path};want={runtime_res}"
        )
    resolver_sha = _sha(resolver_path)
    common_sha = _sha(common_path)
    if resolver_sha != EXPECTED_SHA["blackbox_data_access_resolver_r1.py"]:
        raise RuntimeError("LOADED_RESOLVER_SHA_MISMATCH")
    if common_sha != EXPECTED_SHA["blackbox_data_coverage_common_r1.py"]:
        raise RuntimeError("LOADED_COMMON_SHA_MISMATCH")

    out: dict = {
        "interpreter": sys.executable,
        "python_version": sys.version,
        "is_64bit": sys.maxsize > 2**32,
        "runtime_dir": str(runtime_res),
        "files": files,
        "resolver_file": str(resolver_path),
        "common_file": str(common_path),
        "resolver_sha256": resolver_sha,
        "common_sha256": common_sha,
        "modules": {"resolver": resolver, "common": common},
    }
    try:
        import pandas as pd
        import pyarrow as pa

        out["pandas_version"] = pd.__version__
        out["pyarrow_version"] = pa.__version__
    except Exception as exc:  # noqa: BLE001
        out["package_error"] = f"{type(exc).__name__}:{exc}"
        if require_packages:
            raise RuntimeError(f"REQUIRED_PACKAGE_MISSING:{out['package_error']}") from exc
    return out


def _snapshot_current(resolver) -> dict:
    cur = resolver.read_currents()
    ptr = Path(r"E:\BLACKBOX\数据\回测缓存\CURRENT_CACHE_RELEASE.json")
    return {
        "authority_ready": bool(cur.get("authority_ready")),
        "cache_release_id": cur.get("cache_release_id"),
        "cache_release_root": cur.get("cache_release_root"),
        "cache_asof": cur.get("cache_asof"),
        "pointer_path": str(ptr),
        "pointer_sha256": _sha(ptr) if ptr.is_file() else None,
        "errors": cur.get("errors"),
        "currents": cur,
    }


def _same_current(a: dict, b: dict) -> bool:
    keys = ("authority_ready", "cache_release_id", "cache_release_root", "cache_asof", "pointer_sha256")
    return all(a.get(k) == b.get(k) for k in keys) and bool(a.get("authority_ready")) and bool(b.get("authority_ready"))


def _read_rows(product_path: Path, code: str, start: str, end: str) -> dict:
    import pyarrow as pa
    import pyarrow.dataset as ds

    cols = [
        "date",
        "code",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "money",
        "known_at",
        "price_adj_tag",
        "pit_status",
        "asof_rule",
        "signal_date",
        "data_date",
    ]
    t0 = time.perf_counter()
    dataset = ds.dataset(str(product_path), format="parquet", partitioning="hive")
    schema = dataset.schema
    date_type = schema.field("date").type
    use_cols = [c for c in cols if c in schema.names]
    start_ts = pa.scalar(f"{start}T00:00:00").cast(date_type)
    end_ts = pa.scalar(f"{end}T00:00:00").cast(date_type)
    filt = (
        (ds.field("code") == code)
        & (ds.field("date") >= start_ts)
        & (ds.field("date") <= end_ts)
    )
    filter_expr = f"(code == {code!r}) & (date >= {start!r}) & (date <= {end!r}) [cast date->{date_type}]"
    table = dataset.to_table(filter=filt, columns=use_cols)
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 3)
    rows = table.to_pylist()
    # normalize date to ISO string for JSON
    for r in rows:
        d = r.get("date")
        if hasattr(d, "isoformat"):
            r["date"] = d.isoformat()[:10]
        elif d is not None:
            r["date"] = str(d)[:10]
    rows.sort(key=lambda r: (str(r.get("date")), str(r.get("code"))))
    dates = sorted({str(r.get("date"))[:10] for r in rows if r.get("date")})
    # year partitions touched (hive)
    years = _years(start, end)
    files_used = []
    for y in years:
        yd = product_path / f"year={y}"
        if yd.is_dir():
            files_used.extend(str(p) for p in sorted(yd.glob("*.parquet")))
    return {
        "rows": rows,
        "row_count": len(rows),
        "dates": dates,
        "files_used": files_used,
        "projected_columns": use_cols,
        "filter_expression": filter_expr,
        "date_column_type": str(date_type),
        "query_elapsed_ms": elapsed_ms,
        "materialization": "pyarrow.dataset.to_table(filter=code+date, columns=projected) — no full-year DataFrame first",
    }


def _years(start: str, end: str) -> list[int]:
    y0, y1 = int(start[:4]), int(end[:4])
    if y1 < y0:
        y0, y1 = y1, y0
    return list(range(y0, y1 + 1))


def main() -> int:
    _configure_stdio_utf8()
    ap = argparse.ArgumentParser(description="Bounded readonly STOCK_DAILY_PIT_R1 query (V4/2135)")
    ap.add_argument("--code", required=False)
    ap.add_argument("--start-date", required=False)
    ap.add_argument("--end-date", required=False)
    ap.add_argument("--product", default="STOCK_DAILY_PIT_R1")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()

    try:
        meta = _verify_runtime(require_packages=True)
    except Exception as exc:  # noqa: BLE001
        return _emit({"ok": False, "error": str(exc), "mode": "RUNTIME_VERIFY"}, 2)

    resolver = meta["modules"]["resolver"]
    common = meta["modules"]["common"]
    printable = {k: v for k, v in meta.items() if k != "modules"}

    if args.self_check:
        if printable.get("package_error"):
            return _emit({"ok": False, "mode": "SELF_CHECK", "error": printable["package_error"], **printable}, 2)
        return _emit({"ok": True, "mode": "SELF_CHECK", **printable}, 0)

    if args.product != "STOCK_DAILY_PIT_R1":
        return _emit(
            {
                "ok": False,
                "error": "UNSUPPORTED_PRODUCT_FOR_ENTRY",
                "product": args.product,
                "note": "首版仅 STOCK_DAILY_PIT_R1",
                **printable,
            },
            2,
        )

    if not args.code:
        return _emit(
            {"ok": False, "error": "MISSING_CODE", "note": "需要 --code", **printable},
            2,
        )
    if not args.start_date or not args.end_date:
        return _emit(
            {
                "ok": False,
                "error": "BOUNDED_WINDOW_REQUIRES_CODE_AND_BOTH_ENDPOINTS",
                "note": "需要 --code --start-date --end-date（ISO YYYY-MM-DD）",
                **printable,
            },
            2,
        )

    try:
        d0 = _parse_iso_date(args.start_date, "start-date")
        d1 = _parse_iso_date(args.end_date, "end-date")
    except ValueError as exc:
        return _emit({"ok": False, "error": str(exc), **printable}, 2)
    if d1 < d0:
        return _emit({"ok": False, "error": "END_DATE_BEFORE_START_DATE", **printable}, 2)
    start = d0.isoformat()
    end = d1.isoformat()

    snap0 = _snapshot_current(resolver)
    if not snap0["authority_ready"]:
        return _emit({"ok": False, "error": "AUTHORITY_NOT_READY", "errors": snap0.get("errors"), **printable}, 2)

    currents = snap0["currents"]
    currents["_request_start_date"] = start
    currents["_request_end_date"] = end
    if hasattr(common, "set_expected_range_authority"):
        common.set_expected_range_authority("STOCK_DAILY_PIT_R1", None)

    try:
        resolved = resolver.resolve_product(args.product, currents.get("cache_asof"), None, currents)
    except Exception as exc:  # noqa: BLE001
        return _emit(
            {
                "ok": False,
                "error": f"RESOLVE_EXCEPTION:{type(exc).__name__}:{exc}",
                "coverage_error": currents.get("_coverage_error"),
                **printable,
            },
            2,
        )

    snap1 = _snapshot_current(resolver)
    if not _same_current(snap0, snap1):
        return _emit(
            {
                "ok": False,
                "error": "CURRENT_RELEASE_CHANGED_MID_REQUEST",
                "before": {k: snap0[k] for k in ("cache_release_id", "cache_release_root", "pointer_sha256")},
                "after": {k: snap1[k] for k in ("cache_release_id", "cache_release_root", "pointer_sha256")},
                **printable,
            },
            2,
        )

    if not resolved.get("coverage_ready") or resolved.get("coverage_scope") != "BOUNDED_WINDOW_VERIFIED":
        return _emit(
            {
                "ok": False,
                "error": "COVERAGE_GATE_REJECT",
                "coverage_ready": resolved.get("coverage_ready"),
                "coverage_scope": resolved.get("coverage_scope"),
                "coverage_scope_note": resolved.get("coverage_scope_note"),
                "coverage_mode": resolved.get("coverage_mode"),
                "full_history_status": resolved.get("full_history_status"),
                "missing_trade_days": resolved.get("missing_trade_days"),
                "coverage_error": currents.get("_coverage_error"),
                "note": "非全历史/非证券全量/非因果回测许可；门未过不读业务结果",
                "product_path": resolved.get("product_path"),
                **printable,
            },
            3,
        )

    product_path = Path(resolved["product_path"])
    try:
        data = _read_rows(product_path, args.code, start, end)
    except Exception as exc:  # noqa: BLE001
        return _emit({"ok": False, "error": f"READ_FAIL:{type(exc).__name__}:{exc}", **printable}, 2)

    # post-read CURRENT check
    snap2 = _snapshot_current(resolver)
    if not _same_current(snap0, snap2):
        return _emit(
            {
                "ok": False,
                "error": "CURRENT_CHANGED_DURING_ROW_READ",
                "before": {k: snap0[k] for k in ("cache_release_id", "cache_release_root", "pointer_sha256")},
                "after": {k: snap2[k] for k in ("cache_release_id", "cache_release_root", "pointer_sha256")},
                **printable,
            },
            2,
        )

    known_notes = []
    for r in data["rows"]:
        ka = r.get("known_at")
        if ka is None or ka == "" or str(ka).upper() in ("RAW_NONE", "NONE", "NAN"):
            known_notes.append("known_at_empty_or_RAW_NONE_preserved")
            break

    ok_rows = data["row_count"] > 0
    result = {
        "ok": ok_rows,
        "status": "OK_BOUNDED_ROWS" if ok_rows else "FILTER_NO_MATCH_ROWS",
        "note": (
            "产品日期覆盖通过≠单证券每天都有行；无行=本次过滤无匹配/需缺失门诊断，不自动下载。"
            "非因果回测许可；不做交易建议。"
        ),
        "product_id": args.product,
        "code": args.code,
        "request_start": start,
        "request_end": end,
        "cache_release_id": snap0["cache_release_id"],
        "cache_asof": snap0["cache_asof"],
        "product_path": str(product_path),
        "coverage_scope": resolved.get("coverage_scope"),
        "coverage_scope_note": resolved.get("coverage_scope_note"),
        "coverage_mode": resolved.get("coverage_mode"),
        "full_history_status": resolved.get("full_history_status"),
        "row_count": data["row_count"],
        "dates_present": data["dates"],
        "date_count": len(data["dates"]),
        "known_at_notes": known_notes,
        "projected_columns": data["projected_columns"],
        "filter_expression": data["filter_expression"],
        "date_column_type": data["date_column_type"],
        "query_elapsed_ms": data["query_elapsed_ms"],
        "materialization": data["materialization"],
        "rows": data["rows"],
        "files_used": data["files_used"],
        "runtime": printable,
    }
    return _emit(result, 0 if ok_rows else 4)


if __name__ == "__main__":
    raise SystemExit(main())
