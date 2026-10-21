param(
  [Parameter(Mandatory = $true)][string]$Message,
  [Parameter(Mandatory = $true)][string]$Needle,
  [string]$EvidencePath = ""
)
if ($env:LOCAL_AI_SEND_ARMED -ne '1') {
  $blocked = @{ status = 'QUEUE_ONLY'; reason = 'SEND_NOT_ARMED'; note = 'no type, no Enter' }
  if ($EvidencePath) { $blocked | ConvertTo-Json | Set-Content -LiteralPath $EvidencePath -Encoding UTF8 }
  $blocked | ConvertTo-Json
  exit 0
}
if ($Message -ne 'HUB') {
  @{ status = 'BLOCKED'; reason = 'BODY_MUST_BE_ASCII_HUB' } | ConvertTo-Json
  exit 0
}
# C2G: send into embedded GPT composer; prove delivery only if
# (1) composer emptied after Enter AND (2) needle appears in a non-Edit control.
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

$editCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Edit
)
$edits = $cursor.FindAll([System.Windows.Automation.TreeScope]::Descendants, $editCond)
$box = $null
foreach ($e in $edits) {
  if ($e.Current.Name -match '使用 ChatGPT|询问 ChatGPT|ChatGPT Work|Ask ChatGPT') { $box = $e; break }
}
if (-not $box) {
  @{ status = 'BLOCKED'; reason = 'GPT_COMPOSER_NOT_FOUND'; cursor_window = $cursor.Current.Name } | ConvertTo-Json
  exit 0
}

function Find-NeedleNonEdit([System.Windows.Automation.AutomationElement]$win, [string]$nd, [int]$limit) {
  $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
  $stack = New-Object System.Collections.Generic.Stack[System.Windows.Automation.AutomationElement]
  $stack.Push($win)
  $visited = 0
  $hits = New-Object System.Collections.Generic.List[string]
  while ($stack.Count -gt 0 -and $visited -lt $limit) {
    $el = $stack.Pop()
    $visited++
    try {
      $ct = $el.Current.ControlType
      $isEdit = ($ct -eq [System.Windows.Automation.ControlType]::Edit)
      $nm = $el.Current.Name
      if (-not $isEdit -and $nm -and $nm.Contains($nd)) {
        $snip = $nm
        if ($snip.Length -gt 180) { $snip = $snip.Substring(0, 180) }
        $hits.Add(("[{0}] {1}" -f $ct.ProgrammaticName, $snip)) | Out-Null
        if ($hits.Count -ge 5) { break }
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
  return @{ hits = $hits; visited = $visited }
}

$pre = Find-NeedleNonEdit $cursor $Needle 2000
$vp = $null
try { $vp = $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern) } catch {}
try { $box.SetFocus() } catch {}
Start-Sleep -Milliseconds 150
$method = 'NONE'
if ($vp) {
  try { $vp.SetValue($Message); $method = 'VALUE_PATTERN' } catch {}
}
if ($method -eq 'NONE') {
  [System.Windows.Forms.Clipboard]::SetText($Message)
  [System.Windows.Forms.SendKeys]::SendWait('^a')
  Start-Sleep -Milliseconds 80
  [System.Windows.Forms.SendKeys]::SendWait('^v')
  $method = 'CLIPBOARD_PASTE'
}
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
Start-Sleep -Milliseconds 1800

$rb = ''
try { if ($vp) { $rb = [string]$vp.Current.Value } } catch {}
$composer_empty = [bool](-not $rb -or $rb.Trim().Length -eq 0)
$post = Find-NeedleNonEdit $cursor $Needle 2500

$status = 'ATTEMPTED_NO_THREAD_ECHO'
if ($composer_empty -and $post.hits.Count -gt 0 -and $pre.hits.Count -eq 0) {
  $status = 'DELIVERED_THREAD_ECHO'
} elseif ($post.hits.Count -gt 0 -and -not $composer_empty) {
  $status = 'COMPOSER_STILL_HOLDS_TEXT'
} elseif ($post.hits.Count -gt 0 -and $pre.hits.Count -gt 0) {
  $status = 'ECHO_PREEXISTED'
}

$result = @{
  status = $status
  method = $method
  cursor_window = $cursor.Current.Name
  edit_name = $box.Current.Name
  composer_empty_after_enter = $composer_empty
  composer_readback_len = $(if ($rb) { $rb.Length } else { 0 })
  pre_non_edit_hits = $pre.hits
  post_non_edit_hits = $post.hits
  note = 'DELIVERED_THREAD_ECHO requires empty composer + new non-Edit needle'
}
if ($EvidencePath) {
  $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
}
$result | ConvertTo-Json -Depth 6
