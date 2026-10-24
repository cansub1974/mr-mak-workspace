"""Build the Ivy tab from delivered, copied evidence. Does not run or change Unreal/Blender."""
from pathlib import Path
from html import escape as esc
import json

TASK = Path(__file__).resolve().parent
REPORT = TASK.parent / 'ivy-nanite-iv02-review.html'
REPO = TASK.parents[2]
EVIDENCE = TASK / 'evidence/unreal'
manifest = json.loads((EVIDENCE / 'publication-manifest.json').read_text(encoding='utf-8'))
stats = json.loads((EVIDENCE / 'analysis/summary.json').read_text(encoding='utf-8'))

def url(path):
    return 'ivy-nanite-iv02/' + path

def link(path, label, download=False):
    return f'<a href="{url(path)}"'+(' download' if download else '')+f'>{esc(label)}</a>'

def figure(path, caption):
    u=url(path)
    return f'<figure><a href="{u}"><img src="{u}" alt="{esc(caption)}" loading="lazy"></a><figcaption>{esc(caption)} · <a href="{u}" download>Download image</a></figcaption></figure>'

def table(headers, rows):
    return '<div class="table-scroll"><table><thead><tr>'+''.join(f'<th>{esc(h)}</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{c}</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'

views = {'view0_first_person_045m':'First person · 0.45 m', 'view1_oblique_3m':'Oblique · 3 m',
         'view2_courtyard_15m':'Courtyard · 15 m','view3_distant_60m':'Distant · 60 m',
         'view4_dense_overlap':'Dense overlap','traversal1_cold':'First traversal after process start',
         'traversal2_warm':'Warm traversal'}
configs={'A':('Baseline',0),'B':('One bay',2),'C':('32-bay stress',64),'D':('Heavier stress',128)}

def metric(row, key, q='p50'):
    value=row.get(key,{}).get(q)
    return 'N/A' if value is None else f'{value:.3f}'

def deltas(view,cfg,key):
    if cfg=='A': return '—'
    values=[stats['paired_delta_vs_A'][view][cfg][str(r)].get(key,{}).get('p50') for r in [1,2,3]]
    return ' / '.join('N/A' if x is None else f'{x:+.3f}' for x in values)

def timing_table(view):
    rows=[]
    for cfg,(label,count) in configs.items():
        r=stats['pooled'][view][cfg]
        variation=stats['variation'][view][cfg]['FrameTime']['range_ms']
        rows.append([f'{cfg} · {esc(label)} ({count})',str(r['FrameTime']['n']),metric(r,'FrameTime'),
                     metric(r,'FrameTime','p95'),metric(r,'FrameTime','p99'),metric(r,'GPUTime'),
                     f'{variation:.3f}',deltas(view,cfg,'FrameTime'),deltas(view,cfg,'GPUTime')])
    return table(['Config (ivy instances)','Frames','Frame p50 ms','Frame p95 ms','Frame p99 ms',
                  'GPU p50 ms','Run median range ms','Δ frame p50 ms, runs 1/2/3','Δ GPU p50 ms, runs 1/2/3'],rows)

def pass_table():
    rows=[]
    for view,label in views.items():
        if view.startswith('traversal'): continue
        for cfg in configs:
            r=stats['pooled'][view][cfg]
            rows.append([esc(label),cfg,metric(r,'GameThreadTime'),metric(r,'RenderThreadTime'),
                         metric(r,'RHIThreadTime'),metric(r,'GPU/NaniteVisBuffer'),
                         metric(r,'GPU/NaniteBasePass'),metric(r,'GPU/ShadowDepths')])
    return table(['View','Cfg','Game p50 ms','Render p50 ms','RHI p50 ms','Nanite visibility p50 ms',
                  'Nanite base pass p50 ms','ShadowDepths p50 ms'],rows)

criteria=[
 ('A1–A5 Blender/export','PASS — independently verified; #113 closed','Editable source, master preservation, attributes and both FBX round trips verified.','independent-review-113.md'),
 ('B1 Unreal import','PASS — technical review','33,516 ivy triangles; axis/UV/color/normal/slot checks. Facade opaque/glass split retained original geometry.','import/compare_import.json'),
 ('B2 Fixture and reproduction','PASS — technical review','Saved/reopened isolated map, window/corner/ledge, stable cameras and 0/2/64/128 instances.','fixture/fixture_state_after_reopen.json'),
 ('B3 Shading/shadows/retention','Evidence reviewed; limitations retained','Preserve Area improves distant retention. Its enabled variant has not been timed.','independent-review-114.md'),
 ('B4 Workstation performance','Verified evidence delivered','Three A–D repetitions, five steady views, separate first/warm traversals and raw profiles.','analysis/summary.md'),
 ('B5 Target budget acceptance','NOT RUN / pending','No agreed performance allocation and no RTX 3060 run. Workstation timings do not certify the target.',None),
 ('B6 Jason visual verdict','PENDING','The prototype is ready to inspect; this report does not supply Jason’s verdict.',None),
 ('B7 Scoped delivery','Verified under IV02-r2','Whispers delivery and complete 1,794-file hashed local index reviewed.','independent-review-114.md'),
 ('Complete kit, PCG and hotel installation','NOT BUILT — gated follow-on','This delivery is one prototype patch and an isolated test scene.',None)]
(TASK/'acceptance-status.json').write_text(json.dumps([{'criterion':a,'status':b,'finding':c,'artifact':d} for a,b,c,d in criteria],indent=2),encoding='utf-8')

html='''<!doctype html><html lang="en" data-mak-report="document"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hotel Eden · Ivy IV02 model and evidence</title><link rel="stylesheet" href="../_shared/report.css"><script defer src="../_shared/report.js"></script><style>
nav,.downloads{display:flex;flex-wrap:wrap;gap:12px 22px;margin:22px 0}.notice{padding:20px;border:1px solid var(--mak-border);border-radius:10px;background:var(--mak-surface)}.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}figure{margin:18px 0;min-width:0}figure img{display:block;width:100%;height:auto}figcaption{font-size:13px;color:var(--mak-muted);line-height:1.6;margin-top:8px}.table-scroll{max-width:100%;overflow-x:auto}table{display:table!important;min-width:700px!important}td,th{vertical-align:top;border-bottom:1px solid var(--mak-border)}details{margin:18px 0;padding:12px 0;border-bottom:1px solid var(--mak-border)}summary{cursor:pointer;font-weight:600}a,code{overflow-wrap:anywhere}video{display:block;width:100%;background:var(--mak-bg)}.meta{margin-top:12px}@media(max-width:700px){.gallery{grid-template-columns:1fr}}
</style></head><body><main class="container"><p class="meta">Hotel Eden · IV02 · Evidence published 25 October 2026</p><h1>Ivy prototype: model, game views and measurements</h1>
<p class="notice"><strong>The prototype is built and imported into Unreal.</strong> Blender/export issue #113 is closed after independent verification. The Unreal technical evidence has been reviewed; #114 awaits Jason’s visual verdict. Target-hardware performance acceptance remains pending. This is one ivy patch and an isolated facade test, with no full-kit, PCG or hotel-wide installation claim.</p>
<nav><a href="#model">Get the model</a><a href="#game">Game views</a><a href="#comparisons">Comparisons and video</a><a href="#performance">Measurements</a><a href="#acceptance">Acceptance</a><a href="#files">Evidence and reproduction</a></nav>
<section id="model"><h2>Get the model</h2><p>The editable source retains curves, Geometry Nodes, leaf sources and packed atlas textures. The downloaded copies are byte-identical to the delivered sources.</p><div class="downloads">'''
html+=link('downloads/IV02_Ivy_Prototype.blend','Download editable Blender model · 5.26 MB',True)+link('downloads/SM_Ivy_WallPatch_Prototype.fbx','Download ivy FBX · 2.71 MB',True)+link('downloads/IV02-Ivy-Editable-Source.zip','Download source, FBX, textures and scripts · ZIP',True)
html+='''</div><p><strong>Original Blender source:</strong><br><code>D:\\AI_Modelling\\hotel_eden\\working\\ivy_IV02\\IV02_Ivy_Prototype.blend</code></p><p><strong>Delivered game source:</strong><br><code>D:\\Unreal Projects\\Whispers 5.8\\SourceAssets\\HotelEden\\IV02\\IV02_Ivy_Prototype.blend</code></p><p><strong>Unreal mesh:</strong><br><code>/Game/Whispers/Presentation/Environment/HotelEden/IV02/Meshes/SM_Ivy_WallPatch_Prototype</code><br>A separate <code>_PreserveArea</code> variant is present.</p><p><strong>Unreal test level:</strong><br><code>/Game/Whispers/Tests/HotelEden/IV02/L_IvyPrototype</code></p>'''
html+=table(['Asset attribute','Delivered value'],[[esc(a),esc(b)] for a,b in [
 ('Geometry','33,516 triangles / 21,793 vertices; approximately 233 geometric leaves, petioles and woody stems'),
 ('Bounds','Occupied width ≈80.6 cm; height ≈183 cm; depth ≈7.7 cm; attachment pivot at lower centre'),
 ('Shading','One IvyAtlas slot; opaque, two-sided materials; no WPO, wind or ivy collision'),
 ('Source identity','SHA-256 '+manifest['model_sha256']),
]])
html+='''<p>The last tab update stopped at the Blender handoff. Whispers’ revised specialist contract excluded cross-repository Workspace publication, so the later Unreal evidence stayed in Whispers. This update publishes it here without changing the delivered assets.</p></section>
<section id="game"><h2>Actual Unreal game views</h2><p>Standalone Game captures from the isolated existing MS02 facade section. The first-person view shows leaf silhouettes, veins, stems and cast shadows; the oblique view shows the narrow supported brick strip beside the window. These are delivered game captures, not new renders.</p>'''
for v,label in views.items():
    if not v.startswith('view'): continue
    html+=figure(f'evidence/unreal/shots/visual__cfgB_front_DL__{v}.png',f'Unreal · configuration B · {label} · Default Lit, Preserve Area off')
html+='''<details><summary>Baseline and stress configurations, all five views</summary><p>A/B/C/D use identical 32-bay facade geometry. Ivy counts are 0 / 2 / 64 / 128. C and D are documented stress setups, not a prediction of the full hotel.</p><div class="gallery">'''
for c in configs: html+=figure(f'evidence/unreal/sheets/cfg{c}_front_DL.jpg',f'Configuration {c} · {configs[c][0]} · five fixed views')
html+='''</div></details></section><section id="comparisons"><h2>Reference, materials and Preserve Area</h2><div class="gallery">'''
for p,cap in [('evidence/blender/A2_compare_wall_scale.jpg','Reference / historical IV01 / exported IV02 mesh on the MS02 bay · Blender comparison'),('evidence/blender/A2_compare_close.jpg','Supplied reference crop beside front and oblique exported game mesh · Blender comparison')]: html+=figure(p,cap)
html+='''</div><p>These reference comparisons are retained source QA. They do not substitute for the Unreal views above or Jason’s visual verdict.</p><h3>Distance retention</h3><p>The corrected temporal review found that Preserve Area helps distant ivy survive: at 15 m, 5,581 ivy-green pixels without it versus 9,344 with it; at 60 m, 18 versus 1,043 (each subtracts the matching no-ivy baseline). Without it, the distant ivy is nearly absent. <strong>All timing runs used Preserve Area off.</strong> The retained performance data does not establish the cost of the better-retaining variant.</p>'''
html+=figure('evidence/unreal/temporal/still_view3_distant_60m_A_PA0_PA1_crop.jpg','60 m crop · top: no ivy · middle: Preserve Area off · bottom: Preserve Area on')
html+='''<h3>Repeatable camera route · 44 seconds</h3><video controls preload="metadata" poster="ivy-nanite-iv02/evidence/unreal/temporal/sbs_every2s_sheet.jpg"><source src="ivy-nanite-iv02/evidence/unreal/route-preserve-area-comparison.mp4" type="video/mp4"></video><p>Preserve Area off/on side by side. This 1920×540 review proxy is encoded from the original 3840×1080 capture; it is for playback, not pixel measurement. Original evidence remains at <code>Saved/IV02/runs/video_cfgC_PA_side_by_side.mp4</code>. '''+link('evidence/unreal/route-preserve-area-comparison.mp4','Download review video',True)+'''.</p>
<p>The independent reviewer found no obvious discontinuity in the inspected close/mid-range strips; that does not certify every video frame. The last frame cuts to a fixed camera after the route ends. Retention and temporal limitations are documented in the '''+link('evidence/unreal/ivy-IV02-B.md','complete Unreal report')+'''.</p>
<details><summary>Front/back/local-light material comparisons</summary><p>Opaque Default Lit and Two Sided Foliage were difficult to distinguish on this wall-backed patch. Two Sided Foliage adds 14 pixel instructions and was not separately timed. Its transmission is an artistic approximation. Both use the installed Substrate-enabled project’s supported legacy shading route.</p><div class="gallery">'''
for lighting in ['front','back','local']:
    for material in ['DL','TSF']:
        html+=figure(f'evidence/unreal/sheets/cfgB_{lighting}_{material}.jpg',f'{lighting.title()} light · '+('Default Lit' if material=='DL' else 'Two Sided Foliage'))
html+='''</div></details><details><summary>Overdraw, real shadows and temporal review sheets</summary><p>The dense second ivy layer creates overlap hotspots. No zero-overdraw claim is made. The sun uses actual mesh VSM shadows; local MegaLights use their separate ray-traced shadow route. Simplified shadow casters were not justified by the measured VSM cost.</p><div class="gallery">'''
for p in sorted((EVIDENCE/'diagnostics').glob('*.png')): html+=figure('evidence/unreal/diagnostics/'+p.name,p.stem.replace('_',' '))
html+=figure('evidence/unreal/temporal/sbs_every2s_sheet.jpg','Route review · comparison every two seconds')
html+='''</div></details></section><section id="performance"><h2>Measured workstation performance</h2>
<p><strong>RX 7900 XTX workstation data; render-thread bound.</strong> UE 5.8.4-58902052, D3D12/SM6, Ryzen 9 7900X, 64 GB RAM, AMD driver 32.0.21042.62. This measured build differs from the original 5.8.2 preflight.</p>
<p>Standalone Game, uncooked Development; editor closed for timing. Output 1920×1080; High scalability, TSR, read-back screen percentage 100%, dynamic resolution off, VSync/frame cap off. Default Lit, front lighting, Preserve Area off. Three independent A–D repetitions; each steady view has a 30 s warm-up and 120 s capture. Separate first-use and warm traversal captures retain hitches. The scalability preset’s resolution-quality value was 87 while screen percentage read back 100; exact settings and limits are retained in the report and manifests.</p>
<p>Below: nearest-rank percentiles pooled from raw frames across three repetitions. Median range measures run-to-run variation. Deltas pair the same view/repetition with A; they are milliseconds, not FPS. CPU/GPU times overlap and are not summed.</p><h3>First-person inspection · 0.45 m</h3>'''+timing_table('view0_first_person_045m')
html+='''<details><summary>Other steady viewpoints</summary>'''
for view,label in views.items():
    if view.startswith('view') and view!='view0_first_person_045m': html+=f'<h3>{esc(label)}</h3>'+timing_table(view)
html+='''</details><details><summary>First-use and warm traversal measurements</summary>'''
for view,label in views.items():
    if view.startswith('traversal'): html+=f'<h3>{esc(label)}</h3>'+timing_table(view)
html+='''<p>First-use hitches occur in every configuration, including A. Cold traversal maximum reached 47.65 ms in D. No B/C/D frame exceeded 50 ms in the delivered series; one no-ivy oblique frame reached 58.61 ms. Isolated ~30 ms frames appear across configurations. Do not attribute every hitch to ivy.</p></details><details><summary>Game/render/RHI threads, Nanite and shadow pass costs</summary>'''+pass_table()+'''</details>
<p>The first-person cost is mainly MegaLights and the ray-tracing scene, rather than VSM depth rendering. Local VRAM was approximately 3.69 GB; paired differences of −10 to +14 MB had no consistent sign and are inconclusive. A separate VSM total/page-count counter and CPU temperature/clocks were unavailable on this route and remain N/A. The complete JSON includes per-run pass counters, streaming/memory data and all warm-up statistics.</p>
<p><strong>No agreed current budget or RTX 3060 test exists.</strong> These measurements do not grant target acceptance. They also do not predict the cost of final hotel coverage, other materials, Preserve Area on or PCG.</p><div class="downloads">'''+link('evidence/unreal/analysis/summary.json','Complete measured data · JSON',True)+link('evidence/unreal/analysis/summary.md','All measured tables and analysis',True)+link('evidence/unreal/raw-evidence-index.json','Raw capture index · 1,794 files',True)+'''</div></section>
<section id="acceptance"><h2>Acceptance and remaining work</h2>'''
html+=table(['Criterion','Status','Evidence / limitation'],[[esc(a),esc(b),esc(c)+(' · '+link('evidence/unreal/'+d,'Evidence') if d else '')] for a,b,c,d in criteria])
html+='''<p>Independent technical review: <a href="https://github.com/cansub1974/Whispers/issues/114#issuecomment-6388190669">#114 review</a>. #113 is <code>done / CLOSED</code>; #114 is <code>ready-for-human / OPEN</code> for Jason’s visual verdict. This publishing task has not changed those states.</p></section>
<section id="files"><h2>Evidence and reproduction</h2><p>Open <code>L_IvyPrototype</code> in Whispers, select <code>IV02_Benchmark</code>, choose Configuration A–D, UsePreserveArea and StartBookmark 0–4, then Play. AutoPlayRoute runs the recorded route. Bookmark order: first person, oblique, courtyard, distant, dense overlap. The full reproduction guide includes exact run commands and settings.</p><ul>'''
for p,label in [('evidence/unreal/ivy-IV02-B.md','Complete Unreal delivery report'),('evidence/unreal/ivy-IV02-A.md','Complete Blender delivery report'),('evidence/unreal/fixture-reproduction.md','Fixture README and reproduction guide'),('evidence/unreal/independent-review-113.md','Independent Blender/export review'),('evidence/unreal/independent-review-114.md','Independent Unreal technical review'),('evidence/unreal/publication-manifest.json','Copied evidence/source locations and verified hashes'),('evidence/unreal/raw-evidence-index.json','Original raw evidence index with paths, sizes and SHA-256'),('acceptance-status.json','Current acceptance ledger'),('prototype-blender-packet.md','Original Blender packet · historical'),('prototype-unreal-packet.md','Original Unreal packet · historical')]: html+='<li>'+link(p,label)+'</li>'
html+='''</ul><p>Original raw profiles, logs, frame dumps and route MP4s are at <code>D:\\Unreal Projects\\Whispers 5.8\\Saved\\IV02</code>: 1,794 indexed files, 11,460,553,184 bytes. They remain in place. The selected review copies were checked against that index; this publication did not rerun Unreal tests or rehash all 11.46 GB.</p><p>To verify the full original set from Whispers: <code>python Content/Python/WhispersTests/IV02/build_evidence_index.py --check</code>. Delivered game revision: <code>fa24414542f9c99693a98b399f3ded5ffac5eb72</code>, retaining <code>c9b1b16</code> and <code>2b8dcfc</code>. The copied reports and independent review identify their tested inputs.</p></section></main></body></html>'''
REPORT.write_text(html,encoding='utf-8')
registry=REPO/'workspace/workspace.json'
data=json.loads(registry.read_text(encoding='utf-8'))
card=next(e for e in data['entities'] if e['id']=='whispers-eden')
step=next(s for s in card['steps'] if s['path']==REPORT.name)
step['name']='Ivy - Nanite IV02'
card['updated']=max(card.get('updated',''),'2026-10-25')
registry.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'report':str(REPORT),'source_and_evidence_available':True,'raw_evidence_files':manifest['raw_files']}))
