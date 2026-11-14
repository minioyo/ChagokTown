"""Host-side preservation, routing and APK checks. Does not rewrite any asset."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / 'art/town_season1_v004_roof_tones/source'))
import glb

layout = json.loads((PROJECT / 'android/app/src/main/assets/layout/season1_town.json').read_text(encoding='utf-8'))
report = json.loads((ROOT / 'reports/environment.json').read_text(encoding='utf-8'))
old_layout = json.loads((PROJECT / 'art/runtime_season1_v001/layout.json').read_text(encoding='utf-8'))
assert layout['plots'] == old_layout['plots']
assert layout['camera'] == old_layout['camera']
assert layout['roads'] == report['roads']
assert glb.sha(PROJECT / 'art/town_season1_v004_roof_tones/blend/roof_tones_review.blend') == report['sourceSha256']
manifest = json.loads((PROJECT / 'art/runtime_season1_v001/reports/manifest.json').read_text(encoding='utf-8'))
for asset in manifest['buildings']:
    assert glb.sha(PROJECT / 'android/app/src/main/assets' / asset['path']) == asset['sha256']

# Compare full material definitions and every triangle's position/normal/UV/colour from the actual GLBs.
# Nodes in both environment files are already baked into world coordinates.
def appearance(path):
    doc, blob, _ = glb.read(path)
    assert not doc.get('textures') and not doc.get('animations')
    result = Counter()
    for node in doc['nodes']:
        assert not any(k in node for k in ('matrix', 'translation', 'rotation', 'scale'))
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            material = json.dumps(doc['materials'][primitive['material']], sort_keys=True)
            attributes = sorted(primitive['attributes'])
            arrays = [glb.accessor(doc, blob, primitive['attributes'][key]) for key in attributes]
            indices = [v[0] for v in glb.accessor(doc, blob, primitive['indices'])]
            for i in range(0, len(indices), 3):
                vertices = tuple(sorted(tuple(round(x, 4) for a in arrays for x in a[index]) for index in indices[i:i+3]))
                result[material, tuple(attributes), vertices] += 1
    return result

old = PROJECT / 'art/runtime_season1_v001/exports/town_environment.glb'  # byte-identical to the copy the app used to ship
new = ROOT / 'exports/town_environment.glb'
a, b = appearance(old), appearance(new)
assert a == b, ('Appearance changed', sum((a-b).values()), sum((b-a).values()))

plots = {p['id'] for p in layout['plots']}
visible = lambda built: {r['node'] for r in layout['roads'] if set(r['plots']) & built}
assert not visible(set())
assert len(visible({'home'})) < len(layout['roads'])
assert len(visible(plots)) == len(layout['roads'])
for parent, child in [('bookshop', 'florist'), ('bakery', 'watermill'), ('home_upper_west', 'farmstead'), ('grocer', 'home_upper_west')]:
    rows = [r for r in report['graph'] if r['route'] == parent + ' L3 door']
    assert any(child in r['plots'] for r in rows)
    assert any(r['plots'] == [parent] for r in rows), (parent, 'private door segment')
    assert visible({parent}) | visible({child}) == visible({parent, child})

apks = []
for flavor in ['demo', 'vehicle']:
    path = PROJECT / f'android/app/build/outputs/apk/{flavor}/debug/app-{flavor}-debug.apk'
    with zipfile.ZipFile(path) as apk:
        for asset in [layout['environmentModel'], 'layout/season1_town.json'] + [p for x in layout['plots'] for p in x['models']]:
            assert apk.read('assets/' + asset) == (PROJECT / 'android/app/src/main/assets' / asset).read_bytes()
        assert not any('v005' in name or 'runtime_samples' in name for name in apk.namelist())
    apks.append(str(path.relative_to(PROJECT)))
result = {'protectedBuildings': len(manifest['buildings']), 'sourceBlendSha256': report['sourceSha256'],
          'allTrianglesAndAppearancePreserved': True, 'appearanceComparisonPrecision': '0.0001',
          'cameraPlotsTransformsAndCostsPreserved': True, 'roadGroups': len(layout['roads']),
          'initialHomeRoadGroups': len(visible({'home'})), 'allRoadGroups': len(visible(plots)),
          'environmentTriangles': report['triangles'], 'environmentMeshes': report['meshes'],
          'apkAssetBytesVerified': apks}
(ROOT / 'reports/verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
