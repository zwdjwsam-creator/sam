param([string]$WindowTitleHint = 'BLACKBOX')
# Read-only provider diagnostics. Never exports unknown draft text.
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$AE = [System.Windows.Automation.AutomationElement]
$CT = [System.Windows.Automation.ControlType]
$TS = [System.Windows.Automation.TreeScope]

function Summary([string]$value, [string]$accessibleName) {
  if ($null -eq $value) { $value = '' }
  $visible = New-Object System.Text.StringBuilder
  $categories = @{}
  foreach ($ch in $value.ToCharArray()) {
    $category = [System.Globalization.CharUnicodeInfo]::GetUnicodeCategory($ch).ToString()
    if (-not $categories.ContainsKey($category)) { $categories[$category] = 0 }
    $categories[$category]++
    if (-not [char]::IsWhiteSpace($ch) -and $category -notin @('Format', 'Control', 'LineSeparator', 'ParagraphSeparator')) {
      [void]$visible.Append($ch)
    }
  }
  $visibleText = $visible.ToString()
  $nameVisible = ($accessibleName -replace '\s', '') -replace '\p{Cf}', ''
  $hash = [System.Security.Cryptography.SHA256]::Create()
  try { $digest = ([BitConverter]::ToString($hash.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($value)))).Replace('-', '').ToLowerInvariant() }
  finally { $hash.Dispose() }
  return @{
    length = $value.Length; visible_length = $visibleText.Length
    exact_HUB = ($value -ceq 'HUB'); visible_exact_HUB = ($visibleText -ceq 'HUB')
    equals_accessible_name = ($accessibleName.Length -gt 0 -and $value -ceq $accessibleName)
    visible_equals_accessible_name = ($nameVisible.Length -gt 0 -and $visibleText -ceq $nameVisible)
    whitespace_or_format_only = ($visibleText.Length -eq 0)
    category_counts = $categories; sha256 = $digest
    raw_text = '[NOT_EXPORTED]'
  }
}

$wc = New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Window)
$windowCandidates = @()
foreach ($win in $AE::RootElement.FindAll($TS::Children, $wc)) {
  try {
    $c = $win.Current
    if ($c.Name -notmatch ' - Cursor$' -or $c.Name -notlike "*$WindowTitleHint*" -or $c.IsOffscreen) { continue }
    if ([System.Diagnostics.Process]::GetProcessById($c.ProcessId).ProcessName -ine 'Cursor') { continue }
    $windowCandidates += $win
  } catch {}
}
if ($windowCandidates.Count -ne 1) {
  @{status='BLOCKED_WINDOW_COUNT'; count=$windowCandidates.Count; no_actions=$true} | ConvertTo-Json
  exit 0
}
$boundWindow = $windowCandidates[0]
$ec = New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Edit)
$resultRows = @()
foreach ($edit in $boundWindow.FindAll($TS::Descendants, $ec)) {
  try {
    $c = $edit.Current
    if ($c.IsOffscreen -or -not $c.IsEnabled) { continue }
    if ($c.ClassName -ne 'aislash-editor-input' -and -not ($c.ClassName -eq 'ProseMirror' -and $c.Name -match 'ChatGPT')) { continue }
    $valueResult = @{supported=$false}
    $textResult = @{supported=$false}
    try {
      $vp = $edit.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
      $valueResult = @{supported=$true; readonly=$vp.Current.IsReadOnly; summary=(Summary ([string]$vp.Current.Value) ([string]$c.Name))}
    } catch { $valueResult.error_type = $_.Exception.GetType().Name }
    try {
      $tp = $edit.GetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern)
      # At most 4096 chars from the composer; never read the conversation document.
      $textResult = @{supported=$true; summary=(Summary ([string]$tp.DocumentRange.GetText(4096)) ([string]$c.Name))}
    } catch { $textResult.error_type = $_.Exception.GetType().Name }
    $rid = @(); try {$rid = @($edit.GetRuntimeId())} catch {}
    $resultRows += @{
      class_name = $c.ClassName; accessible_name = $c.Name; runtime_id = $rid
      value_pattern = $valueResult; text_pattern = $textResult
    }
  } catch {}
}
@{
  status='INSPECT_ONLY'; no_actions=$true; window=$boundWindow.Current.Name
  process_id=$boundWindow.Current.ProcessId; hwnd=$boundWindow.Current.NativeWindowHandle
  composers=$resultRows
  limitation='Provider values may contain placeholder or formatting. This report alone does not authorize clearing any draft or sending.'
} | ConvertTo-Json -Depth 9
