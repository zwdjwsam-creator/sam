# -*- coding: utf-8 -*-
"""LOCAL_AI two-window HUB notifier pilot 1913.

Writes only under D:\\LOCAL_AI\\Watchdog and HUB inbox report paths.
Does not mutate BLACKBOX business data planes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
STATE = HERE / "state"
LOGS = HERE / "logs"
EVID = HERE / "evidence"
SEEN = STATE / "seen_events.json"
DELIV = LOGS / "delivery_log.jsonl"
MUTEX = STATE / "notifier.lock"
STATUS_LOCAL = STATE / "STATUS_LIVE.json"


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def log(msg: str) -> None:
    line = f"{now()} {msg}"
    print(line, flush=True)
    with (LOGS / "pilot.out.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def acquire_mutex() -> bool:
    STATE.mkdir(parents=True, exist_ok=True)
    if MUTEX.exists():
        try:
            old = json.loads(MUTEX.read_text(encoding="utf-8"))
            pid = int(old.get("pid") or 0)
            # stale if process gone
            r = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if str(pid) in (r.stdout or "") and "No tasks" not in (r.stdout or ""):
                return False
        except Exception:
            pass
    MUTEX.write_text(json.dumps({"pid": os.getpid(), "at": now()}), encoding="utf-8")
    return True


def release_mutex() -> None:
    try:
        if MUTEX.exists():
            MUTEX.unlink()
    except Exception:
        pass


def load_seen() -> dict:
    if SEEN.exists():
        return json.loads(SEEN.read_text(encoding="utf-8"))
    return {"objects": {}, "deliveries": {}}


def save_seen(seen: dict) -> None:
    SEEN.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")


def append_delivery(rec: dict) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    with DELIV.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def sha1_bytes(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


def mailbox() -> Path:
    return Path(CFG["hub_mailbox"])


def preload_seen(seen: dict) -> int:
    """Mark all current outbox/reviews/inbox files as seen so first poll is silent."""
    n = 0
    box = mailbox()
    for rel in (CFG["outbox_rel"], CFG["reviews_rel"], CFG["inbox_rel"]):
        root = box / rel.replace("/", os.sep)
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".md", ".json", ".jsonl", ".txt", ".csv"}:
                continue
            key = f"{rel}/{p.relative_to(root).as_posix()}"
            h = sha1_bytes(p.read_bytes())
            seen["objects"][key] = h
            n += 1
    save_seen(seen)
    return n


def scan_deltas(seen: dict, roots: list[str]) -> list[dict]:
    deltas = []
    box = mailbox()
    for rel in roots:
        root = box / rel.replace("/", os.sep)
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".md", ".json", ".jsonl", ".txt"}:
                continue
            key = f"{rel}/{p.relative_to(root).as_posix()}"
            h = sha1_bytes(p.read_bytes())
            prev = seen["objects"].get(key)
            if prev == h:
                continue
            kind = "NEW" if prev is None else "CHANGED"
            deltas.append(
                {
                    "key": key,
                    "sha": h,
                    "prev_sha": prev,
                    "kind": kind,
                    "local": str(p),
                    "direction": "GPT_TO_CURSOR" if rel.startswith("agents/chatgpt/outbox") or rel.startswith("agents/chatgpt/reviews") else "CURSOR_TO_GPT",
                    "name": p.name,
                }
            )
            seen["objects"][key] = h
    return deltas


def uia_probe() -> dict:
    ps1 = HERE / "uia_probe.ps1"
    r = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ps1),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    out = {
        "rc": r.returncode,
        "stderr": (r.stderr or "")[:2000],
        "raw": (r.stdout or "")[:8000],
    }
    try:
        out["parsed"] = json.loads(r.stdout or "{}")
    except Exception as e:
        out["parse_error"] = str(e)
    (EVID / "uia_probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def fixed_msg_c2g(report_url: str) -> str:
    return CFG["msg_cursor_to_gpt_template"].format(report_url=report_url)


def fixed_msg_g2c(task_id: str, task_url: str) -> str:
    return CFG["msg_gpt_to_cursor_template"].format(task_id=task_id, task_url=task_url)


def event_id(direction: str, key: str, sha: str) -> str:
    return hashlib.sha1(f"{direction}|{key}|{sha}".encode("utf-8")).hexdigest()


def already_delivered(seen: dict, eid: str) -> bool:
    return eid in (seen.get("deliveries") or {})


def mark_delivered(seen: dict, eid: str, rec: dict) -> None:
    seen.setdefault("deliveries", {})[eid] = rec
    save_seen(seen)
    append_delivery(rec)


def write_test_inbox_file(test_id: str) -> dict:
    """Create isolated pilot evidence under mailbox inbox (HUB communication, not business data)."""
    box = mailbox()
    dest = box / "agents" / "chatgpt" / "inbox" / "LOCAL_AI_TWO_WINDOW_HUB_NOTIFIER_PILOT_20261021_1913"
    dest.mkdir(parents=True, exist_ok=True)
    p = dest / f"PILOT_C2G_TRIGGER_{test_id}.md"
    body = f"""# PILOT_C2G_TRIGGER

