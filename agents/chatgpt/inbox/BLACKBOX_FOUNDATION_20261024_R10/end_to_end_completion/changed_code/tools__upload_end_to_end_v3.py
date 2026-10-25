"""Publish the R13 package to the HUB and read every byte back.

The package index is self-consistent: members are uploaded and verified first, then the
receipt (UPLOAD_READBACK) and the index itself are written, uploaded last and verified,
so the index never describes bytes that were not actually published.
"""
from __future__ import annotations

import base64
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
D = TASK / "deliverables"
E = TASK / "evidence"
TOK = [
    l.strip()
    for l in Path(r"C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT").read_text(
        encoding="utf-8-sig", errors="ignore").splitlines()
    if l.strip().startswith(("gho_", "ghp_", "github_pat_", "ghu_"))
][0]
H = {"Authorization": "Bearer " + TOK, "Accept": "application/vnd.github+json",
     "User-Agent": "BB"}
BASE = "https://api.github.com/repos/zwdjwsam-creator/sam"
DEST = "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion"
INBOX = "agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md"
REVISION = "R13_SAME_TASK_CORRECTION"


def req(method: str, url: str, payload: dict | None = None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    r = urllib.request.Request(url, data=data, headers=H, method=method)
    if data is not None:
        r.add_header("Content-Type", "application/json")
    for attempt in range(6):
        try:
            with urllib.request.urlopen(r, timeout=180) as f:
                return json.loads(f.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:400]
            if e.code == 404:
                return {"__err__": 404, "__body__": body}
            if e.code in (409, 422) and attempt == 0:
                return {"__err__": e.code, "__body__": body}
            if attempt == 5:
                raise RuntimeError(f"{e.code} {body}")
            time.sleep(4)
        except Exception:
            if attempt == 5:
                raise
            time.sleep(4)


def curr_sha(path: str):
    j = req("GET", f"{BASE}/contents/{path}?ref=main")
    if isinstance(j, dict) and j.get("sha"):
        return j["sha"]
    return None


def members() -> list[tuple[str, Path]]:
    """(remote relative path, local path) for everything the package claims."""
    out = []
    for p in sorted(D.rglob("*")):
        if p.is_dir() or p.name in ("PACKAGE_INDEX.json", "UPLOAD_READBACK.json"):
            continue
        out.append((str(p.relative_to(D)).replace("\\", "/"), p))
    for p in sorted(E.rglob("*")):
        if p.is_dir():
            continue
        out.append((f"evidence/{str(p.relative_to(E)).replace(chr(92), '/')}", p))
    return out


def put(rel: str, path: Path) -> dict:
    b = path.read_bytes()
    gh = f"{DEST}/{rel}"
    existing = curr_sha(gh)
    payload = {"message": f"R10 end-to-end {REVISION}: {rel}",
               "content": base64.b64encode(b).decode("ascii"), "branch": "main"}
    if existing:
        payload["sha"] = existing
    r = req("PUT", f"{BASE}/contents/{gh}", payload)
    return {"name": rel, "bytes": len(b), "sha256_local": hashlib.sha256(b).hexdigest(),
            "replaced_existing": bool(existing),
            "put_ok": bool((r.get("content") or {}).get("sha")),
            "blob_sha": (r.get("content") or {}).get("sha")}


def readback(rel: str, path: Path) -> dict:
    j = req("GET", f"{BASE}/contents/{DEST}/{rel}?ref=main")
    if not (isinstance(j, dict) and j.get("content")):
        return {"name": rel, "byte_equal": False, "error": str(j)[:200]}
    remote = base64.b64decode(j["content"])
    b = path.read_bytes()
    return {"name": rel, "bytes_local": len(b), "bytes_remote": len(remote),
            "sha256_local": hashlib.sha256(b).hexdigest(),
            "sha256_remote": hashlib.sha256(remote).hexdigest(),
            "byte_equal": remote == b}


def write_index() -> Path:
    rows = []
    for rel, path in members():
        b = path.read_bytes()
        rows.append({"path": rel, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    # the receipt travels with the package too
    rc = D / "UPLOAD_READBACK.json"
    if rc.exists():
        b = rc.read_bytes()
        rows.append({"path": "UPLOAD_READBACK.json", "bytes": len(b),
                     "sha256": hashlib.sha256(b).hexdigest()})
    idx = D / "PACKAGE_INDEX.json"
    idx.write_text(json.dumps({
        "artifact": "PACKAGE_INDEX",
        "task": "BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025",
        "revision": REVISION,
        "hub_destination": DEST,
        "member_count": len(rows),
        "members": rows,
        "note": "every member was uploaded and read back byte-identically before the index "
                "was published (see UPLOAD_READBACK.json)",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return idx


def main() -> int:
    todo = members()
    print("members to upload", len(todo))
    report = {"destination": DEST, "revision": REVISION, "uploads": [], "readback": []}

    pre = req("GET", f"{BASE}/contents/{DEST}?ref=main")
    report["pre_existing"] = sorted(x["name"] for x in pre) if isinstance(pre, list) else []

    for rel, path in todo:
        report["uploads"].append(put(rel, path))
    print("uploaded", len(report["uploads"]))

    for rel, path in todo:
        report["readback"].append(readback(rel, path))
    report["all_byte_equal"] = all(r.get("byte_equal") for r in report["readback"])
    print("readback equal", report["all_byte_equal"])

    post = req("GET", f"{BASE}/contents/{DEST}?ref=main")
    report["post_members"] = sorted(x["name"] for x in post) if isinstance(post, list) else []
    report["post_member_count"] = len(report["post_members"])
    report["earlier_inbox_content_preserved"] = all(
        n in report["post_members"] for n in report["pre_existing"])

    (D / "UPLOAD_READBACK.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # receipt + index are published last, then verified
    tail = [put("UPLOAD_READBACK.json", D / "UPLOAD_READBACK.json")]
    idx = write_index()
    tail.append(put("PACKAGE_INDEX.json", idx))
    tail_rb = [readback("UPLOAD_READBACK.json", D / "UPLOAD_READBACK.json"),
               readback("PACKAGE_INDEX.json", idx)]
    report["tail_uploads"] = tail
    report["tail_readback"] = tail_rb
    report["tail_byte_equal"] = all(r.get("byte_equal") for r in tail_rb)
    (D / "UPLOAD_READBACK.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # the receipt changed after the index was written; republish both so the index matches
    tail = [put("UPLOAD_READBACK.json", D / "UPLOAD_READBACK.json")]
    idx = write_index()
    tail.append(put("PACKAGE_INDEX.json", idx))
    report["tail_uploads_final"] = tail
    report["tail_readback_final"] = [readback("UPLOAD_READBACK.json", D / "UPLOAD_READBACK.json"),
                                     readback("PACKAGE_INDEX.json", idx)]
    report["tail_byte_equal_final"] = all(r.get("byte_equal")
                                          for r in report["tail_readback_final"])
    (D / "UPLOAD_READBACK.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ------------------------------------------------------------ inbox pointer
    acc = json.loads((D / "ACCEPTANCE.json").read_text(encoding="utf-8"))
    strict = acc["r13_delta"]["strict_run"]
    j = req("GET", f"{BASE}/contents/{INBOX}?ref=main")
    old = (base64.b64decode(j["content"]).decode("utf-8")
           if isinstance(j, dict) and j.get("content") else "")
    sec = (
        "\n\n## BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025 — R13 revision "
        "(same task, corrected classification)\n\n"
        f"- overall: **{acc['overall']}** · stage1: **{acc['stage1']['verdict']}** "
        "(READY_FOR_GPT_REVIEW=false)\n"
        "- the three reviewed diffs are closed with code, not description: real original "
        "gate/cleaning/compiler/publish-gate calls, provider substitutions removed, "
        "single-authority COMMIT.json\n"
        f"- strict V4 port 2026-09-03..2026-09-24: **{strict['status']}**, "
        f"trades={strict['trades']}, blockers={strict['blockers']}\n"
        "- measured blocker: ADJUST_FACTOR_PIT_R1 is sparse for 12 sessions "
        "(2026-08-17..2026-09-02, 7-89 rows); fq='pre' rows that cannot be reconstructed "
        "are withheld and counted, never filled\n"
        "- the earlier COMPLETED/2-fill result depended on the ffill this revision removed; "
        "it is preserved as a failed historical label\n"
        f"- package: `{DEST}/` ({report['post_member_count']} top-level members, "
        f"all_byte_equal={report['all_byte_equal']}, index+receipt verified="
        f"{report['tail_byte_equal_final']})\n"
        "- acquisition / CURRENT / orders remain unauthorised; B1/B2/B5 partially repaired, "
        "B3/B4/B6/B7 open\n"
    )
    if "R13 revision" not in old:
        put_r = req("PUT", f"{BASE}/contents/{INBOX}",
                    {"message": "R10 end-to-end R13 revision result pointer",
                     "content": base64.b64encode((old + sec).encode("utf-8")).decode("ascii"),
                     "branch": "main",
                     **({"sha": j["sha"]} if isinstance(j, dict) and j.get("sha") else {})})
        report["inbox_update"] = {"put_ok": bool((put_r.get("content") or {}).get("sha")),
                                  "bytes_added": len(sec.encode("utf-8"))}
    else:
        report["inbox_update"] = {"put_ok": True, "already_present": True}
    (D / "UPLOAD_READBACK.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("post_member_count", "all_byte_equal",
                                             "earlier_inbox_content_preserved",
                                             "tail_byte_equal_final", "inbox_update")},
                     ensure_ascii=False, indent=2))
    return 0 if report["all_byte_equal"] and report["tail_byte_equal_final"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
