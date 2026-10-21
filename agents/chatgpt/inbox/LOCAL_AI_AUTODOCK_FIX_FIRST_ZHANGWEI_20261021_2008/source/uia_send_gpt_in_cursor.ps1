param(
  [Parameter(Mandatory = $true)][string]$Message,
  [string]$EvidencePath = ""
)
# Hard stop: scheduler and operator stay QUEUE_ONLY until an explicit arm.
if ($env:LOCAL_AI_SEND_ARMED -ne '1') {
  $blocked = @{ status = 'QUEUE_ONLY'; reason = 'SEND_NOT_ARMED'; note = 'no type, no Enter' }
  if ($EvidencePath) { $blocked | ConvertTo-Json | Set-Content -LiteralPath $EvidencePath -Encoding UTF8 }
  $blocked | ConvertTo-Json
  exit 0
}
if ($Message -ne 'HUB') {
  @{ status = 'BLOCKED'; reason = 'BODY_MUST_BE_ASCII_HUB' } | ConvertTo-Json
  exit 0
}
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms

$root = [System.Windows.Automation.AutomationElement]::RootElement
$winCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Window
)
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $winCond)

# Prefer real Cursor IDE window, never external Chrome titled with "Cursor"
$cursor = $null
$candidates = @()
foreach ($w in $wins) {
  $n = $w.Current.Name
  if (-not $n) { continue }
  $candidates += $n
  if ($n -match ' - Cursor$' -or $n -match 'Cursor$') {
    if ($n -notmatch 'Google Chrome|Microsoft Edge|Firefox') {
      $cursor = $w
      break
    }
  }
}
if (-not $cursor) {
  @{
    status = 'BLOCKED'
    reason = 'CURSOR_IDE_WINDOW_NOT_FOUND'
    window_candidates = ($candidates | Select-Object -First 20)
  } | ConvertTo-Json -Depth 4
  exit 0
}

$editCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Edit
)
$edits = $cursor.FindAll([System.Windows.Automation.TreeScope]::Descendants, $editCond)
$box = $null
$names = @()
foreach ($e in $edits) {
  $en = $e.Current.Name
  if ($en) { $names += $en }
  # Embedded ChatGPT composer often exposes Chinese "使用 ChatGPT" / Work / Message
  if ($en -match '使用 ChatGPT|ChatGPT Work|Message|询问|Ask ChatGPT|prompt') {
    $box = $e
    break
  }
}
# Do NOT fall back to arbitrary edit (could be address bar / agent box)
if (-not $box) {
  @{
    status = 'BLOCKED'
    reason = 'GPT_COMPOSER_IN_CURSOR_NOT_FOUND'
    cursor_window = $cursor.Current.Name
    edits = $edits.Count
    edit_names = ($names | Select-Object -First 30)
    note = 'Official Browser MCP preferred; UIA cannot safely locate 接管迁移核验 composer'
  } | ConvertTo-Json -Depth 5
  exit 0
}

try { $box.SetFocus() } catch {}
$vp = $null
try { $vp = $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern) } catch {}
$method = 'NONE'
if ($vp) {
  try { $vp.SetValue($Message); $method = 'VALUE_PATTERN' } catch {}
}
if ($method -eq 'NONE') {
  [System.Windows.Forms.Clipboard]::SetText($Message)
  [System.Windows.Forms.SendKeys]::SendWait('^a')
  Start-Sleep -Milliseconds 100
  [System.Windows.Forms.SendKeys]::SendWait('^v')
  $method = 'CLIPBOARD_PASTE'
}
Start-Sleep -Milliseconds 400
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
Start-Sleep -Milliseconds 900
$rb = ''
try { if ($vp) { $rb = [string]$vp.Current.Value } } catch {}
$result = @{
  status = 'ATTEMPTED'
  method = $method
  cursor_window = $cursor.Current.Name
  edit_name = $box.Current.Name
  readback_empty_after_enter = [bool](-not $rb)
  note = 'ATTEMPTED only; require thread echo for DELIVERED'
}
if ($EvidencePath) {
  $result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
}
$result | ConvertTo-Json -Depth 5
