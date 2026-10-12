# AUTOHUB R2 COMMUNICATION_TEST receiver (ZHANGWEI)
# Polls GitHub results for PING target=ZHANGWEI; writes local ACK staging.
# Does NOT touch BLACKBOX / R9 copy. Never prints tokens.
param(
  [string]$TokenFile = '',
  [string]$OutDir = 'C:\LAN_SHARE_REPORT\AUTOHUB_R2_DESKTOP\receiver_out',
  [string]$StateFile = 'C:\LAN_SHARE_REPORT\AUTOHUB_R2_DESKTOP\receiver_state.json'
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
function Resolve-TokenFile {
  param([string]$Explicit)
  if ($Explicit -and (Test-Path -LiteralPath $Explicit)) { return $Explicit }
  $ptr = 'C:\LAN_SHARE_REPORT\AUTOHUB_R2_DESKTOP\token_path.txt'
  if (Test-Path -LiteralPath $ptr) {
    $p = (Get-Content -LiteralPath $ptr -Encoding UTF8 -TotalCount 1).Trim()
    if ($p -and (Test-Path -LiteralPath $p)) { return $p }
  }
  $hit = Get-ChildItem -Path 'C:\LAN_SHARE_REPORT' -Recurse -Filter 'github_hub_token.TXT' -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName
  if ($hit) { return $hit }
  throw 'NO_TOKEN_FILE'
}
function Get-Token {
  param([string]$Path)
  foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
    $s = $line.Trim().Trim([char]0xFEFF)
    if ($s -and -not $s.StartsWith('#')) { return $s }
  }
  throw 'NO_TOKEN'
}
$TokenFile = Resolve-TokenFile -Explicit $TokenFile
$token = Get-Token -Path $TokenFile
$headers = @{
  Authorization = "Bearer $token"
  Accept = 'application/vnd.github+json'
  'User-Agent' = 'autohub-r2-desktop-receiver'
  'X-GitHub-Api-Version' = '2022-11-28'
}
$api = 'https://api.github.com/repos/zwdjwsam-creator/sam/contents/agents/chatgpt/inbox/AUTOHUB_R2_RESULTS_20261012'
$state = @{ processed = @(); last_run_utc = $null; uploaded = @() }
if (Test-Path -LiteralPath $StateFile) {
  $obj = Get-Content -LiteralPath $StateFile -Raw -Encoding UTF8 | ConvertFrom-Json
  $processed = @()
  if ($obj.processed) { $processed = @($obj.processed) }
  $uploaded = @()
  if ($obj.uploaded) { $uploaded = @($obj.uploaded) }
  $state = @{ processed = $processed; uploaded = $uploaded; last_run_utc = $obj.last_run_utc }
}
$list = Invoke-RestMethod -Uri $api -Headers $headers -Method Get
$acks = @()
foreach ($item in $list) {
  if ($item.name -notlike 'PING_*.json') { continue }
  if ($state.processed -contains $item.name) { continue }
  $rawH = $headers.Clone(); $rawH['Accept'] = 'application/vnd.github.raw'
  $ping = Invoke-RestMethod -Uri $item.download_url -Headers @{ Authorization = $headers.Authorization; 'User-Agent' = $headers.'User-Agent' } -Method Get
  if ($ping.target -ne 'ZHANGWEI') { continue }
  if ($ping.scope -ne 'COMMUNICATION_TEST') { continue }
  if ($ping.task_id -ne 'AUTOHUB_R2_PROTOCOL_REPAIR_20261012') { continue }
  $ackId = 'ACK_ZHANGWEI_FOR_' + ($ping.ping_id)
  $ack = [ordered]@{
    schema = 'AUTOHUB_COMMUNICATION_TEST_V1'
    scope = 'COMMUNICATION_TEST'
    task_id = $ping.task_id
    ack_id = $ackId
    ping_id = $ping.ping_id
    from = 'ZHANGWEI'
    target = 'SAM'
    in_reply_to = "agents/chatgpt/inbox/AUTOHUB_R2_RESULTS_20261012/$($item.name)"
    nonce = $ping.nonce
    acked_utc = (Get-Date).ToUniversalTime().ToString('o')
    receiver = 'powershell_comm_test_receiver_r2_desktop'
    cursor_agent_wake = $false
    r9_hold_unchanged = $true
    copy_authorized = $false
  }
  $ackPath = Join-Path $OutDir ($ackId + '.json')
  ($ack | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $ackPath -Encoding utf8
  $acks += $ackPath
  $state.processed += $item.name
}

function Publish-HubFile {
  param([string]$RelPath, [string]$LocalPath, [string]$Message)
  $url = "https://api.github.com/repos/zwdjwsam-creator/sam/contents/$RelPath"
  $sha = $null
  try {
    $cur = Invoke-RestMethod -Uri $url -Headers $headers -Method Get
    if ($cur.sha) { $sha = $cur.sha }
  } catch {
    # 404 = new file
  }
  $bytes = [System.IO.File]::ReadAllBytes($LocalPath)
  $b64 = [Convert]::ToBase64String($bytes)
  $body = @{ message = $Message; content = $b64; branch = 'main' }
  if ($sha) { $body.sha = $sha }
  $json = $body | ConvertTo-Json -Compress
  Invoke-RestMethod -Uri $url -Headers $headers -Method Put -Body $json -ContentType 'application/json; charset=utf-8' | Out-Null
}

$uploadedNow = @()
Get-ChildItem -LiteralPath $OutDir -Filter 'ACK_*.json' -ErrorAction SilentlyContinue | ForEach-Object {
  if ($state.uploaded -contains $_.Name) { return }
  $rel = "agents/chatgpt/inbox/AUTOHUB_R2_RESULTS_20261012/$($_.Name)"
  try {
    Publish-HubFile -RelPath $rel -LocalPath $_.FullName -Message ("AUTOHUB auto ACK upload: " + $_.Name)
    $state.uploaded += $_.Name
    $uploadedNow += $_.Name
  } catch {
    Write-Output ("UPLOAD_FAIL=" + $_.Name + ":" + $_.Exception.Message)
  }
}

$state.last_run_utc = (Get-Date).ToUniversalTime().ToString('o')
($state | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $StateFile -Encoding utf8
Write-Output ("ACKS=" + ($acks -join ';'))
Write-Output ("UPLOADED=" + ($uploadedNow -join ';'))
# clear token from process env if present
Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue
Remove-Item Env:GH_TOKEN -ErrorAction SilentlyContinue
