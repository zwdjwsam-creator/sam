# R9 authorized visibility — ONE-SHOT elevated READ-ONLY diagnosis
# Task: R9_DESKTOP_AUTHORIZED_VISIBILITY_20261011_1220
# Does NOT kill processes, copy data, change ACLs, or enable migration.
$ErrorActionPreference = 'Continue'
$OUT = 'C:\LAN_SHARE_REPORT'
$utf8 = New-Object System.Text.UTF8Encoding $true
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$doneFlag = Join-Path $OUT 'R9_ADMIN_DIAG_DONE.json'
$log = Join-Path $OUT 'R9_ADMIN_DIAG_RUN.log'

function L($m) {
  $line = "{0} {1}" -f (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'), $m
  [System.IO.File]::AppendAllText($log, $line + [Environment]::NewLine, $utf8)
  Write-Host $line
}

try {
  L "ADMIN_DIAG_START"
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($identity)
  $isAdminGroup = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  $whoamiGroups = (whoami /groups) | Out-String
  $integrity = if ($whoamiGroups -match 'High Mandatory Level') { 'High' }
    elseif ($whoamiGroups -match 'System Mandatory Level') { 'System' }
    elseif ($whoamiGroups -match 'Medium Mandatory Level') { 'Medium' }
    else { 'Unknown' }
  $elevated = ($integrity -eq 'High' -or $integrity -eq 'System')

  $priv = [ordered]@{
    checked_at            = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
    hostname              = $env:COMPUTERNAME
    whoami                = (whoami)
    is_admin_group_member = $isAdminGroup
    integrity_level       = $integrity
    process_elevated      = $elevated
  }
  [System.IO.File]::WriteAllText((Join-Path $OUT 'R9_ZHANGWEI_PRIVILEGE_STATE_ADMIN.json'), ($priv | ConvertTo-Json -Depth 4), $utf8)
  L ("PRIV elevated={0} integrity={1} adminGroup={2}" -f $elevated, $integrity, $isAdminGroup)

  if (-not $elevated) {
    throw "NOT_ELEVATED_AFTER_UAC integrity=$integrity"
  }

  $mgmt = [System.Management.ManagementDateTimeConverter]
  function Detail([int]$id) {
    $c = Get-CimInstance Win32_Process -Filter "ProcessId=$id" -ErrorAction SilentlyContinue
    if (-not $c) { return @{ pid = $id; exists = $false } }
    $owner = $null
    try {
      $o = Invoke-CimMethod -InputObject $c -MethodName GetOwner -ErrorAction Stop
      $owner = "{0}\{1}" -f $o.Domain, $o.User
    } catch {
      $owner = "GETOWNER_FAIL:$($_.Exception.Message)"
    }
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
      WS_MB          = $(if ($gp) { [math]::Round($gp.WorkingSet64 / 1MB, 1) } else { $null })
    }
  }

  $target = 20440
  $p0 = Detail $target
  $chain = @($p0)
  if ($p0.exists) {
    $id = [int]$p0.ppid
    for ($i = 0; $i -lt 6; $i++) {
      $n = Detail $id
      $chain += $n
      if (-not $n.exists -or -not $n.ppid) { break }
      $id = [int]$n.ppid
    }
  }
  $kids = @()
  Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $target } | ForEach-Object {
    $kids += Detail ([int]$_.ProcessId)
  }

  $RID = '20261010_173201_R8_3B85D677'
  $markers = @($RID, 'BLACKBOX_R8_E_COPY', 'PROGRESS_WRAPPER', 'WATCHDOG', 'CAPACITY_OBSERVER', 'EXIT_WAITER', 'E_DRIVE\BLACKBOX')
  $hits = @()
  Get-CimInstance Win32_Process | ForEach-Object {
    $cmd = [string]$_.CommandLine
    if ([string]::IsNullOrWhiteSpace($cmd) -and $_.Name -eq 'ln.exe') {
      $hits += [pscustomobject]@{ pid = $_.ProcessId; name = $_.Name; marker = 'ln.exe_empty_cmdline'; cmd = $null }
      return
    }
    if ([string]::IsNullOrWhiteSpace($cmd)) { return }
    foreach ($m in $markers) {
      if ($cmd -like "*$m*") {
        $hits += [pscustomobject]@{
          pid = $_.ProcessId; name = $_.Name; marker = $m
          cmd = $cmd.Substring(0, [Math]::Min(300, $cmd.Length))
        }
        break
      }
    }
  }

  $procPack = [ordered]@{
    checked_at_elevated = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
    privilege           = $priv
    pid_20440           = $p0
    parent_chain        = $chain
    children            = $kids
    r8_marker_hits      = $hits
    ln_count            = @(Get-Process ln -ErrorAction SilentlyContinue).Count
    cmdline_readable_20440 = ($p0.exists -and -not [string]::IsNullOrWhiteSpace([string]$p0.CommandLine))
  }
  [System.IO.File]::WriteAllText((Join-Path $OUT 'R9_ZHANGWEI_ADMIN_PROCESS_DETAIL.json'), ($procPack | ConvertTo-Json -Depth 8), $utf8)
  L ("PROC20440 exists={0} cmdline_readable={1} hits={2}" -f $p0.exists, $procPack.cmdline_readable_20440, @($hits).Count)

  # Preflight only — no copy switches
  $pfLog = Join-Path $OUT 'COPY_EXECUTOR_R9_PREFLIGHT_ZHANGWEI_ADMIN.json'
  $py = @(
    'copy_executor_r9_1g.py',
    '--preflight-only',
    '--confirm-dest', 'E:\BLACKBOX_MANIFEST_PILOT_R9_1G',
    '--r8-stopped-evidence', 'C:\LAN_SHARE_REPORT\BLACKBOX_R9_OLD_JOB_STOP_REPORT.md',
    '--log', $pfLog
  )
  Push-Location $OUT
  & python @py
  $pfRc = $LASTEXITCODE
  Pop-Location
  L "PREFLIGHT_RC=$pfRc log=$pfLog"

  $done = [ordered]@{
    status                = 'DIAGNOSIS_DONE'
    elevated              = $true
    preflight_exit_code   = $pfRc
    cmdline_readable_20440 = $procPack.cmdline_readable_20440
    finished_at           = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
  }
  [System.IO.File]::WriteAllText($doneFlag, ($done | ConvertTo-Json -Depth 4), $utf8)
  L 'ADMIN_DIAG_DONE'
  exit 0
}
catch {
  L ("ADMIN_DIAG_FAIL $($_.Exception.Message)")
  $fail = [ordered]@{
    status      = 'DIAGNOSIS_FAIL'
    error       = $_.Exception.Message
    finished_at = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
  }
  [System.IO.File]::WriteAllText($doneFlag, ($fail | ConvertTo-Json -Depth 4), $utf8)
  exit 1
}
