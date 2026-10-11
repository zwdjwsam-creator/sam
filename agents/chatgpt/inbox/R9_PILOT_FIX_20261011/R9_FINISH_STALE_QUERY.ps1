# Finish one stale findstr log query + its cmd shell (authorized narrow stop).
# Task: R9_DESKTOP_FINISH_STALE_QUERY_20261011_1227
# Do NOT put legacy RUN_ID in the *launch* command line of this script.
# Does not stop sshd / Cursor / unrelated PowerShell. No /T tree kill. No file delete.
$ErrorActionPreference = 'Stop'
$OUT = 'C:\LAN_SHARE_REPORT'
$utf8 = New-Object System.Text.UTF8Encoding $true
$detailPath = Join-Path $OUT 'R9_ZHANGWEI_ADMIN_PROCESS_DETAIL.json'
$snapPath = Join-Path $OUT 'R9_STALE_QUERY_STOP_SNAPSHOT.json'
$donePath = Join-Path $OUT 'R9_STALE_QUERY_STOP_DONE.json'
$logPath = Join-Path $OUT 'R9_STALE_QUERY_STOP.log'

function L([string]$m) {
  $line = "{0} {1}" -f (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'), $m
  [System.IO.File]::AppendAllText($logPath, $line + [Environment]::NewLine, $utf8)
  Write-Host $line
}

function Get-Detail([int]$id) {
  $c = Get-CimInstance Win32_Process -Filter "ProcessId=$id" -ErrorAction SilentlyContinue
  if (-not $c) { return @{ exists = $false; pid = $id } }
  $owner = $null
  try {
    $o = Invoke-CimMethod -InputObject $c -MethodName GetOwner -ErrorAction Stop
    $owner = "{0}\{1}" -f $o.Domain, $o.User
  } catch { $owner = "GETOWNER_FAIL" }
  $mgmt = [System.Management.ManagementDateTimeConverter]
  $cd = $null
  try { $cd = $mgmt::ToDateTime($c.CreationDate).ToString('o') } catch { $cd = [string]$c.CreationDate }
  $gp = Get-Process -Id $id -ErrorAction SilentlyContinue
  return [ordered]@{
    exists         = $true
    pid            = $id
    name           = $c.Name
    ppid           = $c.ParentProcessId
    CommandLine    = $c.CommandLine
    ExecutablePath = $c.ExecutablePath
    CreationDate   = $cd
    Owner          = $owner
    Path           = $(if ($gp) { $gp.Path } else { $null })
    StartTime      = $(if ($gp -and $gp.StartTime) { $gp.StartTime.ToString('o') } else { $null })
  }
}

function Assert-FindstrIdentity($live, $expected) {
  if (-not $live.exists) { return @{ ok = $true; reason = 'ALREADY_GONE' } }
  $reasons = @()
  if ($live.name -ne 'findstr.exe') { $reasons += "name=$($live.name)" }
  if ([int]$live.ppid -ne 20440) { $reasons += "ppid=$($live.ppid)" }
  if ($live.Owner -ne 'ZHANGWEI\Admin') { $reasons += "owner=$($live.Owner)" }
  $pathOk = ($live.ExecutablePath -and ($live.ExecutablePath -match '(?i)[\\/]system32[\\/]findstr\.exe$')) -or
            ($live.Path -and ($live.Path -match '(?i)[\\/]system32[\\/]findstr\.exe$'))
  if (-not $pathOk) { $reasons += "path=$($live.ExecutablePath)" }
  $cmd = [string]$live.CommandLine
  if ([string]::IsNullOrWhiteSpace($cmd)) { $reasons += 'cmdline_empty' }
  elseif ($cmd -notmatch '(?i)findstr') { $reasons += 'cmdline_not_findstr' }
  elseif ($cmd -notmatch '(?i)DESKTOP_PREFLIGHT\.json') { $reasons += 'cmdline_not_preflight_json' }
  elseif ($cmd -notmatch '(?i)BLACKBOX_MIGRATION_RUN_') { $reasons += 'cmdline_not_migration_run_dir' }
  # StartTime must match expected prefix (same second)
  if ($expected.StartTime -and $live.StartTime) {
    if ($live.StartTime.Substring(0, 19) -ne $expected.StartTime.Substring(0, 19)) {
      $reasons += "start_mismatch live=$($live.StartTime) exp=$($expected.StartTime)"
    }
  }
  # Extra business children under findstr? none expected
  $kids = @(Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq 34324 })
  if ($kids.Count -gt 0) { $reasons += "unexpected_children=$($kids.Count)" }
  return @{ ok = ($reasons.Count -eq 0); reason = ($reasons -join '|'); kids = $kids.Count }
}

