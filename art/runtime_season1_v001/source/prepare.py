"""Freeze the approved v004 buildings and adapt its placements to Android Y-up.

Run with Blender's Python (mathutils is used to read exact GLB node transforms).
Historical art is read-only. Run export_environment.py before this script.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT.parent
sys.path.insert(0, str(ART / 'town_season1_v004_roof_tones/source'))
import glb

OUT = ROOT / 'exports'
OUT.mkdir(parents=True, exist_ok=True)
source = json.loads((ART / 'town_season1_v004_roof_tones/reports/manifest.json').read_text(encoding='utf-8'))
names = {'home': '작은 집', 'cafe': '골목 카페', 'cathedral': '언덕 성당',
         'inn': '마을 여관', 'home_upper_west': '언덕 서쪽 집', 'home_upper_east': '언덕 동쪽 집',
         'town_hall': '마을 회관', 'bookshop': '골목 책방', 'bakery': '빵집', 'florist': '꽃가게',
         'grocer': '식료품점', 'workshop': '공방', 'farmstead': '농가', 'watermill': '물레방앗간'}
copied = []
bounds = {}
for asset in source['assets']:
    path = ART / asset['path']
    assert glb.sha(path) == asset['sha256'], path
    dest = OUT / f"{asset['type']}_level_{asset['level']}.glb"
    shutil.copyfile(path, dest)
    doc, blob, _ = glb.read(dest)
    p = glb.primitive(doc)
    # glb.blender_points evaluates the file's node hierarchy, then converts Y-up to Z-up.
    points = glb.blender_points(doc, glb.accessor(doc, blob, p['attributes']['POSITION']))
    bounds[asset['type'], asset['level']] = (points.min(axis=0), points.max(axis=0))
    copied.append({'type': asset['type'], 'level': asset['level'], 'source': asset['path'],
                   'path': f'models/season1_v001/{dest.name}', 'sha256': glb.sha(dest),
                   'triangles': doc['accessors'][p['indices']]['count'] // 3,
                   'vertices': doc['accessors'][p['attributes']['POSITION']]['count']})

plots = []
for placement in source['layout']:
    kind = placement['kind']
    plot_id = 'home' if placement['id'] == 'home_entry' else placement['id']
    low, high = bounds[kind, 3]
    # Mark only empty/selected plots; this small marker stays inside the existing frontage.
    width = min(float(high[0] - low[0]) * .65, 3.2)
    depth = min(float(high[1] - low[1]) * .65, 3.2)
    plots.append({'id': plot_id, 'sourcePlotId': placement['id'], 'name': names[plot_id],
                  'models': [f'models/season1_v001/{kind}_level_{level}.glb' for level in (1, 2, 3)],
                  'costs': [6, 6, 9] if kind in ('cathedral', 'inn', 'watermill') else [3, 3, 6],
                  'x': placement['xy'][0], 'y': placement['ground'], 'z': -placement['xy'][1],
                  'rotationY': placement['yaw'], 'width': width, 'depth': depth,
                  'padOffsetX': float((low[0] + high[0]) / 2),
                  'padOffsetZ': float(-(low[1] + high[1]) / 2)})
# Keep the existing three entries first so the updated panel and saved flow remain familiar.
order = ['home', 'cafe', 'cathedral', 'bakery', 'bookshop', 'florist', 'grocer', 'workshop',
         'inn', 'town_hall', 'farmstead', 'watermill', 'home_upper_west', 'home_upper_east']
plots.sort(key=lambda p: order.index(p['id']))
layout = {'version': 'season1-v004-runtime-v001', 'costsAreTemporaryDemoValues': True,
          'environmentModel': 'models/season1_v001/town_environment.glb',
          'camera': {'target': [1.8, 6.9, 1.6], 'offset': [24.5, 28.0, 35.0], 'verticalSpan': 40.0},
          'plots': plots}
(ROOT / 'layout.json').write_text(json.dumps(layout, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
report = {'source': 'town_season1_v004_roof_tones', 'excluded': 'town_season1_v005_riverbank',
          'buildings': copied, 'plots': len(plots), 'types': len({a['type'] for a in copied}),
          'saveIdsPreserved': ['home', 'cafe', 'cathedral'], 'homeSourcePlotId': 'home_entry',
          'environmentSha256': glb.sha(OUT / 'town_environment.glb'),
          'buildingsTotalBytes': sum((OUT / Path(a['path']).name).stat().st_size for a in copied)}
(ROOT / 'reports').mkdir(exist_ok=True)
(ROOT / 'reports/manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PREPARED', len(copied), 'buildings;', len(plots), 'plots', flush=True)
