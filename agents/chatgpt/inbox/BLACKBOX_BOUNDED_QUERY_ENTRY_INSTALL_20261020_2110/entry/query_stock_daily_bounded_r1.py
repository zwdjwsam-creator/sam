# -*- coding: utf-8 -*-
"""Independent bounded STOCK_DAILY_PIT_R1 readonly query entry (V4 logic).

Uses ONLY runtime_v4 candidate modules under this READONLY_QUERY tree.
Does NOT import E:\\BLACKBOX\\脚本 empty coverage stubs.
Not a full BLACKBOX restore. Not causal backtest license.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ENTRY_ROOT = Path(__file__).resolve().parent
RUNTIME = ENTRY_ROOT / "runtime_v4"
EXPECTED_SHA = {
    "blackbox_data_coverage_common_r1.py": "0c018fb5f4cd31fc6fc05d783bf66f7bc54503e5464825259c462682fb980769",
    "blackbox_cache_coverage_non_regression_gate_r1.py": "98faa2945ff9b056936ac87b5e39be87a1adf618120805c2f96e269169798fd3",
    "blackbox_data_access_resolver_r1.py": "5d232abbded4043426a51b57b45afa3d799152c368f7b235a4fff2d9cb26c8d6",
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _verify_runtime() -> dict:
    files = {}
    for name, exp in EXPECTED_SHA.items():
        fp = RUNTIME / name
        if not fp.is_file():
            raise SystemExit(json.dumps({"ok": False, "error": f"MISSING_RUNTIME:{name}"}, ensure_ascii=False))
        got = _sha(fp)
        files[name] = {"path": str(fp), "sha256": got, "match": got == exp}
        if got != exp:
            raise SystemExit(
                json.dumps({"ok": False, "error": "RUNTIME_SHA_MISMATCH", "file": name, "got": got, "exp": exp}, ensure_ascii=False)
            )
    # Prefer runtime_v4 over E:\\BLACKBOX\\脚本
    sys.path = [str(RUNTIME)] + [p for p in sys.path if Path(p).resolve() != Path(r"E:\BLACKBOX\脚本").resolve()]
    import blackbox_data_access_resolver_r1 as resolver
    import blackbox_data_coverage_common_r1 as common

    return {
        "interpreter": sys.executable,
        "python_version": sys.version,
        "is_64bit": sys.maxsize > 2**32,
        "runtime_dir": str(RUNTIME),
        "files": files,
        "resolver_file": resolver.__file__,
        "common_file": common.__file__,
        "resolver_sha256": _sha(Path(resolver.__file__)),
        "common_sha256": _sha(Path(common.__file__)),
        "modules": {"resolver": resolver, "common": common},
    }


def _years(start: str, end: str) -> list[int]:
    y0, y1 = int(start[:4]), int(end[:4])
    if y1 < y0:
        y0, y1 = y1, y0
    return list(range(y0, y1 + 1))


def _read_rows(product_path: Path, code: str, start: str, end: str) -> dict:
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

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
    tables = []
    files_used = []
    for y in _years(start, end):
        yd = product_path / f"year={y}"
        if not yd.is_dir():
            continue
        for fp in sorted(yd.glob("*.parquet")):
            files_used.append(str(fp))
            pf = pq.ParquetFile(fp)
            names = set(pf.schema_arrow.names)
            use_cols = [c for c in cols if c in names]
            # column projection; filter in-memory on projected table (avoid full schema load)
            t = pf.read(columns=use_cols)
            if "code" not in t.column_names or "date" not in t.column_names:
                raise ValueError(f"DATE_OR_CODE_COLUMN_MISSING:{fp.name}")
            # normalize date to string YYYY-MM-DD for filter
            dcol = t.column("date")
            # cast via pandas for mixed types safety on this product
            import pandas as pd

            df = t.to_pandas()
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
            df = df[(df["code"] == code) & (df["date"] >= start) & (df["date"] <= end)]
            if not df.empty:
                tables.append(pa.Table.from_pandas(df, preserve_index=False))
    if not tables:
        return {"rows": [], "row_count": 0, "files_used": files_used, "dates": []}
    out = pa.concat_tables(tables, promote_options="default").to_pylist()
    # stable sort
    out.sort(key=lambda r: (str(r.get("date")), str(r.get("code"))))
    dates = sorted({str(r.get("date"))[:10] for r in out if r.get("date")})
    return {"rows": out, "row_count": len(out), "files_used": files_used, "dates": dates}


def main() -> int:
    ap = argparse.ArgumentParser(description="Bounded readonly STOCK_DAILY_PIT_R1 query (V4)")
    ap.add_argument("--code", required=False, help="Security code e.g. 000001.XSHE")
    ap.add_argument("--start-date", required=False)
    ap.add_argument("--end-date", required=False)
    ap.add_argument("--product", default="STOCK_DAILY_PIT_R1")
    ap.add_argument("--self-check", action="store_true", help="Print runtime SHA/interpreter and exit 0")
    args = ap.parse_args()

    meta = _verify_runtime()
    resolver = meta["modules"]["resolver"]
    common = meta["modules"]["common"]
    # strip modules from printable meta
    printable = {k: v for k, v in meta.items() if k != "modules"}
    try:
        import pandas as pd
        import pyarrow as pa

        printable["pandas_version"] = pd.__version__
        printable["pyarrow_version"] = pa.__version__
    except Exception as e:  # noqa: BLE001
        printable["package_error"] = str(e)

    if args.self_check:
        print(json.dumps({"ok": True, "mode": "SELF_CHECK", **printable}, ensure_ascii=False, indent=2))
        return 0

    if args.product != "STOCK_DAILY_PIT_R1":
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "UNSUPPORTED_PRODUCT_FOR_ENTRY",
                    "product": args.product,
                    "note": "首版仅 STOCK_DAILY_PIT_R1",
                    **printable,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    if not args.code or not args.start_date or not args.end_date:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "BOUNDED_WINDOW_REQUIRES_CODE_AND_BOTH_ENDPOINTS",
                    "note": "需要 --code --start-date --end-date",
                    **printable,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    # Fresh CURRENT snapshot every request
    currents = resolver.read_currents()
    if not currents.get("authority_ready"):
        print(json.dumps({"ok": False, "error": "AUTHORITY_NOT_READY", "errors": currents.get("errors"), **printable}, ensure_ascii=False, indent=2))
        return 2

    release_id_before = currents.get("cache_release_id")
    root_before = currents.get("cache_release_root")
    currents["_request_start_date"] = args.start_date
    currents["_request_end_date"] = args.end_date

    # Ensure no fixture authority injection for FULL_HISTORY
    if hasattr(common, "set_expected_range_authority"):
        common.set_expected_range_authority("STOCK_DAILY_PIT_R1", None)

    try:
        resolved = resolver.resolve_product(args.product, currents.get("cache_asof"), None, currents)
    except Exception as e:  # noqa: BLE001
        print(
            json.dumps(
                {"ok": False, "error": f"RESOLVE_EXCEPTION:{type(e).__name__}:{e}", "coverage_error": currents.get("_coverage_error"), **printable},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    # Re-read CURRENT tip; refuse mixed releases
    currents2 = resolver.read_currents()
    if currents2.get("cache_release_id") != release_id_before or currents2.get("cache_release_root") != root_before:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "CURRENT_RELEASE_CHANGED_MID_REQUEST",
                    "before": {"id": release_id_before, "root": root_before},
                    "after": {"id": currents2.get("cache_release_id"), "root": currents2.get("cache_release_root")},
                    **printable,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    if not resolved.get("coverage_ready") or resolved.get("coverage_scope") != "BOUNDED_WINDOW_VERIFIED":
        print(
            json.dumps(
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
                    **printable,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 3

    product_path = Path(resolved["product_path"])
    try:
        data = _read_rows(product_path, args.code, args.start_date, args.end_date)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": f"READ_FAIL:{type(e).__name__}:{e}", **printable}, ensure_ascii=False, indent=2))
        return 2

    # known_at empty/RAW_NONE preserved
    sample = data["rows"][:3]
    known_notes = []
    for r in data["rows"]:
        ka = r.get("known_at")
        if ka is None or ka == "" or str(ka).upper() in ("RAW_NONE", "NONE", "NAN"):
            known_notes.append("known_at_empty_or_RAW_NONE_preserved")
            break

    result = {
        "ok": True if data["row_count"] > 0 else False,
        "status": "OK_BOUNDED_ROWS" if data["row_count"] > 0 else "FILTER_NO_MATCH_ROWS",
        "note": (
            "产品日期覆盖通过≠单证券每天都有行；无行=本次过滤无匹配/需缺失门诊断，不自动下载。"
            "非因果回测许可；不做交易建议。"
        ),
        "product_id": args.product,
        "code": args.code,
        "request_start": args.start_date,
        "request_end": args.end_date,
        "cache_release_id": release_id_before,
        "cache_asof": currents.get("cache_asof"),
        "product_path": str(product_path),
        "coverage_scope": resolved.get("coverage_scope"),
        "coverage_scope_note": resolved.get("coverage_scope_note"),
        "coverage_mode": resolved.get("coverage_mode"),
        "full_history_status": resolved.get("full_history_status"),
        "row_count": data["row_count"],
        "dates_present": data["dates"],
        "date_count": len(data["dates"]),
        "known_at_notes": known_notes,
        "rows": data["rows"],
        "files_used": data["files_used"],
        "runtime": printable,
    }
    if data["row_count"] == 0:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 4
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
