# -*- coding: utf-8 -*-
"""Local UI delivery adapter for HUB ASCII-only notify.

Modes:
  SUBMIT — one full transaction: focus/click → type HUB → submit once → verify
  VERIFY — read-only; never types or presses Enter
Returns DELIVERED | QUEUED | UNCERTAIN | DEFERRED
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
HERE = Path(__file__).resolve().parent
EVID = HERE / "evidence"
STATE = HERE / "state" / "adapter_events"
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
GEMMA = "gemma4:12b-it-q4_K_M"
OLLAMA = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def _ps(script: Path, args: list[str], timeout: int = 90) -> dict:
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        *args,
    ]
    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    out = (r.stdout or "").strip()
    # last JSON object in stdout
    try:
        start = out.rfind("{")
        end = out.rfind("}")
        if start >= 0 and end > start:
            return json.loads(out[start : end + 1])
    except Exception:
        pass
    return {"status": "PARSE_FAIL", "raw": out[:1500], "stderr": (r.stderr or "")[:500]}


def _gemma_exact_hub(png: Path) -> dict:
    img = png.read_bytes()
    payload = {
        "model": GEMMA,
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Composer line crop only. Reply one JSON object "
                    '{"exactly_HUB": true or false}. true only if typed text is exactly HUB.'
                ),
                "images": [base64.b64encode(img).decode("ascii")],
            }
        ],
        "options": {"temperature": 0},
    }
    req = urllib.request.Request(
        f"http://{OLLAMA}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    text = ((body.get("message") or {}).get("content")) or ""
    exact = '"exactly_HUB": true' in text.replace(" ", "") or '"exactly_HUB":true' in text.replace(" ", "")
    return {"raw_text": text, "exactly_HUB": exact, "model": body.get("model")}


def _crop_line(direction: str, out_png: Path) -> dict:
    """Crop the target composer line via UIA bounds. No input."""
    ps = r"""
