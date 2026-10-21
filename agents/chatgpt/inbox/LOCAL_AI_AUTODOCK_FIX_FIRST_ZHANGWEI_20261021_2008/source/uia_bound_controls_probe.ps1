param(
  [long]$WindowHandle = 0,
  [string]$WindowTitleHint = 'BLACKBOX'
)
# Inspect only. No input, clipboard, focus changes, invocation, files or model calls.
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$AE = [System.Windows.Automation.AutomationElement]
$CT = [System.Windows.Automation.ControlType]
$TS = [System.Windows.Automation.TreeScope]
$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker

function Snapshot($element) {
  $c = $element.Current
  $rid = @()
  try { $rid = @($element.GetRuntimeId()) } catch {}
  $r = $c.BoundingRectangle
  $name = [string]$c.Name
  # Only control/window labels; do not read composer values or chat transcript.
  if ($c.ControlType -eq $CT::Text -or $c.ControlType -eq $CT::Document) { $name = '[text omitted]' }
  if ($name.Length -gt 100) { $name = $name.Substring(0, 100) }
  $patterns = @()
  try { $patterns = @($element.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName }) } catch {}
  return [pscustomobject]@{
    name = $name; class_name = [string]$c.ClassName
    automation_id = [string]$c.AutomationId; control_type = $c.ControlType.ProgrammaticName
    runtime_id = $rid; process_id = $c.ProcessId; hwnd = $c.NativeWindowHandle
    enabled = $c.IsEnabled; offscreen = $c.IsOffscreen
    x = $r.X; y = $r.Y; w = $r.Width; h = $r.Height
    supported_patterns = $patterns
  }
}

$windowCondition = New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Window)
$wins = $AE::RootElement.FindAll($TS::Children, $windowCondition)
$windowCandidates = @()
foreach ($win in $wins) {
  try {
    $c = $win.Current
    if ($WindowHandle -ne 0 -and $c.NativeWindowHandle -ne $WindowHandle) { continue }
    if ($c.Name -notmatch ' - Cursor$' -or $c.Name -notlike "*$WindowTitleHint*") { continue }
    $ownerName = [System.Diagnostics.Process]::GetProcessById($c.ProcessId).ProcessName
    if ($ownerName -ine 'Cursor') { continue }
    if (-not $c.IsEnabled -or $c.IsOffscreen) { continue }
    $windowCandidates += $win
  } catch {}
}
if ($windowCandidates.Count -ne 1) {
  @{ status='BLOCKED_WINDOW_COUNT'; window_count=$windowCandidates.Count; no_actions=$true } | ConvertTo-Json -Depth 4
  exit 0
}
$boundWindow = $windowCandidates[0]
$editCondition = New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Edit)
$buttonCondition = New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Button)
$editElements = $boundWindow.FindAll($TS::Descendants, $editCondition)
$candidates = @()
foreach ($edit in $editElements) {
  try {
    $c = $edit.Current
    if (-not $c.IsEnabled -or $c.IsOffscreen -or $c.BoundingRectangle.Width -le 0) { continue }
    $role = $null
    if ($c.ClassName -eq 'aislash-editor-input') { $role = 'CURSOR_AGENT_CANDIDATE' }
    elseif ($c.ClassName -eq 'ProseMirror' -and $c.Name -match 'ChatGPT') { $role = 'GPT_WORK_CANDIDATE' }
    if (-not $role) { continue }  # excludes terminal and arbitrary unnamed edits
    $ancestors = @()
    $ancestor = $walker.GetParent($edit)
    for ($level = 0; $level -lt 7 -and $null -ne $ancestor; $level++) {
      if ($ancestor.Current.ControlType -eq $CT::Window) { break }
      $buttons = @()
      # Discovery only: association with a submit action is NOT established by this scan.
      $buttonElements = $ancestor.FindAll($TS::Descendants, $buttonCondition)
      for ($idx = 0; $idx -lt [Math]::Min($buttonElements.Count, 35); $idx++) {
        $button = $buttonElements.Item($idx)
        if (-not $button.Current.IsOffscreen) { $buttons += Snapshot $button }
      }
      $ancestors += [pscustomobject]@{ level=$level; node=(Snapshot $ancestor); visible_buttons=$buttons }
      $ancestor = $walker.GetParent($ancestor)
    }
    $candidates += [pscustomobject]@{ role=$role; node=(Snapshot $edit); ancestors=$ancestors }
  } catch {
    $candidates += [pscustomobject]@{ role='INSPECTION_ERROR'; reason=$_.Exception.GetType().Name }
  }
}
$agent = @($candidates | Where-Object { $_.role -eq 'CURSOR_AGENT_CANDIDATE' })
$gpt = @($candidates | Where-Object { $_.role -eq 'GPT_WORK_CANDIDATE' })
@{
  status='INSPECT_ONLY_NOT_BOUND_FOR_SEND'; no_actions=$true
  window=(Snapshot $boundWindow); agent_candidate_count=$agent.Count; gpt_candidate_count=$gpt.Count
  candidates=$candidates
  limitation='Class counts are candidates only. Need session identity and submit/history association. No send permission is implied.'
} | ConvertTo-Json -Depth 12
