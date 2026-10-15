# Read only. Requires normal interactive UAC consent; never changes system settings.
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'ADMIN_CONTEXT_REQUIRED'
}
if ($env:COMPUTERNAME -ine 'SAM') { throw 'WRONG_HOST' }
$outDir = 'C:\LAN_SHARE_REPORT\R9_SAM_AUTH_UAC_ONCE_20261015'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$start = [datetimeoffset]::Parse('2026-10-15T02:19:30Z')
$end = [datetimeoffset]::Parse('2026-10-15T02:19:33Z')
$results = @()
$channels = @('Security', 'Microsoft-Windows-SMBServer/Security', 'Microsoft-Windows-SMBServer/Operational')
foreach ($channel in $channels) {
    $selected = @()
    $status = 'QUERY_OK'
    $errorId = $null
    $filter = @{LogName=$channel; StartTime=$start.LocalDateTime; EndTime=$end.LocalDateTime}
    if ($channel -eq 'Security') { $filter.Id = 4625 }
    try {
        $found = @(Get-WinEvent -FilterHashtable $filter -ErrorAction Stop)
        foreach ($ev in $found) {
            $stamp = ([datetimeoffset]$ev.TimeCreated).ToUniversalTime()
            if ($stamp -lt $start -or $stamp -ge $end) { continue }
            $xml = [xml]$ev.ToXml()
            $data = @{}
            foreach ($d in $xml.Event.EventData.Data) {
                if ($d.Name) { $data[[string]$d.Name] = [string]$d.'#text' }
            }
            $peer = @($data['IpAddress'], $data['ClientAddress'], $data['ClientName'], $data['WorkstationName'])
            $relevant = $false
            foreach ($v in $peer) {
                if ($v -match '(?i)^(::ffff:)?192\.168\.100\.1$|^(\\\\)?ZHANGWEI(\..*)?$') { $relevant = $true }
            }
            if (-not $relevant) { continue }
            if ($channel -eq 'Security' -and $data['LogonType'] -ne '3') { continue }
            $selected += [pscustomobject]@{
                event_id=$ev.Id
                time_utc=$stamp.ToString('o')
                time_shanghai=$stamp.ToOffset([timespan]::FromHours(8)).ToString('o')
                target_user=$data['TargetUserName']
                target_domain=$data['TargetDomainName']
                workstation=$data['WorkstationName']
                source_ip=$data['IpAddress']
                client_address=$data['ClientAddress']
                status=$data['Status']
                substatus=$data['SubStatus']
                logon_type=$data['LogonType']
            }
        }
    } catch {
        $errorId = $_.FullyQualifiedErrorId
        if ($errorId -like '*NoMatchingEventsFound*') { $status='NO_EVENTS_RETURNED_BY_QUERY' }
        elseif ($_.Exception -is [UnauthorizedAccessException] -or $errorId -match 'UnauthorizedAccess|AccessDenied') { $status='ACCESS_DENIED' }
        else { $status='QUERY_FAILED' }
    }
    $results += [pscustomobject]@{
        channel=$channel
        query_status=$status
        error_id=$errorId
        matching_event_count=$(if($status -in @('QUERY_OK','NO_EVENTS_RETURNED_BY_QUERY')){$selected.Count}else{$null})
        events=$selected
    }
}
$result = [ordered]@{
    task_id='R9_NOTEBOOK_AUTH_WINDOW_ASSIST_20261015_1005'
    followup_id='R9_SAM_AUTH_UAC_ONCE_20261015_1051'
    execution_host=$env:COMPUTERNAME
    elevated=$true
    identity=$identity.Name
    reported_at=[datetimeoffset]::Now.ToString('o')
    window_half_open_utc='[2026-10-15T02:19:30Z,2026-10-15T02:19:33Z)'
    channels=$results
    copy_authorized=$false
    source_access_valid=$false
}
$json = $result | ConvertTo-Json -Depth 7
$utf8 = New-Object Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $outDir 'AUTH_UAC_QUERY_RESULT.json'), $json, $utf8)
Write-Output $json