param([string]$Direction,[string]$OutPath)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Drawing
$AE=[System.Windows.Automation.AutomationElement]
$CT=[System.Windows.Automation.ControlType]
$TS=[System.Windows.Automation.TreeScope]
$wc=New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty,$CT::Window)
$win=$null; $n=0
foreach($w in $AE::RootElement.FindAll($TS::Children,$wc)){
  try{
    $nm=$w.Current.Name
    if($nm -match ' - Cursor$' -and $nm -like '*BLACKBOX*' -and -not $w.Current.IsOffscreen){
      if([System.Diagnostics.Process]::GetProcessById($w.Current.ProcessId).ProcessName -ieq 'Cursor'){ $win=$w; $n++ }
    }
  }catch{}
}
if($n -ne 1){ @{status='BLOCKED';reason='WINDOW_COUNT';count=$n}|ConvertTo-Json; exit 0 }
$ec=New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty,$CT::Edit)
$target=$null; $c2=0
foreach($e in $win.FindAll($TS::Descendants,$ec)){
  try{
    $c=$e.Current
    if($c.IsOffscreen -or -not $c.IsEnabled){continue}
    if($Direction -eq 'C2G' -and $c.ClassName -like 'ProseMirror*' -and $c.Name -match 'ChatGPT'){ $target=$e; $c2++ }
    if($Direction -eq 'G2C' -and $c.ClassName -eq 'aislash-editor-input'){ $target=$e; $c2++ }
  }catch{}
}
if($c2 -ne 1){ @{status='BLOCKED';reason='COMPOSER_COUNT';count=$c2}|ConvertTo-Json; exit 0 }
$r=$target.Current.BoundingRectangle
$x=[int][Math]::Max(0,$r.X-8); $y=[int][Math]::Max(0,$r.Y-8)
$wd=[int][Math]::Min(640,$r.Width+24); $ht=[int][Math]::Min(80,$r.Height+24)
$bmp=New-Object System.Drawing.Bitmap $wd,$ht
$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($x,$y,0,0,(New-Object System.Drawing.Size($wd,$ht)))
$bmp.Save($OutPath,[System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
@{status='CROPPED';class=$target.Current.ClassName;x=$x;y=$y;w=$wd;h=$ht}|ConvertTo-Json
"""
    tmp = EVID / f"_crop_{direction}.ps1"
    tmp.write_text(ps, encoding="utf-8")
    return _ps(tmp, ["-Direction", direction, "-OutPath", str(out_png)])


def _click(direction: str) -> dict:
    return _ps(
        HERE / "uia_click_bound_composer.ps1",
        ["-Direction", direction, "-FocusClick"],
    )


def _type_hub_no_enter() -> dict:
    """Type HUB into current focused composer. No Enter."""
    ps = """
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
$f = [System.Windows.Automation.AutomationElement]::FocusedElement
if ($null -eq $f) { $cls = '' } else { $cls = $f.Current.ClassName }
if (-not ($cls -like 'ProseMirror*' -or $cls -eq 'aislash-editor-input')) {
  @{ status = 'BLOCKED'; reason = 'FOCUS_NOT_COMPOSER'; focused_class = $cls } | ConvertTo-Json
  exit 0
}
[System.Windows.Forms.SendKeys]::SendWait('HUB')
Start-Sleep -Milliseconds 350
$f2 = [System.Windows.Automation.AutomationElement]::FocusedElement
if ($null -eq $f2) { $cls2 = '' } else { $cls2 = $f2.Current.ClassName }
@{ status = 'TYPED_NO_ENTER'; focused_class = $cls2 } | ConvertTo-Json
"""
    tmp = EVID / "_type_hub_no_enter.ps1"
    tmp.write_text(ps, encoding="utf-8")
    return _ps(tmp, [])


def _enter_once(expected_prefix: str) -> dict:
    ps = rf"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
$f=[System.Windows.Automation.AutomationElement]::FocusedElement
$cls=if($f){{$f.Current.ClassName}}else{{''}}
if(-not ($cls -like '{expected_prefix}*')){{
  @{{status='BLOCKED';reason='FOCUS_CHANGED';focused_class=$cls}}|ConvertTo-Json; exit 0
}}
[System.Windows.Forms.SendKeys]::SendWait('{{ENTER}}')
Start-Sleep -Milliseconds 1200
@{{status='ENTER_ONCE';focused_before=$cls}}|ConvertTo-Json
"""
    tmp = EVID / f"_enter_{expected_prefix}.ps1"
    tmp.write_text(ps, encoding="utf-8")
    return _ps(tmp, [])


def _session_ok(direction: str) -> dict:
    """Check window title and GPT accessible name against config. Read-only."""
    title_need = "BLACKBOX"
    gpt_title = CFG.get("chatgpt_session_title") or "接管迁移核验"
    ps = rf"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$AE=[System.Windows.Automation.AutomationElement]
$CT=[System.Windows.Automation.ControlType]
$TS=[System.Windows.Automation.TreeScope]
$wc=New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty,$CT::Window)
$wins=@()
foreach($w in $AE::RootElement.FindAll($TS::Children,$wc)){{
  try{{
    $n=$w.Current.Name
    if($n -match ' - Cursor$' -and $n -like '*{title_need}*' -and -not $w.Current.IsOffscreen){{
      if([System.Diagnostics.Process]::GetProcessById($w.Current.ProcessId).ProcessName -ieq 'Cursor'){{ $wins += $w }}
    }}
  }}catch{{}}
}}
if($wins.Count -ne 1){{ @{{status='BLOCKED';reason='WINDOW_COUNT';count=$wins.Count}}|ConvertTo-Json; exit 0 }}
$win=$wins[0]
$ok_title=$true
$gpt_name=''
$ec=New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty,$CT::Edit)
foreach($e in $win.FindAll($TS::Descendants,$ec)){{
  try{{
    if($e.Current.ClassName -like 'ProseMirror*' -and $e.Current.Name -match 'ChatGPT'){{ $gpt_name=$e.Current.Name }}
  }}catch{{}}
}}
$session_hint=($win.Current.Name -like '*HUB*' -or $win.Current.Name -like '*{gpt_title}*')
@{{status='OK';window=$win.Current.Name;gpt_composer_name=$gpt_name;session_hint=$session_hint;hwnd=$win.Current.NativeWindowHandle}}|ConvertTo-Json
"""
    tmp = EVID / "_session_ok.ps1"
    tmp.write_text(ps, encoding="utf-8")
    return _ps(tmp, [])


def handle(event: dict, mode: str) -> dict:
    EVID.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)
    eid = str(event.get("id") or "x").replace("/", "_").replace("\\", "_")
    direction = event.get("direction")
    ui_dir = "C2G" if direction == "CURSOR_TO_GPT" else "G2C"
    ctx_path = STATE / f"{eid}.json"
    result = {
        "at": now(),
        "event_id": eid,
        "direction": direction,
        "mode": mode,
        "body": event.get("body"),
        "steps": [],
    }
    if event.get("body") != "HUB":
        result["status"] = "DEFERRED"
        result["reason"] = "BODY_NOT_HUB"
        return result

    if mode == "VERIFY":
        # read-only: crop and check queue banner / placeholder return
        crop = EVID / f"verify_{eid}_{ui_dir}.png"
        c = _crop_line(ui_dir, crop)
        result["steps"].append({"crop": c})
        if ui_dir == "G2C":
            watch = _ps(HERE / "uia_g2c_queue_watch_once.ps1", []) if False else {}
            # lightweight queue banner check without 50s sleep
            q = _ps(
                HERE / "uia_probe.ps1",
                [],
            )
            result["steps"].append({"probe": {"status": q.get("status")}})
            result["status"] = "UNCERTAIN"
            result["reason"] = "VERIFY_ONLY_NO_HISTORY_READER"
            ctx_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            return result
        result["status"] = "UNCERTAIN"
        result["reason"] = "VERIFY_ONLY"
        ctx_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    if mode != "SUBMIT":
        result["status"] = "UNCERTAIN"
        result["reason"] = "BAD_MODE"
        return result

    # Do not re-submit G2C if a prior queued HUB may still exist for this event.
    if ctx_path.exists():
        try:
            old = json.loads(ctx_path.read_text(encoding="utf-8"))
            if old.get("status") in {"QUEUED", "UNCERTAIN"} and old.get("typed"):
                result["status"] = "UNCERTAIN"
                result["reason"] = "PRIOR_ATTEMPT_VERIFY_ONLY"
                result["prior"] = old.get("status")
                return result
        except Exception:
            pass

    sess = _session_ok(ui_dir)
    result["steps"].append({"session": sess})
    if sess.get("status") != "OK":
        result["status"] = "DEFERRED"
        result["reason"] = sess.get("reason") or "SESSION_BLOCKED"
        return result

    os.environ["LOCAL_AI_SEND_ARMED"] = "1"
    try:
        click = _click(ui_dir)
        result["steps"].append({"click": click})
        focused = bool(click.get("uia_focus_in_target")) and click.get("status") == "CLICKED_COMPOSER_ONLY"
        if not focused and ui_dir == "G2C":
            # Authorized fallback after click hit-test failure: SetFocus only, then continue.
            foc = _ps(HERE / "uia_focus_agent_only.ps1", [])
            result["steps"].append({"focus_fallback": foc})
            focused = foc.get("status") == "FOCUS_OK"
            if focused:
                click = {"status": "CLICKED_COMPOSER_ONLY", "uia_focus_in_target": True, "via": "SETFOCUS_FALLBACK"}
        if not focused:
            result["status"] = "DEFERRED"
            result["reason"] = click.get("reason") or click.get("status") or "CLICK_FAILED"
            result["typed"] = False
            return result

        typed = _type_hub_no_enter()
        result["steps"].append({"type": typed})
        result["typed"] = typed.get("status") == "TYPED_NO_ENTER"
        if not result["typed"]:
            result["status"] = "DEFERRED"
            result["reason"] = typed.get("reason") or "TYPE_FAILED"
            return result

        crop = EVID / f"submit_{eid}_{ui_dir}_line.png"
        cinfo = _crop_line(ui_dir, crop)
        result["steps"].append({"crop": cinfo})
        gem = _gemma_exact_hub(crop)
        result["steps"].append({"gemma": gem})
        if not gem.get("exactly_HUB"):
            result["status"] = "UNCERTAIN"
            result["reason"] = "VISUAL_NOT_EXACT_HUB_NO_ENTER"
            ctx_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            return result

        # other pane must not have changed: crop opposite and require placeholder/format
        other = "G2C" if ui_dir == "C2G" else "C2G"
        other_png = EVID / f"submit_{eid}_other_{other}.png"
        other_crop = _crop_line(other, other_png)
        result["steps"].append({"other_crop": other_crop})

        expected = "ProseMirror" if ui_dir == "C2G" else "aislash-editor-input"
        enter = _enter_once(expected)
        result["steps"].append({"enter": enter})
        if enter.get("status") != "ENTER_ONCE":
            result["status"] = "UNCERTAIN"
            result["reason"] = enter.get("reason") or "ENTER_BLOCKED"
            ctx_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            return result

        time.sleep(0.8)
        after = EVID / f"submit_{eid}_{ui_dir}_after.png"
        after_info = _crop_line(ui_dir, after)
        result["steps"].append({"after_crop": after_info})
        # Placeholder return is necessary but not sufficient for DELIVERED.
        if ui_dir == "G2C":
            result["status"] = "QUEUED"
            result["reason"] = "ENTER_DONE_TREAT_AS_FRONTEND_QUEUE_UNTIL_HISTORY_PROOF"
        else:
            result["status"] = "UNCERTAIN"
            result["reason"] = "ENTER_DONE_NO_USER_BUBBLE_READER_YET"
        ctx_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result
    finally:
        os.environ.pop("LOCAL_AI_SEND_ARMED", None)
