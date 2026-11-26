FREECAD FOR HAL3000 (WITH THE FREECAD MCP FOR OPENCODE)
Prepared 27 November 2026. FreeCAD 1.1.4 (official installer, checksum matches the FreeCAD release) and
the FreeCAD MCP add-on 0.1.32 (github.com/neka-nat/freecad-mcp).

WHAT IT INSTALLS (no administrator rights, no internet)
- FreeCAD 1.1.4 for this Windows user in %LOCALAPPDATA%\Programs\FreeCAD 1.1 (Start menu "FreeCAD 1.1", desktop icon, .FCStd files).
- The "MCP Addon" workbench in FreeCAD's user Mod folder. Its server starts by itself when FreeCAD opens and listens on
  127.0.0.1:9875 only (this PC; remote connections stay off).
- OpenCode's side (the "freecad" MCP server) is in the OpenCode-HAL3000 package. Install that too (either order).

INSTALL
1. Close FreeCAD if it is open.
2. Run FreeCAD-HAL3000\INSTALL-FREECAD.bat (double-click). It checks the package, installs FreeCAD and the add-on,
   then opens FreeCAD briefly to check the MCP server answers: "FreeCAD started its MCP server on port 9875" means it works.
3. Re-running is safe: it keeps the installed FreeCAD 1.1.4 and refreshes the add-on (the old add-on folder is kept as FreeCADMCP.bak-<date>).

USING IT
- Open FreeCAD first, then ask OpenCode, e.g. "In FreeCAD, make a 100 x 50 x 10 mm plate with four 8 mm holes 10 mm from the corners."
- OpenCode can create and edit parts, read documents and objects, run FreeCAD Python, take view screenshots and run FEM analyses.
  It can also run a FreeCAD script without the window (headless) using FreeCADCmd.
- Save your own work in FreeCAD before asking for big changes: scripts run inside your open FreeCAD session.
- If OpenCode says it cannot reach FreeCAD: in FreeCAD choose the "MCP Addon" workbench and press "Start RPC Server";
  the menu FreeCAD MCP > Auto-Start Server should be ticked.
- The add-on's parts library and anything online (downloads) do not work at work; modelling does.

TO REMOVE
- Uninstall "FreeCAD 1.1" in Settings > Apps, and delete the FreeCADMCP folder from FreeCAD's user Mod folder
  (in FreeCAD's Python console: import os; print(os.path.join(FreeCAD.getUserAppDataDir(), "Mod"))).
