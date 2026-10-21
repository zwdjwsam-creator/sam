# -*- coding: utf-8 -*-
"""Local AI Operator — Gemma4 decides; constrained UIA controller executes.

NO BLACKBOX business writes. Fixed notices only. UTF-8 throughout.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
HERE = Path(__file__).resolve().parent
STATE = HERE / "state"
LOGS = HERE / "logs"
EVID = HERE / "evidence"
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
OLLAMA = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
GEMMA = "gemma4:12b-it-q4_K_M"
ALLOWED = {
    "NOOP",
    "SCREENSHOT",
    "INSPECT",
    "SCROLL_CHAT_BOTTOM",
    "FOCUS_KNOWN_COMPOSER",
    "TYPE_FIXED_NOTICE",
    "SEND",
    "VERIFY_DELIVERY",
    "BLOCKED_G2C",
    "BLOCKED_C2G",
    "WAIT",
}


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def log(msg: str) -> None:
    line = f"{now()} {msg}"
    print(line, flush=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    with (LOGS / "operator.out.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def ollama_chat(prompt: str, images: list | None = None) -> dict:
    """Call local Gemma; return raw + parsed JSON action if possible."""
    payload = {
        "model": GEMMA,
        "stream": False,
        "keep_alive": "30m",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a constrained Windows dual-window notifier operator. "
                    "Output ONLY one JSON object with keys: action, target, reason, "
                    "message_id. action must be one of: "
                    + ",".join(sorted(ALLOWED))
                    + ". Never invent shell commands. Never claim delivery without verify."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": 0.1},
    }
    if images:
        # vision path: put image on last user message if API supports
        payload["messages"][-1]["images"] = images
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://{OLLAMA}/api/chat",
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    text = ((body.get("message") or {}).get("content")) or ""
    parsed = None
    # extract JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
        except Exception:
            parsed = None
    return {"raw_text": text, "parsed": parsed, "model": body.get("model")}


def uia_inspect() -> dict:
    ps1 = HERE / "uia_deep_cursor.ps1"
    # force prefer - Cursor window: rewrite probe call via send script preference
    r = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(HERE / "uia_probe.ps1"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    try:
        parsed = json.loads(r.stdout or "{}")
    except Exception:
        parsed = {"status": "PARSE_FAIL", "raw": (r.stdout or "")[:2000]}
    return parsed


def agent_composer_unique(inspect: dict) -> bool:
    """Fresh class identity: exactly one visible aislash-editor-input. Names are not used."""
    r = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(HERE / "uia_send_hub_once.ps1"),
            "-Direction",
            "G2C",
            "-Mode",
            "Verify",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    try:
        d = json.loads(r.stdout or "{}")
    except Exception:
        d = {}
    (EVID / "uia_class_verify.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return int(d.get("agent_count") or 0) == 1 and d.get("status") == "VERIFY_ONLY"


def fixed_c2g(url: str) -> str:
    # TWO_SIGNAL contract: body is ASCII HUB only. URL stays in the event record, never in the keystroke.
    return "HUB"


def fixed_g2c(url: str) -> str:
    return "HUB"


def send_armed() -> bool:
    return os.environ.get("LOCAL_AI_SEND_ARMED") == "1"


def _hub_once(direction: str, mode: str, message_id: str | None) -> dict:
    """Send and verify are different modes. Verify never writes."""
    ev = EVID / f"hub_once_{direction}_{mode}_{message_id or 'x'}.json"
    r = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(HERE / "uia_send_hub_once.ps1"),
            "-Direction",
            direction,
            "-Mode",
            mode,
            "-EvidencePath",
            str(ev),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    try:
        return json.loads(r.stdout or "{}")
    except Exception:
        return {"status": "PARSE_FAIL", "raw": (r.stdout or "")[:1500]}


def decide_and_act(event: dict) -> dict:
    """event: direction, url, message_id, uia_summary"""
    EVID.mkdir(parents=True, exist_ok=True)
    inspect = uia_inspect()
    unique_agent = agent_composer_unique(inspect)
    summary = {
        "direction": event.get("direction"),
        "url": event.get("url"),
        "message_id": event.get("message_id"),
        "cursor_found": bool((inspect or {}).get("cursor_found")),
        "gpt_found_top_level": bool((inspect or {}).get("gpt_found")),
        "agent_composer_unique": unique_agent,
        "window_hits": (inspect or {}).get("window_hits"),
    }
    prompt = (
        "Decide next allowed action for dual-window HUB notifier.\n"
        + json.dumps(summary, ensure_ascii=False, indent=2)
        + "\nRules: If direction=GPT_TO_CURSOR and agent_composer_unique is false, "
        "action must be BLOCKED_G2C. If direction=CURSOR_TO_GPT and Cursor window "
        "exists with ChatGPT composer, prefer TYPE_FIXED_NOTICE then VERIFY_DELIVERY. "
        "Do not send to wrong window."
    )
    decision = ollama_chat(prompt)
    parsed = decision.get("parsed") or {}
    action = parsed.get("action") or "NOOP"
    if action not in ALLOWED:
        action = "NOOP"
    # hard safety overrides
    if event.get("direction") == "GPT_TO_CURSOR" and not unique_agent:
        action = "BLOCKED_G2C"
    result = {
        "at": now(),
        "event": event,
        "uia_summary": summary,
        "gemma_decision": decision,
        "action_executed": action,
        "delivery": None,
    }
    if not send_armed() and action in {"TYPE_FIXED_NOTICE", "SEND", "VERIFY_DELIVERY"}:
        action = "WAIT"
        result["action_executed"] = action
        result["delivery"] = {"status": "QUEUE_ONLY", "reason": "SEND_NOT_ARMED", "body": "HUB"}
    elif action == "BLOCKED_G2C":
        result["delivery"] = {"status": "BLOCKED_G2C", "reason": "AGENT_COMPOSER_NOT_UNIQUE"}
    elif action == "VERIFY_DELIVERY":
        direction = "C2G" if event.get("direction") == "CURSOR_TO_GPT" else "G2C"
        result["delivery"] = _hub_once(direction, "Verify", event.get("message_id"))
        result["message_utf8"] = "HUB"
    elif action in {"TYPE_FIXED_NOTICE", "SEND"} and event.get("direction") in {"CURSOR_TO_GPT", "GPT_TO_CURSOR"}:
        direction = "C2G" if event.get("direction") == "CURSOR_TO_GPT" else "G2C"
        result["delivery"] = _hub_once(direction, "Send", event.get("message_id"))
        result["message_utf8"] = "HUB"
    else:
        result["delivery"] = {"status": action}
    outp = EVID / f"operator_{event.get('message_id','x')}.json"
    outp.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"ACTION {action} dir={event.get('direction')} delivery={(result.get('delivery') or {}).get('status')}")
    return result


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test-gemma", action="store_true")
    ap.add_argument("--event-json", default="")
    args = ap.parse_args()
    LOGS.mkdir(parents=True, exist_ok=True)
    EVID.mkdir(parents=True, exist_ok=True)
    if args.self_test_gemma:
        d = ollama_chat(
            'Return JSON {"action":"NOOP","target":"none","reason":"self_test","message_id":"t0"}'
        )
        (EVID / "gemma_self_test.json").write_text(
            json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps({"ok": True, "parsed": d.get("parsed"), "has_raw": bool(d.get("raw_text"))}, ensure_ascii=False))
        return 0
    if args.event_json:
        event = json.loads(Path(args.event_json).read_text(encoding="utf-8"))
        print(json.dumps(decide_and_act(event), ensure_ascii=False, indent=2))
        return 0
    print("usage: --self-test-gemma | --event-json path")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
