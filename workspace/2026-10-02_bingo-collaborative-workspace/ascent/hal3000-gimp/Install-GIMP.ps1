<#
GIMP 3.2.8 for HAL3000, offline, for this Windows user only (no administrator rights).
The installer is the official one from gimp.org (SHA-256 checked, signed by the GIMP Windows packager).
#>
$ErrorActionPreference = 'Stop'
$src = $PSScriptRoot; $exe = Join-Path $src 'gimp-3.2.8-setup.exe'
try {
  foreach ($line in Get-Content (Join-Path $src 'SHA256SUMS.txt')) {
    if (-not $line.Trim()) { continue }
    $h, $n = $line -split '\s+\*?', 2
    if ((Get-FileHash (Join-Path $src $n) -Algorithm SHA256).Hash.ToLower() -ne $h) { throw "$n is damaged (checksum mismatch)." }
  }
  $sig = Get-AuthenticodeSignature $exe
  if ($sig.Status -ne 'Valid') { throw "The GIMP installer's signature is not valid ($($sig.Status))." }
  Write-Host 'Installer checked (checksum and signature). Installing GIMP 3.2.8 for this user; this takes a few minutes...'
  $log = Join-Path $env:TEMP 'gimp-install.log'
  $p = Start-Process $exe -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CURRENTUSER',"/LOG=`"$log`"" -Wait -PassThru
  if ($p.ExitCode -ne 0) { throw "The GIMP installer stopped with code $($p.ExitCode). Its log: $log" }
  $gimp = Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Programs'), $env:ProgramFiles -Filter 'gimp-3*.exe' -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^gimp-3(\.\d+)?\.exe$' } | Select-Object -First 1
  if (-not $gimp) { throw "GIMP did not appear after installing. Its log: $log" }
  Write-Host "GIMP installed: $($gimp.FullName)" -ForegroundColor Green
  Write-Host 'Open it from the Start menu (GIMP 3.2.8). It needs no internet.'
  exit 0
} catch {
  Write-Host ('Stopped: ' + $_.Exception.Message) -ForegroundColor Red
  exit 1
}
