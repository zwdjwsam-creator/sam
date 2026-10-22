param([string]$EvidencePath = '')
# Fallback only: SetFocus on unique aislash-editor-input. No typing/Enter.
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$AE=[System.Windows.Automation.AutomationElement]
$CT=[System.Windows.Automation.ControlType]
$TS=[System.Windows.Automation.TreeScope]
function Emit($o){ $j=$o|ConvertTo-Json -Compress -Depth 5; if($EvidencePath){[System.IO.File]::WriteAllText($EvidencePath,$j,[System.Text.UTF8Encoding]::new($false))}; Write-Output $j }
$wc=New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty,$CT::Window)
$wins=@()
foreach($w in $AE::RootElement.FindAll($TS::Children,$wc)){
  try{
    $n=$w.Current.Name
    if($n -match ' - Cursor$' -and $n -like '*BLACKBOX*' -and -not $w.Current.IsOffscreen){
      if([System.Diagnostics.Process]::GetProcessById($w.Current.ProcessId).ProcessName -ieq 'Cursor'){ $wins += $w }
    }
  }catch{}
}
if($wins.Count -ne 1){ Emit @{status='BLOCKED';reason='WINDOW_COUNT';count=$wins.Count}; exit 0 }
$ec=New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty,$CT::Edit)
$agent=@()
foreach($e in $wins[0].FindAll($TS::Descendants,$ec)){
  try{ if(-not $e.Current.IsOffscreen -and $e.Current.ClassName -eq 'aislash-editor-input'){ $agent += $e } }catch{}
}
if($agent.Count -ne 1){ Emit @{status='BLOCKED';reason='AGENT_COUNT';count=$agent.Count}; exit 0 }
try{ $agent[0].SetFocus() }catch{ Emit @{status='BLOCKED';reason='SETFOCUS_FAILED'}; exit 0 }
Start-Sleep -Milliseconds 200
$f=$AE::FocusedElement
$ok=($f -ne $null -and $f.Current.ClassName -eq 'aislash-editor-input')
Emit @{status=$(if($ok){'FOCUS_OK'}else{'BLOCKED'}); reason=$(if($ok){'SETFOCUS'}else{'FOCUS_NOT_AGENT'}); focused_class=$(if($f){$f.Current.ClassName}else{''}); uia_focus_in_target=$ok; clicked=$false}
