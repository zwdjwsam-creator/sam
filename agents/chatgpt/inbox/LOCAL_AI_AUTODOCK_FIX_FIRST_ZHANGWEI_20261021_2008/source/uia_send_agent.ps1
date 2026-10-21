param(
  [Parameter(Mandatory = $true)][string]$Message,
  [Parameter(Mandatory = $true)][string]$Needle
)
if ($env:LOCAL_AI_SEND_ARMED -ne '1') {
  @{ status = 'QUEUE_ONLY'; reason = 'SEND_NOT_ARMED'; note = 'no type, no Enter' } | ConvertTo-Json
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
$cursor = $null
foreach ($w in $wins) {
  $n = $w.Current.Name
  if ($n -match ' - Cursor$' -and $n -notmatch 'Chrome|Edge|Firefox') { $cursor = $w; break }
}
if (-not $cursor) {
  @{ status = 'BLOCKED'; reason = 'NO_CURSOR' } | ConvertTo-Json
  exit 0
}

$editCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Edit
)
$edits = $cursor.FindAll([System.Windows.Automation.TreeScope]::Descendants, $editCond)
$agentBox = $null
$names = @()
foreach ($e in $edits) {
  $en = [string]$e.Current.Name
  if ($en) { $names += $en }
  # Skip ChatGPT embedded composer
  if ($en -match '使用 ChatGPT|ChatGPT Work|询问 ChatGPT') { continue }
  # Prefer agent-ish names; otherwise last non-GPT enabled edit
  if ($en -match 'Agent|Plan|Ask|Message|聊天|输入|Composer') {
    $agentBox = $e
    break
  }
}
if (-not $agentBox) {
  foreach ($e in $edits) {
    $en = [string]$e.Current.Name
    if ($en -match '使用 ChatGPT|ChatGPT Work|询问 ChatGPT|地址') { continue }
    if ($e.Current.IsEnabled -and -not $e.Current.IsOffscreen) { $agentBox = $e }
  }
}
if (-not $agentBox) {
  @{
    status = 'BLOCKED'
    reason = 'AGENT_COMPOSER_NOT_FOUND'
    edit_names = $names
    edits = $edits.Count
  } | ConvertTo-Json -Depth 4
  exit 0
}

try { $agentBox.SetFocus() } catch {}
Start-Sleep -Milliseconds 200
[System.Windows.Forms.Clipboard]::SetText($Message)
[System.Windows.Forms.SendKeys]::SendWait('^a')
Start-Sleep -Milliseconds 80
[System.Windows.Forms.SendKeys]::SendWait('^v')
Start-Sleep -Milliseconds 250
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
Start-Sleep -Milliseconds 1500

$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$found = $false
$hits = New-Object System.Collections.Generic.List[string]
$stack = New-Object System.Collections.Generic.Stack[System.Windows.Automation.AutomationElement]
$stack.Push($cursor)
$visited = 0
while ($stack.Count -gt 0 -and $visited -lt 3000) {
  $el = $stack.Pop(); $visited++
  try {
    $nm = $el.Current.Name
    if ($nm -and $nm.Contains($Needle)) {
      $found = $true
      if ($hits.Count -lt 5) {
        $snip = $nm; if ($snip.Length -gt 160) { $snip = $snip.Substring(0,160) }
        $hits.Add($snip) | Out-Null
      }
    }
  } catch {}
  try {
    $child = $walker.GetFirstChild($el)
    while ($child -ne $null) { $stack.Push($child); $child = $walker.GetNextSibling($child) }
  } catch {}
}

@{
  status = $(if ($found) { 'DELIVERED_ECHO_FOUND' } else { 'ATTEMPTED_NO_ECHO' })
  edit_name = $agentBox.Current.Name
  cursor_window = $cursor.Current.Name
  hits = $hits
  visited = $visited
  all_edit_names = $names
} | ConvertTo-Json -Depth 5
