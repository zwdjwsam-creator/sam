# SAM LAN preflight: READ ONLY; no IP/network changes.
# Execute on SAM, Windows PowerShell 5.1+, while no critical task is running.
param([string]$OutputDir='C:\LAN_SHARE_REPORT\AUTOHUB_REVIEW_20261013\lan')
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
function Safely { param([scriptblock]$Script)
  try { & $Script } catch { @{error = $_.Exception.Message} }
}
$adapters = @(Get-NetAdapter -IncludeHidden | Select-Object Name,InterfaceDescription,ifIndex,Status,LinkSpeed,MacAddress)
$ips = @(Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias,InterfaceIndex,IPAddress,PrefixLength,PrefixOrigin,AddressState,SkipAsSource)
$routes = @(Get-NetRoute -AddressFamily IPv4 | Where-Object { $_.DestinationPrefix -in @('192.168.100.0/24','0.0.0.0/0') } |
  Select-Object InterfaceAlias,InterfaceIndex,DestinationPrefix,NextHop,RouteMetric,PolicyStore)
$usb = @($adapters | Where-Object { $_.InterfaceDescription -match 'USB.*2\.5G|2\.5G.*USB|Realtek Gaming USB 2\.5GbE' })
$old = @($ips | Where-Object { $_.IPAddress -eq '192.168.100.2' })
$usbIps = @($ips | Where-Object { $usb.ifIndex -contains $_.InterfaceIndex })
$probe = Safely { Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
   Where-Object { $_.RemoteAddress -in @('192.168.100.1','192.168.100.2') -or $_.LocalPort -eq 445 -or $_.RemotePort -eq 445 } |
   Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State }
$smb = Safely { Get-SmbConnection | Select-Object ServerName,ShareName,NumOpens }
$taskNames = @('AUTOHUB_SAM_NOTEBOOK_POLLER','AUTOHUB_R2_COMM_TEST_RECEIVER_SAM')
$tasks = foreach($name in $taskNames) {
  $t = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if($t) {
    $i = Get-ScheduledTaskInfo -TaskName $name -ErrorAction SilentlyContinue
    [pscustomobject]@{Name=$name;State=[string]$t.State;LastRun=$i.LastRunTime;LastTaskResult=$i.LastTaskResult;
      Action=@($t.Actions | ForEach-Object { $_.Execute + ' ' + $_.Arguments }) }
  }
}
$case = [ordered]@{
  schema='SAM_LAN_PREFLIGHT_READONLY_V1'
  inspected_at=(Get-Date).ToString('o')
  host=$env:COMPUTERNAME
  adapters=$adapters
  ipv4=$ips
  routes=$routes
  usb_25g_adapters=$usb
  usb_ipv4=$usbIps
  holders_of_192_168_100_2=$old
  tcp_445_connections=$probe
  smb_connections=$smb
  watched_tasks=@($tasks)
  notes=@('READ_ONLY','NO_IP_CHANGE','NO_REBOOT','NO_BLACKBOX_WRITE','NO_MIGRATION','R9_HOLD')
}
$report = Join-Path $OutputDir 'sam_lan_preflight.json'
$case | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $report -Encoding UTF8
Write-Output ('WROTE: ' + $report)
Write-Output ('USB_2P5G_COUNT=' + @($usb).Count)
Write-Output ('USB_IPV4=' + (@($usbIps | ForEach-Object {$_.IPAddress}) -join ','))
Write-Output ('OLD_IP_192_168_100_2_OWNERS=' + @($old).Count)
Write-Output ('SCHEDULED_TASKS=' + @($tasks).Count)
