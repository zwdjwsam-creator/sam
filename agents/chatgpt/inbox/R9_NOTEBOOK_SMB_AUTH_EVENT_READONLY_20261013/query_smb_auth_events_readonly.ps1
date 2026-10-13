# R9_NOTEBOOK_SMB_AUTH_EVENT_READONLY_20261013 — readonly diagnostics
# COPY_AUTHORIZED=false | no net use, cmdkey, ACL changes

$ErrorActionPreference = 'Continue'
$OutRoot = 'C:\LAN_SHARE_REPORT\R9_NOTEBOOK_SMB_AUTH_EVENT_READONLY_20261013\reports'
$MaxEvents = 80
$RefDesktopIp = '192.168.100.1'
$RefWorkstation = 'ZHANGWEI'

$StartLocal = [DateTime]::Parse('2026-10-13T20:10:00')
$EndLocal = [DateTime]::Parse('2026-10-13T20:40:00')

function Get-EventDataField {
    param($EventRecord, [string]$Name)
    try {
        $xml = [xml]$EventRecord.ToXml()
        $n = $xml.Event.EventData.Data | Where-Object { $_.Name -eq $Name } | Select-Object -First 1
        if ($null -eq $n) { return $null }
        $t = $n.'#text'
        if ([string]::IsNullOrWhiteSpace($t)) { return $null }
        return $t.Trim()
    } catch { return $null }
}

function Normalize-Ip {
    param([string]$Ip)
    if ([string]::IsNullOrWhiteSpace($Ip)) { return $null }
    $Ip = $Ip.Trim()
    if ($Ip -match '^::ffff:(.+)$') { return $Matches[1] }
    if ($Ip -eq '-' -or $Ip -eq '::1') { return $Ip }
    return $Ip
}

$result = @{
    task_id = 'R9_NOTEBOOK_SMB_AUTH_EVENT_READONLY_20261013_2101'
    collected_at_local = (Get-Date).ToString('o')
    time_window_local = @{ start = $StartLocal.ToString('o'); end = $EndLocal.ToString('o') }
    readonly = $true
    security_4625 = @{ status = 'UNKNOWN'; access_denied = $false; error = $null; raw_in_window = 0; matched = @() }
    smb_server_logs = @{ shares = @(); operational = $null; security = $null; audit = $null }
    current_identity = $null
    local_users = @()
    smb_share_access = @()
}

# Current identity
try {
    $wi = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $result.current_identity = @{
        Name = $wi.Name
        AuthenticationType = $wi.AuthenticationType
        IsAuthenticated = $wi.IsAuthenticated
    }
} catch {
    $result.current_identity = @{ error = $_.Exception.Message }
}

# Security 4625
$matched = [System.Collections.Generic.List[object]]::new()
try {
    $filter = @{
        LogName   = 'Security'
        Id        = 4625
        StartTime = $StartLocal
        EndTime   = $EndLocal
    }
    $events = Get-WinEvent -FilterHashtable $filter -ErrorAction Stop
    $result.security_4625.raw_in_window = @($events).Count
    foreach ($ev in $events) {
        if ($matched.Count -ge $MaxEvents) { break }
        $logonType = Get-EventDataField -EventRecord $ev -Name 'LogonType'
        $ws = Get-EventDataField -EventRecord $ev -Name 'WorkstationName'
        $ip = Normalize-Ip (Get-EventDataField -EventRecord $ev -Name 'IpAddress')
        $ltOk = ($logonType -eq '3')
        $wsOk = ($ws -and ($ws -eq $RefWorkstation -or $ws -like "*$RefWorkstation*"))
        $ipOk = ($ip -and ($ip -eq $RefDesktopIp -or $ip -like '192.168.100.*'))
        if (-not $ltOk) { continue }
        if (-not ($wsOk -or $ipOk)) { continue }
        $matched.Add([ordered]@{
            TimeCreated = $ev.TimeCreated.ToString('o')
            EventID = $ev.Id
            RecordID = $ev.RecordId
            TargetUserName = Get-EventDataField -EventRecord $ev -Name 'TargetUserName'
            TargetDomainName = Get-EventDataField -EventRecord $ev -Name 'TargetDomainName'
            WorkstationName = $ws
            IpAddress = $ip
            LogonType = $logonType
            Status = Get-EventDataField -EventRecord $ev -Name 'Status'
            SubStatus = Get-EventDataField -EventRecord $ev -Name 'SubStatus'
            FailureReason = Get-EventDataField -EventRecord $ev -Name 'FailureReason'
            AuthenticationPackageName = Get-EventDataField -EventRecord $ev -Name 'AuthenticationPackageName'
            LogonProcessName = Get-EventDataField -EventRecord $ev -Name 'LogonProcessName'
        })
    }
    $result.security_4625.status = 'OK'
    $result.security_4625.matched = $matched
} catch {
    $msg = $_.Exception.Message
    $fqid = $_.FullyQualifiedErrorId
    if ($fqid -like 'NoMatchingEventsFound*') {
        $result.security_4625.status = 'OK'
        $result.security_4625.raw_in_window = 0
        $result.security_4625.error = $null
    } elseif ($msg -match 'Access is denied|拒绝访问|0x00000005|UnauthorizedAccess') {
        $result.security_4625.error = $msg
        $result.security_4625.access_denied = $true
        $result.security_4625.status = 'ACCESS_DENIED'
    } else {
        $result.security_4625.error = $msg
        $result.security_4625.status = 'QUERY_FAILED'
    }
}

