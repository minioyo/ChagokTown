"""Copy and hash-check the prepared season pack and matching UI thumbnails."""
import hashlib
import json
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT.parents[1] / 'android/app/src/main/assets'
manifest = json.loads((ROOT / 'reports/manifest.json').read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
files = [(ROOT / 'layout.json', ASSETS / 'layout/season1_town.json')]
for entry in manifest['buildings']:
    source = ROOT / 'exports' / Path(entry['path']).name
    assert sha(source) == entry['sha256']
    files.append((source, ASSETS / entry['path']))
    thumb = ROOT / 'thumbnails' / source.with_suffix('.png').name
    header = thumb.read_bytes()
    assert header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', header[16:24]) == (320, 320)
    files.append((thumb, ASSETS / 'thumbnails/season1_v001' / thumb.name))
environment = ROOT / 'exports/town_environment.glb'
assert sha(environment) == manifest['environmentSha256']
files.append((environment, ASSETS / 'models/season1_v001/town_environment.glb'))
published = []
for source, target in files:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    assert sha(source) == sha(target)
    published.append({'path': str(target.relative_to(ASSETS)).replace('\\', '/'), 'sha256': sha(target), 'bytes': target.stat().st_size})
(ROOT / 'reports/published.json').write_text(json.dumps(published, indent=2) + '\n', encoding='utf-8')
print('PUBLISHED', len(files), 'files;', sum(p['bytes'] for p in published), 'bytes')
