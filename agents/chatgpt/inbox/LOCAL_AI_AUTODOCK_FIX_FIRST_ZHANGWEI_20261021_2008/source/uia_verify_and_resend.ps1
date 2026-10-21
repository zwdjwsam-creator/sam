param(
  [Parameter(Mandatory = $true)][string]$Needle,
  [Parameter(Mandatory = $true)][string]$Message
)
if ($env:LOCAL_AI_SEND_ARMED -ne '1') {
  @{ status = 'QUEUE_ONLY'; reason = 'SEND_NOT_ARMED'; note = 'search-only path disabled while disarmed' } | ConvertTo-Json
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

# Search name/helptext for needle in descendants (bounded)
$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$found = $false
$hits = New-Object System.Collections.Generic.List[string]
$stack = New-Object System.Collections.Generic.Stack[System.Windows.Automation.AutomationElement]
$stack.Push($cursor)
$visited = 0
while ($stack.Count -gt 0 -and $visited -lt 2500) {
  $el = $stack.Pop()
  $visited++
  try {
    $nm = $el.Current.Name
    if ($nm -and $nm.Contains($Needle)) {
      $found = $true
      if ($hits.Count -lt 5) {
        $snip = $nm
        if ($snip.Length -gt 160) { $snip = $snip.Substring(0, 160) }
        $hits.Add($snip) | Out-Null
      }
    }
  } catch {}
  try {
    $child = $walker.GetFirstChild($el)
    while ($child -ne $null) {
      $stack.Push($child)
      $child = $walker.GetNextSibling($child)
    }
  } catch {}
}

if ($found) {
  @{
    status = 'DELIVERED_ECHO_FOUND'
    cursor_window = $cursor.Current.Name
    visited = $visited
    hits = $hits
  } | ConvertTo-Json -Depth 4
  exit 0
}

# Resend via clipboard into 使用 ChatGPT Work
$editCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Edit
)
$edits = $cursor.FindAll([System.Windows.Automation.TreeScope]::Descendants, $editCond)
$box = $null
foreach ($e in $edits) {
  # Match embedded GPT composers: 使用/询问 ChatGPT Work / Message
  if ($e.Current.Name -match '使用 ChatGPT|询问 ChatGPT|ChatGPT Work|Ask ChatGPT') { $box = $e; break }
}
if (-not $box) {
  @{ status = 'BLOCKED'; reason = 'NO_COMPOSER_FOR_RESEND'; visited = $visited } | ConvertTo-Json
  exit 0
}
try { $box.SetFocus() } catch {}
Start-Sleep -Milliseconds 200
[System.Windows.Forms.Clipboard]::SetText($Message)
[System.Windows.Forms.SendKeys]::SendWait('^a')
Start-Sleep -Milliseconds 80
[System.Windows.Forms.SendKeys]::SendWait('^v')
Start-Sleep -Milliseconds 250
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
Start-Sleep -Milliseconds 1200

# second search
$found2 = $false
$hits2 = New-Object System.Collections.Generic.List[string]
$stack2 = New-Object System.Collections.Generic.Stack[System.Windows.Automation.AutomationElement]
$stack2.Push($cursor)
$visited2 = 0
while ($stack2.Count -gt 0 -and $visited2 -lt 2500) {
  $el = $stack2.Pop()
  $visited2++
  try {
    $nm = $el.Current.Name
    if ($nm -and $nm.Contains($Needle)) {
      $found2 = $true
      if ($hits2.Count -lt 5) {
        $snip = $nm
        if ($snip.Length -gt 160) { $snip = $snip.Substring(0, 160) }
        $hits2.Add($snip) | Out-Null
      }
    }
  } catch {}
  try {
    $child = $walker.GetFirstChild($el)
    while ($child -ne $null) {
      $stack2.Push($child)
      $child = $walker.GetNextSibling($child)
    }
  } catch {}
}

@{
  status = $(if ($found2) { 'DELIVERED_ECHO_FOUND' } else { 'ATTEMPTED_NO_ECHO' })
  method = 'CLIPBOARD_PASTE_ENTER'
  cursor_window = $cursor.Current.Name
  visited_before = $visited
  visited_after = $visited2
  hits = $hits2
  note = 'If ATTEMPTED_NO_ECHO, Browser MCP still preferred; do not claim SENT'
} | ConvertTo-Json -Depth 5
