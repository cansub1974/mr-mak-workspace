<#
Ascent status: checks every Ascent service BCW uses and says in plain words what is up or down.
  -Tunnel   at home, through the SSH tunnel (ports 18080, 18081, 18793, 18188 on this PC; Gitea is not tunnelled)
#>
param([string]$Ascent = '192.168.2.45', [switch]$Tunnel)
$ErrorActionPreference = 'Continue'
$h = if ($Tunnel) { '127.0.0.1' } else { $Ascent }
$p = if ($Tunnel) { @{ chat = 18080; search = 18081; docling = 18793; images = 18188; gitea = $null; ssh = $null } }
     else         { @{ chat = 8080;  search = 8081;  docling = 8793;  images = 8188;  gitea = 3000;  ssh = 22 } }
$bad = 0
function Get-Url($url) {
  try { $r = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 8; return @{ code = [int]$r.StatusCode; body = $r.Content } }
  catch { if ($_.Exception.Response) { return @{ code = [int]$_.Exception.Response.StatusCode; body = '' } } return $null }
}
function Show($ok, $name, $text) {
  if ($ok) { Write-Host ('  OK    ' + $name.PadRight(30) + $text) -ForegroundColor Green }
  else { Write-Host ('  DOWN  ' + $name.PadRight(30) + $text) -ForegroundColor Red; $script:bad++ }
}
Write-Host ''
Write-Host "Ascent status ($h)  $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor Cyan
$ping = Test-Connection $h -Count 1 -Quiet -ErrorAction SilentlyContinue
if (-not $Tunnel) { Show $ping 'Ascent on the network' $(if ($ping) { 'answers' } else { 'no answer: check its power and network cable' }) }

$r = Get-Url "http://${h}:$($p.chat)/models"
if ($r -and $r.code -eq 200) {
  $m = ($r.body | ConvertFrom-Json).data
  $loaded = ($m | Where-Object { $_.status.value -eq 'loaded' } | ForEach-Object id) -join ', '
  Show $true 'Chat (Assistant, OpenCode)' $(if ($loaded) { "model loaded: $loaded" } else { 'running; no model loaded yet (the first question loads it, about a minute)' })
} else { Show $false 'Chat (Assistant, OpenCode)' 'not answering on port 8080: Assistant, Codex and OpenCode will fail' }

$r = Get-Url "http://${h}:$($p.search)/models"
Show ($r -and $r.code -eq 200) 'Library search models' $(if ($r -and $r.code -eq 200) { 'running' } else { 'not answering on 8081: Library search falls back to words only' })
$r = Get-Url "http://${h}:$($p.docling)/"
Show ($null -ne $r) 'Docling (reads documents)' $(if ($r) { 'running' } else { 'not answering on 8793: new and scanned documents wait to be read' })
$r = Get-Url "http://${h}:$($p.images)/system_stats"
Show ($r -and $r.code -eq 200) 'ComfyUI (images)' $(if ($r -and $r.code -eq 200) { 'running' } else { 'not answering on 8188: image jobs stay queued' })
if ($p.gitea) {
  $r = Get-Url "http://${h}:$($p.gitea)/api/healthz"
  Show ($r -and $r.code -eq 200) 'Gitea (BCW code)' $(if ($r -and $r.code -eq 200) { 'running' } else { 'not answering on 3000: OpenCode cannot pull or push code' })
  $ssh = Test-NetConnection $h -Port 22 -InformationLevel Quiet -WarningAction SilentlyContinue
  Show $ssh 'SSH (management)' $(if ($ssh) { 'open' } else { 'closed: cannot log in to manage the Ascent' })
}

# BCW on this PC, if installed
$cfgFile = Join-Path $env:USERPROFILE 'Documents\BCW\data\config.json'
if (Test-Path $cfgFile) {
  $cfg = Get-Content $cfgFile -Raw | ConvertFrom-Json
  $r = Get-Url ($cfg.bridge_url + '/api/health')
  Show ($r -and $r.code -eq 200) 'BCW on this PC' $(if ($r -and $r.code -eq 200) { (($r.body | ConvertFrom-Json).version) + ' running' } else { 'not running: start it from its usual launcher' })
}
Write-Host ''
if ($bad -eq 0) { Write-Host 'Everything is answering.' -ForegroundColor Green }
else {
  if ($ping -and $bad -ge 4) { Write-Host "$bad problem(s). The Ascent answers but its services do not reach this PC: check this PC's own address starts with 192.168.2 (ipconfig); the Ascent only lets that network in." -ForegroundColor Yellow }
  elseif (-not $ping -and -not $Tunnel) { Write-Host "$bad problem(s). The Ascent does not answer at all: check it is on and its network cable is plugged in." -ForegroundColor Yellow }
  else { Write-Host "$bad problem(s)." -ForegroundColor Yellow }
  Write-Host "To restart one service: ssh bmt01@$Ascent, then sudo systemctl restart llama-chat (or llama-retrieval, comfyui); Docling: sudo docker restart docling." -ForegroundColor Yellow
}
