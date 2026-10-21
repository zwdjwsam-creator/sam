param(
  [Parameter(Mandatory = $true)][ValidateSet('C2G', 'G2C')][string]$Direction,
  [ValidateSet('Send', 'Verify')][string]$Mode = 'Send',
  [string]$EvidencePath = ''
)
# One event. Body is ASCII HUB. Verify mode never writes or presses Enter.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
if ($Mode -eq 'Send') { Add-Type -AssemblyName System.Windows.Forms }

$AE = [System.Windows.Automation.AutomationElement]
$CT = [System.Windows.Automation.ControlType]
$TS = [System.Windows.Automation.TreeScope]
$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker

function Rid($el) {
  try { return ((@($el.GetRuntimeId())) -join ',') } catch { return '' }
}

function Emit($obj) {
  $json = $obj | ConvertTo-Json -Depth 8 -Compress
  if ($EvidencePath) {
    [System.IO.File]::WriteAllText($EvidencePath, $json, [System.Text.UTF8Encoding]::new($false))
  }
  Write-Output $json
}

if ($Mode -eq 'Send' -and $env:LOCAL_AI_SEND_ARMED -ne '1') {
  Emit @{ status = 'QUEUE_ONLY'; reason = 'SEND_NOT_ARMED'; direction = $Direction }
  exit 0
}

$wins = $AE::RootElement.FindAll($TS::Children, (New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Window)))
$window = $null
foreach ($w in $wins) {
  try {
    $n = $w.Current.Name
    if ($n -match ' - Cursor$' -and $n -like '*BLACKBOX*' -and $n -notmatch 'Chrome|Edge|Firefox') {
      $owner = [System.Diagnostics.Process]::GetProcessById($w.Current.ProcessId).ProcessName
      if ($owner -ieq 'Cursor' -and $w.Current.IsEnabled -and -not $w.Current.IsOffscreen) { $window = $w; break }
    }
  } catch {}
}
if (-not $window) { Emit @{ status = 'BLOCKED'; reason = 'CURSOR_WINDOW_NOT_UNIQUE'; direction = $Direction }; exit 0 }

$edits = $window.FindAll($TS::Descendants, (New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Edit)))
$agent = @(); $gpt = @(); $term = 0
foreach ($e in $edits) {
  try {
    $c = $e.Current
    if (-not $c.IsEnabled -or $c.IsOffscreen -or $c.BoundingRectangle.Width -le 0) { continue }
    if ($c.ClassName -eq 'xterm-helper-textarea') { $term++; continue }
    if ($c.ClassName -eq 'aislash-editor-input') { $agent += $e }
    elseif ($c.ClassName -eq 'ProseMirror' -and $c.Name -match 'ChatGPT') { $gpt += $e }
  } catch {}
}
$target = $null
$other = $null
if ($Direction -eq 'G2C') {
  if ($agent.Count -ne 1) { Emit @{ status = 'BLOCKED_G2C'; reason = 'AGENT_CLASS_NOT_UNIQUE'; agent_count = $agent.Count; gpt_count = $gpt.Count }; exit 0 }
  $target = $agent[0]; $other = $(if ($gpt.Count -ge 1) { $gpt[0] } else { $null })
} else {
  if ($gpt.Count -ne 1) { Emit @{ status = 'BLOCKED_C2G'; reason = 'GPT_CLASS_NOT_UNIQUE'; agent_count = $agent.Count; gpt_count = $gpt.Count }; exit 0 }
  $target = $gpt[0]; $other = $(if ($agent.Count -ge 1) { $agent[0] } else { $null })
}

function Contains($root, $el) {
  if (-not $root -or -not $el) { return $false }
  $want = Rid $el
  $stack = New-Object System.Collections.Generic.Stack[System.Windows.Automation.AutomationElement]
  $stack.Push($root)
  $n = 0
  while ($stack.Count -gt 0 -and $n -lt 4000) {
    $cur = $stack.Pop(); $n++
    if ((Rid $cur) -eq $want) { return $true }
    try {
      $ch = $walker.GetFirstChild($cur)
      while ($ch) { $stack.Push($ch); $ch = $walker.GetNextSibling($ch) }
    } catch {}
  }
  return $false
}

$pane = $target
$node = $target
while ($true) {
  $parent = $walker.GetParent($node)
  if (-not $parent) { break }
  if ($parent.Current.ControlType -eq $CT::Window) { break }
  if ($other -and (Contains $parent $other)) { break }
  $pane = $parent
  $node = $parent
}

