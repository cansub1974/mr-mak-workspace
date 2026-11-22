TOOLS FOR HAL3000 (OFFLINE)
Prepared 22 November 2026. Each installer is the maker's official download; its SHA-256 matched the checksum the maker
publishes (GIMP help: valid gimp.org signature) and is checked again before installing.

INSTALL
Run Tools-HAL3000\INSTALL-TOOLS.bat (double-click). No administrator rights or internet needed. Each tool installs on its
own and a summary shows OK or why one failed. Install GIMP (GIMP-HAL3000) first so its offline help can join it.
Only some tools:  INSTALL-TOOLS.bat -Only status,keepass   (names: status vscode gimphelp keepass 7zip notepadpp drawio)

WHAT YOU GET
- Ascent status (desktop shortcut): checks chat, Library search, Docling, ComfyUI, Gitea, SSH and BCW on this PC, and says
  in plain words what is down and what that affects. First thing to run when "the Assistant isn't answering".
  At home through the SSH tunnel: Ascent-Status.cmd -Tunnel
- VS Code 1.147 with the Python extensions (Python, Pylance, debugger, environments). For reading and reviewing BCW code in
  C:\OpenCode\bcw before it is pushed. Updates and telemetry are switched off.
- GIMP offline help (English): GIMP's Help menu works without internet.
- KeePassXC 2.8.0: offline password manager for the Ascent, Gitea and BCW passwords. Keep the database file on HAL3000,
  a copy on this USB, and the master password in your head (it cannot be recovered).
- 7-Zip 26.06 (Start menu: 7-Zip File Manager; no right-click menu without administrator rights).
- Notepad++ 8.9.9.1: for logs and settings files.
- draw.io 32.7.4: offline diagrams (schedules, layouts, process flows). Ignore any update notice.

TESTED AT HOME: the status check (through the tunnel and against a blocked address), and the KeePassXC, 7-Zip and Notepad++
installs. VS Code, GIMP help and draw.io run their makers' own installers for this user; they were not run on the home PC.
