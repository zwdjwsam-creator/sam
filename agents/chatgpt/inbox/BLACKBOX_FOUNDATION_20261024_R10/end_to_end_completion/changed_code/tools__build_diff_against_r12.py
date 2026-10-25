"""Build DIFF.patch against the R12 copies that were actually uploaded to the HUB.

The R12 package is the baseline: `changed_code/*.py` under the published inbox path.
Fetching it (read-only) means the diff compares against what the reviewer already has,
instead of against a locally reconstructed guess. Files that did not exist in R12 are
shown as additions.
"""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
DELIV = TASK / "deliverables"
BASE_DIR = TASK / "_baseline_r12"
EVID = TASK / "evidence"

BASE = "https://api.github.com/repos/zwdjwsam-creator/sam"
DEST = "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/changed_code"

# current source -> flat name used in changed_code/
CURRENT = {
    "candidate/local_plane/provider.py": "candidate__local_plane__provider.py",
    "candidate/run_engine_backtest.py": "candidate__run_engine_backtest.py",
    "tools/run_connected_pipeline.py": "tools__run_connected_pipeline.py",
    "tools/candidate_commit.py": "tools__candidate_commit.py",
    "tools/build_candidate_cleaning_from_retained.py":
        "tools__build_candidate_cleaning_from_retained.py",
    "tools/run_original_compiler_candidate.py": "tools__run_original_compiler_candidate.py",
    "tools/verify_provider_semantics.py": "tools__verify_provider_semantics.py",
    "tools/commit_recovery_selftest.py": "tools__commit_recovery_selftest.py",
    "tools/build_delivery_v3.py": "tools__build_delivery_v3.py",
    "tools/measure_factor_density.py": "tools__measure_factor_density.py",
    "candidate/local_plane/minute_bridge.py": "candidate__local_plane__minute_bridge.py",
    "candidate/run_r15_cleaning_replay.py": "candidate__run_r15_cleaning_replay.py",
    "candidate/run_publish_atomic_rehearsal.py": "candidate__run_publish_atomic_rehearsal.py",
    "tools/build_minute_plane_evidence.py": "tools__build_minute_plane_evidence.py",
    "tools/trace_factor_source.py": "tools__trace_factor_source.py",
    "tools/classify_factor_series.py": "tools__classify_factor_series.py",
    "tools/profile_corrupt_factor_dates.py": "tools__profile_corrupt_factor_dates.py",
    "tools/inspect_factor_schema.py": "tools__inspect_factor_schema.py",
    "tools/find_factor_nondate_rows.py": "tools__find_factor_nondate_rows.py",
    "tools/consolidate_r13_round2.py": "tools__consolidate_r13_round2.py",
}


def token() -> str:
    import os
    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(key):
            return os.environ[key].strip()
    p = Path(r"C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT")
    for line in p.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("github_token"):
            line = line.split("=", 1)[-1].strip()
        if line.startswith(("ghp_", "gho_", "ghu_", "ghs_", "github_pat_")):
            return line
    raise SystemExit("no hub token")


def get(path: str) -> bytes | None:
    url = f"{BASE}/contents/{path}?ref=main"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        print("miss", path, type(e).__name__)
        return None
    if isinstance(data, dict) and data.get("content"):
        return base64.b64decode(data["content"])
    return None


def main() -> int:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    report = {"artifact": "DIFF_PROVENANCE", "baseline": f"{DEST}/ (R12 upload)",
              "files": []}
    for rel, flat in CURRENT.items():
        cur = TASK / rel
        if not cur.exists():
            continue
        base_path = BASE_DIR / flat
        if not base_path.exists():
            blob = get(f"{DEST}/{flat}")
            if blob is None:
                base_path.write_text("", encoding="utf-8")
                base_path.with_suffix(".MISSING").write_text("1", encoding="utf-8")
            else:
                base_path.write_bytes(blob)
        old = base_path.read_text(encoding="utf-8", errors="replace")
        new = cur.read_text(encoding="utf-8", errors="replace")
        missing = base_path.with_suffix(".MISSING").exists()
        if old == new:
            report["files"].append({"file": rel, "changed": False, "baseline": "identical"})
            continue
        import difflib
        d = list(difflib.unified_diff(
            old.splitlines(keepends=True), new.splitlines(keepends=True),
            fromfile=f"a/{rel}" if not missing else "/dev/null", tofile=f"b/{rel}"))
        lines.extend(d)
        added = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
        removed = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
        report["files"].append({
            "file": rel, "changed": True, "baseline": "absent_in_r12" if missing else "differs",
            "lines_added": added, "lines_removed": removed,
            "current_sha256_note": "see PACKAGE_INDEX.json",
        })
    (DELIV / "DIFF.patch").write_text("".join(lines), encoding="utf-8")
    report["diff_bytes"] = (DELIV / "DIFF.patch").stat().st_size
    report["changed_files"] = [f["file"] for f in report["files"] if f["changed"]]
    EVID.mkdir(exist_ok=True)
    (EVID / "DIFF_PROVENANCE.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"changed": len(report["changed_files"]),
                      "diff_bytes": report["diff_bytes"],
                      "files": report["files"]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
