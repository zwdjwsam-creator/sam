param(
  [Parameter(Mandatory = $true)][ValidateSet('C2G', 'G2C')][string]$Direction,
  [string]$EvidencePath = ''
)
# Focus-checked keyboard input of ASCII HUB. No Ctrl+A. No SetValue loop. No voice/model buttons.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinFg {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr hWnd, uint flags);
}
"@

$AE = [System.Windows.Automation.AutomationElement]
$CT = [System.Windows.Automation.ControlType]
$TS = [System.Windows.Automation.TreeScope]
$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker

function Emit($obj) {
  $json = $obj | ConvertTo-Json -Depth 6 -Compress
  if ($EvidencePath) { [System.IO.File]::WriteAllText($EvidencePath, $json, [System.Text.UTF8Encoding]::new($false)) }
  Write-Output $json
}
if ($env:LOCAL_AI_SEND_ARMED -ne '1') { Emit @{ status = 'QUEUE_ONLY'; reason = 'SEND_NOT_ARMED'; direction = $Direction }; exit 0 }

function Rid($el) { try { return ((@($el.GetRuntimeId())) -join ',') } catch { return '' } }
function VisibleSummary([string]$value, [string]$accessibleName) {
  if ($null -eq $value) { $value = '' }
  $sb = New-Object System.Text.StringBuilder
  foreach ($ch in $value.ToCharArray()) {
    $cat = [System.Globalization.CharUnicodeInfo]::GetUnicodeCategory($ch).ToString()
    if (-not [char]::IsWhiteSpace($ch) -and $cat -notin @('Format', 'Control', 'LineSeparator', 'ParagraphSeparator')) { [void]$sb.Append($ch) }
  }
  $vis = $sb.ToString()
  $nameVis = ($accessibleName -replace '\s', '')
  return @{
    length = $value.Length; visible_length = $vis.Length
    format_only = ($vis.Length -eq 0)
    visible_exact_HUB = ($vis -ceq 'HUB')
    visible_equals_name = ($nameVis.Length -gt 0 -and $vis -ceq $nameVis)
    visible_is_name_plus_HUB = ($nameVis.Length -gt 0 -and $vis -ceq ($nameVis + 'HUB'))
  }
}

$wc = New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Window)
$windows = @()
foreach ($w in $AE::RootElement.FindAll($TS::Children, $wc)) {
  try {
    $n = $w.Current.Name
    if ($n -notmatch ' - Cursor$' -or $n -notlike '*BLACKBOX*' -or $w.Current.IsOffscreen -or -not $w.Current.IsEnabled) { continue }
    if ($n -match 'Chrome|Edge|Firefox') { continue }
    if ([System.Diagnostics.Process]::GetProcessById($w.Current.ProcessId).ProcessName -ine 'Cursor') { continue }
    $windows += $w
  } catch {}
}
if ($windows.Count -ne 1) { Emit @{ status = 'BLOCKED'; reason = 'WINDOW_COUNT'; window_count = $windows.Count; direction = $Direction }; exit 0 }
$window = $windows[0]
$edits = $window.FindAll($TS::Descendants, (New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Edit)))
$agent = @(); $gpt = @()
foreach ($e in $edits) {
  try {
    $c = $e.Current
    if (-not $c.IsEnabled -or $c.IsOffscreen -or $c.BoundingRectangle.Width -le 0) { continue }
    if ($c.ClassName -eq 'aislash-editor-input') { $agent += $e }
    elseif ($c.ClassName -eq 'ProseMirror' -and $c.Name -match 'ChatGPT') { $gpt += $e }
  } catch {}
}
if ($Direction -eq 'G2C') {
  if ($agent.Count -ne 1) { Emit @{ status = 'BLOCKED_G2C'; reason = 'AGENT_COUNT'; agent_count = $agent.Count }; exit 0 }
  $target = $agent[0]; $other = $(if ($gpt.Count -ge 1) { $gpt[0] } else { $null })
} else {
  if ($gpt.Count -ne 1) { Emit @{ status = 'BLOCKED_C2G'; reason = 'GPT_COUNT'; gpt_count = $gpt.Count }; exit 0 }
  $target = $gpt[0]; $other = $(if ($agent.Count -ge 1) { $agent[0] } else { $null })
}

function Contains($root, $el) {
  if (-not $root -or -not $el) { return $false }
  $want = Rid $el
  $stack = New-Object System.Collections.Generic.Stack[System.Windows.Automation.AutomationElement]
  $stack.Push($root); $n = 0
  while ($stack.Count -gt 0 -and $n -lt 4000) {
    $cur = $stack.Pop(); $n++
    if ((Rid $cur) -eq $want) { return $true }
    try { $ch = $walker.GetFirstChild($cur); while ($ch) { $stack.Push($ch); $ch = $walker.GetNextSibling($ch) } } catch {}
  }
  return $false
}
$pane = $target; $node = $target
while ($true) {
  $parent = $walker.GetParent($node)
  if (-not $parent -or $parent.Current.ControlType -eq $CT::Window) { break }
  if ($other -and (Contains $parent $other)) { break }
  $pane = $parent; $node = $parent
}
function Count-HubOutsideComposer($root, $composer) {
  $hits = 0
  $stack = New-Object System.Collections.Generic.Stack[System.Windows.Automation.AutomationElement]
  $stack.Push($root); $n = 0
  while ($stack.Count -gt 0 -and $n -lt 5000) {
    $cur = $stack.Pop(); $n++
    if ((Rid $cur) -eq (Rid $composer)) { continue }
    try { if ([string]$cur.Current.Name -ceq 'HUB') { $hits++ } } catch {}
    try { $ch = $walker.GetFirstChild($cur); while ($ch) { $stack.Push($ch); $ch = $walker.GetNextSibling($ch) } } catch {}
  }
  return $hits
}
function Read-Vis($el) {
  $name = [string]$el.Current.Name
  $raw = ''
  try {
    $tp = $el.GetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern)
    $raw = [string]$tp.DocumentRange.GetText(256)
  } catch {}
  return (VisibleSummary $raw $name)
}