# SMBServer / related log channels (existence + enabled only)
function Get-LogChannelMeta {
    param([string]$Name)
    $meta = @{ name = $Name; exists = $false; enabled = $null; error = $null }
    try {
        $log = Get-WinEvent -ListLog $Name -ErrorAction Stop
        $meta.exists = $true
        $meta.enabled = [bool]$log.IsEnabled
        $meta.record_count = $log.RecordCount
        $meta.maximum_size_mb = $log.MaximumSizeInBytes / 1MB
    } catch {
        $meta.error = $_.Exception.Message
    }
    return $meta
}

$result.smb_server_logs.operational = Get-LogChannelMeta 'Microsoft-Windows-SMBServer/Operational'
$result.smb_server_logs.security = Get-LogChannelMeta 'Microsoft-Windows-SMBServer/Security'
$result.smb_server_logs.audit = Get-LogChannelMeta 'Microsoft-Windows-SMBServer/Audit'

try {
    $shares = Get-SmbShare -ErrorAction Stop | Where-Object { $_.Name -in @('E_DRIVE','D_DRIVE','BLACKBOX') -or $_.Path -match '^[ED]:\\' }
    foreach ($s in $shares) {
        $result.smb_server_logs.shares += @{ Name = $s.Name; Path = $s.Path; Description = $s.Description }
    }
} catch {
    $result.smb_server_logs.share_enum_error = $_.Exception.Message
}

# Target usernames from events + current user short name
$candidates = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($m in $matched) {
    if ($m.TargetUserName) { [void]$candidates.Add($m.TargetUserName) }
}
if ($result.current_identity.Name) {
    $short = ($result.current_identity.Name -split '\\')[-1]
    if ($short) { [void]$candidates.Add($short) }
}

foreach ($un in $candidates) {
    $lu = @{ UserName = $un; exists = $false; Enabled = $null; PrincipalSource = $null; PasswordRequired = $null; error = $null }
    try {
        $u = Get-LocalUser -Name $un -ErrorAction Stop
        $lu.exists = $true
        $lu.Enabled = $u.Enabled
        $lu.PrincipalSource = $u.PrincipalSource.ToString()
        $lu.PasswordRequired = $u.PasswordRequired
    } catch {
        $lu.error = $_.Exception.Message
    }
    $result.local_users += $lu
}

# Share ACL summary for E_DRIVE / D_DRIVE
$shareNames = @('E_DRIVE','D_DRIVE')
try {
    $allShares = Get-SmbShare -ErrorAction SilentlyContinue
    foreach ($sn in $shareNames) {
        $share = $allShares | Where-Object { $_.Name -eq $sn } | Select-Object -First 1
        if (-not $share) {
            $result.smb_share_access += @{ ShareName = $sn; found = $false }
            continue
        }
        $access = @()
        try {
            $acl = Get-SmbShareAccess -Name $sn -ErrorAction Stop
            foreach ($a in $acl) {
                $acct = $a.AccountName
                $keep = $false
                foreach ($c in $candidates) {
                    if ($acct -like "*$c*") { $keep = $true; break }
                }
                if ($acct -match 'Everyone|Authenticated Users|BUILTIN\\Users') { $keep = $true }
                if ($keep) {
                    $access += @{
                        AccountName = $acct
                        AccessControlType = $a.AccessControlType.ToString()
                        AccessRight = $a.AccessRight.ToString()
                    }
                }
            }
        } catch {
            $access = @(@{ error = $_.Exception.Message })
        }
        $result.smb_share_access += @{
            ShareName = $sn
            found = $true
            Path = $share.Path
            access_entries = $access
        }
    }
} catch {
    $result.smb_share_access_error = $_.Exception.Message
}

