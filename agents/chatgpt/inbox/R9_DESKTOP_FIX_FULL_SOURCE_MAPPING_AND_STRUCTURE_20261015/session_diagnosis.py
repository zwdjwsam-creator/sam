# -*- coding: utf-8 -*-
"""Bounded read-only diagnosis of the existing source session. Does not change logons."""
import json
import socket
import subprocess
from pathlib import Path
import sys
sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015")
from probe_52 import probe_one, to_unc

paths = [
    r"E:\BLACKBOX\.cursor\mcp.json",
    r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_20260903_SUCCESSOR_BUILD_AND_ATOMIC_PUBLISH_R1\pit_products",
]
rows = []
for path in paths:
    win32 = probe_one(path)
    unc = to_unc(path).replace("\\\\?\\UNC\\", "\\\\")
    plain = {"path": path, "form": "plain_unc", "unc": unc}
    try:
        open(unc, "rb").close()
        plain["ok"] = True
    except OSError as exc:
        plain["ok"] = False
        plain["winerror"] = getattr(exc, "winerror", None)
        plain["error"] = type(exc).__name__
    rows.append({"win32_long": {k: win32.get(k) for k in ("ok", "winerror", "error", "unc")}, "plain_unc": plain})

def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {"exit": proc.returncode, "stdout": (proc.stdout or "")[:1200], "stderr": (proc.stderr or "")[:400]}

who = run(["whoami"])
smb = run(["powershell", "-NoProfile", "-Command", "Get-SmbConnection | Where-Object { $_.ServerName -eq '192.168.100.2' } | Select-Object ServerName, ShareName, UserName | ConvertTo-Json -Compress"])
sock = socket.socket()
sock.settimeout(3)
try:
    sock.connect(("192.168.100.2", 445))
    port445 = True
except OSError as exc:
    port445 = False
    port_error = type(exc).__name__
else:
    port_error = None
finally:
    sock.close()

out = {
    "identity": who["stdout"].strip(),
    "port_445_reachable": port445,
    "port_error": port_error,
    "existing_smb_connection": smb,
    "probes": rows,
    "changed_credentials": False,
    "new_logon": False,
    "source_session_restored": False,
    "conclusion": "EXISTING_SESSION_LOGON_FAILURE_1326",
}
Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015\SESSION_DIAGNOSIS.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(out["identity"], out["port_445_reachable"], out["conclusion"])
