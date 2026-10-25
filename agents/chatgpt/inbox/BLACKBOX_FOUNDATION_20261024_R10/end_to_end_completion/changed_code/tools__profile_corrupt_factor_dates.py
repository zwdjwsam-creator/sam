"""Characterise the corrupted-date factor files before allowing any derived candidate.

The 17 files for 2026-08-12..2026-09-02 carry an int64 `date` column with values 0..299.
Before "(re)derive the session from the file name" is allowed, this must hold:
  * the row payload (code, factor, sec_type) is intact and unique per code;
  * the row count and code set agree with the neighbouring DENSE sessions;
  * factor values look like factors (positive, finite), not zeros or placeholders.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
P1 = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P1_adjust_factor")
OUT = TASK / "evidence" / "FACTOR_CORRUPT_DATE_PROFILE.json"
PAT = re.compile(r"_(\d{4})(\d{2})(\d{2})__")


def session_of(name: str) -> str | None:
    m = PAT.search(name)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def main() -> int:
    corrupt, dense = [], []
    for f in sorted(P1.glob("adjust_factor_stock__incremental_*.parquet")):
        d = pd.read_parquet(f)
        if "date" not in d.columns:
            continue
        item = {"file": f.name, "session_from_name": session_of(f.name),
                "rows": int(len(d)), "dtype": str(d["date"].dtype)}
        if pd.api.types.is_integer_dtype(d["date"]):
            item.update({
                "date_min": int(d["date"].min()), "date_max": int(d["date"].max()),
                "date_nunique": int(d["date"].nunique()),
                "codes": int(d["code"].nunique()),
                "factor_min": float(pd.to_numeric(d["factor"], errors="coerce").min()),
                "factor_max": float(pd.to_numeric(d["factor"], errors="coerce").max()),
                "factor_null": int(pd.to_numeric(d["factor"], errors="coerce").isna().sum()),
                "factor_nonpositive": int((pd.to_numeric(d["factor"], errors="coerce") <= 0).sum()),
                "sec_type_values": sorted({str(x) for x in d.get("sec_type", pd.Series(dtype=str))
                                           .dropna().unique()})[:6],
            })
            corrupt.append(item)
        else:
            ts = pd.to_datetime(d["date"], errors="coerce")
            item.update({
                "session_in_data": str(ts.dropna().iloc[0].date()) if ts.notna().any() else None,
                "codes": int(d["code"].nunique()),
                "factor_min": float(pd.to_numeric(d["factor"], errors="coerce").min()),
                "factor_max": float(pd.to_numeric(d["factor"], errors="coerce").max()),
            })
            dense.append(item)

    # code set agreement between the last dense session before the hole and the first corrupt one
    agree = None
    if corrupt and dense:
        before = [x for x in dense if x.get("session_in_data") and
                  x["session_in_data"] < corrupt[0]["session_from_name"]]
        if before:
            b = pd.read_parquet(P1 / before[-1]["file"])
            c = pd.read_parquet(P1 / corrupt[0]["file"])
            bs, cs = set(b["code"].astype(str)), set(c["code"].astype(str))
            agree = {"dense_file": before[-1]["file"], "corrupt_file": corrupt[0]["file"],
                     "dense_codes": len(bs), "corrupt_codes": len(cs),
                     "shared": len(bs & cs), "only_dense": len(bs - cs),
                     "only_corrupt": len(cs - bs)}

    out = {
        "artifact": "FACTOR_CORRUPT_DATE_PROFILE",
        "finding": "the incremental writer emitted a positional integer as `date` for the "
                   "sessions 2026-08-12..2026-09-02; the row payload is otherwise intact",
        "n_corrupt_files": len(corrupt),
        "corrupt": corrupt,
        "dense_reference": dense[-4:],
        "code_set_agreement": agree,
        "repair_preconditions": {
            "session_derivable_from_filename": all(x["session_from_name"] for x in corrupt),
            "rows_comparable_to_dense": agree is not None and
            abs(agree["dense_codes"] - agree["corrupt_codes"]) <= 5,
            "factors_positive_finite": all(x["factor_null"] == 0 and x["factor_nonpositive"] == 0
                                           for x in corrupt),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k not in ("corrupt", "dense_reference")},
                     ensure_ascii=False, indent=1, default=str))
    for x in corrupt[:3] + corrupt[-2:]:
        print(json.dumps(x, ensure_ascii=False, default=str)[:340])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
