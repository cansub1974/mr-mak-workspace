"""Copy verified IV02 deliverables/evidence into Workspace, without changing source assets."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess
import zipfile

TASK = Path(__file__).resolve().parent
GAME = Path('D:/Unreal Projects/Whispers 5.8')
SOURCE = GAME / 'SourceAssets/HotelEden/IV02'
RAW = GAME / 'Saved/IV02'
DEST = TASK / 'evidence/unreal'
DEST.mkdir(parents=True, exist_ok=True)
(TASK / 'downloads').mkdir(exist_ok=True)
index = json.loads((RAW / 'evidence_index.json').read_text(encoding='utf-8'))
indexed = {r['path'].replace('\\', '/'): r for r in index['rows']}
copies = []

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def copy(src, dst, indexed_raw=False):
    sha = digest(src)
    if indexed_raw:
        row = indexed[src.relative_to(GAME).as_posix()]
        assert row['bytes'] == src.stat().st_size and row['sha256'] == sha, src
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    assert digest(dst) == sha
    copies.append({'source':str(src), 'workspace':dst.relative_to(TASK).as_posix(),
                   'bytes':dst.stat().st_size, 'sha256':sha, 'matches_original_index':indexed_raw})

for filename in ['IV02_Ivy_Prototype.blend', 'exports/SM_Ivy_WallPatch_Prototype.fbx']:
    copy(SOURCE / filename, TASK / 'downloads' / Path(filename).name)
original = Path('D:/AI_Modelling/hotel_eden/working/ivy_IV02/IV02_Ivy_Prototype.blend')
assert digest(original) == digest(SOURCE / 'IV02_Ivy_Prototype.blend')
archive = TASK / 'downloads/IV02-Ivy-Editable-Source.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in [SOURCE / 'IV02_Ivy_Prototype.blend', SOURCE / 'exports/SM_Ivy_WallPatch_Prototype.fbx',
              *sorted((SOURCE / 'textures').glob('*')), *sorted((SOURCE / 'scripts').glob('*.py'))]:
        if p.is_file():
            z.write(p, p.relative_to(SOURCE).as_posix())

for p in sorted((RAW / 'runs/visual/sheets').glob('*.jpg')):
    copy(p, DEST / 'sheets' / p.name, True)
for p in sorted((RAW / 'runs/visual/shots').glob('visual__cfgB_front_DL__*.png')):
    copy(p, DEST / 'shots' / p.name, True)
for p in sorted((RAW / 'analysis/temporal_review').glob('*')):
    if p.is_file():
        copy(p, DEST / 'temporal' / p.name, True)
for relative in ['cfgA_dense_nanite_overdraw.png', 'cfgB_dense_nanite_overdraw.png',
                 'cfgD_dense_nanite_overdraw.png', 'cfgD_dense_vsm_vpage.png']:
    p = RAW / 'evidence/editor_vis' / relative
    if p.exists():
        copy(p, DEST / 'diagnostics' / relative, True)
for relative in ['analysis/summary.json','analysis/summary.md','fixture/placement_manifest.json',
                 'fixture/fixture_state_after_reopen.json','import/compare_import.json',
                 'import/readback.json','analysis/visual_pairs.json','analysis/video_pa.json']:
    copy(RAW / relative, DEST / relative, True)
copy(RAW / 'evidence_index.json', DEST / 'raw-evidence-index.json')
for letter in ['A','B']:
    copy(GAME / f'docs/verification/ivy-IV02-{letter}.md', DEST / f'ivy-IV02-{letter}.md')
copy(GAME / 'docs/features/hotel-eden-ivy-iv02.md', DEST / 'fixture-reproduction.md')

issues = []
for number in [113,114]:
    d = json.loads(subprocess.check_output(['gh','issue','view',str(number),'--repo','cansub1974/Whispers',
         '--json','number,state,labels,comments,url'],text=True,encoding='utf-8'))
    review = next(c for c in reversed(d['comments']) if c['body'].startswith('## Verification'))
    (DEST / f'independent-review-{number}.md').write_text(review['body']+'\n\nSource: '+review['url']+'\n',encoding='utf-8')
    issues.append({'number':number,'state':d['state'],'labels':[x['name'] for x in d['labels']],
                   'url':d['url'],'review_url':review['url'],'review_created':review['createdAt']})
video_source = RAW / 'runs/video_cfgC_PA_side_by_side.mp4'
video_row = indexed[video_source.relative_to(GAME).as_posix()]
assert digest(video_source) == video_row['sha256']
video = DEST / 'route-preserve-area-comparison.mp4'
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-i',str(video_source),
                '-vf','scale=1920:-2','-c:v','libx264','-preset','fast','-crf','24','-an',
                '-movflags','+faststart',str(video)],check=True)
result={'published_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'model_original':str(original),'model_delivery':str(SOURCE / 'IV02_Ivy_Prototype.blend'),
        'model_sha256':digest(original),'source_and_delivery_identical':True,
        'unreal_level':'/Game/Whispers/Tests/HotelEden/IV02/L_IvyPrototype',
        'unreal_mesh':'/Game/Whispers/Presentation/Environment/HotelEden/IV02/Meshes/SM_Ivy_WallPatch_Prototype',
        'raw_root':str(RAW),'raw_files':index['files'],'raw_bytes':index['bytes'],
        'raw_index_sha256':digest(RAW / 'evidence_index.json'),
        'review_video':{'path':video.relative_to(TASK).as_posix(),'bytes':video.stat().st_size,
                        'sha256':digest(video),'original_sha256':video_row['sha256'],
                        'derivative':'1920x540 H.264 CRF24 display proxy; original 3840x1080 MP4 unchanged'},
        'issues':issues,'copied_files':copies,
        'limits':'Copied review subset verified against delivered index. This did not re-run Unreal tests or rehash all 11.46 GB. Video proxy is a separate display derivative; original MP4 remains in Saved/IV02.'}
(DEST / 'publication-manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'model_found':str(original),'sha256':result['model_sha256'],
                  'copied_files':len(copies),'issues':issues,'archive_bytes':archive.stat().st_size}))
