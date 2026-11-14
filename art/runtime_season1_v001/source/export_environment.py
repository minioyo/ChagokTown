"""Export v004 terrain/water/paths/trees unchanged, merged by existing material.

No building instances, v005 riverbank additions, camera or light are exported.
Only evaluated copies are joined; no historical .blend is saved or modified.
"""
import bpy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'town_season1_v004_roof_tones/blend/roof_tones_review.blend'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before_sha = sha(SOURCE)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
source_scene = bpy.data.scenes['AFTER roof tones • final']
bpy.context.window.scene = source_scene
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
objects = [o for o in source_scene.objects if o.type == 'MESH' and not o.hide_render and not o.get('plot_id')]
target = bpy.data.scenes.new('Runtime environment export')
groups = {}
report = {'sourceSha256': before_sha, 'sourceScene': source_scene.name, 'objects': []}
expected_triangles = 0
for obj in objects:
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    mesh.calc_loop_triangles()
    expected_triangles += len(mesh.loop_triangles)
    copy = bpy.data.objects.new(obj.name, mesh)
    target.collection.objects.link(copy)
    copy.matrix_world = obj.matrix_world.copy()
    key = tuple(m.name for m in mesh.materials)
    groups.setdefault(key, []).append(copy)
    report['objects'].append({'name': obj.name, 'triangles': len(mesh.loop_triangles), 'materials': key})
bpy.context.window.scene = target
for key, copies in groups.items():
    bpy.ops.object.select_all(action='DESELECT')
    for obj in copies:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.join()
    joined = copies[0]
    joined.name = 'Environment - ' + ' + '.join(key)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
OUT = ROOT / 'exports'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(OUT / 'town_environment.glb'), export_format='GLB',
                          use_selection=True, use_active_scene=True, export_cameras=False, export_lights=False,
                          export_animations=False, export_extras=False)
report['triangles'] = expected_triangles
report['meshes'] = len(groups)
report['sha256'] = sha(OUT / 'town_environment.glb')
assert sha(SOURCE) == before_sha
# Independent reimport: count topology and compare rounded world-space triangle positions.
def triangles(scene):
    result = []
    for obj in scene.objects:
        if obj.type != 'MESH':
            continue
        obj.data.calc_loop_triangles()
        for tri in obj.data.loop_triangles:
            result.append(tuple(sorted(tuple(round(c, 4) for c in obj.matrix_world @ obj.data.vertices[i].co) for i in tri.vertices)))
    return sorted(result)
expected = triangles(target)
verify = bpy.data.scenes.new('Independent runtime reimport')
bpy.context.window.scene = verify
bpy.ops.import_scene.gltf(filepath=str(OUT / 'town_environment.glb'))
bpy.context.view_layer.update()
actual = triangles(verify)
print('TRIANGLE_CHECK', len(actual), expected_triangles, flush=True)
assert len(actual) == expected_triangles
# Axis conversion can alter the last float bit; compare within 0.1 mm.
import numpy as np
error = float(np.max(np.abs(np.asarray(expected) - np.asarray(actual))))
assert error <= .00011, error
report['reimportMaxTriangleCoordinateErrorMetres'] = error
(ROOT / 'reports').mkdir(exist_ok=True)
(ROOT / 'reports/environment.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ENVIRONMENT_COMPLETE', expected_triangles, 'triangles', len(groups), 'meshes', flush=True)