function Count-Hub($root) {
  $hits = 0
  $stack = New-Object System.Collections.Generic.Stack[System.Windows.Automation.AutomationElement]
  $stack.Push($root)
  $n = 0
  while ($stack.Count -gt 0 -and $n -lt 4000) {
    $cur = $stack.Pop(); $n++
    try {
      if ($cur.Current.ControlType -ne $CT::Edit) {
        $nm = [string]$cur.Current.Name
        if ($nm -eq 'HUB') { $hits++ }
      }
    } catch {}
    try {
      $ch = $walker.GetFirstChild($cur)
      while ($ch) { $stack.Push($ch); $ch = $walker.GetNextSibling($ch) }
    } catch {}
  }
  return $hits
}

$before = Count-Hub $pane
$meta = @{
  direction = $Direction
  mode = $Mode
  window = $window.Current.Name
  process_id = $window.Current.ProcessId
  hwnd = $window.Current.NativeWindowHandle
  target_class = $target.Current.ClassName
  target_name = $target.Current.Name
  target_rid = (Rid $target)
  pane_rid = (Rid $pane)
  hub_before = $before
  terminal_edits_excluded = $term
  agent_count = $agent.Count
  gpt_count = $gpt.Count
}

if ($Mode -eq 'Verify') {
  $meta.status = 'VERIFY_ONLY'
  $meta.hub_now = $before
  Emit $meta
  exit 0
}

$vp = $null
try { $vp = $target.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern) } catch {}
if (-not $vp) { $meta.status = 'BLOCKED'; $meta.reason = 'NO_VALUE_PATTERN'; Emit $meta; exit 0 }
$draft = ''
try { $draft = [string]$vp.Current.Value } catch {}
if ($draft -and $draft.Trim().Length -gt 0) {
  $meta.status = 'BLOCKED'
  $meta.reason = 'DRAFT_PRESENT'
  $meta.draft_len = $draft.Length
  Emit $meta
  exit 0
}
try { $vp.SetValue('HUB') } catch {
  $meta.status = 'BLOCKED'; $meta.reason = 'SETVALUE_FAILED'; Emit $meta; exit 0
}
Start-Sleep -Milliseconds 200
$rb = ''
try { $rb = [string]$vp.Current.Value } catch {}
if ($rb.Trim() -ne 'HUB') {
  $meta.status = 'BLOCKED'; $meta.reason = 'VALUE_READBACK_NOT_HUB'; $meta.readback_len = $rb.Length; Emit $meta; exit 0
}

# Re-find a send button inside the pane. Do not invoke 开始语音 / 听写.
$buttons = $pane.FindAll($TS::Descendants, (New-Object System.Windows.Automation.PropertyCondition($AE::ControlTypeProperty, $CT::Button)))
$sendBtn = $null
foreach ($b in $buttons) {
  try {
    if ($b.Current.IsOffscreen) { continue }
    $bn = [string]$b.Current.Name
    if ($bn -match '^(发送|Send|Send message|发送消息)$') { $sendBtn = $b; break }
  } catch {}
}
$method = ''
if ($sendBtn) {
  $inv = $null
  try { $inv = $sendBtn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern) } catch {}
  if ($inv) { $inv.Invoke(); $method = 'INVOKE_SEND' }
}
if (-not $method) {
  try { $target.SetFocus() } catch {
    try { if ($vp.Current.Value -eq 'HUB') { $vp.SetValue('') } } catch {}
    $meta.status = 'BLOCKED'; $meta.reason = 'SETFOCUS_FAILED'; Emit $meta; exit 0
  }
  Start-Sleep -Milliseconds 180
  $focused = $null
  try { $focused = $AE::FocusedElement } catch {}
  $fid = $(if ($focused) { Rid $focused } else { '' })
  if ($fid -ne (Rid $target)) {
    try { if ($vp.Current.Value -eq 'HUB') { $vp.SetValue('') } } catch {}
    $meta.status = 'BLOCKED'
    $meta.reason = 'FOCUS_NOT_TARGET'
    $meta.focused_class = $(if ($focused) { $focused.Current.ClassName } else { '' })
    $meta.focused_rid = $fid
    Emit $meta
    exit 0
  }
  [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
  $method = 'FOCUS_ENTER_ONCE'
}
Start-Sleep -Milliseconds 1600
$afterDraft = ''
try { $afterDraft = [string]$vp.Current.Value } catch {}
$after = Count-Hub $pane
$meta.method = $method
$meta.hub_after = $after
$meta.composer_empty = [bool](-not $afterDraft -or $afterDraft.Trim().Length -eq 0)
$meta.draft_len_after = $(if ($afterDraft) { $afterDraft.Length } else { 0 })
if ($meta.composer_empty -and $after -gt $before) { $meta.status = 'DELIVERED_PANE_HUB' }
elseif (-not $meta.composer_empty) { $meta.status = 'NOT_SUBMITTED' }
else { $meta.status = 'DELIVERY_UNCERTAIN' }
Emit $meta
