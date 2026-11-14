"""Verify source preservation, runtime references and the APK's actual bundled assets."""
import hashlib
import json
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
ART = ROOT.parent
ASSETS = PROJECT / 'android/app/src/main/assets'
sha = lambda data: hashlib.sha256(data).hexdigest()
source = json.loads((ART / 'town_season1_v004_roof_tones/reports/manifest.json').read_text(encoding='utf-8'))
manifest = json.loads((ROOT / 'reports/manifest.json').read_text(encoding='utf-8'))
layout = json.loads((ASSETS / 'layout/season1_town.json').read_text(encoding='utf-8'))
published = json.loads((ROOT / 'reports/published.json').read_text(encoding='utf-8'))
environment = json.loads((ROOT / 'reports/environment.json').read_text(encoding='utf-8'))
thumbs = json.loads((ROOT / 'reports/render_report.json').read_text(encoding='utf-8'))
assert len(layout['plots']) == 14 and len({p['id'] for p in layout['plots']}) == 14
assert sha((ART / 'town_season1_v004_roof_tones/blend/roof_tones_review.blend').read_bytes()) == environment['sourceSha256']
for entry in source['assets']:
    assert sha((ART / entry['path']).read_bytes()) == entry['sha256']
for entry in manifest['buildings']:
    assert sha((ASSETS / entry['path']).read_bytes()) == entry['sha256']
    assert thumbs['models'][f"{entry['type']}_level_{entry['level']}"]['source_sha256'] == entry['sha256']
for p in layout['plots']:
    original = next(o for o in source['layout'] if o['id'] == p['sourcePlotId'])
    assert [p['x'], p['y'], p['z']] == [original['xy'][0], original['ground'], -original['xy'][1]]
    assert p['rotationY'] == original['yaw'] and original['scale'] == 1.0
    assert p['models'] == [f"models/season1_v001/{original['kind']}_level_{level}.glb" for level in (1, 2, 3)]
env_data = (ROOT / 'exports/town_environment.glb').read_bytes()
json_length = struct.unpack_from('<I', env_data, 12)[0]
env_doc = json.loads(env_data[20:20 + json_length])
assert len(env_doc['scenes']) == 1 and len(env_doc['meshes']) == 8
assert not env_doc.get('cameras') and not env_doc.get('animations') and not env_doc.get('textures')
assert all(n.get('name', '').startswith('Environment - ') for n in env_doc['nodes'])
assert all(m.get('alphaMode', 'OPAQUE') == 'OPAQUE' for m in env_doc['materials'])
apk_results = []
for flavor in ('demo', 'vehicle'):
    path = PROJECT / f'android/app/build/outputs/apk/{flavor}/debug/app-{flavor}-debug.apk'
    with zipfile.ZipFile(path) as apk:
        for entry in published:
            assert sha(apk.read('assets/' + entry['path'])) == entry['sha256']
        models = [n for n in apk.namelist() if n.startswith('assets/models/') and n.endswith('.glb')]
        thumbnails = [n for n in apk.namelist() if n.startswith('assets/thumbnails/') and n.endswith('.png')]
        assert len(models) == 37 and len(thumbnails) == 36
        assert not any('runtime_samples_v001' in n or 'riverbank' in n for n in apk.namelist())
        apk_results.append({'flavor': flavor, 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes()),
                            'models': len(models), 'thumbnails': len(thumbnails), 'all74PublishedFilesMatch': True})
by_path = {b['path']: b for b in manifest['buildings']}
stages = {str(level): {'buildingTriangles': sum(by_path[p['models'][level - 1]]['triangles'] for p in layout['plots']),
                      'environmentTriangles': environment['triangles']} for level in (1, 2, 3)}
for s in stages.values():
    s['totalTriangles'] = s['buildingTriangles'] + s['environmentTriangles']
result = {'source36GlbsAndBlendUnchanged': True, 'plotsMatchApprovedCoordinates': True,
          'thumbnailsUseExactRuntimeInputs': True, 'stageCounts': stages,
          'runtimeFilesBytes': sum(p['bytes'] for p in published), 'apk': apk_results}
(ROOT / 'reports/verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
