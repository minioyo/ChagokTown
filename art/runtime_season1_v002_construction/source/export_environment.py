"""Non-destructive v004 environment derivation: exact geometry, independently visible roads.

Run with Blender --background --python this_file. Never saves the source .blend.
Road ownership follows the authored route graph, including junctions in other plots' roads.
"""
import bpy
import bmesh
import hashlib
import heapq
import json
import math
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parents[1]
SOURCE = PROJECT / 'art/town_season1_v004_roof_tones/blend/roof_tones_review.blend'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = sha(SOURCE)
access = json.loads((PROJECT / 'art/town_season1_v002_integrated/reports/access.json').read_text())
routes = [r for r in access['routes'] if r.get('level', 3) == 3]

def project(point, route):
    best = (1e10, 0)
    distance = 0
    for a, b in zip(route['points'], route['points'][1:]):
        delta = Vector(b) - Vector(a)
        t = max(0, min(1, (Vector(point) - Vector(a)).dot(delta) / delta.length_squared))
        candidate = ((Vector(point) - Vector(a) - t * delta).length, distance + t * delta.length)
        best = min(best, candidate)
        distance += delta.length
    return best

lengths = [sum(math.dist(a, b) for a, b in zip(r['points'], r['points'][1:])) for r in routes]
cuts = [{0.0, length} for length in lengths]
connections = []
# Arrival joins the spine; each subsequent authored door route ends at the preceding network.
for i in range(1, len(routes)):
    distance, j, param = min((project(routes[i]['points'][-1], r)[0], j,
                              project(routes[i]['points'][-1], r)[1]) for j, r in enumerate(routes[:i]))
    # The rasterized path endpoint meets the *width* of the earlier strip, not necessarily its centre.
    assert distance < (routes[i]['width'] + routes[j]['width']) / 2, (routes[i]['name'], distance)
    if param < .00001:
        param = 0.0
    elif lengths[j] - param < .00001:
        param = lengths[j]
    cuts[j].add(param)
    connections.append((i, j, param, distance))
cuts = [sorted(c) for c in cuts]
graph = defaultdict(list)
def edge(a, b, length, key):
    graph[a].append((b, length, key))
    graph[b].append((a, length, key))
for i, cc in enumerate(cuts):
    for j in range(len(cc) - 1):
        edge((i, j), (i, j + 1), cc[j + 1] - cc[j], (i, j))
for i, j, param, distance in connections:
    edge((i, len(cuts[i]) - 1), (j, cuts[j].index(param)), distance, None)
origin = (1, 0)  # south end of Village arrival
cost = {origin: 0}
previous = {}
queue = [(0, origin)]
while queue:
    distance, node = heapq.heappop(queue)
    if distance != cost[node]:
        continue
    for nxt, length, key in graph[node]:
        new = distance + length
        if new < cost.get(nxt, 1e10):
            cost[nxt] = new
            previous[nxt] = (node, key)
            heapq.heappush(queue, (new, nxt))
owners = defaultdict(set)
for i in range(2, len(routes)):
    plot = routes[i]['name'].split(' L3')[0]
    plot = 'home' if plot == 'home_entry' else plot
    node = (i, 0)
    while node != origin:
        node, key = previous[node]
        if key is not None:
            owners[key].add(plot)
assert all(owners[i, j] for i, cc in enumerate(cuts) for j in range(len(cc) - 1)), [
    (routes[i]['name'], cc[j], cc[j+1]) for i, cc in enumerate(cuts) for j in range(len(cc)-1) if not owners[i,j]]

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.data.scenes['AFTER roof tones • final']
bpy.context.window.scene = scene
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
source_objects = [o for o in scene.objects if o.type == 'MESH' and not o.hide_render and not o.get('plot_id')]
target = bpy.data.scenes.new('Runtime construction environment')
groups = defaultdict(list)
report = {'sourceSha256': before, 'sourceScene': scene.name, 'roads': [], 'objects': []}
route_ids = {r['name']: i for i, r in enumerate(routes)}
expected = []

