# Whispers model library

The editable 3D asset library is available from this workspace at
[`projects/ai-modelling`](../../projects/ai-modelling/). It is a local Windows
junction to `D:\AI_Modelling`; both paths open the same files.

The library stays outside this repository so Blender sources, exports, Unreal
assets, previews, and intermediate files are not copied into the workspace Git
history. The link itself is ignored by Git and is available on this machine.

## Current library map

| Area | Purpose | Useful contents |
| --- | --- | --- |
| `hotel_eden/current` | Accepted baseline of the Hotel Eden building | Drawings, geometry, model sources, schedules, views, and QA previews |
| `hotel_eden/working` | Active Hotel Eden modelling iterations | Blender walkthrough, roof, window, and Unreal staging iterations |
| `hotel_eden/artistic` | Visual exploration | Rear-elevation studies and references |
| `hotel_eden/archive` | Superseded and preserved iterations | Earlier blockouts, exterior renders, plans, and maintenance backups |
| `room7` | Staff-bedroom model | Blender source, build/refinement scripts, and entrance/preview renders |
| `staff_quarters` | Connected staff-room modelling work | Blender sources, assembly manifests, layout reviews, and room previews |

## Working with an asset

1. Start in the appropriate `current` or `working` folder and read its local README or documentation before changing geometry.
2. Keep editable source files, exports, previews, and QA evidence together in that asset’s own folder.
3. Treat `current` as the accepted baseline. Use a named folder under `working` for an active revision, then promote it only after review.
4. Import or stage approved assets in the live Unreal project at `D:\Unreal Projects\Whispers`; use the Whispers MCP tools to inspect the editor state before changing assets there.
5. Record modelling decisions, review results, and the next handoff in the Whispers workspace notes or a GitHub Issue when implementation work begins.

## What I can do here

I can inspect and organize these files, open and revise Blender-oriented sources when the required toolchain is available, prepare FBX/Unreal import handoffs, generate previews and inventories, and connect approved assets to the running Whispers project. I will keep large working assets local unless you explicitly ask to add selected deliverables to a repository.
