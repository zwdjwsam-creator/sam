"""Coverage-aware parquet file index for the local value plane.

Why this module exists
----------------------
R01 selected files by scanning filename tokens for any 8-digit group, so a *build*
timestamp such as ``20260612_090000`` was read as coverage and a 2014 file could be
selected for a 2026 request. R01 also de-duplicated whole "families" by newest build
stamp, which silently dropped complementary segments and changed a 22-row answer into
10 rows.

Rules implemented here
----------------------
1. Coverage comes from the parquet footer statistics of the actual time column
   (``data_coverage``). Filename tokens are kept only as secondary hints
   (``name_coverage``); ``YYYYMMDD_HHMMSS`` build stamps are stripped before parsing.
2. Files are grouped by ``family`` (basename with build stamps removed). Two files with
   the same family and the same data coverage are versions of one segment: the newest
   build wins. Two files with the same family but *different* coverage are complementary
   segments and are both kept.
3. The index is built once per dataset/layer and cached, keyed by a directory-mtime
   signature. Requests do not re-enumerate the dataset tree.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

BUILD_STAMP_RE = re.compile(r"(?<![0-9])(\d{8})_(\d{6})(?![0-9])")
TIME_COLUMNS = ("time", "timestamp", "date", "trade_date", "day")

INDEX_DIR = Path(__file__).resolve().parents[2] / "runtime"
INDEX_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class FileEntry:
    path: str
    name: str
    family: str
    version: str
    size: int
    mtime_ns: int
    rows: int
    time_col: str
    data_start: Optional[str]
    data_end: Optional[str]
    name_coverage: Dict[str, Any] = field(default_factory=dict)
    columns: List[str] = field(default_factory=list)
    span_days: int = 0
    specificity_rank: int = 1
    read_error: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path, "name": self.name, "family": self.family, "version": self.version,
            "size": self.size, "mtime_ns": self.mtime_ns, "rows": self.rows, "time_col": self.time_col,
            "data_start": self.data_start, "data_end": self.data_end, "name_coverage": self.name_coverage,
            "columns": self.columns, "span_days": self.span_days,
            "specificity_rank": self.specificity_rank, "read_error": self.read_error,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FileEntry":
        return cls(**d)

    def rank(self) -> Tuple[int, str]:
        """Revision priority: narrower coverage first, then newer build stamp."""
        return (self.specificity_rank, self.version)


# --------------------------------------------------------------------------- filename hint parsing
def parse_name_coverage(basename: str) -> Dict[str, Any]:
    """Parse coverage hints from a filename *after* removing build stamps.

    A build stamp (``YYYYMMDD_HHMMSS``) is never coverage. Remaining numeric tokens are
    parsed in this priority order: dashed range, compact day range, dashed day, compact
    day, half year, year. Matched text is blanked so a later rule cannot re-read it.
    """
    stamps = [f"{m.group(1)}_{m.group(2)}" for m in BUILD_STAMP_RE.finditer(basename)]
    work = BUILD_STAMP_RE.sub(" ", basename)
    starts: List[str] = []
    ends: List[str] = []
    kinds: List[str] = []

    def blank(span: Tuple[int, int]) -> None:
        nonlocal work
        chars = list(work)
        for i in range(span[0], min(span[1], len(chars))):
            chars[i] = " "
        work = "".join(chars)

    def scan(pattern: str, kind: str, extract) -> None:
        while True:
            m = re.search(pattern, work)
            if not m:
                return
            got = extract(m)
            if got:
                s, e = got
                if s:
                    starts.append(s)
                if e:
                    ends.append(e)
                kinds.append(kind)
            blank(m.span())

    scan(r"(20\d{2}-\d{2}-\d{2})_(20\d{2}-\d{2}-\d{2})", "range",
         lambda m: (m.group(1), m.group(2)))
    scan(r"(?<!\d)((?:20\d{2})(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))_"
         r"((?:20\d{2})(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))(?!\d)", "range",
         lambda m: (_compact_to_date(m.group(1)), _compact_to_date(m.group(2))))
    scan(r"20\d{2}-\d{2}-\d{2}", "day", lambda m: (m.group(0), m.group(0)))
    scan(r"(?<!\d)(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)", "day",
         lambda m: (_compact_to_date(m.group(0)), _compact_to_date(m.group(0))))
    scan(r"(?<!\d)(20\d{2})_H([12])(?!\d)", "half_year",
         lambda m: (f"{m.group(1)}-01-01" if m.group(2) == "1" else f"{m.group(1)}-07-01",
                    f"{m.group(1)}-06-30" if m.group(2) == "1" else f"{m.group(1)}-12-31"))
    scan(r"(?<!\d)(20\d{2})(?!\d)", "year",
         lambda m: (f"{m.group(1)}-01-01", f"{m.group(1)}-12-31"))

    out: Dict[str, Any] = {"build_stamps": stamps, "kinds": kinds}
    if starts:
        out["start"] = min(starts)
        out["end"] = max(ends) if ends else max(starts)
        out["kind"] = "range" if len(kinds) > 1 or kinds[0] == "range" else kinds[0]
    return out


def _compact_to_date(s: str) -> str:
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"


def build_family(basename: str) -> Tuple[str, str]:
    """Return (family, version). Build stamp is the version, never part of the family."""
    stamps = list(BUILD_STAMP_RE.finditer(basename))
    version = f"{stamps[-1].group(1)}_{stamps[-1].group(2)}" if stamps else ""
    fam = BUILD_STAMP_RE.sub("", basename)
    fam = re.sub(r"\.parquet$", "", fam)
    fam = re.sub(r"_{2,}", "__", fam).strip("_")
    return fam, version


# --------------------------------------------------------------------------- footer statistics
def detect_time_column(names: Sequence[str]) -> Optional[str]:
    for c in TIME_COLUMNS:
        if c in names:
            return c
    return None


def _norm_date(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v)
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    if len(s) == 8 and s.isdigit():
        return _compact_to_date(s)
    return s[:10]


def file_stats(path: str) -> Dict[str, Any]:
    import pyarrow.parquet as pq
    try:
        pf = pq.ParquetFile(path)
        md = pf.metadata
        names = [md.schema.column(i).name for i in range(md.num_columns)]
        tc = detect_time_column(names)
        if tc is None:
            return {"read_error": "NO_TIME_COLUMN", "columns": names, "rows": md.num_rows}
        idx = names.index(tc)
        lo = hi = None
        for rg in range(md.num_row_groups):
            st = md.row_group(rg).column(idx).statistics
            if st is None or st.min is None or st.max is None:
                lo = hi = None
                break
            lo = st.min if lo is None else min(lo, st.min)
            hi = st.max if hi is None else max(hi, st.max)
        if lo is None:
            t = pq.read_table(path, columns=[tc])
            col = t.column(tc).to_pylist()
            lo, hi = (min(col), max(col)) if col else (None, None)
        return {"read_error": None, "columns": names, "rows": md.num_rows, "time_col": tc,
                "data_start": _norm_date(lo), "data_end": _norm_date(hi)}
    except Exception as exc:  # corrupt file / unreadable footer
        return {"read_error": f"{type(exc).__name__}: {exc}"[:200], "columns": [], "rows": 0}


def dir_signature(root: str) -> Dict[str, Any]:
    """Cheap change detector: directory mtimes + parquet count (no per-file stat)."""
    dirs: Dict[str, int] = {}
    n = 0
    for dp, _, fns in os.walk(root):
        try:
            dirs[dp] = os.stat(dp).st_mtime_ns
        except OSError:
            dirs[dp] = 0
        n += sum(1 for f in fns if f.endswith(".parquet"))
    return {"dirs": dirs, "n_parquet": n}


def list_parquet(root: str) -> List[str]:
    out: List[str] = []
    if not os.path.isdir(root):
        return out
    for dp, _, fns in os.walk(root):
        out.extend(os.path.join(dp, f) for f in fns if f.endswith(".parquet"))
    return sorted(out)


def build_index(dataset_id: str, layer: str, root: str, *, force: bool = False,
                max_files: Optional[int] = None) -> Dict[str, Any]:
    cache_path = INDEX_DIR / f"file_index_{dataset_id}_{layer}.json"
    sig = dir_signature(root) if os.path.isdir(root) else {"dirs": {}, "n_parquet": 0}
    if not force and cache_path.is_file():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached.get("signature") == sig and cached.get("root") == root:
                return cached
        except Exception:
            pass
    files = list_parquet(root)
    if max_files:
        files = files[:max_files]
    entries: List[FileEntry] = []
    t0 = time.time()
    for p in files:
        st = file_stats(p)
        family, version = build_family(os.path.basename(p))
        ds, de = st.get("data_start"), st.get("data_end")
        span = 0
        if ds and de:
            from datetime import date
            try:
                span = (date.fromisoformat(de) - date.fromisoformat(ds)).days + 1
            except Exception:
                span = 0
        rank = 3 if 0 < span <= 1 else (2 if 0 < span <= 45 else 1)
        try:
            sz = os.path.getsize(p)
            mt = os.stat(p).st_mtime_ns
        except OSError:
            sz = mt = 0
        entries.append(FileEntry(
            path=p, name=os.path.basename(p), family=family, version=version, size=sz, mtime_ns=mt,
            rows=st.get("rows", 0), time_col=st.get("time_col") or "",
            data_start=ds, data_end=de,
            name_coverage=parse_name_coverage(os.path.basename(p)),
            columns=st.get("columns") or [], span_days=span,
            specificity_rank=rank, read_error=st.get("read_error"),
        ))
    idx = {
        "dataset_id": dataset_id, "layer": layer, "root": root,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "build_seconds": round(time.time() - t0, 3),
        "signature": sig, "n_files": len(entries),
        "observed_start": min((e.data_start for e in entries if e.data_start), default=None),
        "observed_end": max((e.data_end for e in entries if e.data_end), default=None),
        "files": [e.as_dict() for e in entries],
    }
    cache_path.write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")
    return idx


# --------------------------------------------------------------------------- selection
def load_entries(index: Dict[str, Any]) -> List[FileEntry]:
    return [FileEntry.from_dict(d) for d in index.get("files", [])]


def effective_coverage(e: FileEntry) -> Tuple[Optional[str], Optional[str], str]:
    """Data coverage when the footer is readable, else the filename hint (still never a build stamp)."""
    if e.data_start and e.data_end:
        return e.data_start, e.data_end, "DATA_STATISTICS"
    nc = e.name_coverage or {}
    if nc.get("start") and nc.get("end"):
        return nc["start"], nc["end"], "FILENAME_HINT_ONLY"
    return None, None, "UNKNOWN"


def select(index: Dict[str, Any], start: str, end: str, *,
           max_files: int = 512) -> Dict[str, Any]:
    """Select files whose *data* coverage intersects [start, end].

    Returns accounting for selected / version-superseded / budget-skipped so callers can
    refuse a complete-success admission instead of silently dropping work.
    """
    entries = load_entries(index)
    hits: List[Tuple[FileEntry, str, str, str]] = []
    for e in entries:
        lo, hi, basis = effective_coverage(e)
        if not lo or not hi:
            hits.append((e, start, end, "UNKNOWN_REQUIRES_REVIEW"))
            continue
        if hi < start or lo > end:
            continue
        hits.append((e, lo, hi, basis))
    # version grouping: same family + same coverage => one segment, newest build wins
    best: Dict[Tuple[str, str, str], Tuple[FileEntry, str]] = {}
    superseded: List[str] = []
    for e, lo, hi, basis in hits:
        key = (e.path, lo, hi)  # no unproved version suppression
        cur = best.get(key)
        if cur is None or e.version > cur[0].version:
            if cur is not None:
                superseded.append(cur[0].path)
            best[key] = (e, basis)
        else:
            superseded.append(e.path)
    pairs = sorted(best.values(), key=lambda p: (p[0].data_start or "", -p[0].specificity_rank, p[0].version))
    pairs.sort(key=lambda p: (p[0].specificity_rank, p[0].version), reverse=True)
    budget_skipped = [p[0].path for p in pairs[max_files:]]
    pairs = sorted(pairs[:max_files], key=lambda p: (p[0].data_start or "", p[0].path))
    return {
        "files": [p[0] for p in pairs],
        "coverage_basis_per_file": {p[0].path: p[1] for p in pairs},
        "selected": len(pairs),
        "matched_before_budget": len(best),
        "budget_skipped": budget_skipped,
        "version_superseded": superseded,
        "n_index_files": len(entries),
        "unindexed_unreadable": [e.path for e in entries if e.read_error],
    }
