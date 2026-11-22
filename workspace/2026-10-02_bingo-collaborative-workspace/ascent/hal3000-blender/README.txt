BLENDER 5.2.4 LTS + MCP FOR BLENDER, FOR HAL3000 (OFFLINE)
Prepared 22 November 2026. Same 5.2 LTS line as the home PC, so .blend files open the same.

WHAT IT INSTALLS (no administrator rights, no internet)
- Blender 5.2.4 LTS in %LOCALAPPDATA%\Programs\Blender\5.2.4 (checksum matches blender.org).
- The "MCP for Blender" add-on (version 2.0, installed as blender_mcp), enabled. Its server starts by itself when Blender opens
  (port 9876, this PC only), so OpenCode's Blender MCP can drive Blender.
- A desktop shortcut "Blender 5.2.4"; .blend files open with it (this Windows user only).

INSTALL
1. Install OpenCode first (OpenCode-HAL3000\INSTALL-OPENCODE.bat) if you want OpenCode to drive Blender.
2. Close Blender if it is open. Run Blender-HAL3000\INSTALL-BLENDER.bat (double-click).
3. The last step opens Blender briefly and checks its MCP server answers. "OpenCode can drive Blender" means it works.
Re-running is safe; an existing blender_mcp add-on is backed up first.

USE
1. Open Blender (desktop shortcut). The MCP for Blender tab is in the 3D view sidebar (press N); it shows the server running.
2. Open "OpenCode (Ascent)" and ask, for example: "Describe the Blender scene" or "Add a 2 m cube at the origin".
   If Blender was opened after OpenCode, restart OpenCode.
Works offline: scene info, Python scripting of Blender, viewport screenshots. Needs internet (not at work): Poly Haven,
Sketchfab, Poly Pizza and 3D generation.

NOT INCLUDED
- Your home Blender add-ons (HardOps, Boxcutter, DECALmachine, MACHIN3tools, MESHmachine, etc.) and preferences.
