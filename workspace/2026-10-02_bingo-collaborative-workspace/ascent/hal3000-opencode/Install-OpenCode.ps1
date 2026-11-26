<#
OpenCode for HAL3000, configured for the Ascent GX10. Offline, no administrator rights.
Installs into %LOCALAPPDATA%\OpenCode-Ascent, settings into %USERPROFILE%\.config\opencode,
work folder C:\OpenCode, and BCW code from Gitea into C:\OpenCode\bcw.
Re-running it is safe: it refreshes the program and settings and keeps the work folder and sessions.
#>
param(
  [string]$Ascent = '192.168.2.45',
  [string]$ModelUrl = '',          # default http://<Ascent>:8080/v1 (a test can point it elsewhere)
  [string]$GiteaUrl = '',          # default http://<Ascent>:3000
  [string]$WorkRoot = 'C:\OpenCode',
  [switch]$SkipGitea,
  [switch]$NoShortcut,             # tests: leave the desktop, the user PATH and environment alone
  [switch]$SkipDesktop             # tests: do not install the OpenCode Desktop app
)
$ErrorActionPreference = 'Stop'
if (-not $ModelUrl) { $ModelUrl = "http://${Ascent}:8080/v1" }
if (-not $GiteaUrl) { $GiteaUrl = "http://${Ascent}:3000" }
$src   = $PSScriptRoot
$root  = Join-Path $env:LOCALAPPDATA 'OpenCode-Ascent'
$cfg   = Join-Path $env:USERPROFILE '.config\opencode'
function Step($t) { Write-Host ''; Write-Host "== $t" -ForegroundColor Cyan }
$tar = Join-Path $env:SystemRoot 'System32\tar.exe'   # Windows' own tar (not Git's)
function J($p) { ($p -replace '\\','/') }

Step 'Checking the package'
foreach ($f in 'payload.zip','PortableGit.7z.exe','opencode-cache.zip','opencode-desktop-win-x64.exe','AGENTS.md','SHA256SUMS.txt') { if (!(Test-Path (Join-Path $src $f))) { throw "Missing $f beside this installer." } }
foreach ($line in Get-Content (Join-Path $src 'SHA256SUMS.txt')) {
  if (-not $line.Trim()) { continue }
  $h, $n = $line -split '\s+\*?', 2
  if ((Get-FileHash (Join-Path $src $n) -Algorithm SHA256).Hash.ToLower() -ne $h) { throw "$n is damaged (checksum mismatch)." }
}
Write-Host 'Package checksums OK.'

