"""IV02: hash every deliverable under the ivy_IV02 root into qa/IV02_file_manifest.json.
Excludes logs/, scratch/, *.blend1 backups and the manifest itself (the delivery set).
  python make_manifest.py <ivy_IV02 root>
"""
import sys, json, hashlib, datetime
from pathlib import Path
ROOT = Path(sys.argv[1])
CAP = 50 * 1024 * 1024
files = []
for p in sorted(ROOT.rglob('*'), key=lambda q: q.relative_to(ROOT).as_posix().lower()):
    rel = p.relative_to(ROOT).as_posix()
    if not p.is_file() or rel.split('/')[0] in ('logs', 'scratch') or p.suffix == '.blend1' or rel == 'qa/IV02_file_manifest.json':
        continue
    data = p.read_bytes()
    files.append({'path': rel, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'over_50MB': len(data) >= CAP})
out = {'root': ROOT.as_posix(), 'generated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'excluded': ['logs/**', 'scratch/**', '*.blend1', 'qa/IV02_file_manifest.json'], 'files': files}
(ROOT / 'qa' / 'IV02_file_manifest.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
print(len(files), sum(f['bytes'] for f in files), [f['path'] for f in files if f['over_50MB']])
