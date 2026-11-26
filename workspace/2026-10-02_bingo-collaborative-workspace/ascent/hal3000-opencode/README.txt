OPENCODE FOR HAL3000 (ASCENT GX10, OFFLINE)
Prepared 22 November 2026, Desktop app and ComfyUI added 27 November 2026. OpenCode 1.19.6.

WHAT IT INSTALLS (no administrator rights, no internet)
- The OpenCode Desktop app (the full windowed app, "OpenCode" in the Start menu and on the desktop) and the terminal version
  ("OpenCode (Ascent)"). Both use the same model, skills, MCP servers, safety rules and sessions.
- OpenCode, using Inkling 2 Mini on the Ascent (http://192.168.2.45:8080/v1). Flash-Next, Qwen3.8-27B and gpt-oss-120b can be picked
  with /models as fallbacks; picking one makes the Ascent swap models (a minute or two) for BCW too, so switch back afterwards.
- MCP servers: Playwright (drives a browser, e.g. to check BCW pages), Blender and FreeCAD (each works once that program is
  installed and open, see below)
  and ComfyUI (makes images and runs workflows on the Ascent's ComfyUI at :8188; installing nodes, downloading models,
  updating or starting a ComfyUI, and paid cloud models are switched off).
- 76 skills: the Matt Pocock set, Superpowers, skill-creator, frontend-design, bcw-plow, and the 3D/Blender skills.
- Private Git, Node and Python, so nothing else on HAL3000 is changed.
- BCW code from Gitea on the Ascent into C:\OpenCode\bcw (Gitea account "opencode", write access to bcw only).
Programs: %LOCALAPPDATA%\OpenCode-Ascent    Settings: %USERPROFILE%\.config\opencode    Work folder: C:\OpenCode

BEFORE YOU START
- The Ascent is on the work network and answers at http://192.168.2.45:8080/v1/models (see BCW-V0.17-WORK-UPGRADE.txt).
- Sign in to HAL3000 as the Windows user who will use OpenCode (not an administrator account).

INSTALL
1. Run OpenCode-HAL3000\INSTALL-OPENCODE.bat (double-click). It checks the package, then installs.
2. When asked, type the Ascent's bmt01 SSH password. The installer fetches OpenCode's Gitea sign-in from the Ascent (you never see or type it) and downloads the BCW code.
   On the very first connection it trusts the Ascent's SSH key automatically.
3. The last step asks Inkling for a test reply. "OpenCode answered through Inkling: READY" means everything works.
4. Open "OpenCode" (the Desktop app) from the Start menu or the desktop, choose Open project and pick C:\OpenCode or C:\OpenCode\bcw.
   Or open "OpenCode (Ascent)" for the terminal version. The terminal version starts in C:\OpenCode. In a terminal, "opencode-ascent C:\OpenCode\bcw" starts it in the BCW code.
Re-running the .bat is safe: it refreshes the program and settings and keeps C:\OpenCode and your sessions.
If the Ascent was not reachable, the Gitea step is skipped with a message; re-run the .bat later.

SAFETY RULES BUILT IN
- OpenCode asks before every file change and every command, except plain read-only checks (git status/log/diff, ls, cat, grep, docker ps/logs/inspect, ipconfig, ping).
- Blocked outright: deleting folders, stopping/removing/restarting Docker containers or volumes, docker compose up/down,
  force-push, branch deletion, git reset --hard, git clean, shutdown/restart, stopping services, editing anything under Documents\BCW.
- Its rules file (%USERPROFILE%\.config\opencode\AGENTS.md) tells it the live BCW is read-only: it diagnoses and proposes, you apply fixes.
- Gitea refuses force-pushes and branch deletion for everyone, so its commits can always be undone.
- Shared model: OpenCode uses the same two Inkling slots as BCW's users. During long OpenCode jobs, BCW answers can wait.

BLENDER
- Install it from Blender-HAL3000\INSTALL-BLENDER.bat on this USB (after this OpenCode install). It enables the add-on and
  starts its server with Blender automatically. Then open Blender and ask OpenCode to describe the scene.
- Poly Haven, Sketchfab and 3D generation need internet and do not work at work; scripting Blender does.

FREECAD
- Install it from FreeCAD-HAL3000\INSTALL-FREECAD.bat on this USB. It adds the MCP add-on and starts its server with
  FreeCAD automatically. Open FreeCAD, then ask OpenCode to model something. See FreeCAD-HAL3000\README.txt.

BCW CODE AT WORK
- C:\OpenCode\bcw is a copy of Gitea's bcw (branch release/0.17). Read its AGENTS.md and docs\WORK-SYNC.md.
- OpenCode commits there when asked; push sends it to Gitea. Bringing it home is the usual USB export on the Ascent.
- Codex on the Ascent works on the same Gitea repository. Pull before starting (git pull) so both stay in step.

IF SOMETHING STOPS
- "checksum mismatch": the USB copy is damaged; copy OpenCode-HAL3000 again from home.
- Logs: %USERPROFILE%\.local\share\opencode\log
- Desktop app: if it was open during the install, close and reopen it (it reads the offline settings at start).
  Its own log: %APPDATA%\ai.opencode.desktop\logs. It may say it cannot check for updates; that is expected offline.
- To remove: uninstall "OpenCode" in Settings > Apps, then delete %LOCALAPPDATA%\OpenCode-Ascent and %USERPROFILE%\.config\opencode, the desktop shortcut, and the OpenCode-Ascent entry in the user PATH. C:\OpenCode holds your work; keep it.
