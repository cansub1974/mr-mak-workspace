OPENCODE FOR HAL3000 (ASCENT GX10, OFFLINE)
Prepared 22 November 2026. OpenCode 1.19.6.

WHAT IT INSTALLS (no administrator rights, no internet)
- OpenCode, using Flash-Next on the Ascent (http://192.168.2.45:8080/v1). gpt-oss-120b and Qwen3.8-27B can be picked with /models.
- MCP servers: Playwright (drives a browser, e.g. to check BCW pages) and Blender (works once Blender is installed, see below).
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
3. The last step asks Flash-Next for a test reply. "OpenCode answered through Flash-Next: READY" means everything works.
4. Open "OpenCode (Ascent)" on the desktop. It starts in C:\OpenCode. In a terminal, "opencode-ascent C:\OpenCode\bcw" starts it in the BCW code.
Re-running the .bat is safe: it refreshes the program and settings and keeps C:\OpenCode and your sessions.
If the Ascent was not reachable, the Gitea step is skipped with a message; re-run the .bat later.

SAFETY RULES BUILT IN
- OpenCode asks before every file change and every command, except plain read-only checks (git status/log/diff, ls, cat, grep, docker ps/logs/inspect, ipconfig, ping).
- Blocked outright: deleting folders, stopping/removing/restarting Docker containers or volumes, docker compose up/down,
  force-push, branch deletion, git reset --hard, git clean, shutdown/restart, stopping services, editing anything under Documents\BCW.
- Its rules file (%USERPROFILE%\.config\opencode\AGENTS.md) tells it the live BCW is read-only: it diagnoses and proposes, you apply fixes.
- Gitea refuses force-pushes and branch deletion for everyone, so its commits can always be undone.
- Shared model: OpenCode uses the same two Flash-Next slots as BCW's users. During long OpenCode jobs, BCW answers can wait.

BLENDER (after installing Blender)
1. In Blender: Edit > Preferences > Add-ons > Install from Disk, choose %LOCALAPPDATA%\OpenCode-Ascent\blender\addon.py, enable "MCP for Blender".
2. In the 3D view press N, open the BlenderMCP tab, click Connect (port 9876).
3. Start OpenCode and ask it to describe the Blender scene. Restart OpenCode if Blender was opened after it.
Poly Haven, Sketchfab and 3D generation need internet and do not work at work; scripting Blender does.

BCW CODE AT WORK
- C:\OpenCode\bcw is a copy of Gitea's bcw (branch release/0.17). Read its AGENTS.md and docs\WORK-SYNC.md.
- OpenCode commits there when asked; push sends it to Gitea. Bringing it home is the usual USB export on the Ascent.
- Codex on the Ascent works on the same Gitea repository. Pull before starting (git pull) so both stay in step.

IF SOMETHING STOPS
- "checksum mismatch": the USB copy is damaged; copy OpenCode-HAL3000 again from home.
- Logs: %USERPROFILE%\.local\share\opencode\log
- To remove: delete %LOCALAPPDATA%\OpenCode-Ascent and %USERPROFILE%\.config\opencode, the desktop shortcut, and the OpenCode-Ascent entry in the user PATH. C:\OpenCode holds your work; keep it.