# Write JSON outputs
$eventsJson = @{
    task_id = $result.task_id
    query = $result.security_4625
    smb_server_logs = $result.smb_server_logs
    matched_count = $matched.Count
}
$accountJson = @{
    task_id = $result.task_id
    current_identity = $result.current_identity
    local_users = $result.local_users
    smb_share_access = $result.smb_share_access
}

$eventsJson | ConvertTo-Json -Depth 12 | Set-Content -Path (Join-Path $OutRoot 'SMB_SERVER_AUTH_EVENTS.json') -Encoding UTF8
$accountJson | ConvertTo-Json -Depth 12 | Set-Content -Path (Join-Path $OutRoot 'SOURCE_ACCOUNT_AUTH_INFO.json') -Encoding UTF8

# AUTH_NEXT_ACTION heuristic (evidence-only)
$subMap = @{
    '0xC0000064' = 'ACCOUNT_DOES_NOT_EXIST'
    '0xC000006A' = 'WRONG_PASSWORD'
    '0xC0000234' = 'ACCOUNT_LOCKED'
    '0xC0000072' = 'ACCOUNT_DISABLED'
    '0xC000006F' = 'LOGON_HOURS_RESTRICTION'
    '0xC000015B' = 'LOGON_TYPE_NOT_GRANTED'
}
$cause = 'UNKNOWN'
$evidence = @()
$sourceCandidate = $null
$secretNeeded = 'UNKNOWN'
$nextAction = 'Collect more readonly evidence or verify Security log read permissions.'

if ($result.security_4625.access_denied) {
    $cause = 'UNKNOWN'
    $evidence += 'Security log query returned AccessDenied.'
    $nextAction = 'Run readonly query under account with Security log read rights (e.g. elevated admin); do not change audit policy.'
} elseif ($matched.Count -eq 0) {
    $cause = 'NO_MATCHING_EVENT'
    $evidence += 'No LogonType=3 4625 events in window matching ZHANGWEI or 192.168.100.* source.'
    $nextAction = 'Confirm desktop retry occurred in window; if outside window, widen only via new authorized task.'
} else {
    $top = $matched[0]
    $sourceCandidate = if ($top.TargetDomainName -and $top.TargetUserName) { "$($top.TargetDomainName)\$($top.TargetUserName)" } else { $top.TargetUserName }
    $evidence += "Latest match: Time=$($top.TimeCreated) Status=$($top.Status) SubStatus=$($top.SubStatus) Target=$sourceCandidate Workstation=$($top.WorkstationName) Ip=$($top.IpAddress)"
    $ss = $top.SubStatus
    if ($ss -and $subMap.ContainsKey($ss)) {
        $cause = $subMap[$ss]
        if ($cause -eq 'WRONG_PASSWORD') {
            $secretNeeded = $true
            $nextAction = 'Provide Windows credential for SOURCE_ACCOUNT_CANDIDATE via native credential manager on desktop (not PIN); no password collection on SAM.'
        } elseif ($cause -eq 'ACCOUNT_DOES_NOT_EXIST') {
            $secretNeeded = $false
            $nextAction = 'Use correct SAM local or Microsoft account username format for SMB; verify account exists on SAM.'
        } else {
            $secretNeeded = 'UNKNOWN'
            $nextAction = "Address cause $cause for candidate account; readonly — no ACL/password reset on SAM."
        }
    } else {
        $cause = 'UNKNOWN'
        $evidence += 'SubStatus missing or not mapped; do not infer 1326 as password error without SubStatus.'
    }
}

$authNext = [ordered]@{
    task_id = $result.task_id
    AUTH_FAILURE_CAUSE = $cause
    AUTH_FAILURE_EVIDENCE = $evidence
    SOURCE_ACCOUNT_CANDIDATE = $sourceCandidate
    USER_LOCAL_SECRET_ENTRY_NEEDED = $secretNeeded
    NEXT_MINIMAL_ACTION = $nextAction
    COPY_AUTHORIZED = $false
    FORMAT_DONE = $false
    FULL_MIGRATION = $false
}
$authNext | ConvertTo-Json -Depth 6 | Set-Content -Path (Join-Path $OutRoot 'AUTH_NEXT_ACTION.json') -Encoding UTF8

Write-Output "MATCHED_COUNT=$($matched.Count)"
Write-Output "SECURITY_STATUS=$($result.security_4625.status)"
Write-Output "AUTH_FAILURE_CAUSE=$cause"
