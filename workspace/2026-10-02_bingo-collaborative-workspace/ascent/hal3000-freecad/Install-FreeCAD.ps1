<#
FreeCAD 1.1.4 for HAL3000 with the FreeCAD MCP add-on (neka-nat freecad-mcp 0.1.32). Offline, no administrator rights.
FreeCAD goes to %LOCALAPPDATA%\Programs\FreeCAD 1.1 (this Windows user only); the add-on to FreeCAD's user Mod folder,
with its server starting automatically when FreeCAD opens (port 9875, this PC only).
OpenCode's FreeCAD MCP (OpenCode-HAL3000 package) talks to it. Re-running is safe.
#>
param([string]$InstallDir = (Join-Path $env:LOCALAPPDATA 'Programs\FreeCAD 1.1'))
$ErrorActionPreference = 'Stop'
$src = $PSScriptRoot
$setup = 'FreeCAD_1.1.4-Windows-x86_64-py311-installer.exe'
$tar = Join-Path $env:SystemRoot 'System32\tar.exe'
function Step($t) { Write-Host ''; Write-Host "== $t" -ForegroundColor Cyan }

Step 'Checking the package'
foreach ($line in Get-Content (Join-Path $src 'SHA256SUMS.txt')) {
  if (-not $line.Trim()) { continue }
  $h, $n = $line -split '\s+\*?', 2
  $f = Join-Path $src $n
  if (!(Test-Path $f)) { throw "Missing $n beside this installer." }
  if ((Get-FileHash $f -Algorithm SHA256).Hash.ToLower() -ne $h) { throw "$n is damaged (checksum mismatch)." }
}
Write-Host 'Package checksums OK (FreeCAD matches the official FreeCAD release checksum).'

if (Get-Process FreeCAD, FreeCADCmd -ErrorAction SilentlyContinue) { throw 'FreeCAD is open. Save your work, close FreeCAD, then run this again.' }
# FreeCAD's own setup refuses to install the same version twice, so a re-run keeps the installed 1.1.4 and refreshes the add-on.
$existing = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\FreeCAD114' -ErrorAction SilentlyContinue
$existingDir = if ($existing.UninstallString) { Split-Path ($existing.UninstallString.Trim('"')) } else { $null }
if ($existingDir -and (Test-Path (Join-Path $existingDir 'bin\FreeCAD.exe'))) {
  $InstallDir = $existingDir
  Step "FreeCAD 1.1.4 is already installed in $InstallDir (keeping it)"
} else {
  Step "Installing FreeCAD 1.1.4 into $InstallDir"
  $p = Start-Process (Join-Path $src $setup) -ArgumentList '/S', '/CurrentUser', "/D=$InstallDir" -Wait -PassThru
  if ($p.ExitCode -or !(Test-Path (Join-Path $InstallDir 'bin\FreeCAD.exe'))) { throw "The FreeCAD setup did not finish (exit code $($p.ExitCode))." }
  Write-Host 'FreeCAD installed for this Windows user (Start menu: FreeCAD 1.1).'
}
$exe = Join-Path $InstallDir 'bin\FreeCAD.exe'; $cmd = Join-Path $InstallDir 'bin\FreeCADCmd.exe'

Step 'Installing the FreeCAD MCP add-on'
$out = & $cmd -c "import FreeCAD; print('USERDIR=' + FreeCAD.getUserAppDataDir())" 2>&1 | Out-String
$userDir = ($out -split "`r?`n" | Where-Object { $_ -like 'USERDIR=*' } | Select-Object -First 1) -replace '^USERDIR=', ''
if (-not $userDir) { throw "FreeCAD did not report its user folder:`n$out" }
$mod = Join-Path $userDir 'Mod'
New-Item -ItemType Directory -Force $mod | Out-Null
$addon = Join-Path $mod 'FreeCADMCP'
if (Test-Path $addon) { Move-Item $addon (Join-Path $mod ('FreeCADMCP.bak-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))) }
& $tar -xf (Join-Path $src 'FreeCADMCP-0.1.32.zip') -C $mod
if ($LASTEXITCODE -or !(Test-Path (Join-Path $addon 'InitGui.py'))) { throw 'Unpacking the add-on failed.' }
# Start the add-on's server with FreeCAD; this PC only, as the add-on's own defaults.
$settingsFile = Join-Path $userDir 'freecad_mcp_settings.json'
$settings = [ordered]@{ remote_enabled = $false; allowed_ips = '127.0.0.1'; auto_start_rpc = $true; auth_token = '' }
[IO.File]::WriteAllText($settingsFile, ($settings | ConvertTo-Json), (New-Object Text.UTF8Encoding $false))
Write-Host "Add-on in $addon; its server starts with FreeCAD (127.0.0.1:9875)."

Step 'Checking the add-on server starts with FreeCAD'
$fc = Start-Process $exe -PassThru -WindowStyle Minimized
$ok = $false
for ($i = 0; $i -lt 120 -and -not $ok; $i++) {
  Start-Sleep 1
  try {
    $body = '<?xml version="1.0"?><methodCall><methodName>ping</methodName><params/></methodCall>'
    $r = Invoke-WebRequest 'http://127.0.0.1:9875/RPC2' -Method Post -Body $body -ContentType 'text/xml' -UseBasicParsing -TimeoutSec 3
    $ok = $r.Content -match '<boolean>1</boolean>'
  } catch { }
}
Stop-Process -Id $fc.Id -Force -ErrorAction SilentlyContinue
if ($ok) { Write-Host 'FreeCAD started its MCP server on port 9875: OpenCode can drive FreeCAD.' -ForegroundColor Green }
else { Write-Host 'FreeCAD is installed, but its MCP server did not answer within 2 minutes. Open FreeCAD, choose the MCP Addon workbench and press Start RPC Server; see README.txt.' -ForegroundColor Yellow }

Write-Host ''
Write-Host 'Done. Open FreeCAD (it starts the MCP server itself), then ask OpenCode, for example: "In FreeCAD, make a 100 x 50 x 10 mm plate with four 8 mm holes."' -ForegroundColor Green