function Assert-CmdIdentity($live, $expected) {
  if (-not $live.exists) { return @{ ok = $true; reason = 'ALREADY_GONE' } }
  $reasons = @()
  if ($live.name -ne 'cmd.exe') { $reasons += "name=$($live.name)" }
  if ([int]$live.ppid -ne 3348) { $reasons += "ppid=$($live.ppid)" }
  if ($live.Owner -ne 'ZHANGWEI\Admin') { $reasons += "owner=$($live.Owner)" }
  $pathOk = ($live.ExecutablePath -and ($live.ExecutablePath -match '(?i)[\\/]system32[\\/]cmd\.exe$')) -or
            ($live.Path -and ($live.Path -match '(?i)[\\/]system32[\\/]cmd\.exe$'))
  if (-not $pathOk) { $reasons += "path=$($live.ExecutablePath)" }
  $cmd = [string]$live.CommandLine
  if ([string]::IsNullOrWhiteSpace($cmd)) { $reasons += 'cmdline_empty' }
  elseif ($cmd -notmatch '(?i)cmd\.exe') { $reasons += 'cmdline_not_cmd' }
  elseif ($cmd -notmatch '(?i)/c') { $reasons += 'cmdline_not_c_shell' }
  elseif ($cmd -notmatch '(?i)findstr') { $reasons += 'cmdline_not_findstr_shell' }
  elseif ($cmd -notmatch '(?i)DESKTOP_PREFLIGHT\.json') { $reasons += 'cmdline_not_preflight_json' }
  if ($expected.StartTime -and $live.StartTime) {
    if ($live.StartTime.Substring(0, 19) -ne $expected.StartTime.Substring(0, 19)) {
      $reasons += "start_mismatch live=$($live.StartTime) exp=$($expected.StartTime)"
    }
  }
  # Remaining children besides possibly conhost (allowed to self-exit)
  $kids = @(Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq 20440 })
  $bad = @($kids | Where-Object { $_.Name -notmatch '^(conhost|findstr)\.exe$' })
  if ($bad.Count -gt 0) { $reasons += "unexpected_child_names" }
  return @{ ok = ($reasons.Count -eq 0); reason = ($reasons -join '|'); kid_names = @($kids | ForEach-Object { $_.Name }) }
}

try {
  L 'STOP_SCRIPT_START'
  if (-not (Test-Path -LiteralPath $detailPath)) { throw "MISSING_DETAIL $detailPath" }
  $expected = Get-Content -LiteralPath $detailPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $expFs = $expected.pid_20440
  $expFind = @($expected.children | Where-Object { $_.name -eq 'findstr.exe' } | Select-Object -First 1)
  if (-not $expFind) { throw 'EXPECTED_FINDSTR_MISSING_IN_DETAIL_JSON' }

  $before = [ordered]@{
    at        = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
    findstr   = Get-Detail 34324
    cmd       = Get-Detail 20440
    sshd_3348 = Get-Detail 3348
  }
  [System.IO.File]::WriteAllText($snapPath, ($before | ConvertTo-Json -Depth 8), $utf8)

  $actions = @()

  # --- findstr 34324 ---
  $fsLive = Get-Detail 34324
  $chkFs = Assert-FindstrIdentity $fsLive $expFind
  if (-not $chkFs.ok -and $chkFs.reason -ne 'ALREADY_GONE') {
    throw "FINDSTR_IDENTITY_MISMATCH:$($chkFs.reason)"
  }
  if ($fsLive.exists) {
    L 'STOP findstr 34324 (identity matched)'
    try {
      Stop-Process -Id 34324 -Force -ErrorAction Stop
      $actions += @{ target = 'findstr'; pid = 34324; action = 'Stop-Process'; ok = $true }
    } catch {
      $actions += @{ target = 'findstr'; pid = 34324; action = 'Stop-Process'; ok = $false; error = $_.Exception.Message }
      throw
    }
  } else {
    L 'findstr 34324 already gone'
    $actions += @{ target = 'findstr'; pid = 34324; action = 'ALREADY_GONE'; ok = $true }
  }

  Start-Sleep -Seconds 3

  # --- cmd 20440 ---
  $cmdLive = Get-Detail 20440
  if (-not $cmdLive.exists) {
    L 'cmd 20440 exited after findstr stop'
    $actions += @{ target = 'cmd'; pid = 20440; action = 'NATURAL_EXIT'; ok = $true }
  } else {
    $chkCmd = Assert-CmdIdentity $cmdLive $expFs
    if (-not $chkCmd.ok) { throw "CMD_IDENTITY_MISMATCH:$($chkCmd.reason)" }
    L 'STOP cmd 20440 (same stale /c findstr shell)'
    try {
      Stop-Process -Id 20440 -Force -ErrorAction Stop
      $actions += @{ target = 'cmd'; pid = 20440; action = 'Stop-Process'; ok = $true }
    } catch {
      $actions += @{ target = 'cmd'; pid = 20440; action = 'Stop-Process'; ok = $false; error = $_.Exception.Message }
      throw
    }
  }

  Start-Sleep -Seconds 2
  $after = [ordered]@{
    at        = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
    findstr   = Get-Detail 34324
    cmd       = Get-Detail 20440
    sshd_3348 = Get-Detail 3348
    sshd_alive = [bool](Get-Process -Id 3348 -ErrorAction SilentlyContinue)
  }

  $done = [ordered]@{
    status              = 'STOP_DONE'
    finished_at         = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
    actions             = $actions
    before              = $before
    after               = $after
    sshd_not_stopped    = $after.sshd_alive
    note                = 'Narrow stop only; no /T; sshd left running'
  }
  [System.IO.File]::WriteAllText($donePath, ($done | ConvertTo-Json -Depth 10), $utf8)
  L 'STOP_SCRIPT_DONE'
  exit 0
}
catch {
  L ("STOP_SCRIPT_FAIL $($_.Exception.Message)")
  $fail = [ordered]@{
    status      = 'STOP_FAIL'
    error       = $_.Exception.Message
    finished_at = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
  }
  [System.IO.File]::WriteAllText($donePath, ($fail | ConvertTo-Json -Depth 6), $utf8)
  exit 1
}
