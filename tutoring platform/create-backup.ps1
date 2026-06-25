param(
  [string]$ProjectPath = "outputs\tutoring-platform",
  [string]$Label = "",
  [int]$KeepCount = 3
)

$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent $PSScriptRoot
$outputsRoot = Split-Path -Parent $workspaceRoot
$sourcePath = Join-Path $outputsRoot (Split-Path $ProjectPath -Leaf)

if (-not (Test-Path -LiteralPath $sourcePath)) {
  throw "Project path not found: $sourcePath"
}

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$safeLabel = ($Label -replace '[^a-zA-Z0-9_-]', '-').Trim('-')
$backupName = if ([string]::IsNullOrWhiteSpace($safeLabel)) {
  "{0}-backup-{1}" -f (Split-Path $sourcePath -Leaf), $timestamp
} else {
  "{0}-backup-{1}-{2}" -f (Split-Path $sourcePath -Leaf), $timestamp, $safeLabel
}

$destinationPath = Join-Path $outputsRoot $backupName

Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Recurse

$backupPrefix = "{0}-backup" -f (Split-Path $sourcePath -Leaf)
$oldBackups = Get-ChildItem -LiteralPath $outputsRoot -Directory |
  Where-Object { $_.Name -like "$backupPrefix*" } |
  Sort-Object LastWriteTime -Descending

if ($KeepCount -gt 0 -and $oldBackups.Count -gt $KeepCount) {
  $oldBackups | Select-Object -Skip $KeepCount | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Recurse -Force
  }
}

Write-Output $destinationPath
