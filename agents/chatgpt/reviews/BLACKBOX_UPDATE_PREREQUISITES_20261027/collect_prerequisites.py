"""Bounded evidence collection only. No supplier or business module execution."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import sys

ROOT = Path(r"E:\BLACKBOX")
OUT_BASE = Path(r"C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027")
ROLES = {"SAM", "ZHANGWEI"}
NEEDLES = (
    "BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260924_20260925_034534",
    "BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439",
)
TEXT_EXT = {".py", ".ps1", ".json", ".jsonl", ".md", ".txt", ".log", ".csv"}
DENY_WORDS = {"secrets", "credentials", ".git", ".venv", "node_modules"}
SECRET_PATTERNS = (
    rb"gh[pousr]_[A-Za-z0-9]{30,}",
    rb"github_pat_[A-Za-z0-9_]{50,}",
    rb"sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}",
    rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
)
MAX_FILE = 2 * 1024 * 1024
MAX_SEARCH_FILES = 6000
MAX_SEARCH_BYTES = 64 * 1024 * 1024
MAX_SEARCH_DIRS = 1500
SEARCH_DEPTH = 3
TASK_NAME_TOKENS = (
    "R45", "20260924", "0924", "DAILY_TIP", "FUND_ETF_NAV_PREMIUM",
    "BLACKBOX_FULL_DATA_UPDATE_R15", "BLACKBOX_POST_SEAL_FINANCE_INDEX_AUG_INCREMENT_R13",
)
RECEIPT_BASENAMES = {
    "TASK_CONTROL.json", "DOWNLOAD_CONTRACT.json", "DOWNLOAD_ACCEPTANCE.json",
    "DOWNLOAD_RESULTS.json", "STAGING_MANIFEST.json", "ACCEPTANCE.json",
    "REPORT.md", "CURRENT.json", "CHECKPOINT.json",
}

def digest(b):
    return hashlib.sha256(b).hexdigest()

def reparse(p):
    s = p.lstat()
    return p.is_symlink() or bool(getattr(s, "st_file_attributes", 0) & 0x400)

def confined(root, p):
    try:
        p.resolve(strict=False).relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False

def permitted(root, p):
    if not confined(root, p):
        return False
    rel = p.relative_to(root)
    return not any(part.lower() in DENY_WORDS for part in rel.parts)

def read_text_bytes(root, p):
    if not permitted(root, p):
        raise ValueError("PATH_NOT_ALLOWED")
    before = p.stat()
    size = before.st_size
    if size > MAX_FILE:
        raise ValueError("SIZE_LIMIT")
    b = p.read_bytes()
    after = p.stat()
    identity = lambda s: (s.st_size, s.st_mtime_ns, s.st_dev, s.st_ino)
    if identity(before) != identity(after) or len(b) != size:
        raise ValueError("SOURCE_CHANGED_DURING_READ")
    if len(b) > MAX_FILE:
        raise ValueError("SIZE_LIMIT")
    if any(re.search(rx, b) for rx in SECRET_PATTERNS):
        raise ValueError("SECRET_PATTERN_BLOCKED")
    for codec in ("utf-8-sig", "utf-16"):
        try:
            s = b.decode(codec)
            if "\x00" in s:
                continue
            return b, s
        except UnicodeError:
            pass
    raise ValueError("TEXT_DECODE_FAILED")

def atomic_new_json(p, obj):
    with p.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=True, indent=2)
        f.write("\n")

def capture(root, p, out, known, records):
    label = str(p)
    if label in records:
        return records[label]
    r = {"source_path": label, "source_absence_claim_allowed": False}
    records[label] = r
    try:
        b, text = read_text_bytes(root, p)
        sha = digest(b)
        r.update(status="READ", bytes=len(b), sha256=sha)
        if sha in known:
            r.update(status="REUSED_HUB_BODY", hub_originals=known[sha])
        else:
            dst = out / "bodies" / ("%04d%s" % (len(records), p.suffix))
            with dst.open("xb") as f:
                f.write(b)
            if dst.read_bytes() != b:
                raise RuntimeError("LOCAL_READBACK_MISMATCH")
            r["captured_body"] = str(dst.relative_to(out))
        r["release_references"] = [n for n in NEEDLES if n in text]
        if p.suffix == ".py":
            try:
                tree = ast.parse(text)
                r["functions"] = [
                    {"name": n.name, "first_line": n.lineno, "last_line": n.end_lineno}
                    for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                r["source_parsed_only_not_executed"] = True
            except SyntaxError:
                r["ast_status"] = "PARSE_FAILED_BODY_PRESERVED"
    except FileNotFoundError:
        r["status"] = "NOT_FOUND_AT_EXACT_PATH"
    except (OSError, ValueError, RuntimeError) as e:
        r.update(status="BLOCKED_OR_READ_ERROR", error_type=type(e).__name__, reason=str(e))
    return r

def lookup_tasks(root, out, known, records):
    result = {"scope": str(root / "\u4efb\u52a1"), "matches": [], "limits": [],
              "directories": 0, "files_read": 0, "bytes_read": 0,
              "no_global_scan": True, "producer_execution_proven": False}
    tasks = root / "\u4efb\u52a1"
    try:
        if reparse(tasks):
            result["limits"].append("TASK_ROOT_REPARSE_NOT_TRAVERSED")
            return result
        with os.scandir(tasks) as it:
            candidates = []
            for e in it:
                p = Path(e.path)
                if reparse(p):
                    result["limits"].append({"top_level_reparse_not_followed": str(p)})
                    continue
                if e.is_dir(follow_symlinks=False) and any(t in e.name.upper() for t in TASK_NAME_TOKENS):
                    candidates.append(p)
    except OSError as e:
        result["limits"].append("TASK_ROOT_READ_ERROR:" + type(e).__name__)
        return result
    result["candidate_task_directories"] = [str(p) for p in sorted(candidates)]
    stopped = False
    for task in sorted(candidates):
        stack = [(task, 0)]
        task_files = []
        task_matches = []
        while stack and not stopped:
            d, depth = stack.pop()
            result["directories"] += 1
            if result["directories"] > MAX_SEARCH_DIRS:
                result["limits"].append("DIRECTORY_LIMIT")
                stopped = True
                break
            try:
                with os.scandir(d) as it:
                    entries = sorted(it, key=lambda e:e.name)
                for e in entries:
                    p = Path(e.path)
                    if not permitted(root, p):
                        continue
                    if reparse(p):
                        result["limits"].append({"reparse_not_followed": str(p)})
                        continue
                    if e.is_dir(follow_symlinks=False):
                        if depth < SEARCH_DEPTH:
                            stack.append((p, depth + 1))
                        else:
                            result["limits"].append({"depth_not_followed": str(p)})
                        continue
                    if p.suffix.lower() not in TEXT_EXT:
                        continue
                    result["files_read"] += 1
                    if result["files_read"] > MAX_SEARCH_FILES:
                        result["limits"].append("FILE_LIMIT")
                        stopped = True
                        break
                    try:
                        b, text = read_text_bytes(root, p)
                    except (OSError, ValueError) as ex:
                        result["limits"].append({"unread": str(p), "reason": str(ex)})
                        continue
                    result["bytes_read"] += len(b)
                    if result["bytes_read"] > MAX_SEARCH_BYTES:
                        result["limits"].append("TOTAL_BYTE_LIMIT")
                        stopped = True
                        break
                    task_files.append(p)
                    found = [n for n in NEEDLES if n in text]
                    if found:
                        r = capture(root, p, out, known, records)
                        hit = {"task_directory": str(task), "file": str(p),
                               "release_ids": found, "identity_record": r,
                               "evidence_role": "REFERENCE_ONLY_NOT_PRODUCER_ATTESTATION"}
                        task_matches.append(hit)
            except OSError as ex:
                result["limits"].append({"directory_read_error": str(d), "reason": str(ex)})
        result["matches"].extend(task_matches)
        if task_matches:
            for p in task_files:
                if p.name in RECEIPT_BASENAMES:
                    capture(root, p, out, known, records)
        if stopped:
            break
    result["search_complete_within_declared_scope"] = not result["limits"]
    result["no_match_means"] = "NO_REFERENCE_IN_READ_PORTION_ONLY; NOT_SOURCE_ABSENCE"
    return result

def collect(root, out, role, plan, known):
    if out.exists():
        raise FileExistsError("OUTPUT_EXISTS_NO_OVERWRITE")
    out.mkdir(parents=True)
    (out / "bodies").mkdir()
    records = {}
    guards = {}
    for rel in plan["guard_paths"]:
        p = root / rel
        try:
            b, unused = read_text_bytes(root, p)
            guards[rel] = digest(b)
        except (OSError, ValueError):
            guards[rel] = None
    for rel in plan["exact_paths"][role]:
        capture(root, root / rel, out, known, records)
    lookup = lookup_tasks(root, out, known, records) if role == "SAM" else None
    if role == "ZHANGWEI":
        commit_path = root / plan["commit_relative_path"]
        try:
            unused, text = read_text_bytes(root, commit_path)
            commit = json.loads(text)
            for key in ("checkpoint_path",):
                if isinstance(commit.get(key), str):
                    p = Path(commit[key])
                    if confined(root / plan["candidate_relative_root"], p):
                        capture(root, p, out, known, records)
                    else:
                        records["DYNAMIC_" + key] = {"status":"BLOCKED_OUTSIDE_CANDIDATE","key":key}
            release_root = commit.get("release_root")
            if isinstance(release_root, str):
                rr = Path(release_root)
                if confined(root / plan["candidate_relative_root"], rr):
                    for name in ("RELEASE.json", "SEAL.json", "MANIFEST.json"):
                        capture(root, rr / name, out, known, records)
        except (OSError, ValueError, json.JSONDecodeError) as e:
            records["COMMIT_BINDING"] = {"status":"UNRESOLVED","reason":type(e).__name__}
    changes = []
    for rel, before in guards.items():
        try:
            after = digest(read_text_bytes(root, root / rel)[0])
        except (OSError, ValueError):
            after = None
        if before != after:
            changes.append({"path": rel, "before": before, "after": after})
    sensitive = root / "\u914d\u7f6e" / "secrets" / "\u5df2\u9a8c\u8bc1" / "\u805a\u5bbd\u8d26\u53f7.txt"
    result = {
        "schema": "BLACKBOX_PREREQUISITE_CAPTURE_V1", "execution_host": role,
        "actual_hostname": platform.node(), "interpreter": sys.executable,
        "python_version": platform.python_version(), "records": list(records.values()),
        "task_lookup": lookup, "guard_changes": changes,
        "credential_locator_present_only": sensitive.exists(),
        "credential_contents_read": False, "supplier_calls": 0,
        "supplier_quota_status": "NOT_MEASURED_BY_THIS_TASK",
        "acquisition_authorized": False, "current_switch_authorized": False,
        "order_allowed": False, "business_modules_imported": False,
    }
    atomic_new_json(out / "COLLECTION.json", result)
    manifest = []
    for p in sorted((out / "bodies").iterdir()):
        b = p.read_bytes()
        manifest.append({"path":str(p.relative_to(out)), "bytes":len(b), "sha256":digest(b)})
    b = (out / "COLLECTION.json").read_bytes()
    manifest.append({"path":"COLLECTION.json","bytes":len(b),"sha256":digest(b)})
    atomic_new_json(out / "DELIVERY_MANIFEST.json", {"files":manifest})
    readback = [{"path":r["path"], "matches":digest((out/r["path"]).read_bytes())==r["sha256"]}
                for r in manifest]
    if not all(r["matches"] for r in readback):
        raise RuntimeError("FINAL_LOCAL_READBACK_FAILED")
    atomic_new_json(out / "LOCAL_READBACK.json", {"files":readback})
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", choices=sorted(ROLES), required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if os.name != "nt" or platform.node().upper() != args.role:
        print("HOST_MISMATCH_NO_COLLECTION", file=sys.stderr)
        return 3
    out = Path(args.out)
    if not confined(OUT_BASE, out) or out.resolve() == OUT_BASE.resolve():
        print("OUTPUT_OUTSIDE_AUTHORIZED_DIRECTORY", file=sys.stderr)
        return 3
    here = Path(__file__).resolve().parent
    plan = json.loads((here/"CAPTURE_PLAN.json").read_text(encoding="utf-8"))
    known = json.loads((here/"KNOWN_HUB_BODIES.json").read_text(encoding="utf-8"))
    result = collect(ROOT, out, args.role, plan, known)
    errors = [r for r in result["records"] if r.get("status") in
              {"NOT_FOUND_AT_EXACT_PATH", "BLOCKED_OR_READ_ERROR", "UNRESOLVED", "BLOCKED_OUTSIDE_CANDIDATE"}]
    bounded = result["task_lookup"] and result["task_lookup"]["limits"]
    print(json.dumps({"host":args.role,"records":len(result["records"]),
                      "unresolved":len(errors),"search_limits":bool(bounded),
                      "guard_changes":len(result["guard_changes"])}, sort_keys=True))
    return 2 if errors or bounded or result["guard_changes"] else 0

if __name__ == "__main__":
    raise SystemExit(main())

