<#
Blender 5.2.4 LTS for HAL3000 with the "MCP for Blender" add-on enabled. Offline, no administrator rights.
Blender goes to %LOCALAPPDATA%\Programs\Blender\5.2.4; the add-on to Blender's user add-ons (as blender_mcp),
enabled, with its server starting automatically when Blender opens (port 9876, this PC only).
OpenCode's Blender MCP (OpenCode-HAL3000 package) talks to it. Re-running is safe.
#>
param([switch]$NoShortcut)   # tests: leave the desktop and file associations alone
$ErrorActionPreference = 'Stop'
$src = $PSScriptRoot
$ver = '5.2.4'
$dest = Join-Path $env:LOCALAPPDATA "Programs\Blender\$ver"
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
Write-Host 'Package checksums OK (Blender matches the official blender.org checksum).'

Step "Installing Blender $ver into $dest"
if (Get-Process blender -ErrorAction SilentlyContinue) { throw 'Blender is open. Save your work, close Blender, then run this again.' }
if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
$tmp = Join-Path $env:TEMP 'blender-install'
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
New-Item -ItemType Directory -Force $tmp | Out-Null
& $tar -xf (Join-Path $src "blender-$ver-windows-x64.zip") -C $tmp
if ($LASTEXITCODE) { throw 'Unpacking Blender failed.' }
New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
Move-Item (Join-Path $tmp "blender-$ver-windows-x64") $dest
Remove-Item $tmp -Recurse -Force
$exe = Join-Path $dest 'blender.exe'
Write-Host ((& $exe --version 2>$null | Select-Object -First 1))

Step 'Installing and enabling the MCP for Blender add-on'
$py = @'
import bpy, addon_utils, os, shutil, sys, time
src = sys.argv[sys.argv.index("--") + 1]
d = bpy.utils.user_resource("SCRIPTS", path="addons", create=True)
dst = os.path.join(d, "blender_mcp.py")
if os.path.exists(dst):
    shutil.copy2(dst, dst + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
shutil.copy2(src, dst)
bpy.utils.refresh_script_paths()   # the add-ons folder may be new this run
if d not in sys.path:
    sys.path.append(d)
addon_utils.modules_refresh()
mod = addon_utils.enable("blender_mcp", default_set=True, persistent=True)
bpy.ops.wm.save_userpref()
print("ADDON_ENABLED" if mod else "ADDON_FAILED", dst)
'@
$pyFile = Join-Path $env:TEMP 'enable-blender-mcp.py'
Set-Content $pyFile $py -Encoding ascii
$out = & $exe -b --python $pyFile -- (Join-Path $src 'blender_mcp.py') 2>&1 | Out-String
Remove-Item $pyFile
if ($out -notmatch 'ADDON_ENABLED') { throw "The add-on could not be enabled:`n$out" }
Write-Host ($out -split "`n" | Where-Object { $_ -match 'ADDON_ENABLED' })

if (-not $NoShortcut) {
  Step 'Shortcut and .blend files'
  $ws = New-Object -ComObject WScript.Shell
  $lnk = $ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) "Blender $ver.lnk"))
  $lnk.TargetPath = Join-Path $dest 'blender-launcher.exe'; $lnk.WorkingDirectory = $dest; $lnk.Save()
  & $exe -r 2>$null | Out-Null   # open .blend files with this Blender (this Windows user only)
  Write-Host "Desktop shortcut 'Blender $ver' created; .blend files open with it."
}

Step 'Checking the add-on server starts with Blender'
$p = Start-Process (Join-Path $dest 'blender.exe') -PassThru -WindowStyle Minimized
$ok = $false
for ($i = 0; $i -lt 90 -and -not $ok; $i++) {
  Start-Sleep 1
  try { $c = New-Object Net.Sockets.TcpClient; $c.Connect('127.0.0.1', 9876); $ok = $c.Connected; $c.Close() } catch { }
}
Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
if ($ok) { Write-Host 'Blender started its MCP server on port 9876: OpenCode can drive Blender.' -ForegroundColor Green }
else { Write-Host 'Blender opened but its MCP server did not answer within 90 seconds. Open Blender, press N, open the MCP for Blender tab and click Connect.' -ForegroundColor Yellow }

Write-Host ''
Write-Host 'Done. Open Blender, then OpenCode (Ascent), and ask OpenCode to describe the Blender scene.' -ForegroundColor Green
