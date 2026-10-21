# Readonly UIA probe for Cursor + ChatGPT (接管迁移核验)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::RootElement
$winCond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
  [System.Windows.Automation.ControlType]::Window
)
$wins = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $winCond)

$hits = @()
foreach ($w in $wins) {
  $name = $w.Current.Name
  if (-not $name) { continue }
  if ($name -notmatch 'Cursor|ChatGPT|chatgpt|接管') { continue }

  $editCond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
    [System.Windows.Automation.ControlType]::Edit
  )
  $docCond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
    [System.Windows.Automation.ControlType]::Document
  )
  $edits = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, $editCond)
  $docs = $w.FindAll([System.Windows.Automation.TreeScope]::Descendants, $docCond)

  $editNames = New-Object System.Collections.Generic.List[string]
  $i = 0
  foreach ($e in $edits) {
    if ($i -ge 15) { break }
    $n = $e.Current.Name
    if ($n) {
      if ($n.Length -gt 100) { $n = $n.Substring(0, 100) }
      $editNames.Add($n) | Out-Null
      $i++
    }
  }
  $docNames = New-Object System.Collections.Generic.List[string]
  $j = 0
  foreach ($d in $docs) {
    if ($j -ge 10) { break }
    $n = $d.Current.Name
    if ($n) {
      if ($n.Length -gt 100) { $n = $n.Substring(0, 100) }
      $docNames.Add($n) | Out-Null
      $j++
    }
  }

  $hits += [pscustomobject]@{
    name = $name
    class = $w.Current.ClassName
    edits = $edits.Count
    docs = $docs.Count
    edit_names = (($editNames | Select-Object -First 15) -join ' || ')
    doc_names = (($docNames | Select-Object -First 10) -join ' || ')
    looks_cursor = [bool]($name -match 'Cursor')
    looks_gpt = [bool]($name -match 'ChatGPT|chatgpt|接管')
  }
}

@{
  at = (Get-Date).ToString('o')
  window_hits = $hits
  cursor_found = [bool]($hits | Where-Object { $_.looks_cursor })
  gpt_found = [bool]($hits | Where-Object { $_.looks_gpt })
} | ConvertTo-Json -Depth 6
