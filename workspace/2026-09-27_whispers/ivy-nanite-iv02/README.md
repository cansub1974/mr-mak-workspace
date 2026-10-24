# IV02 — opaque static Nanite ivy

Revision IV02-r1, 24 October 2026. **Pre-implementation packet. No ivy has been authored, imported or benchmarked in IV02.**

Live packets: [#113 — Blender source/export](https://github.com/cansub1974/Whispers/issues/113) and [#114 — Unreal prototype/measurement](https://github.com/cansub1974/Whispers/issues/114). Both read back OPEN and `needs-triage`; #114 is natively blocked by #113. No assignment, issue claim or editor/resource lock was acquired by this session. IssueBridge and the lead own triage/assignment; publication alone does not authorize execution under an assigned specialist contract.

Jason requested a reusable opaque ivy kit and reproducible placement/performance workflow, starting with one existing Hotel Eden facade section. The current increment is the prototype only. The complete kit and PCG rollout depend on its measured result and Jason's visual verdict.

## Source and constraints

- Authoritative hotel: `D:/AI_Modelling/hotel_eden/working/master_MS02/Hotel_Eden_Master_MS02.blend`. Read-only dependency for IV02; no architecture edits and no second hotel `.blend`.
- A separate background Blender opened the master and produced `evidence/master-inventory.json`; it saved no `.blend`. Installed Blender: 5.2.1 LTS, hash 9e2066aef7ef. Some user add-ons logged compatibility errors, but the inventory completed and the process exited 0. Use `--factory-startup --disable-autoexec` for subsequent independent background inspections.
- New ivy source belongs in `D:/AI_Modelling/hotel_eden/working/ivy_IV02/`. The ivy `.blend` retains only ivy curves, Geometry Nodes, leaf sources, materials and export meshes. The facade is exported from a read-only master process to a fixture FBX; it is never saved into an ivy or hotel copy `.blend`.
- Blender → Unreal changes require two linked issues under the current project workflow. Blender and Unreal work have different role profiles and evidence. Neither issue is complete without independent verification and scoped remote delivery.
- The historical asset template still names MS01. The current owner instruction, master README and quality directive supersede that reference: **MS02 only**.

## Observed baseline

Live identity, engine and rendering are recorded in the evidence links in the Workspace tab. UE 5.8.2, CL 56702186, D3D12/SM6; project `D:/Unreal Projects/Whispers 5.8/Whispers.uproject`; editor PID 70640, bridge 1.4.8, protocol 2, binary built 24 October 13:20:22. Open map `/Game/Whispers/World/EdenE2K/L_EdenE2K`, PIE/simulate stopped, zero dirty packages at inspection. The Git checkout contains unrelated modifications; cleanliness in the editor is not Git cleanliness.

Live editor cvars: Epic scalability (all queried groups 3), TSR (`r.AntiAliasingMethod=4`), screen percentage 100, VSync 0, frame cap 0, Nanite 1, VSM 1, Substrate 1, experimental Nanite Foliage 1, Nanite ray tracing mode 1, hardware Lumen 1, texture pool 3000 MB. These are **editor readbacks**, not a frozen benchmark configuration or a measured frame-time baseline. Output resolution has not been established for the new fixture.

Host: Radeon RX 7900 XTX, 24,560 MiB dedicated VRAM reported by D3D12; AMD driver 32.0.21042.62, Adrenalin 2026.04.17; Ryzen 9 7900X, 12 cores / 24 threads; 67,816,374,272 bytes installed RAM. WMI's 32-bit AdapterRAM truncates VRAM; use the engine adapter log instead.

### Performance proposal to the lead — not agreed

Historical IV01 knowledge names an RTX 3060 / 60 FPS direction. It does not specify a current complete target platform or an ivy allocation. Propose RTX 3060 **12 GB desktop**, Ryzen 5 5600, 32 GB RAM, 1920×1080 output, High scalability, TSR at fixed 100% render percentage, dynamic resolution off, Development build, D3D12/SM6. These CPU/RAM/VRAM/settings are proposed, not facts about Jason's target machine.

Proposed full-coverage incremental allocation: paired median GPU delta ≤ 1.0 ms; total frame p95 ≤ 16.67 ms and p99 ≤ 20.0 ms; traversal p99 ≤ 25 ms and no repeatable ivy-attributable frame > 50 ms; additional resident GPU memory ≤ 256 MiB. Repeated differences inside the observed variation are inconclusive. These thresholds require a recorded lead decision; do not certify against this proposal. Host results remain workstation-only, regardless of how fast they are.

## Sourcing decision

Fab was authenticated; `list_library` reported 92 records (including duplicate representations). Owned-title searches ivy/vine/climber each returned zero. A complete title inventory was examined; the metadata shortlist is in `evidence/fab-shortlist.json`:

- **Sharur's Normandy Village + PCG Plants**, owned ID `901d90cacd2346b1896d45431d502119`. Metadata explicitly mentions wall ivy. Current compatibility flag is false. Leaf geometry, opacity, atlas and source availability remain unverified. Do not import the entire pack merely to inspect one asset.
- **Dark Ruins Megascans Sample**, owned ID `aafa85a424d04402b654171e43e63d52`. Compatible flag true; metadata does not establish suitable ivy. This is a pack to inspect, not a proven ivy match.
- **Existing local assets**: `/Game/Whispers/Presentation/Environment/HotelEden/FG02/Meshes/SM_FG02_Ivy_Left` and `_Right`; historical IV01 editable source/generator under `workspace/2026-09-27_whispers/ivy/`; MS02 ivy materials in MM01. Inspect reuse before fresh authoring. Historical appearance approval applies to IV01 only.

The local Megascans UAssets index contains an empty assets array. This does not prove that all Quixel entitlements are absent; it describes the checked local index and Fab service results only. No imports, purchases, claims or licence acceptance occurred. If a pack download is large, show the owner its exact selection and size before importing. Shipped sourced assets go in Whispers `docs/credits-log.md` with their provenance.

## Required rollout

1. The lead finalizes and queues the paired prototype packets through IssueBridge. No packet is promoted while consequential choices or its required locks are unresolved.
2. The Blender artist inspects owned/local candidates, exports a bounded existing facade fixture, and authors or adapts **one** open-surface ivy patch. Its own export evidence is independently verified before the tech artist starts the dependent import.
3. The technical artist builds the isolated test map, captures the no-ivy baseline, verifies import/shading/shadows, and runs the A–D suite. Retain all raw captures and exact settings. The acceptance ledger records absent evidence as NOT RUN, never zero milliseconds.
4. After technical evidence and Jason's visual decision, the lead writes the kit/PCG continuation against the accepted prototype. This increment does not authorize hotel-wide installation.

## Evidence and acceptance status

Environment/sourcing/source inspection: collected. Facade export, baseline performance, prototype mesh, Unreal import, material comparison, Nanite retention, A–D captures, percentiles, streaming hitches, PCG, final coverage, Jason's visual acceptance, independent technical verification and remote implementation delivery: **NOT RUN / pending**.

No technical pass or failure can be inferred from the environment inspection. The prototype and full workflow are **not accepted**. Old IV01 timing numbers are historical and are excluded from IV02 results.

## Reproduce read-only inspection

From the Workspace repository, run:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --factory-startup --disable-autoexec --background 'D:/AI_Modelling/hotel_eden/working/master_MS02/Hotel_Eden_Master_MS02.blend' --python 'C:/Users/Jason McKay/Documents/Codex/mr-mak-workspace/workspace/2026-09-27_whispers/ivy-nanite-iv02/inspect_master.py'
```

This writes JSON only. Verify source size/mtime/hash before and after; never save the master during inspection. For editor readbacks use the project MCP routes in `docs/agents/ue-mcp-toolchain.md`. Check dirty packages before VibeUE `execute_python_code`, which otherwise auto-saves them.

## Technical sources

- [Epic: working with Nanite-enabled content](https://dev.epicgames.com/documentation/unreal-engine/working-with-naniteenabled-content): Preserve Area, aggregate geometry and overdraw inspection.
- [Epic: Substrate materials](https://dev.epicgames.com/documentation/unreal-engine/overview-of-substrate-materials-in-unreal-engine): the enabled material framework requires an explicitly documented opaque foliage equivalent or verified legacy conversion.
- [Epic: Virtual Shadow Maps](https://dev.epicgames.com/documentation/unreal-engine/virtual-shadow-maps-in-unreal-engine): VSM inspection and normal Nanite shadow route. Fallback geometry is not a VSM shadow proxy.

Local code/readback wins over assumptions about the installed build. The lighting guide describes `r.RayTracing.Nanite.Mode=1` as offline-only while the current project sets it to 1 for E2K. Record the discrepancy for the lead; freeze the actual test route and measure its traversal costs. Do not silently change global settings to make an ivy result pass.
