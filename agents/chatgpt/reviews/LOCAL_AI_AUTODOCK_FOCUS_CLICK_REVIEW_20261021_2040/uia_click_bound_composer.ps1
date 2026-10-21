param(
  [Parameter(Mandatory=$true)][ValidateSet('C2G','G2C')][string]$Direction,
  [switch]$FocusClick
)
# Inspect by default. Optional ONE click on a freshly hit-tested composer.
# Never types, clears, presses Enter, invokes a send button or reads draft values.
$ErrorActionPreference='Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class HubComposerMouse {
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X; public int Y; }
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(POINT p);
  [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr h, uint flags);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);
}
"@
$AE=[System.Windows.Automation.AutomationElement]
$CT=[System.Windows.Automation.ControlType]
$TS=[System.Windows.Automation.TreeScope]
$walker=[System.Windows.Automation.TreeWalker]::RawViewWalker
function Rid($e) { if (-not $e) { return '' }; try { return ((@($e.GetRuntimeId())) -join ',') } catch { return '' } }
function IsWithin($element,$ancestor) {
  $wanted=Rid $ancestor
  if (-not $wanted) { return $false }
  $cur=$element
  for ($i=0;$i -lt 20 -and $cur;$i++) {
    if ((Rid $cur) -eq $wanted) { return $true }
    try {$cur=$walker.GetParent($cur)} catch {return $false}
  }
  return $false
}
function Emit($o) {$o | ConvertTo-Json -Depth 6 -Compress}
$wc=New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty,$CT::Window)
$windowCandidates=@()
foreach($w in $AE::RootElement.FindAll($TS::Children,$wc)) {
  try {
    $c=$w.Current
    if($c.Name -notmatch ' - Cursor$' -or $c.Name -notlike '*BLACKBOX*' -or $c.IsOffscreen -or -not $c.IsEnabled){continue}
    if([System.Diagnostics.Process]::GetProcessById($c.ProcessId).ProcessName -ine 'Cursor'){continue}
    $windowCandidates+=$w
  }catch{}
}
if($windowCandidates.Count -ne 1){Emit @{status='BLOCKED';reason='WINDOW_COUNT';count=$windowCandidates.Count};exit 0}
$window=$windowCandidates[0]
$ec=New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty,$CT::Edit)
$composerCandidates=@()
foreach($e in $window.FindAll($TS::Descendants,$ec)) {
  try {
    $c=$e.Current
    if($c.IsOffscreen -or -not $c.IsEnabled -or $c.BoundingRectangle.Width -le 0){continue}
    if(($Direction -eq 'C2G' -and $c.ClassName -eq 'ProseMirror' -and $c.Name -match 'ChatGPT') -or
       ($Direction -eq 'G2C' -and $c.ClassName -eq 'aislash-editor-input')){$composerCandidates+=$e}
  }catch{}
}
if($composerCandidates.Count -ne 1){Emit @{status='BLOCKED';reason='COMPOSER_COUNT';count=$composerCandidates.Count};exit 0}
$target=$composerCandidates[0]
$meta=@{direction=$Direction;target_class=$target.Current.ClassName;target_rid=(Rid $target);hwnd=$window.Current.NativeWindowHandle;clicked=$false;typed=$false;submitted=$false}
if(-not $FocusClick){$meta.status='INSPECT_ONLY';Emit $meta;exit 0}
if($env:LOCAL_AI_SEND_ARMED -ne '1'){$meta.status='QUEUE_ONLY';$meta.reason='FOCUS_CLICK_NOT_ARMED';Emit $meta;exit 0}
$hwnd=[IntPtr]$window.Current.NativeWindowHandle
[HubComposerMouse]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Milliseconds 150
if([HubComposerMouse]::GetForegroundWindow() -ne $hwnd){$meta.status='BLOCKED';$meta.reason='FOREGROUND_NOT_WINDOW';Emit $meta;exit 0}
try {$point=$target.GetClickablePoint()}catch{$meta.status='BLOCKED';$meta.reason='NO_CLICKABLE_POINT';Emit $meta;exit 0}
$r=$target.Current.BoundingRectangle
if(-not $r.Contains($point)){$meta.status='BLOCKED';$meta.reason='POINT_OUTSIDE_COMPOSER';Emit $meta;exit 0}
$pointNative=New-Object HubComposerMouse+POINT
$pointNative.X=[int][Math]::Round($point.X);$pointNative.Y=[int][Math]::Round($point.Y)
$hitWindow=[HubComposerMouse]::WindowFromPoint($pointNative)
if([HubComposerMouse]::GetAncestor($hitWindow,2) -ne $hwnd){$meta.status='BLOCKED';$meta.reason='POINT_OBSCURED_OTHER_WINDOW';Emit $meta;exit 0}
try{$hitElement=$AE::FromPoint($point)}catch{$meta.status='BLOCKED';$meta.reason='UIA_HIT_TEST_FAILED';Emit $meta;exit 0}
if(-not (IsWithin $hitElement $target)){$meta.status='BLOCKED';$meta.reason='HIT_NOT_COMPOSER_SUBTREE';$meta.hit_class=$hitElement.Current.ClassName;Emit $meta;exit 0}
if([HubComposerMouse]::GetForegroundWindow() -ne $hwnd){$meta.status='BLOCKED';$meta.reason='FOREGROUND_CHANGED';Emit $meta;exit 0}
if(-not [HubComposerMouse]::SetCursorPos($pointNative.X,$pointNative.Y)){$meta.status='BLOCKED';$meta.reason='CURSOR_POSITION_FAILED';Emit $meta;exit 0}
[HubComposerMouse]::mouse_event(0x0002,0,0,0,[UIntPtr]::Zero)
[HubComposerMouse]::mouse_event(0x0004,0,0,0,[UIntPtr]::Zero)
Start-Sleep -Milliseconds 180
$focused=$null;try{$focused=$AE::FocusedElement}catch{}
$meta.clicked=$true;$meta.click_x=$pointNative.X;$meta.click_y=$pointNative.Y
$meta.foreground_after=[HubComposerMouse]::GetForegroundWindow().ToInt64()
$meta.uia_focus_in_target=(IsWithin $focused $target)
$meta.focused_class=$(if($focused){$focused.Current.ClassName}else{''})
$meta.status='CLICKED_COMPOSER_ONLY'
$meta.note='No typing/submission. UIA focus and actual rendered caret still require validation.'
Emit $meta
