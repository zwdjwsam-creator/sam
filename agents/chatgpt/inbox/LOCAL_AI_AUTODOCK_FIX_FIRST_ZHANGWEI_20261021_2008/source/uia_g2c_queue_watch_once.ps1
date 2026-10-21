# Read-only. Waits for this Agent turn to end, then records whether a queued HUB is still shown.
# Does not type, click, or press Enter.
Start-Sleep -Seconds 50
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$AE = [System.Windows.Automation.AutomationElement]
$CT = [System.Windows.Automation.ControlType]
$TS = [System.Windows.Automation.TreeScope]
$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$wc = New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Window)
$win = $null
foreach ($w in $AE::RootElement.FindAll($TS::Children, $wc)) {
  try {
    $n = $w.Current.Name
    if ($n -match ' - Cursor$' -and $n -like '*BLACKBOX*' -and -not $w.Current.IsOffscreen) { $win = $w; break }
  } catch {}
}
$queued = 0
$hubName = 0
if ($win) {
  $stack = New-Object System.Collections.Generic.Stack[System.Windows.Automation.AutomationElement]
  $stack.Push($win)
  $n = 0
  while ($stack.Count -gt 0 -and $n -lt 4000) {
    $el = $stack.Pop(); $n++
    try {
      $nm = [string]$el.Current.Name
      if ($nm -match 'Queued Message|排队') { $queued++ }
      if ($nm -ceq 'HUB') { $hubName++ }
    } catch {}
    try {
      $ch = $walker.GetFirstChild($el)
      while ($ch) { $stack.Push($ch); $ch = $walker.GetNextSibling($ch) }
    } catch {}
  }
}
$out = "D:\LOCAL_AI\Watchdog\hub_two_window_notifier_1913\evidence\g2c_queue_consume_2040.json"
@{
  at = (Get-Date).ToString('o')
  status = $(if ($queued -gt 0) { 'STILL_QUEUED' } else { 'QUEUE_BANNER_ABSENT' })
  queued_name_hits = $queued
  exact_hub_name_hits = $hubName
  note = 'Read-only. QUEUE_BANNER_ABSENT is not by itself history delivery.'
} | ConvertTo-Json | Set-Content -LiteralPath $out -Encoding UTF8