test_id: {test_id}
at: {now()}
purpose: Cursor->GPT fixed notification pilot trigger
NO_BLACKBOX_BUSINESS_WRITES: true
"""
    p.write_text(body, encoding="utf-8")
    return {"path": str(p), "sha": sha1_bytes(p.read_bytes()), "repo_hint": f"agents/chatgpt/inbox/LOCAL_AI_TWO_WINDOW_HUB_NOTIFIER_PILOT_20261021_1913/{p.name}"}


def write_test_outbox_file(test_id: str) -> dict:
    box = mailbox()
    dest = box / "agents" / "chatgpt" / "outbox"
    dest.mkdir(parents=True, exist_ok=True)
    p = dest / f"PILOT_G2C_TRIGGER_{test_id}.md"
    body = f"""# PILOT_G2C_TRIGGER

task_id: PILOT_G2C_{test_id}
test_id: {test_id}
at: {now()}
purpose: GPT/HUB->Cursor fixed notification pilot trigger
status: PILOT_ONLY
NO_BLACKBOX_BUSINESS_WRITES: true
"""
    p.write_text(body, encoding="utf-8")
    return {
        "path": str(p),
        "sha": sha1_bytes(p.read_bytes()),
        "task_id": f"PILOT_G2C_{test_id}",
        "repo_hint": f"agents/chatgpt/outbox/{p.name}",
    }


def try_uia_type_to_cursor(message: str, evidence_name: str) -> dict:
    """Controlled UIA attempt: find Cursor window Edit, ValuePattern set, Enter.
    Returns structured result; never claims success without verification field.
    """
    ps = f"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
$msg = @'
{message}
'@
$root = [System.Windows.Automation.AutomationElement]::RootElement
$winCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Window)
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $winCond)
$target = $null
foreach ($w in $wins) {{
  if ($w.Current.Name -match 'Cursor') {{ $target = $w; break }}
}}
if (-not $target) {{
  @{{ status='BLOCKED'; reason='CURSOR_WINDOW_NOT_FOUND' }} | ConvertTo-Json
  exit 0
}}
$editCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Edit)
$edits = $target.FindAll([System.Windows.Automation.TreeScope]::Descendants, $editCond)
$box = $null
foreach ($e in $edits) {{
  $n = $e.Current.Name
  if ($n -match 'Chat|Agent|Ask|Message|输入|Composer|Plan') {{ $box = $e; break }}
}}
if (-not $box -and $edits.Count -gt 0) {{ $box = $edits.Item($edits.Count-1) }}
if (-not $box) {{
  @{{ status='BLOCKED'; reason='CURSOR_EDIT_NOT_FOUND'; edits=$edits.Count; window=$target.Current.Name }} | ConvertTo-Json
  exit 0
}}
try {{
  $box.SetFocus()
}} catch {{}}
$vp = $null
try {{
  $vp = $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
}} catch {{}}
$typed = $false
if ($vp) {{
  try {{ $vp.SetValue($msg); $typed = $true }} catch {{}}
}}
if (-not $typed) {{
  [System.Windows.Forms.Clipboard]::SetText($msg)
  [System.Windows.Forms.SendKeys]::SendWait('^v')
  Start-Sleep -Milliseconds 300
  $typed = $true
  $method = 'CLIPBOARD_PASTE'
}} else {{
  $method = 'VALUE_PATTERN'
}}
[System.Windows.Forms.SendKeys]::SendWait('{{ENTER}}')
Start-Sleep -Milliseconds 800
$readback = ''
try {{ if ($vp) {{ $readback = $vp.Current.Value }} }} catch {{}}
@{{
  status = 'ATTEMPTED'
  method = $method
  window = $target.Current.Name
  edit_name = $box.Current.Name
  typed = $typed
  readback_len = ($readback | Measure-Object -Character).Characters
  note = 'Enter sent; verify echo in Cursor UI evidence separately'
}} | ConvertTo-Json -Depth 4
"""
    ps_path = EVID / f"{evidence_name}_type.ps1"
    ps_path.write_text(ps, encoding="utf-8")
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    out = {"rc": r.returncode, "stdout": (r.stdout or "")[:4000], "stderr": (r.stderr or "")[:2000]}
    try:
        out["parsed"] = json.loads(r.stdout or "{}")
    except Exception:
        out["parsed"] = {"status": "BLOCKED", "reason": "UIA_PARSE_FAIL"}
    (EVID / f"{evidence_name}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def run_poll_cycles(seen: dict, cycles: int, interval: int) -> dict:
    results = []
    silent_rounds = 0
    for i in range(1, cycles + 1):
        deltas_out = scan_deltas(seen, [CFG["outbox_rel"], CFG["reviews_rel"]])
        deltas_in = scan_deltas(seen, [CFG["inbox_rel"]])
        # filter: outbox/reviews -> GPT_TO_CURSOR notify; inbox -> CURSOR_TO_GPT notify
        # exclude PILOT echo and notify messages themselves if marked
        actionable_out = [d for d in deltas_out if "PILOT_" in d["name"] or d["name"].endswith(".md")]
        # For normal operation we would notify; for cycles after preload, expect silence unless we inject
        c2g = [d for d in deltas_in if "LOCAL_AI_TWO_WINDOW" in d["key"] or "PILOT_C2G" in d["name"]]
        g2c = [d for d in actionable_out if "PILOT_G2C" in d["name"] or d["key"].startswith(CFG["outbox_rel"])]
        # Don't auto-notify on every outbox change during pilot cycles after preload —
        # only count detections. Actual sends are explicit in --pilot-send tests.
        save_seen(seen)
        silent = (len(deltas_out) + len(deltas_in)) == 0
        if silent:
            silent_rounds += 1
        rec = {
            "cycle": i,
            "at": now(),
            "deltas_out": len(deltas_out),
            "deltas_in": len(deltas_in),
            "silent": silent,
        }
        results.append(rec)
        log(f"CYCLE {i}/{cycles} silent={silent} out={len(deltas_out)} in={len(deltas_in)}")
        STATUS_LOCAL.write_text(json.dumps({"last_cycle": rec, "at": now()}, ensure_ascii=False, indent=2), encoding="utf-8")
        if i < cycles:
            time.sleep(interval)
    return {"cycles": results, "silent_rounds": silent_rounds, "interval_sec": interval}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preload-seen", action="store_true")
    ap.add_argument("--uia-probe", action="store_true")
    ap.add_argument("--poll-cycles", type=int, default=0)
    ap.add_argument("--interval", type=int, default=180)
    ap.add_argument("--write-c2g-trigger", action="store_true")
    ap.add_argument("--write-g2c-trigger", action="store_true")
    ap.add_argument("--test-id", default="")
    ap.add_argument("--record-delivery", default="", help="json file to merge as delivery evidence")
    args = ap.parse_args()

    LOGS.mkdir(parents=True, exist_ok=True)
    EVID.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)

    if not acquire_mutex():
        log("MUTEX_HELD")
        return 2
    try:
        seen = load_seen()
        out: dict = {"at": now(), "task_id": CFG["task_id"]}

        if args.preload_seen:
            n = preload_seen(seen)
            out["preload_seen"] = n
            log(f"PRELOAD_SEEN n={n}")

        if args.uia_probe:
            out["uia"] = uia_probe()
            log(f"UIA_PROBE cursor={out['uia'].get('parsed',{}).get('cursor_found')} gpt={out['uia'].get('parsed',{}).get('gpt_found')}")

        tid = args.test_id or datetime.now(CN).strftime("%Y%m%d_%H%M%S")
        if args.write_c2g_trigger:
            out["c2g_trigger"] = write_test_inbox_file(tid)
            log(f"C2G_TRIGGER {out['c2g_trigger']}")
        if args.write_g2c_trigger:
            out["g2c_trigger"] = write_test_outbox_file(tid)
            # also attempt UIA delivery of fixed message
            url = f"https://github.com/{CFG['hub_repo']}/blob/main/{out['g2c_trigger']['repo_hint']}"
            msg = fixed_msg_g2c(out["g2c_trigger"]["task_id"], url)
            out["g2c_message"] = msg
            out["g2c_uia"] = try_uia_type_to_cursor(msg, f"g2c_{tid}")
            eid = event_id("GPT_TO_CURSOR", out["g2c_trigger"]["repo_hint"], out["g2c_trigger"]["sha"])
            status = (out["g2c_uia"].get("parsed") or {}).get("status")
            rec = {
                "at": now(),
                "event_id": eid,
                "direction": "GPT_TO_CURSOR",
                "test_id": tid,
                "status": status,
                "message": msg,
                "evidence": f"evidence/g2c_{tid}.json",
            }
            if status == "ATTEMPTED":
                mark_delivered(seen, eid, rec)
            out["g2c_delivery"] = rec
            log(f"G2C_UIA status={status}")

        if args.record_delivery:
            rec = json.loads(Path(args.record_delivery).read_text(encoding="utf-8"))
            eid = rec.get("event_id") or event_id(rec.get("direction", "X"), rec.get("key", ""), rec.get("sha", ""))
            mark_delivered(seen, eid, rec)
            out["recorded"] = rec
            log(f"RECORDED {eid}")

        if args.poll_cycles > 0:
            out["poll"] = run_poll_cycles(seen, args.poll_cycles, args.interval)

        (EVID / "last_run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    finally:
        release_mutex()


if __name__ == "__main__":
    raise SystemExit(main())
