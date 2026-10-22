# -*- coding: utf-8 -*-
"""Unified Market Data Plane Reader R1 — production read API.

Reads ONLY paths returned by the unified plane resolver for a date.
Does not invent directories. Day-partition dates prefer exchange files;
year-batch dates require explicit year-batch scan (caller supplies codes filter).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

import pyarrow.parquet as pq
import pyarrow.compute as pc

from blackbox_unified_market_data_plane_r1 import classify_date, resolve_product


def read_stock_1m_day(product_id: str, trade_date: str, columns: Optional[List[str]] = None):
    """Read one trading day of minute bars via authoritative plane.

    For CLEANING_DAY_PARTITION: concatenates exchange day parquets.
    For YEAR_BATCH planes: filters year-batch files by calendar date (slower).
    """
    resolved = resolve_product(product_id)
    row = classify_date(resolved, trade_date)
    if row["status"] != "PRESENT":
        raise FileNotFoundError(
            f"UNIFIED_PLANE_DATE_NOT_PRESENT: product={resolved['product_id']} date={trade_date} status={row['status']}"
        )
    plane = row["authoritative_plane"]
    cols = columns or ["time", "code", "open", "close", "high", "low", "volume", "money"]

    if plane == "CLEANING_DAY_PARTITION":
        tables = []
        for fp in row["files"]:
            tables.append(pq.read_table(fp, columns=[c for c in cols if c in pq.read_schema(fp).names]))
        if not tables:
            raise FileNotFoundError(f"EMPTY_DAY_FILES: {trade_date}")
        out = tables[0]
        for t in tables[1:]:
            out = pa_concat(out, t)
        return out, plane

    # Year-batch path: filter by date derived from time column
    files = row.get("files") or []
    if plane == "RAW_YEAR_BATCH":
        raw_dir = Path(resolved["planes"]["P2_RAW_REPLACEMENT"]["dir"])
        glob_tmpl = resolved["planes"]["P2_RAW_REPLACEMENT"]["glob"]
        files = [str(p) for p in raw_dir.glob(glob_tmpl.format(year=trade_date[:4]))]
    if not files:
        raise FileNotFoundError(f"NO_YEAR_BATCH_FILES: {trade_date} plane={plane}")

    tables = []
    for fp in files:
        schema_names = pq.read_schema(fp).names
        use_cols = [c for c in cols if c in schema_names]
        if "time" not in use_cols and "time" in schema_names:
            use_cols = ["time"] + use_cols
        t = pq.read_table(fp, columns=use_cols)
        # filter rows whose time date == trade_date
        if "time" not in t.column_names:
            continue
        # time may be timestamp or string
        import pyarrow as pa

        times = t.column("time")
        # cast to string date prefix
        try:
            as_str = pc.strftime(times, format="%Y-%m-%d")
            mask = pc.equal(as_str, trade_date)
        except Exception:
            as_str = pc.utf8_slice_codeunits(pc.cast(times, pa.string()), 0, 10)
            mask = pc.equal(as_str, trade_date)
        ft = t.filter(mask)
        if ft.num_rows:
            tables.append(ft)
    if not tables:
        raise FileNotFoundError(f"YEAR_BATCH_FILTERED_EMPTY: {trade_date} plane={plane}")
    out = tables[0]
    for t in tables[1:]:
        out = pa_concat(out, t)
    return out, plane


def pa_concat(a, b):
    import pyarrow as pa

    return pa.concat_tables([a, b], promote_options="default")


def n_codes_day(product_id: str, trade_date: str) -> dict:
    table, plane = read_stock_1m_day(product_id, trade_date, columns=["code"])
    codes = set(table.column("code").to_pylist())
    return {
        "product_id": product_id,
        "date": trade_date,
        "authoritative_plane": plane,
        "n_rows": table.num_rows,
        "n_codes": len(codes),
    }
