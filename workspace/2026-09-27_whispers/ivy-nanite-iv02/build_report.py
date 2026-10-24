"""Render the IV02 Workspace evidence tab from collected facts, never synthetic timings."""
from pathlib import Path
from html import escape
import datetime
import json

TASK = Path(__file__).resolve().parent
WORKSPACE = TASK.parent
REPO = WORKSPACE.parent.parent
ev = TASK / 'evidence'

criteria = [
 ('Environment', 'PASS — inspection only', 'Engine/project/editor/map/PIE/dirty readbacks', 'editor-state.json'),
 ('Rendering state', 'PASS — inspection only', 'Live Epic/TSR/100%/VSM/Substrate/Nanite cvars', 'editor-rendering.json'),
 ('Host hardware', 'PASS — identified', 'CPU/RAM via CIM; GPU/VRAM/driver via engine startup log', 'hardware.json'),
 ('Target platform and budget', 'PENDING LEAD DECISION', 'Historical RTX 3060/60 FPS direction; complete current profile/allocation unagreed', None),
 ('Fab/Quixel audit', 'PASS — audit only', 'Authenticated, 92 records reported; shortlisted packs and local candidates; no imports/licence actions', 'fab-shortlist.json'),
 ('Existing facade section', 'PASS — source identified', '62 candidate objects in existing MS02 crop; export/visual content not yet verified', 'facade-selection.json'),
 ('MS02 preservation', 'PARTIAL', 'Size/mtime unchanged; no pre-inspection hash, so no content-hash proof', 'source-preservation.json'),
 ('A1–A5 Blender/export', 'NOT RUN', 'Source, opaque geometry, atlas, masks, axis/pivots, FBX round trip and independent delivery', None),
 ('B1 Unreal import', 'NOT RUN', 'Nanite, dimensions, normals, slots, UVs and vertex colors', None),
 ('B2 Isolated fixture/route', 'NOT RUN', 'Actual facade materials/lighting, exclusions, cameras and save/reopen', None),
 ('B3 Shading/shadows/Nanite', 'NOT RUN', 'Material and Preserve Area comparisons, overdraw, VSM and temporal inspection', None),
 ('B4 A–D profiling', 'NOT RUN', 'Three comparable captures per configuration/view plus separate traversal, raw profiles, p95/p99, variability', None),
 ('B5 Agreed budget acceptance', 'NOT RUN', 'No agreed current allocation or target-hardware measurements', None),
 ('B6 Jason visual verdict', 'NOT RUN', 'Actual game-mesh/reference comparison for this prototype', None),
 ('B7 Independent verification/delivery', 'PENDING', 'Implementation has not begun; packet publication is not implementation delivery', None),
 ('Full kit and PCG placement', 'GATED — NOT RUN', 'Requires accepted prototype and continuation contract', None),
 ('Final full-coverage suite', 'GATED — NOT RUN', 'Final material/PCG coverage, actual hotel or documented representative stress scene', None),
]
(TASK / 'acceptance-status.json').write_text(json.dumps([dict(zip(['criterion','status','evidence','artifact'],r)) for r in criteria],indent=2),encoding='utf-8')

def link(path, label=None):
    return f'<a href="ivy-nanite-iv02/{escape(path)}">{escape(label or path)}</a>'

