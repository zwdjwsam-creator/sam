# Deep UIA inside Cursor window: find ChatGPT-like edits and Agent composer
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::RootElement
$winCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Window
)
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $winCond)
$cursor = $null
foreach ($w in $wins) {
  if ($w.Current.Name -match 'Cursor') { $cursor = $w; break }
}
if (-not $cursor) {
  @{ status = 'BLOCKED'; reason = 'NO_CURSOR_WINDOW' } | ConvertTo-Json
  exit 0
}

$editCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Edit
)
$docCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Document
)
$btnCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Button
)

$edits = $cursor.FindAll([System.Windows.Automation.TreeScope]::Descendants, $editCond)
$docs = $cursor.FindAll([System.Windows.Automation.TreeScope]::Descendants, $docCond)
$btns = $cursor.FindAll([System.Windows.Automation.TreeScope]::Descendants, $btnCond)

$editInfo = @()
$i = 0
foreach ($e in $edits) {
  if ($i -ge 40) { break }
  $n = $e.Current.Name
  $aid = $e.Current.AutomationId
  $editInfo += [pscustomobject]@{
    name = $(if ($n) { if ($n.Length -gt 120) { $n.Substring(0,120) } else { $n } } else { '' })
    automation_id = $aid
    enabled = $e.Current.IsEnabled
    offscreen = $e.Current.IsOffscreen
  }
  $i++
}

$docInfo = @()
$j = 0
foreach ($d in $docs) {
  if ($j -ge 20) { break }
  $n = $d.Current.Name
  $docInfo += [pscustomobject]@{
    name = $(if ($n) { if ($n.Length -gt 120) { $n.Substring(0,120) } else { $n } } else { '' })
  }
  $j++
}

$interestingBtns = @()
$k = 0
foreach ($b in $btns) {
  $n = $b.Current.Name
  if (-not $n) { continue }
  if ($n -match 'Send|发送|ChatGPT|Browser|Simple|Agent|Submit|Stop|听写') {
    $interestingBtns += $n
    $k++
    if ($k -ge 30) { break }
  }
}

@{
  status = 'OK'
  cursor_window = $cursor.Current.Name
  edits = $edits.Count
  docs = $docs.Count
  buttons = $btns.Count
  edit_samples = $editInfo
  doc_samples = $docInfo
  interesting_buttons = $interestingBtns
  gpt_composer_candidate = [bool]($editInfo | Where-Object { $_.name -match 'ChatGPT|Work|Message|Ask|prompt|输入' })
  agent_composer_candidate = [bool]($editInfo | Where-Object { $_.name -match 'Agent|Plan|Chat|Composer|Ask' })
} | ConvertTo-Json -Depth 6
