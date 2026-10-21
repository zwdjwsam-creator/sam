# Inspect-only target binding. Never types, never Enter, never clipboard.
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::RootElement
$winCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Window
)
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $winCond)
$cursor = $null
$titles = @()
foreach ($w in $wins) {
  $n = $w.Current.Name
  if ($n) { $titles += $n }
  if ($n -match ' - Cursor$' -and $n -notmatch 'Chrome|Edge|Firefox') { $cursor = $w; break }
}
if (-not $cursor) {
  @{ status = 'BLOCKED'; reason = 'NO_CURSOR_WINDOW'; titles = ($titles | Select-Object -First 15) } | ConvertTo-Json -Depth 4
  exit 0
}

$editCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Edit
)
$edits = $cursor.FindAll([System.Windows.Automation.TreeScope]::Descendants, $editCond)
$rows = @()
foreach ($e in $edits) {
  $n = [string]$e.Current.Name
  $kind = 'OTHER'
  if ($n -match '使用 ChatGPT|询问 ChatGPT|ChatGPT Work|Ask ChatGPT') { $kind = 'GPT_WORK_CANDIDATE' }
  elseif ($n -match '地址|终端|Terminal') { $kind = 'NON_COMPOSER' }
  elseif ($n -match 'Agent|Plan|Composer|Ask') { $kind = 'AGENT_NAME_HIT' }
  $rect = $e.Current.BoundingRectangle
  $rows += [pscustomobject]@{
    kind = $kind
    name = $(if ($n.Length -gt 80) { $n.Substring(0, 80) } else { $n })
    automation_id = [string]$e.Current.AutomationId
    class_name = [string]$e.Current.ClassName
    process_id = $e.Current.ProcessId
    hwnd = $e.Current.NativeWindowHandle
    offscreen = $e.Current.IsOffscreen
    x = [int]$rect.X
    y = [int]$rect.Y
    w = [int]$rect.Width
    h = [int]$rect.Height
  }
}
$gpt = @($rows | Where-Object { $_.kind -eq 'GPT_WORK_CANDIDATE' -and -not $_.offscreen })
$agent = @($rows | Where-Object { $_.kind -eq 'AGENT_NAME_HIT' -and -not $_.offscreen })
@{
  status = 'INSPECT_ONLY'
  mode = 'QUEUE_ONLY'
  cursor_window = $cursor.Current.Name
  cursor_process_id = $cursor.Current.ProcessId
  cursor_hwnd = $cursor.Current.NativeWindowHandle
  edit_count = $edits.Count
  gpt_work_visible = $gpt.Count
  agent_name_visible = $agent.Count
  c2g_binding = $(if ($gpt.Count -eq 1) { 'CANDIDATE_NOT_PROVEN' } elseif ($gpt.Count -eq 0) { 'NOT_FOUND' } else { 'AMBIGUOUS' })
  g2c_binding = $(if ($agent.Count -eq 1) { 'CANDIDATE_NOT_PROVEN' } else { 'NOT_UNIQUE' })
  edits = $rows
  note = 'Name match is not session proof. No keystrokes sent.'
} | ConvertTo-Json -Depth 6
