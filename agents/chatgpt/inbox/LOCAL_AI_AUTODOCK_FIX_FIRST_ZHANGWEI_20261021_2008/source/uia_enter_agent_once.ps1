param([string]$EvidencePath = '')
# One Enter only. Does not type. Requires the Agent composer to already be focused as aislash-editor-input.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinFg2 {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
"@
$AE = [System.Windows.Automation.AutomationElement]
$CT = [System.Windows.Automation.ControlType]
$TS = [System.Windows.Automation.TreeScope]
function Emit($o) {
  $j = $o | ConvertTo-Json -Compress -Depth 5
  if ($EvidencePath) { [System.IO.File]::WriteAllText($EvidencePath, $j, [System.Text.UTF8Encoding]::new($false)) }
  Write-Output $j
}
if ($env:LOCAL_AI_SEND_ARMED -ne '1') { Emit @{ status = 'QUEUE_ONLY' }; exit 0 }
$wc = New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Window)
$win = $null; $nwin = 0
foreach ($w in $AE::RootElement.FindAll($TS::Children, $wc)) {
  try {
    $n = $w.Current.Name
    if ($n -match ' - Cursor$' -and $n -like '*BLACKBOX*' -and -not $w.Current.IsOffscreen) {
      if ([System.Diagnostics.Process]::GetProcessById($w.Current.ProcessId).ProcessName -ieq 'Cursor') { $win = $w; $nwin++ }
    }
  } catch {}
}
if ($nwin -ne 1) { Emit @{ status = 'BLOCKED'; reason = 'WINDOW_COUNT'; window_count = $nwin }; exit 0 }
$ec = New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Edit)
$agent = @()
foreach ($e in $win.FindAll($TS::Descendants, $ec)) {
  try { if ($e.Current.ClassName -eq 'aislash-editor-input' -and -not $e.Current.IsOffscreen) { $agent += $e } } catch {}
}
if ($agent.Count -ne 1) { Emit @{ status = 'BLOCKED'; reason = 'AGENT_COUNT'; agent_count = $agent.Count }; exit 0 }
try { $agent[0].SetFocus() } catch { Emit @{ status = 'BLOCKED'; reason = 'SETFOCUS_FAILED' }; exit 0 }
Start-Sleep -Milliseconds 200
$focused = $AE::FocusedElement
if (-not $focused -or $focused.Current.ClassName -ne 'aislash-editor-input') {
  Emit @{ status = 'BLOCKED'; reason = 'FOCUS_NOT_AGENT'; focused_class = $(if ($focused) { $focused.Current.ClassName } else { '' }) }
  exit 0
}
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
Start-Sleep -Milliseconds 1200
Emit @{ status = 'ENTER_ONCE'; focused_class = 'aislash-editor-input'; foreground = [WinFg2]::GetForegroundWindow().ToInt64() }
