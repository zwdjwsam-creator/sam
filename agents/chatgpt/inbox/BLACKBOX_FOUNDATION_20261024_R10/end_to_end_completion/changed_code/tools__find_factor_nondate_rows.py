"""Find the rows whose `date` is not a calendar timestamp, and identify their real key.

88,584 rows in P1 do not parse as a date. They must be identified before any statement
about 2026-08-12..2026-09-02 absence is allowed: if these rows ARE those sessions under a
different encoding, the "upstream hole" claim is wrong.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
P1 = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P1_adjust_factor")
OUT = TASK / "evidence" / "FACTOR_NONDATE_ENCODING.json"


def main() -> int:
    hits = []
    for f in sorted(P1.glob("*.parquet")):
        try:
            d = pd.read_parquet(f)
        except Exception:  # noqa: BLE001
            continue
        if "date" not in d.columns:
            continue
        if pd.api.types.is_integer_dtype(d["date"]):
            hits.append({
                "file": f.name, "rows": int(len(d)),
                "dtype": str(d["date"].dtype),
                "raw_head": [str(x) for x in d["date"].head(8)],
                "raw_int_min": int(d["date"].min()), "raw_int_max": int(d["date"].max()),
                "kind": "INTEGER_COLUMN",
            })
            continue
        ts = pd.to_datetime(d["date"], errors="coerce")
        bad = ts.isna()
        if int(bad.sum()):
            hits.append({
                "file": f.name, "rows": int(len(d)),
                "dtype": str(d["date"].dtype),
                "n_bad": int(bad.sum()),
                "raw_head": [str(x) for x in d.loc[bad, "date"].head(8)],
                "kind": "PARTIAL_NON_DATE",
            })
    out = {"artifact": "FACTOR_NONDATE_ENCODING",
           "files_with_non_date": len(hits),
           "rows": sum(h.get("n_bad", h["rows"]) for h in hits),
           "detail": hits[:20],
           "conclusion_pending_ratio": (
               "if every non-date row maps to a session inside 2026-08-12..2026-09-02 the "
               "absence claim is false")}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "detail"},
                     ensure_ascii=False, indent=1))
    for h in hits[:8]:
        print(json.dumps(h, ensure_ascii=False, default=str)[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