Step "Installing programs into $root"
if (Test-Path $root) { Remove-Item $root -Recurse -Force }
New-Item -ItemType Directory -Force $root | Out-Null
& $tar -xf (Join-Path $src 'payload.zip') -C $root
if ($LASTEXITCODE) { throw 'Unpacking payload.zip failed.' }
& (Join-Path $src 'PortableGit.7z.exe') -o"$root\git" -y | Out-Null
if (!(Test-Path "$root\git\bin\git.exe")) { throw 'Portable Git did not unpack.' }
# What OpenCode would otherwise download on first run: its plugin packages (settings folder) and the model catalogue.
$tmp = Join-Path $env:TEMP 'opencode-ascent-cache'
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
New-Item -ItemType Directory -Force $tmp | Out-Null
& $tar -xf (Join-Path $src 'opencode-cache.zip') -C $tmp
if ($LASTEXITCODE) { throw 'Unpacking opencode-cache.zip failed.' }
New-Item -ItemType Directory -Force $cfg, (Join-Path $env:USERPROFILE '.cache\opencode') | Out-Null
if (Test-Path "$cfg\node_modules") { Remove-Item "$cfg\node_modules" -Recurse -Force }
Copy-Item "$tmp\config\*" $cfg -Recurse -Force
Copy-Item "$tmp\cache\models.json" (Join-Path $env:USERPROFILE '.cache\opencode\models.json') -Force
Remove-Item $tmp -Recurse -Force
# comfy-cli (used by the ComfyUI MCP): no usage reporting, no first-run question.
cmd /c "`"$root\comfy-lib\comfy.cmd`" --skip-prompt tracking disable" *> $null
Write-Host 'OpenCode, Git, Node, Python, Playwright, and the Blender, FreeCAD and ComfyUI MCPs are in place.'

Step "Writing settings into $cfg"
New-Item -ItemType Directory -Force $cfg | Out-Null
if (Test-Path "$cfg\skills") { Remove-Item "$cfg\skills" -Recurse -Force }
Copy-Item "$root\skills" "$cfg\skills" -Recurse
Copy-Item (Join-Path $src 'AGENTS.md') "$cfg\AGENTS.md" -Force
$node = J "$root\node\node.exe"; $py = J "$root\python\python.exe"
$config = [ordered]@{
  '$schema' = 'https://opencode.ai/config.json'
  autoupdate = $false
  share = 'disabled'
  model = 'ascent/inkling-2-mini'
  small_model = 'ascent/inkling-2-mini'
  provider = @{ ascent = [ordered]@{
    npm = '@ai-sdk/openai-compatible'; name = 'Ascent GX10'
    options = @{ baseURL = $ModelUrl }
    models = [ordered]@{
      'inkling-2-mini' = @{ name = 'Inkling 2 Mini (default)'; limit = @{ context = 262144; output = 32768 }; attachment = $true; modalities = @{ input = @('text','image'); output = @('text') } }
      'flash-next'   = @{ name = 'Flash-Next (fallback; the Ascent swaps models)'; limit = @{ context = 131072; output = 32768 }; attachment = $true; modalities = @{ input = @('text','image'); output = @('text') } }
      'gpt-oss-120b' = @{ name = 'gpt-oss-120b'; limit = @{ context = 131072; output = 32768 } }
      'qwen3.8-27b'  = @{ name = 'Qwen3.8-27B'; limit = @{ context = 262144; output = 32768 }; attachment = $true; modalities = @{ input = @('text','image'); output = @('text') } }
    } } }
  mcp = [ordered]@{
    playwright = @{ type = 'local'; enabled = $true
      command = @($node, (J "$root\mcp\playwright\node_modules\@playwright\mcp\cli.js"), '--browser', 'chromium')
      environment = @{ PLAYWRIGHT_BROWSERS_PATH = (J "$root\ms-playwright") } }
    blender = @{ type = 'local'; enabled = $true
      command = @($py, '-c', 'from blender_mcp.server import main; main()')
      environment = @{ DISABLE_TELEMETRY = 'true'; BLENDER_MCP_DISABLE_TELEMETRY = 'true' } }
    comfy = @{ type = 'local'; enabled = $true
      command = @($py, '-c', "import sys; sys.path.insert(0, r'$(J "$root\comfy-lib")'); from comfy_mcp.server import main; main()")
      environment = @{ PYTHONPATH = (J "$root\comfy-lib"); COMFY_BIN = (J "$root\comfy-lib\comfy.cmd"); COMFYUI_URL = "http://${Ascent}:8188"; DO_NOT_TRACK = '1' } }
    freecad = @{ type = 'local'; enabled = $true
      command = @($py, '-c', "import sys; sys.path.insert(0, r'$(J "$root\freecad-lib")'); from freecad_mcp.server import main; main()",
        '--freecadcmd', (J (Join-Path $env:LOCALAPPDATA 'Programs\FreeCAD 1.1\bin\FreeCADCmd.exe')))
      environment = @{ PYTHONPATH = (J "$root\freecad-lib") } }
  }
  # ComfyUI MCP: generate and run workflows on the Ascent's ComfyUI. Tools that would install, update,
  # download or start a ComfyUI on HAL3000, or use paid cloud models, are switched off.
  tools = [ordered]@{
    'comfy_launch_comfyui' = $false; 'comfy_stop_comfyui' = $false; 'comfy_restart_comfyui' = $false; 'comfy_update_comfyui' = $false
    'comfy_switch_comfyui_version' = $false; 'comfy_install_node' = $false; 'comfy_download_model' = $false; 'comfy_download' = $false
    'comfy_auth_login' = $false; 'comfy_partner_generate' = $false; 'comfy_emit_partner_workflow' = $false
  }
  permission = [ordered]@{
    read = [ordered]@{ '*' = 'allow'; '*.env' = 'ask'; '*.env.*' = 'ask'; '*.env.example' = 'allow' }
    edit = [ordered]@{ '*' = 'ask'; '*Documents?BCW*' = 'deny'; '*\.git\*' = 'deny'; '*/.git/*' = 'deny' }
    bash = [ordered]@{
      '*' = 'ask'
      'git status*' = 'allow'; 'git log*' = 'allow'; 'git diff*' = 'allow'; 'git show*' = 'allow'; 'git branch' = 'allow'; 'git branch -a' = 'allow'; 'git fetch*' = 'allow'
      'ls*' = 'allow'; 'dir*' = 'allow'; 'cat *' = 'allow'; 'head *' = 'allow'; 'tail *' = 'allow'; 'grep *' = 'allow'; 'rg *' = 'allow'; 'wc *' = 'allow'; 'pwd' = 'allow'
      'docker ps*' = 'allow'; 'docker logs*' = 'allow'; 'docker inspect*' = 'allow'; 'docker compose ps*' = 'allow'; 'docker images*' = 'allow'; 'docker stats --no-stream*' = 'allow'
      'ipconfig*' = 'allow'; 'ping *' = 'allow'
      'rm -r*' = 'deny'; 'rm -fr*' = 'deny'; 'rm -rf*' = 'deny'; 'rmdir *' = 'deny'; 'rd /s*' = 'deny'; 'del /s*' = 'deny'; '*Remove-Item*-Recurse*' = 'deny'; 'format *' = 'deny'
      'docker rm*' = 'deny'; 'docker stop*' = 'deny'; 'docker kill*' = 'deny'; 'docker restart*' = 'deny'; 'docker volume*' = 'deny'; 'docker system*' = 'deny'
      'docker compose down*' = 'deny'; 'docker compose stop*' = 'deny'; 'docker compose rm*' = 'deny'; 'docker compose up*' = 'deny'
      'git push*--force*' = 'deny'; 'git push -f*' = 'deny'; 'git push*--delete*' = 'deny'; 'git reset --hard*' = 'deny'; 'git clean*' = 'deny'; 'git checkout -- *' = 'deny'
      'shutdown*' = 'deny'; '*Restart-Computer*' = 'deny'; '*Stop-Computer*' = 'deny'; '*Stop-Service*' = 'deny'; 'sc stop*' = 'deny'; 'sc delete*' = 'deny'; 'net user*' = 'deny'; 'reg delete*' = 'deny'; '*Set-ExecutionPolicy*' = 'deny'
    }
    external_directory = 'ask'
    webfetch = 'ask'
    websearch = 'deny'
    doom_loop = 'ask'
  }
}
[IO.File]::WriteAllText("$cfg\opencode.json", ($config | ConvertTo-Json -Depth 12), (New-Object Text.UTF8Encoding $false))

Step 'Creating the launcher'
New-Item -ItemType Directory -Force $WorkRoot | Out-Null
$launcher = @"
@echo off
rem OpenCode on the Ascent: offline switches, private Git and Node; starts in the work folder, or in the folder given.
set OPENCODE_DISABLE_MODELS_FETCH=1
set OPENCODE_DISABLE_AUTOUPDATE=1
set OPENCODE_DISABLE_LSP_DOWNLOAD=1
set OPENCODE_GIT_BASH_PATH=$root\git\bin\bash.exe
set DISABLE_TELEMETRY=true
set PATH=$root\opencode;$root\git\cmd;$root\git\bin;$root\node;%PATH%
if "%~1"=="" (cd /d "$WorkRoot") else (cd /d "%~1")
"$root\opencode\opencode.exe"
"@
Set-Content "$root\opencode-ascent.cmd" $launcher -Encoding ascii
if (-not $NoShortcut) {
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'OpenCode (Ascent).lnk'))
$lnk.TargetPath = "$root\opencode-ascent.cmd"; $lnk.WorkingDirectory = $WorkRoot; $lnk.IconLocation = "$root\opencode\opencode.exe,0"; $lnk.Save()
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($userPath -notlike "*$root*") { [Environment]::SetEnvironmentVariable('Path', ($userPath.TrimEnd(';') + ";$root"), 'User') }
Write-Host "Desktop shortcut 'OpenCode (Ascent)' created; 'opencode-ascent' works in new terminals (add a folder to start there)."
# The Desktop app starts from the Start menu, not the launcher, so it reads the same offline switches from the user environment.
foreach ($kv in @{ OPENCODE_DISABLE_MODELS_FETCH = '1'; OPENCODE_DISABLE_AUTOUPDATE = '1'; OPENCODE_DISABLE_LSP_DOWNLOAD = '1'; OPENCODE_GIT_BASH_PATH = "$root\git\bin\bash.exe"; DISABLE_TELEMETRY = 'true' }.GetEnumerator()) {
  [Environment]::SetEnvironmentVariable($kv.Key, $kv.Value, 'User')
}
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
foreach ($d in "$root\git\cmd", "$root
ode") { if ($userPath -notlike "*$d*") { $userPath = $userPath.TrimEnd(';') + ";$d" } }
[Environment]::SetEnvironmentVariable('Path', $userPath, 'User')
}

if (-not $SkipDesktop) {
  Step 'Installing the OpenCode Desktop app (for this Windows user)'
  $setup = Start-Process (Join-Path $src 'opencode-desktop-win-x64.exe') -ArgumentList '/S', '/currentuser' -Wait -PassThru
  $app = Join-Path $env:LOCALAPPDATA 'Programs\@opencode-aidesktop\OpenCode.exe'
  if ($setup.ExitCode -or !(Test-Path $app)) { throw "The OpenCode Desktop setup did not finish (exit code $($setup.ExitCode))." }
  Write-Host "OpenCode Desktop $((Get-Item $app).VersionInfo.ProductVersion) installed. Start it from the Start menu or the 'OpenCode' desktop icon."
  Write-Host 'It uses the same model, skills, MCP servers and safety rules as the terminal version.'
}

$git = "$root\git\cmd\git.exe"
if (-not $SkipGitea) {
  Step 'Connecting to Gitea on the Ascent (BCW code)'
  try {
    Write-Host "Fetching OpenCode's Gitea token from the Ascent: enter the Ascent (bmt01) SSH password when asked."
    $token = ((& "$root\git\usr\bin\ssh.exe" -o StrictHostKeyChecking=accept-new "bmt01@$Ascent" 'cat ~/opencode-gitea-token.txt') | Out-String).Trim()
    if ($token.Length -lt 20) { throw 'no token came back' }
    $u = [uri]$GiteaUrl
    "protocol=$($u.Scheme)`nhost=$($u.Authority)`nusername=opencode`npassword=$token`n" | & $git -c credential.helper=manager credential approve
    $token = $null
    & $git config --global "credential.$GiteaUrl.helper" manager
    & $git config --global "credential.$GiteaUrl.username" opencode
    $repo = Join-Path $WorkRoot 'bcw'
    if (!(Test-Path "$repo\.git")) { & $git clone -b release/0.17 "$GiteaUrl/bmt01/bcw.git" $repo; if ($LASTEXITCODE) { throw 'clone failed' } }
    else { & $git -C $repo fetch origin }
    & $git -C $repo config user.name 'OpenCode on HAL3000'
    & $git -C $repo config user.email 'opencode@hal3000.local'
    Write-Host "BCW code is in $repo (branch release/0.17). OpenCode commits and pushes there; the USB export brings it home."
  } catch {
    Write-Host "Gitea step skipped: $($_.Exception.Message). Everything else is installed; re-run INSTALL-OPENCODE.bat when the Ascent is reachable." -ForegroundColor Yellow
  }
}

Step 'Testing the Ascent model server'
try {
  $r = Invoke-RestMethod "$ModelUrl/models" -TimeoutSec 15
  Write-Host ('Ascent answers; models: ' + (($r.data | ForEach-Object id) -join ', '))
  $env:OPENCODE_DISABLE_MODELS_FETCH = '1'; $env:OPENCODE_DISABLE_AUTOUPDATE = '1'; $env:OPENCODE_DISABLE_LSP_DOWNLOAD = '1'
  $env:OPENCODE_GIT_BASH_PATH = "$root\git\bin\bash.exe"; $env:DISABLE_TELEMETRY = 'true'
  Push-Location $WorkRoot
  $ErrorActionPreference = 'Continue'   # OpenCode writes progress to stderr; that is not a failure
  $reply = & "$root\opencode\opencode.exe" run 'Reply with exactly: OPENCODE READY' 2>&1 | Out-String
  $ErrorActionPreference = 'Stop'
  Pop-Location
  if ($reply -match 'OPENCODE READY') { Write-Host 'OpenCode answered through Inkling: READY' -ForegroundColor Green }
  else { Write-Host "OpenCode ran but the reply was unexpected:`n$reply" -ForegroundColor Yellow }
} catch { Write-Host "The Ascent did not answer at $ModelUrl ($($_.Exception.Message)). OpenCode is installed; it works once the Ascent is on the network." -ForegroundColor Yellow }

Write-Host ''
Write-Host 'Done. Open "OpenCode (Ascent)" on the desktop. README.txt on the USB has the safety rules and Blender steps.' -ForegroundColor Green