$beforeVis = Read-Vis $target
$allow = $false
if ($Direction -eq 'G2C' -and $beforeVis.format_only) { $allow = $true }
if ($Direction -eq 'C2G' -and ($beforeVis.format_only -or $beforeVis.visible_equals_name)) { $allow = $true }
$meta = @{
  direction = $Direction; status = 'BLOCKED'; window_count = 1
  hwnd = $window.Current.NativeWindowHandle; process_id = $window.Current.ProcessId
  target_class = $target.Current.ClassName
  before = $beforeVis; hub_history_before = (Count-HubOutsideComposer $pane $target)
}
if (-not $allow) { $meta.reason = 'WAIT_USER_DRAFT'; $meta.status = 'WAIT_USER_DRAFT'; Emit $meta; exit 0 }

$hwnd = [IntPtr]$window.Current.NativeWindowHandle
[WinFg]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Milliseconds 200
try { $target.SetFocus() } catch { $meta.reason = 'SETFOCUS_FAILED'; Emit $meta; exit 0 }
Start-Sleep -Milliseconds 200
$fg = [WinFg]::GetForegroundWindow()
$fgRoot = [WinFg]::GetAncestor($fg, 2)
$hwndRoot = [WinFg]::GetAncestor($hwnd, 2)
if ($fgRoot -ne $hwndRoot) { $meta.reason = 'FOREGROUND_NOT_TARGET'; $meta.foreground = $fg.ToInt64(); $meta.foreground_root = $fgRoot.ToInt64(); Emit $meta; exit 0 }
$focused = $null
try { $focused = $AE::FocusedElement } catch {}
$fid = $(if ($focused) { Rid $focused } else { '' })
$focusOk = ($fid -eq (Rid $target)) -or ($(if ($focused) { Contains $target $focused } else { $false }))
if (-not $focusOk) {
  $meta.reason = 'FOCUS_NOT_TARGET'
  $meta.focused_class = $(if ($focused) { $focused.Current.ClassName } else { '' })
  Emit $meta
  exit 0
}
[System.Windows.Forms.SendKeys]::SendWait('HUB')
Start-Sleep -Milliseconds 350
$mid = Read-Vis $target
$meta.typed = 'HUB'
$meta.after_type = $mid
if ($mid.visible_is_name_plus_HUB -and $focusOk) {
  [System.Windows.Forms.SendKeys]::SendWait('{BACKSPACE}{BACKSPACE}{BACKSPACE}')
  $meta.status = 'REVERTED_APPEND_TO_PLACEHOLDER'
  $meta.reason = 'TYPED_ONTO_PLACEHOLDER_NOT_SUBMITTED'
  Emit $meta
  exit 0
}
if (-not $mid.visible_exact_HUB) {
  $meta.provider = 'PROVIDER_UNRELIABLE'
  $meta.status = 'TYPED_AWAITING_VISUAL'
  $meta.reason = 'TEXTPATTERN_DID_NOT_SHOW_HUB'
  Emit $meta
  exit 0
}
$buttons = $pane.FindAll($TS::Descendants, (New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Button)))
$sent = $false
foreach ($b in $buttons) {
  try {
    if ($b.Current.IsOffscreen) { continue }
    if ([string]$b.Current.Name -match '^(发送|Send|Send message|发送消息)$') {
      $inv = $b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
      if ($inv) { $inv.Invoke(); $meta.method = 'INVOKE_SEND'; $sent = $true; break }
    }
  } catch {}
}
if (-not $sent) {
  $focused2 = $AE::FocusedElement
  $fid2 = Rid $focused2
  if ($fid2 -ne (Rid $target) -and -not (Contains $target $focused2)) {
    $meta.status = 'DELIVERY_UNCERTAIN'
    $meta.reason = 'FOCUS_LOST_BEFORE_ENTER'
    Emit $meta
    exit 0
  }
  $fg2 = [WinFg]::GetForegroundWindow()
  if ([WinFg]::GetAncestor($fg2, 2) -ne $hwndRoot) {
    $meta.status = 'DELIVERY_UNCERTAIN'; $meta.reason = 'FOREGROUND_LOST_BEFORE_ENTER'; Emit $meta; exit 0
  }
  [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
  $meta.method = 'FOCUS_ENTER_ONCE'
}
Start-Sleep -Milliseconds 1500
$after = Read-Vis $target
$hist = Count-HubOutsideComposer $pane $target
$meta.after_submit = $after
$meta.hub_history_after = $hist
$meta.composer_clear = [bool]($after.format_only -or $after.visible_equals_name)
if ($meta.composer_clear -and $hist -gt $meta.hub_history_before) { $meta.status = 'DELIVERED_HISTORY_HUB' }
elseif (-not $meta.composer_clear -and $after.visible_exact_HUB) { $meta.status = 'NOT_SUBMITTED' }
else { $meta.status = 'DELIVERY_UNCERTAIN' }
Emit $meta