def table(headers, rows):
    return '<div class="table-scroll"><table><thead><tr>'+''.join(f'<th>{escape(h)}</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{c}</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'

html = '''<!doctype html>
<html lang="en" data-mak-report="document"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hotel Eden — opaque Nanite ivy IV02</title><link rel="stylesheet" href="../_shared/report.css"><script defer src="../_shared/report.js"></script>
<style>.table-scroll{max-width:100%;overflow-x:auto}td,th{border-bottom:1px solid var(--mak-border);vertical-align:top}table{display:table!important;min-width:640px!important}.notice{padding:18px 22px;border:1px solid var(--mak-border);background:var(--mak-surface);border-radius:10px}nav{display:flex;flex-wrap:wrap;gap:10px 24px;margin:24px 0}li{margin-bottom:6px}details{padding:14px 0;border-bottom:1px solid var(--mak-border)}summary{cursor:pointer;font-weight:600}section{margin-top:32px}h2{margin-bottom:12px!important}</style></head><body><main>
<p class="meta">Whispers · Hotel Eden · IV02-r1 · 24 October 2026</p>
<h1>Opaque Nanite ivy: prototype and evidence</h1>
<p class="notice"><strong>Pre-implementation. The ivy workflow has not been built or performance-accepted.</strong><br>The required linked packets are published for project triage. This tab contains observed environment/source facts and the proposed test contract. No IV02 timings, prototype exports or Unreal test level exist yet.</p>
<nav><a href="#status">Acceptance</a><a href="#facts">Observed baseline</a><a href="#sourcing">Asset shortlist</a><a href="#budget">Budget proposal</a><a href="#results">Performance results</a><a href="#files">Sources and reproduction</a></nav>
<p><a href="https://github.com/cansub1974/Whispers/issues/113">#113 — Blender source and export</a> → <a href="https://github.com/cansub1974/Whispers/issues/114">#114 — Unreal prototype and measurement</a>. Both were read back OPEN with <code>needs-triage</code>; #114 has a native blocked-by dependency on #113. No issue or editor lock was claimed by this session.</p>
<section id="status"><h2>Acceptance ledger</h2>'''
html += table(['Criterion','Result','Evidence / next proof'],[(escape(a),escape(b),escape(c)+(f' · {link("evidence/"+d,"raw JSON")}' if d else '')) for a,b,c,d in criteria])
html += '''</section><section id="facts"><h2>Observed baseline</h2>
<p>These are editor/environment observations. They do not establish the no-ivy gameplay frame-time baseline.</p>'''
html += table(['Item','Observed value'],[(escape(a),escape(b)) for a,b in [
 ('Engine/build','5.8.2-56702186+++UE5+Release-5.8; D3D12 / SM6'),
 ('Editor identity','PID 70640; Whispers 5.8; bridge 1.4.8 / protocol 2; binary built 24 Oct 2026 13:20:22'),
 ('Map/state','/Game/Whispers/World/EdenE2K/L_EdenE2K; editor mode; PIE/simulate stopped; zero dirty packages at inspection'),
 ('GPU/driver','AMD Radeon RX 7900 XTX; 24,560 MiB dedicated VRAM from D3D12; AMD 32.0.21042.62 / Adrenalin 2026.04.17'),
 ('CPU/RAM','Ryzen 9 7900X, 12 cores / 24 threads; installed RAM 67,816,374,272 bytes (63.16 GiB)'),
 ('Editor quality','All queried scalability groups 3 (Epic); TSR, screen percentage 100; VSync 0; t.MaxFPS 0'),
 ('Renderer','Standard Nanite and VSM enabled; hardware Lumen, Substrate and MegaLights enabled; Nanite RT mode 1'),
 ('Experimental foliage','r.Nanite.Foliage=1 for existing project trees. IV02 contract uses standard static Nanite meshes and no voxel/assembly foliage.'),
 ('Resolution/build mode','New fixture output resolution and Standalone/packaged run not established. No runtime measurements collected.'),
 ('Source/master','MS02 opened in a separate background Blender 5.2.1 process; 12,252 mesh objects inventoried; no blend saved'),
 ('Unrelated state','Unreal Git checkout and Workspace contain pre-existing unrelated changes. No staging/reverting/saving of them.'),
]])
html += '''<p>The current Nanite RT mode conflicts with an older offline-only warning in the lighting guide. The packet asks the lead to record the tested route; it does not silently change global rendering settings. Existing Experimental Foliage settings do not authorize that route for this ivy.</p>
<p>The selected facade crop is Blender X −1.0…8.1 m, Y −0.4…2.4 m, Z −0.2…4.2 m, including existing window, corner and ledge objects. Exported visible surfaces still need inspection. The sole hotel master stays read-only; the new ivy source will contain ivy only.</p>
</section><section id="sourcing"><h2>Owned assets and reuse shortlist</h2>
<p>Fab authenticated successfully. Its library returned 92 records, including duplicate representations. Exact title searches “ivy”, “vine” and “climber” returned no matches. The local Megascans UAssets index is empty; that does not establish the extent of Quixel entitlements.</p>'''
html += table(['Candidate','Observed suitability','Action'],[(escape(a),escape(b),escape(c)) for a,b,c in [
 ("Sharur’s Normandy Village + PCG Plants",'Owned; description explicitly mentions wall ivy; current compatibility flag false','Inspect individual source/opacity/geometry before choosing. No full-pack import performed.'),
 ('Dark Ruins Megascans Sample','Owned; compatibility true; suitable ivy not established','Metadata shortlist only; not a proven ivy source.'),
 ('Existing FG02 ivy + historical IV01','Local mesh/source candidates; IV01 visual direction accepted historically','Inspect for reusable geometry/atlas/curves; previous acceptance and timing do not certify IV02.'),
]])
html += '<p>No assets were imported, bought or claimed, and no licence was accepted. '+link('evidence/fab-shortlist.json','Owned asset metadata and exact IDs')+'.</p>'
html += '''</section><section id="budget"><h2>Proposed budget — awaiting the lead</h2>
<p>The historical target is RTX 3060 / 60 FPS. A complete current platform, settings profile and ivy allocation have not been agreed. The following is a proposal, not a user hardware claim or accepted performance contract.</p>'''
html += table(['Proposed test profile / threshold','Value'],[(escape(a),escape(b)) for a,b in [
 ('Target platform','RTX 3060 12 GB desktop; Ryzen 5 5600; 32 GB RAM'),
 ('Settings','1920×1080; High; TSR; fixed 100% render percentage; dynamic resolution off; Development D3D12/SM6'),
 ('Full-coverage incremental GPU median','≤ 1.0 ms against matched no-ivy A'),
 ('Sustained total frame','p95 ≤ 16.67 ms; p99 ≤ 20.0 ms'),
 ('Traversal','p99 ≤ 25 ms; no repeatable ivy-attributable frame > 50 ms'),
 ('Additional resident GPU memory','≤ 256 MiB'),
]])
html += '''<p>Measurements may proceed before this decision. Acceptance may not. No RTX 3060 is available in the inspected host, so any host data remains RX 7900 XTX data.</p>
</section><section id="results"><h2>IV02 performance results</h2>
<p><strong>No captures have run.</strong> Missing values are unmeasured, not zero. The table is a configuration/status ledger; no performance improvement is claimed.</p>'''
html += table(['Configuration','Setup in packet','Runs','Frame/GPU delta vs A','p95 / p99','Acceptance'],[(escape(a),escape(b),'NOT RUN','Unmeasured','Unmeasured','Pending') for a,b in [
 ('A — no ivy','Identical facade array/camera/light state; zero ivy'),
 ('B — expected bay coverage','One bay’s supported patch placement, with exclusions; exact count frozen after support checks'),
 ('C — representative stress','32 repeated facade bays at supported B coverage; explicitly not a full-hotel prediction'),
 ('D — headroom stress','Same facade layout; double B density/layers, intersections inspected'),
]])
html += '''<details><summary>Reproducible capture requirements</summary><p>Five fixed views: first-person, oblique, courtyard, distant and dense overlap/shadow. Freeze transforms/FOV, resolution, scalability, render percentage, upscaler, lighting/exposure and scene state. Disable VSync/frame caps; finish shaders and warm streaming before ≥120 s steady captures, three comparable runs per configuration/view. Save separate first-use and warm traversal/streaming runs so warm-up does not conceal stalls.</p><p>Retain raw CSV, Insights traces, GPU profiles and available memory/streaming counters. Report frame/GPU/game/render distributions, per-run variation, p95/p99, pass costs and paired millisecond deltas. Identify CPU/GPU bound cases and unsupported counters. Keep screenshots/visualizations and profiler overhead separate from primary timings. Do not linearly extrapolate patch cost.</p></details>
<details><summary>Rendering and visual comparisons</summary><p>Standard Nanite, opaque geometric leaves, no WPO. Actual meshes cast VSM shadows. Compare Preserve Area on/off and opaque Default Lit/Two Sided Foliage (or verified Substrate equivalents) under front/back/local lights. Inspect leaf retention, temporal shimmer/popping, Nanite overdraw, layering, shadow detail, intersections and repetition. No fallback/VSM proxy confusion or physically correct transmission claim. Simplified shadow casters and localized POM are conditional profiling experiments, not defaults.</p></details>
<details><summary>Gated kit and PCG continuation</summary><p>After prototype acceptance: wall patches with sparse edges/transitions, corner-anchored pillar wraps, top-pivot hanging dangles and shared material instances. PCG uses explicit facade inclusion and window/door exclusions, directed surface queries, growth-up orientation, footprint support checks, distinct wall/corner/ledge rules, stable seeds, spacing/overlap limits, appropriate instancing/bounds/culling. Rigid patches do not conform from a single surface normal. Re-run the suite on final materials and PCG coverage.</p></details>
</section><section id="files"><h2>Sources and reproduction</h2><ul>'''
for path,title in [('README.md','Findings, limitations and read-only reproduction'),('prototype-blender-packet.md','Complete Blender packet #113'),('prototype-unreal-packet.md','Complete Unreal packet #114'),('asset-contract.md','Shared asset contract'),('continuation.md','Gated kit and PCG design'),('workflow-specification.md','Combined workflow specification'),('acceptance-status.json','Machine-readable acceptance ledger'),('inspect_master.py','Read-only Blender inventory script'),('prepare_packet.py','Packet reproduction script'),('evidence/master-inventory.json','Full read-only source object inventory'),('evidence/source-preservation.json','Master preservation observations')]:
    html += '<li>'+link(path,title)+'</li>'
html += '''</ul><p>Report preview verified at 1440 px and 390 px: no page errors, no page-level horizontal overflow and all 24 local links resolved. This checks the report only; no Unreal game capture or benchmark was run.</p><p>Heavy future source/profiling files stay local when ≥50 MB, with paths, sizes and hashes in the delivery manifest. Account identifiers, credentials and signed URLs are excluded from this report. Historical IV01 timings are not mixed into IV02 results.</p>
<p>Technical references: <a href="https://dev.epicgames.com/documentation/unreal-engine/working-with-naniteenabled-content">Epic Nanite content</a>, <a href="https://dev.epicgames.com/documentation/unreal-engine/overview-of-substrate-materials-in-unreal-engine">Substrate</a>, <a href="https://dev.epicgames.com/documentation/unreal-engine/virtual-shadow-maps-in-unreal-engine">Virtual Shadow Maps</a>. Installed API discovery and measured outcomes govern this prototype.</p>
</section></main></body></html>'''
(WORKSPACE / 'ivy-nanite-iv02-review.html').write_text(html,encoding='utf-8')

registry = REPO / 'workspace/workspace.json'
data = json.loads(registry.read_text(encoding='utf-8'))
card = next(x for x in data['entities'] if x['id']=='whispers-eden')
step = {'name':'Ivy — Nanite IV02','path':'ivy-nanite-iv02-review.html'}
if not any(s['path']==step['path'] for s in card['steps']):
    card['steps'].insert(1,step)
card['updated']='2026-10-24'
card['defaultStep']=next(i for i,s in enumerate(card['steps']) if s['path']==step['path'])
registry.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'tab':step,'criteria':len(criteria),'timing_runs':0}))
