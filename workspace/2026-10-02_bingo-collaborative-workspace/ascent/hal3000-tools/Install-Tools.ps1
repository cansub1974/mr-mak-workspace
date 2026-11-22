<#
Tools for HAL3000, offline, for this Windows user (no administrator rights). Each tool installs on its own;
one failure does not stop the others. Re-running is safe.
  Ascent status check, VS Code + Python extensions, GIMP offline help, KeePassXC, 7-Zip, Notepad++, draw.io
Optional: -Only vscode,keepass,... to install a subset (names: status, vscode, gimphelp, keepass, 7zip, notepadpp, drawio)
#>
param([string[]]$Only)
$ErrorActionPreference = 'Stop'
if ($Only) { $Only = @($Only -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
$src = $PSScriptRoot
$prog = Join-Path $env:LOCALAPPDATA 'Programs'
$tar = Join-Path $env:SystemRoot 'System32\tar.exe'
$startMenu = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
$desktop = [Environment]::GetFolderPath('Desktop')
$results = [ordered]@{}
function Want($n) { -not $Only -or $Only -contains $n }
function Shortcut($folder, $name, $target, $arguments = '') {
  $ws = New-Object -ComObject WScript.Shell; $l = $ws.CreateShortcut((Join-Path $folder "$name.lnk"))
  $l.TargetPath = $target; $l.Arguments = $arguments; $l.WorkingDirectory = Split-Path $target; $l.Save()
}
function Step($n, $title, [scriptblock]$do) {
  if (-not (Want $n)) { return }
  Write-Host ''; Write-Host "== $title" -ForegroundColor Cyan
  try { $msg = & $do; $results[$title] = 'OK  ' + $msg; Write-Host $msg -ForegroundColor Green }
  catch { $results[$title] = 'FAILED  ' + $_.Exception.Message; Write-Host ('Failed: ' + $_.Exception.Message) -ForegroundColor Red }
}
function Run($exe, [string[]]$a) { $p = Start-Process $exe -ArgumentList $a -Wait -PassThru; if ($p.ExitCode) { throw "$(Split-Path $exe -Leaf) stopped with code $($p.ExitCode)" } }
function Unzip($zip, $dest) { if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }; New-Item -ItemType Directory -Force $dest | Out-Null; & $tar -xf $zip -C $dest; if ($LASTEXITCODE) { throw "could not unpack $(Split-Path $zip -Leaf)" } }

Write-Host 'Checking the package...'
foreach ($line in Get-Content (Join-Path $src 'SHA256SUMS.txt')) {
  if (-not $line.Trim()) { continue }
  $h, $n = $line -split '\s+\*?', 2
  if ((Get-FileHash (Join-Path $src $n) -Algorithm SHA256).Hash.ToLower() -ne $h) { throw "$n is damaged (checksum mismatch). Copy Tools-HAL3000 again." }
}
Write-Host 'All files match their checksums (each also matches its maker''s published checksum).'

Step 'status' 'Ascent status check' {
  $d = Join-Path $prog 'Ascent-Status'; New-Item -ItemType Directory -Force $d | Out-Null
  Copy-Item (Join-Path $src 'Ascent-Status.ps1') $d -Force
  Set-Content (Join-Path $d 'Ascent-Status.cmd') "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"%~dp0Ascent-Status.ps1`" %*`r`necho.`r`npause" -Encoding ascii
  Shortcut $desktop 'Ascent status' (Join-Path $d 'Ascent-Status.cmd')
  'desktop shortcut "Ascent status"'
}
Step 'vscode' 'VS Code 1.147 + Python extensions' {
  Run (Join-Path $src 'VSCodeUserSetup-x64-1.147.0.exe') @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/MERGETASKS=!runcode,addcontextmenufiles,addcontextmenufolders,addtopath')
  $code = Join-Path $prog 'Microsoft VS Code\bin\code.cmd'
  if (!(Test-Path $code)) { throw 'VS Code did not appear in ' + (Split-Path (Split-Path $code)) }
  $settings = Join-Path $env:APPDATA 'Code\User\settings.json'
  if (!(Test-Path $settings)) {
    New-Item -ItemType Directory -Force (Split-Path $settings) | Out-Null
    Set-Content $settings '{ "update.mode": "none", "telemetry.telemetryLevel": "off", "extensions.autoUpdate": false, "extensions.autoCheckUpdates": false, "workbench.enableExperiments": false }' -Encoding utf8
  }
  foreach ($v in 'ms-python.vscode-python-envs-1.44.0.vsix', 'ms-python.debugpy-2026.6.0.vsix', 'ms-python.vscode-pylance-2026.4.1.vsix', 'ms-python.python-2026.10.0.vsix') {
    & $code --install-extension (Join-Path $src $v) --force 2>&1 | Out-Null
  }
  $have = & $code --list-extensions 2>$null
  $missing = 'ms-python.python', 'ms-python.vscode-pylance', 'ms-python.debugpy', 'ms-python.vscode-python-envs' | Where-Object { $have -notcontains $_ }
  if ($missing) { throw 'extensions not installed: ' + ($missing -join ', ') }
  'installed with the Python extensions; updates and telemetry off'
}
Step 'gimphelp' 'GIMP offline help (English)' {
  $gimp = Get-ChildItem $prog, $env:ProgramFiles -Filter 'gimp-3*.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $gimp) { throw 'GIMP is not installed yet: run GIMP-HAL3000\INSTALL-GIMP.bat first, then this again' }
  Run (Join-Path $src 'gimp-help-3.2.0-en-setup.exe') @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CURRENTUSER')
  'installed; GIMP''s Help menu now works offline'
}
Step 'keepass' 'KeePassXC 2.8.0' {
  $d = Join-Path $prog 'KeePassXC'; Unzip (Join-Path $src 'KeePassXC-2.8.0-x64.zip') $d
  $exe = Get-ChildItem $d -Filter KeePassXC.exe -Recurse | Select-Object -First 1
  Shortcut $startMenu 'KeePassXC' $exe.FullName
  'Start menu shortcut "KeePassXC"; keep the database file on HAL3000 and a copy on the USB'
}
Step '7zip' '7-Zip 26.06' {
  $d = Join-Path $prog '7-Zip'; Unzip (Join-Path $src '7z2606-x64.exe') $d
  Shortcut $startMenu '7-Zip File Manager' (Join-Path $d '7zFM.exe')
  'Start menu shortcut "7-Zip File Manager" (no Explorer right-click menu without administrator rights)'
}
Step 'notepadpp' 'Notepad++ 8.9.9.1' {
  $d = Join-Path $prog 'Notepad++'; Unzip (Join-Path $src 'npp.8.9.9.1.portable.x64.zip') $d
  Shortcut $startMenu 'Notepad++' (Join-Path $d 'notepad++.exe')
  'Start menu shortcut "Notepad++"'
}
Step 'drawio' 'draw.io 32.7.4' {
  Run (Join-Path $src 'draw.io-32.7.4-windows-installer.exe') @('/S', '/currentuser')
  $exe = Get-ChildItem $prog -Filter 'draw.io.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $exe) { throw 'draw.io did not appear in ' + $prog }
  'installed for this user (works offline; ignore any update notice)'
}

Write-Host ''; Write-Host 'Summary' -ForegroundColor Cyan
$results.GetEnumerator() | ForEach-Object { Write-Host ('  ' + $_.Key.PadRight(36) + $_.Value) }
if ($results.Values -match '^FAILED') { exit 1 }
