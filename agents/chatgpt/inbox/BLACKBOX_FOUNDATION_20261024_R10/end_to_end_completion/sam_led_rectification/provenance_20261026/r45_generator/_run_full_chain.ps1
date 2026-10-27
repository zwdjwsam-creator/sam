# Auto-generated unattended tip chain for 2026-09-24
$ErrorActionPreference = "Continue"
$py = "E:\BLACKBOX\.venv\Scripts\python.exe"
$d = "D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924"
$log = Join-Path $d "FULL_CHAIN.log"
function L([string]$m) {
  $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"), $m
  Add-Content -Path $log -Value $line -Encoding utf8
  Write-Output $line
}
function RunPy([string]$script) {
  L ("RUN " + $script)
  & $py -u $script 2>&1 | Tee-Object -FilePath $log -Append
  if ($LASTEXITCODE -ne 0) {
    L ("FAIL rc=" + $LASTEXITCODE + " " + $script)
    exit $LASTEXITCODE
  }
}
L "START FULL_CHAIN tip=2026-09-24"
RunPy "$d\download_daily_r1.py"
RunPy "$d\download_val_adjust_r1.py"
RunPy "$d\download_billboard_ingest_r1.py"
RunPy "$d\download_xr_xd_r1.py"
RunPy "$d\code\minute_download_20260924.py"
RunPy "$d\ingest_minutes_r1.py"
RunPy "$d\ingest_minutes_flat_r1.py"
RunPy "$d\sw_l123_asof_20260924.py"
RunPy "$d\code\index_minute_20260924.py"
RunPy "$d\code\align_index_minute_20260924.py"
RunPy "$d\clean_switch_r1.py"
L "CLEAN_DONE — tip rebase"
& $py -u "E:\BLACKBOX\脚本\blackbox_daily_increment_orchestrator_r1.py" --run-target-date 2026-09-24 --cleaning-json "E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json" 2>&1 | Tee-Object -FilePath $log -Append
$candName = (& $py -u "D:\CURSOR_TASK_ARCHIVE\JQ_TIP_CATCHUP_UNATTENDED_R1\pick_cache_candidate_r1.py" "20260924" 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or -not $candName -or $candName -eq "NO_CACHE_CANDIDATE") { L "NO_CACHE_CANDIDATE"; exit 3 }
L ("CACHE_CAND=" + $candName)
$patch = "$d\code\patch_candidate_val_sw_republish_r1.py"
$txt = [System.IO.File]::ReadAllText($patch)
$txt2 = [regex]::Replace($txt, "BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_[A-Z0-9_]+", $candName)
[System.IO.File]::WriteAllText($patch, $txt2)
RunPy $patch
L "FUND_NAV"
& $py -u "E:\BLACKBOX\脚本\blackbox_fund_etf_nav_premium_plane_r1.py" --asof 2026-09-24 --phase all 2>&1 | Tee-Object -FilePath $log -Append
if ($LASTEXITCODE -ne 0) { L ("FUND_NAV_FAIL=" + $LASTEXITCODE); exit $LASTEXITCODE }
L "EXTERNAL+SCOPE+PLANE"
& $py -u "E:\BLACKBOX\脚本\blackbox_external_evidence_materialization_r2.py" --phase asof_align --asof 2026-09-24 2>&1 | Tee-Object -FilePath $log -Append
& $py -u "E:\BLACKBOX\脚本\blackbox_external_evidence_materialization_r2.py" --phase acceptance --asof 2026-09-24 2>&1 | Tee-Object -FilePath $log -Append
& $py -u "E:\BLACKBOX\脚本\blackbox_full_data_update_scope_refresh_r1.py" 2>&1 | Tee-Object -FilePath $log -Append
$asofCompact = "20260924"
& $py -u "E:\BLACKBOX\脚本\run_blackbox_daily_incremental_data_plane_r1.py" --mode run --date $asofCompact --skip-jq --skip-t-external --skip-sellside-if-done 2>&1 | Tee-Object -FilePath $log -Append
L "FULL_CHAIN_PASS tip=2026-09-24"
exit 0
