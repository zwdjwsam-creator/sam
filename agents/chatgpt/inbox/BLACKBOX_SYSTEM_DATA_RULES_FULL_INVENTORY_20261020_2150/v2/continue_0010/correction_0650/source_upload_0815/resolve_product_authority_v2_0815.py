# -*- coding: utf-8 -*-
"""Isolated inventory authority resolver v2 — asset_type + frequency (0815).

Does NOT modify production data. Used only for inventory identity correction.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


def _freq_token(pid: str) -> str | None:
    for tok in ("1M", "5M", "30M", "60M"):
        if tok in pid:
            return tok.lower()  # 1m / 5m
    return None


def _asset_kind(pid: str) -> str:
    u = pid.upper()
    if "ETF" in u:
        return "ETF"
    if "STOCK" in u or "STK" in u:
        return "STOCK"
    if "CBOND" in u or "BOND" in u:
        return "BOND"
    if "FUND" in u:
        return "FUND"
    if "INDEX" in u:
        return "INDEX"
    return "UNKNOWN"


def resolve_product_authority_v2(pid: str, cache: dict, clean: dict, sidecar: dict, catalog, uni) -> dict:
    """v2: never accept stock minute dir for ETF (and vice versa) by frequency-only match."""
    main_root = Path(cache["release_root"])
    main_path = main_root / pid
    row = {
        "product_id": pid,
        "authority_kind": "",
        "authority_path": "",
        "exists": False,
        "status": "PENDING",
        "reason": "",
        "resolver": "v2_0815",
        "asset_kind": _asset_kind(pid),
        "freq": _freq_token(pid),
        "in_main_cache_catalog": pid in (catalog or set()),
    }
    # sidecar / main cache first (identity preserved)
    sp = (sidecar.get("products") or {}).get(pid) if isinstance(sidecar, dict) else None
    if sp and sp.get("cache_product_path"):
        p = Path(sp["cache_product_path"])
        row.update(
            authority_kind="SIDECAR_CACHE",
            authority_path=str(p),
            exists=p.exists(),
            status="VERIFIED_WITHIN_DECLARED_SCOPE" if p.exists() else "BLOCKED",
            reason="sidecar_CURRENT",
        )
        return row
    if main_path.exists():
        row.update(
            authority_kind="MAIN_CACHE_RELEASE",
            authority_path=str(main_path),
            exists=True,
            status="PENDING_COVERAGE",
            reason="main_cache_dir",
        )
        return row

    if "MINUTE" not in pid:
        row.update(
            authority_kind="NOT_MINUTE",
            authority_path=str(main_path),
            exists=False,
            status="NOT_IN_MAIN_CACHE_ROOT",
            reason="non_minute_no_fallback_in_v2_scope",
        )
        return row

    freq = _freq_token(pid)
    asset = _asset_kind(pid)
    products = (uni or {}).get("products") or {}
    meta = products.get(pid) if isinstance(products, dict) else None
    if isinstance(meta, dict):
        for k in ("clean_path", "clean", "raw_root", "raw", "source_path", "path"):
            if meta.get(k) and Path(str(meta[k])).exists():
                row.update(
                    authority_kind="MINUTE_PLANE_REGISTRY",
                    authority_path=str(meta[k]),
                    exists=True,
                    status="VERIFIED_PARTIAL",
                    reason=f"unified_registry.{k}",
                )
                return row

    std = Path(clean.get("standard_root") or "")
    if not std.exists() or not freq:
        row.update(
            authority_kind="MINUTE_NOT_IN_MAIN_CACHE",
            authority_path=str(main_path),
            exists=False,
            status="UNKNOWN",
            reason="no_standard_root_or_freq",
        )
        return row

    # asset-constrained patterns — order matters; do NOT scan stock before etf for ETF products
    if asset == "ETF":
        patterns = [f"**/ETF_{freq}", f"**/etf_{freq}", f"**/*ETF*{freq}*"]
    elif asset == "STOCK":
        patterns = [f"**/A股_stock_{freq}", f"**/stock_{freq}", f"**/*stock*{freq}*"]
    else:
        row.update(
            authority_kind="MINUTE_ASSET_UNKNOWN",
            authority_path=str(main_path),
            exists=False,
            status="UNKNOWN",
            reason="asset_kind_unknown_no_frequency_only_fallback",
        )
        return row

    hits: list[Path] = []
    for pattern in patterns:
        for p in std.glob(pattern):
            pl = str(p).lower().replace("\\", "/")
            # reject cross-asset
            if asset == "ETF" and ("stock" in pl or "a股_stock" in pl or "a股_stock" in str(p)):
                continue
            if asset == "STOCK" and re.search(r"(^|/)etf(_|/)", pl):
                continue
            if freq not in pl:
                continue
            hits.append(p)
            break
        if hits:
            break

    if hits:
        p = hits[0]
        row.update(
            authority_kind="CLEANING_MINUTE_PLANE_V2",
            authority_path=str(p),
            exists=True,
            status="VERIFIED_PARTIAL",
            reason="asset_and_frequency_constrained",
        )
        return row

    # explicit: both exist but wrong asset → UNKNOWN not stock fallback
    stock_pat = list(std.glob(f"**/A股_stock_{freq}"))
    etf_pat = list(std.glob(f"**/ETF_{freq}"))
    row.update(
        authority_kind="MINUTE_AUTHORITY_UNRESOLVED",
        authority_path=str(main_path),
        exists=False,
        status="UNKNOWN",
        reason="no_matching_asset_dir",
        observed_stock_dirs=[str(x) for x in stock_pat[:3]],
        observed_etf_dirs=[str(x) for x in etf_pat[:3]],
    )
    return row


def regression_fixture() -> dict:
    """Same dual-asset fixture as GPT review; v2 must pick ETF for ETF."""
    standard = r"E:\synthetic_clean\standard"
    stock1 = standard + r"\finance\A股_stock_1m"
    etf1 = standard + r"\finance\ETF_1m"
    stock5 = standard + r"\finance\A股_stock_5m"
    etf5 = standard + r"\finance\ETF_5m"
    existing = {standard, stock1, etf1, stock5, etf5}
    by_pattern = {
        "**/A股_stock_1m": [stock1],
        "**/ETF_1m": [etf1],
        "**/A股_stock_5m": [stock5],
        "**/ETF_5m": [etf5],
        "**/etf_1m": [],
        "**/etf_5m": [],
        "**/stock_1m": [],
        "**/stock_5m": [],
        "**/*ETF*1m*": [etf1],
        "**/*ETF*5m*": [etf5],
        "**/*stock*1m*": [stock1],
        "**/*stock*5m*": [stock5],
    }

    class FakePath(type(Path())):  # type: ignore
        def __new__(cls, *args):
            return super().__new__(cls, *args)

        def exists(self):
            return str(self) in existing

        def glob(self, pattern):
            return (FakePath(p) for p in by_pattern.get(pattern, []))

    import resolve_product_authority_v2_0815 as mod

    # monkeypatch Path inside resolve by passing FakePath via clean root only —
    # call with patched module Path
    real_Path = mod.Path
    mod.Path = FakePath  # type: ignore
    try:
        rows = []
        expect = {
            "ETF_MINUTE_1M_R1": etf1,
            "ETF_MINUTE_5M_R1": etf5,
            "STOCK_MINUTE_1M_R1": stock1,
            "STOCK_MINUTE_5M_R1": stock5,
        }
        for pid, want in expect.items():
            row = mod.resolve_product_authority_v2(
                pid,
                {"release_root": r"E:\synthetic_cache"},
                {"standard_root": standard},
                {},
                set(),
                {},
            )
            rows.append(
                {
                    "product_id": pid,
                    "selected": row["authority_path"],
                    "want": want,
                    "ok": row["authority_path"] == want,
                    "status": row["status"],
                }
            )
        # negative: ETF must not equal stock
        etf_stock_collision = rows[0]["selected"] == rows[2]["selected"]
        pass_all = all(r["ok"] for r in rows) and not etf_stock_collision
        return {"PASS": bool(pass_all), "rows": rows, "etf_stock_collision": etf_stock_collision}
    finally:
        mod.Path = real_Path  # type: ignore


if __name__ == "__main__":
    print(json.dumps(regression_fixture(), ensure_ascii=False, indent=2))
