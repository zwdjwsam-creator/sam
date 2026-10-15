# READONLY auth/SMB window query for R9_NOTEBOOK_AUTH_WINDOW_ASSIST_20261015
# Window: 2026-10-15 10:19:30—10:19:32 +08:00 (UTC 02:19:30—02:19:32)
# No net use / cmdkey mutate / ACL / audit policy / E|D writes.

$ErrorActionPreference = 'Continue'
$OutDir = if ($PSScriptRoot) { $PSScriptRoot } else { 'C:\LAN_SHARE_REPORT\R9_NOTEBOOK_AUTH_WINDOW_ASSIST_20261015' }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$winStartLocal = [datetimeoffset]::Parse('2026-10-15T10:19:30+08:00')
$winEndLocal   = [datetimeoffset]::Parse('2026-10-15T10:19:32+08:00')
# API StartTime/EndTime are local wall clock on this machine
$apiStart = $winStartLocal.LocalDateTime
$apiEnd   = $winEndLocal.LocalDateTime.AddSeconds(1) # inclusive pad; filter exact later

$events = @()
$query_errors = @()
$access_denied = $false

function Add-EvtObj($ev, $logName) {
  $dto = [datetimeoffset]$ev.TimeCreated
  $xml = [xml]$ev.ToXml()
  $data = @{}
  foreach ($d in $xml.Event.EventData.Data) {
    if ($d.Name) { $data[$d.Name] = [string]$d.'#text' }
  }
  $msg = $null
  try { $msg = $ev.Message } catch {}
  [pscustomobject]@{
    LogName = $logName
    Id = $ev.Id
    LevelDisplayName = $ev.LevelDisplayName
    TimeCreatedLocal = $dto.ToOffset([timespan]::FromHours(8)).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz')
    TimeCreatedUtc = $dto.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ss.fff') + 'Z'
    ProviderName = $ev.ProviderName
    MachineName = $ev.MachineName
    TargetUserName = $data['TargetUserName']
    TargetDomainName = $data['TargetDomainName']
    SubjectUserName = $data['SubjectUserName']
    IpAddress = $data['IpAddress']
    WorkstationName = $data['WorkstationName']
    Status = $data['Status']
    SubStatus = $data['SubStatus']
    FailureReason = $data['FailureReason']
    LogonType = $data['LogonType']
    EventData = $data
    MessagePreview = if ($msg) { ($msg -replace '\s+', ' ').Substring(0, [Math]::Min(400, ($msg -replace '\s+', ' ').Length)) } else { $null }
  }
}

function In-Window([datetimeoffset]$t) {
  return ($t -ge $winStartLocal -and $t -le $winEndLocal)
}

# Security 4625
try {
  $sec = Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4625
    StartTime = $apiStart
    EndTime = $apiEnd
  } -ErrorAction Stop
  foreach ($ev in @($sec)) {
    $t = [datetimeoffset]$ev.TimeCreated
    if (-not (In-Window $t)) { continue }
    $events += ,(Add-EvtObj $ev 'Security')
  }
} catch {
  $msg = $_.Exception.Message
  if ($msg -match 'Access is denied|拒绝访问|UnauthorizedAccess') { $access_denied = $true }
  if ($msg -notmatch 'No events were found|找不到任何事件') {
    $query_errors += "Security/4625: $msg"
  }
}

# Microsoft-Windows-SMBServer/* common channels
$smbLogs = @(
  'Microsoft-Windows-SMBServer/Security',
  'Microsoft-Windows-SMBServer/Operational',
  'Microsoft-Windows-SMBServer/Audit',
  'Microsoft-Windows-SmbClient/Security',
  'Microsoft-Windows-SmbClient/Connectivity'
)
foreach ($log in $smbLogs) {
  try {
    $found = Get-WinEvent -FilterHashtable @{
      LogName = $log
      StartTime = $apiStart
      EndTime = $apiEnd
    } -ErrorAction Stop
    foreach ($ev in @($found)) {
      $t = [datetimeoffset]$ev.TimeCreated
      if (-not (In-Window $t)) { continue }
      $events += ,(Add-EvtObj $ev $log)
    }
  } catch {
    $msg = $_.Exception.Message
    if ($msg -match 'Access is denied|拒绝访问|UnauthorizedAccess') { $access_denied = $true }
    if ($msg -match 'does not exist|不存在| purging') {
      $query_errors += "${log}: LOG_NOT_PRESENT_OR_EMPTY ($msg)"
    } elseif ($msg -notmatch 'No events were found|找不到任何事件') {
      $query_errors += "${log}: $msg"
    }
  }
}

# Relevance filter: ZHANGWEI / 192.168.100.1 / admin mention in fields
function Is-Relevant($e) {
  $blob = (@(
    $e.TargetUserName, $e.TargetDomainName, $e.SubjectUserName,
    $e.IpAddress, $e.WorkstationName, $e.MessagePreview
  ) + @($e.EventData.Values)) -join '|'
  return ($blob -match '(?i)ZHANGWEI|192\.168\.100\.1|\badmin\b')
}

$matching = @($events | Where-Object { Is-Relevant $_ })
$allInWindow = @($events)

$status = if ($access_denied -and $allInWindow.Count -eq 0) {
  'AccessDenied'
} elseif ($matching.Count -gt 0) {
  'MATCHING_EVENTS'
} elseif ($allInWindow.Count -gt 0) {
  'EVENTS_IN_WINDOW_NO_ZHANGWEI_IP_MATCH'
} else {
  'NO_MATCHING_EVENT'
}

$result = [ordered]@{
  task_id = 'R9_NOTEBOOK_AUTH_WINDOW_ASSIST_20261015_1005'
  execution_host = 'SAM'
  hostname = $env:COMPUTERNAME
  queried_at_local = (Get-Date).ToString('yyyy-MM-ddTHH:mm:sszzz')
  window_start = @{ local = '2026-10-15T10:19:30+08:00'; utc = '2026-10-15T02:19:30Z' }
  window_end   = @{ local = '2026-10-15T10:19:32+08:00'; utc = '2026-10-15T02:19:32Z' }
  status = $status
  access_denied = $access_denied
  event_count_in_window = $allInWindow.Count
  matching_event_count = $matching.Count
  matching_events = $matching
  all_events_in_window = $allInWindow
  query_errors = $query_errors
  notes = 'READONLY Get-WinEvent only; exact local window filter after API pad; secrets not included.'
}

$jsonPath = Join-Path $OutDir 'AUTH_WINDOW_EVENTS.json'
($result | ConvertTo-Json -Depth 8) | Set-Content -Path $jsonPath -Encoding UTF8

# Alias for pickup naming
Copy-Item $jsonPath (Join-Path $OutDir 'AUTH_WINDOW_RESULT.json') -Force

Write-Output "STATUS=$status MATCH=$($matching.Count) ALL=$($allInWindow.Count) ACCESS_DENIED=$access_denied"
Write-Output "ERRORS=$($query_errors -join ' | ')"
