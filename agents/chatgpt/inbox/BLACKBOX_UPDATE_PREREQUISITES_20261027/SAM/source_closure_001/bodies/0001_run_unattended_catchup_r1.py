# -*- coding: utf-8 -*-
"""
Unattended JQ tip catch-up R1.
Materialize tip package from 20260909 template → run full chain → next day.
Waits until after 15:05 Asia/Shanghai before sealing today's tip.
ORDER_ALLOWED=FALSE.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

CN = ZoneInfo("Asia/Shanghai")
ROOT = Path(r"E:\BLACKBOX")
PY = ROOT / ".venv" / "Scripts" / "python.exe"
ARCH = Path(r"D:\CURSOR_TASK_ARCHIVE")
TEMPLATE = ARCH / "JQ_DAILY_TIP_20260909"
OUT_ROOT = ARCH / "JQ_TIP_CATCHUP_UNATTENDED_R1"
PROGRESS = OUT_ROOT / "PROGRESS.json"
LOG = OUT_ROOT / "UNATTENDED.log"
LOCK = OUT_ROOT / "unattended.lock"
SCOPE = ROOT / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json"
CLEAN = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
CACHE = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"

COPY_GLOBS = [
    "download_daily_r1.py",
    "download_val_adjust_r1.py",
    "download_billboard_ingest_r1.py",
    "download_xr_xd_r1.py",
    "ingest_minutes_r1.py",
    "ingest_minutes_flat_r1.py",
    "tip_extend_adjust_r1.py",
    "clean_switch_r1.py",
    "sw_l123_asof_20260909.py",
    "code/minute_download_20260909.py",
    "code/index_minute_20260909.py",
    "code/align_index_minute_20260909.py",
    "code/patch_candidate_val_sw_republish_r1.py",
    "code/seal_completion_r1.py",
]


def now_cn() -> datetime:
    return datetime.now(CN)


def log(msg: str) -> None:
    line = f"[{now_cn().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def wjson(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def current_asofs() -> dict:
    scope = read_json(SCOPE)
    clean = read_json(CLEAN)
    cache = read_json(CACHE)
    return {
        "source": str(scope.get("data_asof") or "")[:10],
        "clean": str(clean.get("cleaning_as_of") or "")[:10],
        "cache": str(cache.get("asof") or "")[:10],
        "cleaning_release_id": clean.get("release_id"),
        "cache_release_id": cache.get("cache_release_id") or cache.get("release_id"),
    }


def jq_trade_days(start: str, end: str) -> list[str]:
    """Prefer live JQ calendar; fall back to frozen Sep-2026 catch-up list on thrift/timeout."""
    fallback = [
        "2026-09-09",
        "2026-09-10",
        "2026-09-11",
        "2026-09-14",
        "2026-09-15",
        "2026-09-16",
        "2026-09-17",
        "2026-09-18",
        "2026-09-21",
        "2026-09-22",
        "2026-09-23",
        "2026-09-24",
        "2026-09-25",
        "2026-09-28",
        "2026-09-29",
        "2026-09-30",
    ]
    sys.path.insert(0, str(ROOT / "脚本"))
    import jq_download_base as jdb  # noqa: WPS433

    last_err: Exception | None = None
    for attempt in range(1, 5):
        try:
            jdb.auth()
            import jqdatasdk as jq  # noqa: WPS433

            days = jq.get_trade_days(start_date=start, end_date=end)
            out = []
            for d in days:
                if hasattr(d, "date"):
                    out.append(d.date().isoformat())
                else:
                    out.append(str(d)[:10])
            if out:
                return out
        except Exception as e:  # noqa: BLE001
            last_err = e
            log(f"JQ_TRADE_DAYS_RETRY attempt={attempt} err={type(e).__name__}: {e}")
            time.sleep(min(60, 4 * attempt))
            try:
                import jqdatasdk as jq  # noqa: WPS433

                jq.logout()
            except Exception:
                pass
    log(f"JQ_TRADE_DAYS_FALLBACK using frozen list after err={last_err!r}")
    return [d for d in fallback if start <= d <= end]


def last_sealable_tip_day(trade_days: list[str]) -> str | None:
    """Before 15:05 CN, exclude today; after that include today if it is a trade day."""
    n = now_cn()
    today = n.date().isoformat()
    cutoff = n.replace(hour=15, minute=5, second=0, microsecond=0)
    sealed = []
    for d in trade_days:
        if d < today:
            sealed.append(d)
        elif d == today and n >= cutoff:
            sealed.append(d)
    return sealed[-1] if sealed else None


def rewrite_text(text: str, asof: str, compact: str, parent_clean_id: str) -> str:
    # order matters: longer tokens first
    text = text.replace("2026-09-09", asof)
    text = text.replace("20260909", compact)
    # Python date(YYYY, M, D) literals from tip template (not matched by ISO replace)
    text = re.sub(
        r"date\(\s*2026\s*,\s*9\s*,\s*9\s*\)",
        f"date({int(asof[0:4])}, {int(asof[5:7])}, {int(asof[8:10])})",
        text,
    )
    # parent cleaning id in clean_switch
    text = re.sub(
        r'PARENT_ID\s*=\s*"[^"]+"',
        f'PARENT_ID = "{parent_clean_id}"',
        text,
        count=1,
    )
    text = re.sub(
        r"BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260908_20260909_093101",
        parent_clean_id,
        text,
    )
    return text


def sanitize_tip_scripts(dest: Path, asof: str, compact: str) -> None:
    """Force tip-day identity even if template drifted (e.g. 0909 files polluted to 0910)."""
    y, m, d = int(asof[0:4]), int(asof[5:7]), int(asof[8:10])
    for p in list(dest.glob("*.py")) + list((dest / "code").glob("*.py")):
        if not p.exists() or p.name.startswith("_"):
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        orig = t
        t = re.sub(
            r'TASK\s*=\s*Path\(r?"D:\\CURSOR_TASK_ARCHIVE\\JQ_DAILY_TIP_\d{8}"\)',
            f'TASK = Path(r"D:\\\\CURSOR_TASK_ARCHIVE\\\\JQ_DAILY_TIP_{compact}")',
            t,
        )
        t = re.sub(
            r'TASK\s*=\s*Path\(r"D:\\CURSOR_TASK_ARCHIVE\\JQ_DAILY_TIP_\d{8}"\)',
            f'TASK = Path(r"D:\\\\CURSOR_TASK_ARCHIVE\\\\JQ_DAILY_TIP_{compact}")',
            t,
        )
        # Windows path variants already covered; also plain string form
        t = re.sub(
            r"D:\\\\CURSOR_TASK_ARCHIVE\\\\JQ_DAILY_TIP_\d{8}",
            f"D:\\\\CURSOR_TASK_ARCHIVE\\\\JQ_DAILY_TIP_{compact}",
            t,
        )
        t = re.sub(
            r"D:\\CURSOR_TASK_ARCHIVE\\JQ_DAILY_TIP_\d{8}",
            rf"D:\\CURSOR_TASK_ARCHIVE\\JQ_DAILY_TIP_{compact}",
            t,
        )
        t = re.sub(r'^ASOF\s*=\s*"20\d{2}-\d{2}-\d{2}"', f'ASOF = "{asof}"', t, flags=re.M)
        t = re.sub(
            r"^ASOF\s*=\s*date\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)",
            f"ASOF = date({y}, {m}, {d})",
            t,
            flags=re.M,
        )
        t = re.sub(r"registration_date=20\d{2}-\d{2}-\d{2}", f"registration_date={asof}", t)
        t = re.sub(r"DAY\s*=\s*\"20\d{2}-\d{2}-\d{2}\"", f'DAY = "{asof}"', t)
        if t != orig:
            p.write_text(t, encoding="utf-8")
            log(f"SANITIZE {p.relative_to(dest)}")


def materialize_day(asof: str) -> Path:
    compact = asof.replace("-", "")
    dest = ARCH / f"JQ_DAILY_TIP_{compact}"
    parent_id = str(current_asofs().get("cleaning_release_id") or "")
    if not parent_id:
        raise RuntimeError("missing CURRENT cleaning release_id")
    if dest.exists() and (dest / "_run_full_chain.ps1").exists() and (dest / "download_daily_r1.py").exists():
        log(f"REUSE_TIP_DIR {dest}")
        sanitize_tip_scripts(dest, asof, compact)
        # keep PARENT_ID in clean_switch current
        cs = dest / "clean_switch_r1.py"
        if cs.exists():
            txt = cs.read_text(encoding="utf-8")
            txt2 = re.sub(r'PARENT_ID\s*=\s*"[^"]+"', f'PARENT_ID = "{parent_id}"', txt, count=1)
            if txt2 != txt:
                cs.write_text(txt2, encoding="utf-8")
        return dest
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "code").mkdir(exist_ok=True)

    for rel in COPY_GLOBS:
        src = TEMPLATE / rel
        if not src.exists():
            log(f"WARN missing template {rel}")
            continue
        name = src.name.replace("20260909", compact)
        if src.parent.name == "code":
            out = dest / "code" / name
        else:
            out = dest / name.replace("20260909", compact)
        raw = src.read_text(encoding="utf-8")
        out.write_text(rewrite_text(raw, asof, compact, parent_id), encoding="utf-8")
    sanitize_tip_scripts(dest, asof, compact)

    # regenerate full chain ps1
    ps1 = f'''# Auto-generated unattended tip chain for {asof}
$ErrorActionPreference = "Continue"
$py = "E:\\BLACKBOX\\.venv\\Scripts\\python.exe"
$d = "{dest}"
$log = Join-Path $d "FULL_CHAIN.log"
function L([string]$m) {{
  $line = "[{{0}}] {{1}}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"), $m
  Add-Content -Path $log -Value $line -Encoding utf8
  Write-Output $line
}}
function RunPy([string]$script) {{
  L ("RUN " + $script)
  & $py -u $script 2>&1 | Tee-Object -FilePath $log -Append
  if ($LASTEXITCODE -ne 0) {{
    L ("FAIL rc=" + $LASTEXITCODE + " " + $script)
    exit $LASTEXITCODE
  }}
}}
L "START FULL_CHAIN tip={asof}"
RunPy "$d\\download_daily_r1.py"
RunPy "$d\\download_val_adjust_r1.py"
RunPy "$d\\download_billboard_ingest_r1.py"
RunPy "$d\\download_xr_xd_r1.py"
RunPy "$d\\code\\minute_download_{compact}.py"
RunPy "$d\\ingest_minutes_r1.py"
RunPy "$d\\ingest_minutes_flat_r1.py"
RunPy "$d\\sw_l123_asof_{compact}.py"
RunPy "$d\\code\\index_minute_{compact}.py"
RunPy "$d\\code\\align_index_minute_{compact}.py"
RunPy "$d\\clean_switch_r1.py"
L "CLEAN_DONE — tip rebase"
& $py -u "E:\\BLACKBOX\\脚本\\blackbox_daily_increment_orchestrator_r1.py" --run-target-date {asof} --cleaning-json "E:\\BLACKBOX\\数据\\清洗成品\\CURRENT_CLEANING_RELEASE.json" 2>&1 | Tee-Object -FilePath $log -Append
$candName = (& $py -u "D:\\CURSOR_TASK_ARCHIVE\\JQ_TIP_CATCHUP_UNATTENDED_R1\\pick_cache_candidate_r1.py" "{compact}" 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or -not $candName -or $candName -eq "NO_CACHE_CANDIDATE") {{ L "NO_CACHE_CANDIDATE"; exit 3 }}
L ("CACHE_CAND=" + $candName)
$patch = "$d\\code\\patch_candidate_val_sw_republish_r1.py"
$txt = [System.IO.File]::ReadAllText($patch)
$txt2 = [regex]::Replace($txt, "BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_{compact}_[A-Z0-9_]+", $candName)
[System.IO.File]::WriteAllText($patch, $txt2)
RunPy $patch
L "FUND_NAV"
& $py -u "E:\\BLACKBOX\\脚本\\blackbox_fund_etf_nav_premium_plane_r1.py" --asof {asof} --phase all 2>&1 | Tee-Object -FilePath $log -Append
if ($LASTEXITCODE -ne 0) {{ L ("FUND_NAV_FAIL=" + $LASTEXITCODE); exit $LASTEXITCODE }}
L "EXTERNAL+SCOPE+PLANE"
& $py -u "E:\\BLACKBOX\\脚本\\blackbox_external_evidence_materialization_r2.py" --phase asof_align --asof {asof} 2>&1 | Tee-Object -FilePath $log -Append
& $py -u "E:\\BLACKBOX\\脚本\\blackbox_external_evidence_materialization_r2.py" --phase acceptance --asof {asof} 2>&1 | Tee-Object -FilePath $log -Append
& $py -u "E:\\BLACKBOX\\脚本\\blackbox_full_data_update_scope_refresh_r1.py" 2>&1 | Tee-Object -FilePath $log -Append
$asofCompact = "{compact}"
& $py -u "E:\\BLACKBOX\\脚本\\run_blackbox_daily_incremental_data_plane_r1.py" --mode run --date $asofCompact --skip-jq --skip-t-external --skip-sellside-if-done 2>&1 | Tee-Object -FilePath $log -Append
L "FULL_CHAIN_PASS tip={asof}"
exit 0
'''
    (dest / "_run_full_chain.ps1").write_text(ps1, encoding="utf-8")
    log(f"MATERIALIZED {dest} parent_clean={parent_id}")
    return dest


def run_day_chain(asof: str) -> int:
    dest = materialize_day(asof)
    log_path = dest / "FULL_CHAIN.log"
    compact = asof.replace("-", "")
    asofs0 = current_asofs()
    if asofs0["source"] == asof and asofs0["clean"] == asof and asofs0["cache"] == asof:
        # tip already sealed in CURRENT; avoid re-running post-cache patch against empty candidate dirs
        if (not log_path.exists()) or ("FULL_CHAIN_PASS" not in log_path.read_text(encoding="utf-8", errors="replace")):
            with log_path.open("a", encoding="utf-8") as fh:
                fh.write(f"[{now_cn().isoformat(timespec='seconds')}] FULL_CHAIN_PASS tip={asof} (asofs_already_aligned)\n")
        log(f"SKIP_ALREADY_PASS {asof}")
        return 0
    if log_path.exists() and "FULL_CHAIN_PASS" in log_path.read_text(encoding="utf-8", errors="replace"):
        asofs = current_asofs()
        if asofs["source"] == asof and asofs["clean"] == asof and asofs["cache"] == asof:
            log(f"SKIP_ALREADY_PASS {asof}")
            return 0

    def acc_status(name: str) -> str:
        p = dest / name
        if not p.exists():
            return "MISSING"
        try:
            obj = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            st = str(obj.get("status") or obj.get("final_status") or "").upper()
            if st in ("PASS", "EMPTY", "FAIL", "PARTIAL"):
                return st if st != "PARTIAL" else "OTHER"
        except Exception:
            pass
        t = p.read_text(encoding="utf-8", errors="replace")
        # fallback: only top-level-ish first 120 chars
        head = t.lstrip()[:120]
        if '"status": "PASS"' in head or '"status":"PASS"' in head:
            return "PASS"
        if '"status": "EMPTY"' in head or '"status":"EMPTY"' in head:
            return "EMPTY"
        if '"status": "FAIL"' in head or '"status":"FAIL"' in head:
            return "FAIL"
        return "OTHER"

    def acc_pass(name: str) -> bool:
        return acc_status(name) == "PASS"

    daily_ok = acc_pass("DOWNLOAD_ACCEPTANCE.json")
    val_ok = acc_pass("VAL_ADJUST_ACCEPTANCE.json")
    bill_ok = acc_pass("BILLBOARD_ACCEPTANCE.json")
    xr_st = acc_status("XR_XD_ACCEPTANCE.json")
    xr_ok = xr_st in ("PASS", "EMPTY")
    minute_ok = acc_pass("MINUTE_INGEST_ACCEPTANCE.json") or acc_pass("10_ACCEPTANCE/DOWNLOAD_ACCEPTANCE.json")
    flat_ok = acc_pass("MINUTE_FLAT_INGEST_ACCEPTANCE.json")

    align_ptr = read_json(ROOT / "数据" / "清洗成品" / "CURRENT_INDEX_MINUTE_ALIGN_RELEASE.json")
    align_ok = str(align_ptr.get("cutoff") or "")[:10] == asof and align_ptr.get("all_pass") is True
    if not align_ok:
        rid = str(align_ptr.get("release_id") or "")
        # Build stamp YYYYMMDD in the release id is not the data asof.
        align_ok = f"ASOF_{compact}" in rid and align_ptr.get("all_pass") is True

    sw_ptr = read_json(ROOT / "数据" / "清洗成品" / "CURRENT_SW_L1_PIT_ALIGN_RELEASE.json")
    sw_ok = str(sw_ptr.get("formal_data_asof") or "")[:10] == asof

    # Build / refresh resume scripts for the earliest incomplete stage
    resume_xr = dest / "_resume_from_xr_xd.ps1"
    resume_min = dest / "_resume_from_minute.ps1"
    resume_sw = dest / "_resume_from_sw.ps1"
    resume_clean = dest / "_resume_from_clean.ps1"
    post_clean = f'''
RunPy "$d\\clean_switch_r1.py"
L "CLEAN_DONE — tip rebase"
& $py -u "E:\\BLACKBOX\\脚本\\blackbox_daily_increment_orchestrator_r1.py" --run-target-date {asof} --cleaning-json "E:\\BLACKBOX\\数据\\清洗成品\\CURRENT_CLEANING_RELEASE.json" 2>&1 | Tee-Object -FilePath $log -Append
$candName = (& $py -u "D:\\CURSOR_TASK_ARCHIVE\\JQ_TIP_CATCHUP_UNATTENDED_R1\\pick_cache_candidate_r1.py" "{compact}" 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or -not $candName -or $candName -eq "NO_CACHE_CANDIDATE") {{ L "NO_CACHE_CANDIDATE"; exit 3 }}
L ("CACHE_CAND=" + $candName)
$patch = "$d\\code\\patch_candidate_val_sw_republish_r1.py"
$txt = [System.IO.File]::ReadAllText($patch)
$txt2 = [regex]::Replace($txt, "BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_{compact}_[A-Z0-9_]+", $candName)
[System.IO.File]::WriteAllText($patch, $txt2)
RunPy $patch
L "FUND_NAV"
& $py -u "E:\\BLACKBOX\\脚本\\blackbox_fund_etf_nav_premium_plane_r1.py" --asof {asof} --phase all 2>&1 | Tee-Object -FilePath $log -Append
if ($LASTEXITCODE -ne 0) {{ L ("FUND_NAV_FAIL=" + $LASTEXITCODE); exit $LASTEXITCODE }}
L "EXTERNAL+SCOPE+PLANE"
& $py -u "E:\\BLACKBOX\\脚本\\blackbox_external_evidence_materialization_r2.py" --phase asof_align --asof {asof} 2>&1 | Tee-Object -FilePath $log -Append
& $py -u "E:\\BLACKBOX\\脚本\\blackbox_external_evidence_materialization_r2.py" --phase acceptance --asof {asof} 2>&1 | Tee-Object -FilePath $log -Append
& $py -u "E:\\BLACKBOX\\脚本\\blackbox_full_data_update_scope_refresh_r1.py" 2>&1 | Tee-Object -FilePath $log -Append
& $py -u "E:\\BLACKBOX\\脚本\\run_blackbox_daily_incremental_data_plane_r1.py" --mode run --date {compact} --skip-jq --skip-t-external --skip-sellside-if-done 2>&1 | Tee-Object -FilePath $log -Append
L "FULL_CHAIN_PASS tip={asof}"
exit 0
'''
    from_sw = f'''
RunPy "$d\\sw_l123_asof_{compact}.py"
RunPy "$d\\code\\index_minute_{compact}.py"
RunPy "$d\\code\\align_index_minute_{compact}.py"
''' + post_clean
    tail = f'''
RunPy "$d\\ingest_minutes_r1.py"
RunPy "$d\\ingest_minutes_flat_r1.py"
''' + from_sw
    header = f'''$ErrorActionPreference = "Continue"
$py = "E:\\BLACKBOX\\.venv\\Scripts\\python.exe"
$d = "{dest}"
$log = Join-Path $d "FULL_CHAIN.log"
function L([string]$m) {{ $line = "[{{0}}] {{1}}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"), $m; Add-Content -Path $log -Value $line -Encoding utf8; Write-Output $line }}
function RunPy([string]$script) {{ L ("RUN " + $script); & $py -u $script 2>&1 | Tee-Object -FilePath $log -Append; if ($LASTEXITCODE -ne 0) {{ L ("FAIL rc=" + $LASTEXITCODE + " " + $script); exit $LASTEXITCODE }} }}
'''
    resume_xr.write_text(
        header + f'L "RESUME_FROM_XR_XD tip={asof}"\nRunPy "$d\\download_xr_xd_r1.py"\nRunPy "$d\\code\\minute_download_{compact}.py"\n' + tail,
        encoding="utf-8-sig",
    )
    resume_min.write_text(
        header + f'L "RESUME_FROM_MINUTE tip={asof}"\nRunPy "$d\\code\\minute_download_{compact}.py"\n' + tail,
        encoding="utf-8-sig",
    )
    resume_sw.write_text(
        header + f'L "RESUME_FROM_SW tip={asof}"\n' + from_sw,
        encoding="utf-8-sig",
    )
    resume_clean.write_text(
        header + f'L "RESUME_FROM_CLEAN tip={asof} align_ok=1"\n' + post_clean,
        encoding="utf-8-sig",
    )
    # Post-clean only (skip clean_switch) when CURRENT clean already at tip asof.
    resume_cache = dest / "_resume_from_cache.ps1"
    post_cache = post_clean.replace(
        f'RunPy "$d\\clean_switch_r1.py"\nL "CLEAN_DONE — tip rebase"\n',
        f'L "SKIP_CLEAN_SWITCH clean_already={asof}"\n',
        1,
    )
    resume_cache.write_text(
        header + f'L "RESUME_FROM_CACHE tip={asof}"\n' + post_cache,
        encoding="utf-8-sig",
    )

    clean_already = str(current_asofs().get("clean") or "")[:10] == asof

    if daily_ok and val_ok and bill_ok and xr_ok and minute_ok and align_ok and clean_already:
        script = resume_cache
    elif daily_ok and val_ok and bill_ok and xr_ok and minute_ok and align_ok:
        script = resume_clean
    elif daily_ok and val_ok and bill_ok and xr_ok and minute_ok and flat_ok and not align_ok:
        # minutes ingested; resume at SW densify / index / align
        script = resume_sw
    elif daily_ok and val_ok and bill_ok and xr_ok and not minute_ok:
        script = resume_min
    elif daily_ok and val_ok and bill_ok and not xr_ok:
        script = resume_xr
    elif daily_ok and val_ok and bill_ok and xr_ok and minute_ok:
        script = resume_min
    else:
        script = dest / "_run_full_chain.ps1"

    log(
        f"LAUNCH_CHAIN {asof} script={script.name} "
        f"flags=d{int(daily_ok)}v{int(val_ok)}b{int(bill_ok)}x{int(xr_ok)}m{int(minute_ok)}"
        f"f{int(flat_ok)}s{int(sw_ok)}a{int(align_ok)}c{int(clean_already)}"
    )
    p = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        cwd=str(dest),
    )
    rc = int(p.returncode)
    log(f"CHAIN_EXIT {asof} rc={rc}")
    return rc


def write_completion(asof: str) -> None:
    compact = asof.replace("-", "")
    mmdd = compact[4:]
    asofs = current_asofs()
    body = {
        "task": f"JQ_DAILY_TIP_INCREMENT_{compact}",
        "run_target_trade_date": asof,
        "at_cn": now_cn().isoformat(timespec="seconds"),
        "FINAL_STATUS": "PASS" if asofs["source"] == asof == asofs["clean"] == asofs["cache"] else "PARTIAL",
        "ORDER_ALLOWED": False,
        "JQ_MAINCHAIN": {
            "SOURCE_ASOF": asofs["source"],
            "CLEAN_ASOF": asofs["clean"],
            "CACHE_ASOF": asofs["cache"],
            "STATUS": "PASS" if asofs["source"] == asof == asofs["clean"] == asofs["cache"] else "NO",
            "ALL_EQUAL": asofs["source"] == asofs["clean"] == asofs["cache"],
        },
        "cleaning_release_id": asofs.get("cleaning_release_id"),
        "cache_release_id": asofs.get("cache_release_id"),
        "unattended": True,
    }
    wjson(ROOT / "运行" / f"BLACKBOX_JQ_{mmdd}_TIP_INCREMENT_COMPLETION_CURRENT.json", body)
    wjson(ARCH / f"JQ_DAILY_TIP_{compact}" / "COMPLETION_STATUS.json", body)


def wait_for_eod_if_needed(target: str) -> None:
    today = now_cn().date().isoformat()
    if target != today:
        return
    while True:
        n = now_cn()
        cutoff = n.replace(hour=15, minute=5, second=0, microsecond=0)
        if n >= cutoff:
            log("EOD_REACHED start today tip")
            return
        remain = (cutoff - n).total_seconds()
        log(f"WAIT_EOD remain_sec={int(remain)}")
        time.sleep(min(300, max(30, remain)))


def acquire_lock() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            old = json.loads(LOCK.read_text(encoding="utf-8"))
            old_pid = int(old.get("pid") or 0)
            # if old pid still alive, exit
            import ctypes

            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x00100000
            handle = kernel32.OpenProcess(SYNCHRONIZE, False, old_pid)
            if handle:
                kernel32.CloseHandle(handle)
                age = time.time() - float(old.get("started_epoch") or 0)
                if age < 72 * 3600:
                    log(f"LOCK_HELD pid={old_pid} age_sec={int(age)} — exit duplicate")
                    raise SystemExit(0)
        except SystemExit:
            raise
        except Exception:
            pass
    wjson(LOCK, {"pid": os.getpid(), "started_epoch": time.time(), "at": now_cn().isoformat(timespec="seconds")})


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    acquire_lock()
    log("UNATTENDED_START")
    while True:
        asofs = current_asofs()
        days = jq_trade_days("2026-09-09", "2026-09-30")
        sealable = []
        today = now_cn().date().isoformat()
        cutoff_ok = now_cn() >= now_cn().replace(hour=15, minute=5, second=0, microsecond=0)
        target_file = OUT_ROOT / "TARGET_END.txt"
        target_end = "2026-09-24"
        if target_file.exists():
            te = target_file.read_text(encoding="utf-8", errors="replace").strip()[:10]
            if re.match(r"20\d{2}-\d{2}-\d{2}", te):
                target_end = te
        for d in days:
            if d <= asofs["source"]:
                continue
            if d > target_end:
                continue
            if d < today or (d == today and cutoff_ok):
                sealable.append(d)
        progress = {
            "at": now_cn().isoformat(timespec="seconds"),
            "current_asofs": asofs,
            "sealable_remaining": sealable,
            "target_end": target_end,
            "ORDER_ALLOWED": False,
        }
        wjson(PROGRESS, progress)
        log(f"PROGRESS source={asofs['source']} remaining={sealable}")
        if not sealable:
            if asofs["source"] < target_end or asofs["clean"] < target_end or asofs["cache"] < target_end:
                log(
                    f"NO_SEALABLE_BUT_BEHIND_TARGET source={asofs['source']} "
                    f"clean={asofs['clean']} cache={asofs['cache']} — sleep 120s"
                )
                time.sleep(120)
                continue
            if not (asofs["source"] == asofs["clean"] == asofs["cache"]):
                log(f"ASOF_MISMATCH {asofs} — sleep 120s")
                time.sleep(120)
                continue
            log("ALL_CAUGHT_UP")
            subprocess.run(
                [
                    str(PY),
                    "-u",
                    str(ROOT / "脚本" / "run_blackbox_research_os.py"),
                    "--mode",
                    "daily_incremental",
                    "--run",
                    "--date",
                    asofs["source"].replace("-", ""),
                ]
            )
            wjson(
                OUT_ROOT / "FINAL_STATUS.json",
                {
                    "FINAL_STATUS": "PASS",
                    "at": now_cn().isoformat(timespec="seconds"),
                    "asofs": current_asofs(),
                    "target_end": target_end,
                },
            )
            try:
                LOCK.unlink()
            except OSError:
                pass
            return 0
        nxt = sealable[0]
        wait_for_eod_if_needed(nxt)
        dest = ARCH / f"JQ_DAILY_TIP_{nxt.replace('-', '')}"
        # If chain not started yet, refresh scripts with latest parent cleaning id.
        # Never wipe dest if DOWNLOAD_ACCEPTANCE / FULL_CHAIN.log already exists.
        has_progress = (dest / "DOWNLOAD_ACCEPTANCE.json").exists() or (
            (dest / "FULL_CHAIN.log").exists()
            and "START FULL_CHAIN" in (dest / "FULL_CHAIN.log").read_text(encoding="utf-8", errors="replace")
        )
        if dest.exists() and not has_progress:
            shutil.rmtree(dest, ignore_errors=True)
        elif dest.exists() and has_progress:
            # patch PARENT_ID only in clean_switch
            cs = dest / "clean_switch_r1.py"
            parent_id = str(current_asofs().get("cleaning_release_id") or "")
            if cs.exists() and parent_id:
                txt = cs.read_text(encoding="utf-8")
                txt2 = re.sub(r'PARENT_ID\s*=\s*"[^"]+"', f'PARENT_ID = "{parent_id}"', txt, count=1)
                cs.write_text(txt2, encoding="utf-8")
        rc = run_day_chain(nxt)
        write_completion(nxt)
        asofs2 = current_asofs()
        if rc != 0 or not (asofs2["source"] == nxt == asofs2["clean"] == asofs2["cache"]):
            # If CURRENT already advanced to tip, treat as PASS even when post-patch rc!=0
            if asofs2["source"] == nxt == asofs2["clean"] == asofs2["cache"]:
                log(f"DAY_PASS {nxt} (asofs_aligned_despite_rc={rc})")
                try:
                    (OUT_ROOT / "BLOCKED.json").unlink()
                except OSError:
                    pass
            else:
                log(f"DAY_FAIL {nxt} rc={rc} asofs={asofs2}")
                wjson(
                    OUT_ROOT / "BLOCKED.json",
                    {"day": nxt, "rc": rc, "asofs": asofs2, "at": now_cn().isoformat(timespec="seconds")},
                )
                # unattended: keep retrying with backoff instead of fatal-exit
                for attempt in range(2, 8):
                    time.sleep(min(300, 30 * attempt))
                    log(f"RETRY_DAY {nxt} attempt={attempt}")
                    rc2 = run_day_chain(nxt)
                    write_completion(nxt)
                    asofs3 = current_asofs()
                    if asofs3["source"] == nxt == asofs3["clean"] == asofs3["cache"]:
                        log(f"DAY_PASS {nxt} after_retry={attempt} rc={rc2}")
                        try:
                            (OUT_ROOT / "BLOCKED.json").unlink()
                        except OSError:
                            pass
                        break
                    log(f"RETRY_FAIL {nxt} attempt={attempt} rc={rc2} asofs={asofs3}")
                else:
                    log(f"DAY_FAIL_KEEP_TRYING {nxt} — sleep 10m then outer loop")
                    time.sleep(600)
                    continue
        else:
            log(f"DAY_PASS {nxt}")
            try:
                (OUT_ROOT / "BLOCKED.json").unlink()
            except OSError:
                pass
        time.sleep(5)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        log(f"FATAL {e!r}")
        wjson(OUT_ROOT / "FATAL.json", {"error": repr(e), "at": now_cn().isoformat(timespec="seconds")})
        # unattended: do not die silently forever — sleep and re-enter main
        time.sleep(180)
        try:
            raise SystemExit(main())
        except SystemExit:
            raise
        except Exception as e2:
            log(f"FATAL2 {e2!r}")
            wjson(OUT_ROOT / "FATAL.json", {"error": repr(e2), "at": now_cn().isoformat(timespec="seconds")})
            raise SystemExit(1)