def triangles(obj):
    obj.data.calc_loop_triangles()
    return [tuple(sorted(tuple(round(c, 4) for c in obj.matrix_world @ obj.data.vertices[i].co)
                         for i in t.vertices)) for t in obj.data.loop_triangles]

for obj in source_objects:
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    copy = bpy.data.objects.new(obj.name, mesh)
    target.collection.objects.link(copy)
    copy.matrix_world = obj.matrix_world.copy()
    expected.extend(triangles(copy))
    name = obj.name
    face_groups = defaultdict(set)
    for face in mesh.polygons:
        if name.startswith('Shared alley • '):
            ri = route_ids[name.removeprefix('Shared alley • ')]
            _, param = project((obj.matrix_world @ face.center)[:2], routes[ri])
            interval = min(len(cuts[ri]) - 2, bisect_right(cuts[ri], param) - 1)
            visible_for = tuple(sorted(owners[ri, interval]))
        elif name == 'Shared court • cathedral' or name.startswith('Upper court • shallow stair tread'):
            visible_for = ('cathedral', 'home_upper_east', 'town_hall')
        elif name == 'Shared court • market':
            visible_for = tuple(sorted({'cafe', 'bookshop', 'florist', 'inn', 'grocer', 'farmstead',
                                        'home_upper_west', 'cathedral', 'town_hall', 'home_upper_east'}))
        else:
            visible_for = ()
        face_groups[visible_for].add(face.index)
    for visible_for, indices in face_groups.items():
        part = mesh.copy()
        bm = bmesh.new()
        bm.from_mesh(part)
        bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in indices], context='FACES')
        bm.to_mesh(part)
        bm.free()
        part.update()
        piece = bpy.data.objects.new(name, part)
        target.collection.objects.link(piece)
        piece.matrix_world = obj.matrix_world.copy()
        groups[visible_for, tuple(m.name for m in mesh.materials)].append(piece)
    bpy.data.objects.remove(copy, do_unlink=True)
    report['objects'].append(name)

bpy.context.window.scene = target
for index, ((visible_for, materials), parts) in enumerate(sorted(groups.items())):
    bpy.ops.object.select_all(action='DESELECT')
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    joined = parts[0]
    joined.name = f'Road_{index:02d}' if visible_for else 'Environment - ' + ' + '.join(materials)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if visible_for:
        report['roads'].append({'node': joined.name, 'plots': list(visible_for)})

out = ROOT / 'exports'
out.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(out / 'town_environment.glb'), export_format='GLB',
    use_selection=True, use_active_scene=True, export_cameras=False, export_lights=False,
    export_animations=False, export_extras=False)
verify = bpy.data.scenes.new('Reimport derived GLB')
bpy.context.window.scene = verify
bpy.ops.import_scene.gltf(filepath=str(out / 'town_environment.glb'))
bpy.context.view_layer.update()
actual = [t for o in verify.objects if o.type == 'MESH' for t in triangles(o)]
import numpy as np
assert len(expected) == len(actual)
error = float(np.max(np.abs(np.asarray(sorted(expected)) - np.asarray(sorted(actual)))))
assert error <= .00011, error
assert before == sha(SOURCE)
report.update(triangles=len(actual), meshes=len(groups), sha256=sha(out / 'town_environment.glb'),
              reimportMaxTriangleCoordinateErrorMetres=error,
              graph=[{'route': routes[i]['name'], 'from': cuts[i][j], 'to': cuts[i][j+1], 'plots': sorted(pp)}
                     for (i, j), pp in sorted(owners.items())])
(ROOT / 'reports').mkdir(exist_ok=True)
(ROOT / 'reports/environment.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('VERIFIED', len(actual), 'triangles', len(report['roads']), 'road groups', error, flush=True)
