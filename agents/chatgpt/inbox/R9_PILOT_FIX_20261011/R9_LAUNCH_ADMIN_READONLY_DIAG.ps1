# Launches R9_ADMIN_READONLY_DIAG.ps1 via normal UAC consent (RunAs).
# User must click Yes on the UAC prompt. No silent elevation.
$ErrorActionPreference = 'Stop'
$script = 'C:\LAN_SHARE_REPORT\R9_ADMIN_READONLY_DIAG.ps1'
$marker = 'C:\LAN_SHARE_REPORT\R9_ADMIN_DIAG_UAC_REQUESTED.json'
$utf8 = New-Object System.Text.UTF8Encoding $true
$req = [ordered]@{
  requested_at = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
  script       = $script
  method       = 'Start-Process -Verb RunAs'
  purpose      = 'Read-only process identity + preflight-only for R9 gate; no kill/copy/ACL change'
}
[System.IO.File]::WriteAllText($marker, ($req | ConvertTo-Json), $utf8)
Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList @(
  '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $script
) -Wait
exit $LASTEXITCODE
