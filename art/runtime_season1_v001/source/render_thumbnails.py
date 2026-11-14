"""Render transparent UI thumbnails from the exact runtime GLBs in art/runtime_season1_v001 (read-only).

Run: blender -b --factory-startup -P art/runtime_season1_v001/source/render_thumbnails.py
One orthographic camera per family, shared by its three levels, so growth reads at a fixed ground point.
"""
import bpy, hashlib, json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'exports'
OUT = ROOT / 'thumbnails'
OUT.mkdir(parents=True, exist_ok=True)
FAMILIES = ('house', 'cafe', 'cathedral', 'bakery', 'bookshop', 'florist', 'grocer', 'workshop', 'inn', 'town_hall', 'farmstead', 'watermill')
VIEW = Vector((7, -11, 8)).normalized()  # Same oblique direction as the reference renders and the in-app camera.
SIZE = 320

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
device = 'CPU'
for kind in ('OPTIX', 'CUDA'):
    try:
        prefs.compute_device_type = kind
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type != 'CPU']
        if gpus:
            for d in prefs.devices:
                d.use = d.type != 'CPU'
            device = 'GPU'
            break
    except Exception:
        pass
scene.cycles.device = device
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = SIZE
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
if 'AgX' in [x.identifier for x in scene.view_settings.bl_rna.properties['view_transform'].enum_items]:
    scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = .35

world = bpy.data.worlds.new('Warm studio')
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (.65, .72, .78, 1)
bg.inputs['Strength'].default_value = .35
scene.world = world
for name, loc, power, size, color in [('Warm window', (-6, -8, 13), 1800, 8, (1, .86, .72)),
                                       ('Sky fill', (7, -1, 10), 1100, 7, (.77, .87, 1)),
                                       ('Back rim', (0, 7, 10), 1400, 6, (1, .94, .80))]:
    d = bpy.data.lights.new(name, 'AREA'); d.energy = power; d.shape = 'DISK'; d.size = size; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (-o.location).to_track_quat('-Z', 'Y').to_euler()

# No ground or shadow catcher: a clean cut-out reads better at list-icon size.

# Runtime look: opaque, metallic 0, roughness about 0.68, colour from COLOR_0.
mat = bpy.data.materials.new('Vertex colour')
mat.use_nodes = True
nodes = mat.node_tree.nodes
bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
bsdf.inputs['Roughness'].default_value = .68
bsdf.inputs['Metallic'].default_value = 0
attr = nodes.new('ShaderNodeVertexColor')
mat.node_tree.links.new(attr.outputs['Color'], bsdf.inputs['Base Color'])

cam_data = bpy.data.cameras.new('Thumb camera'); cam_data.type = 'ORTHO'
cam = bpy.data.objects.new('Thumb camera', cam_data); scene.collection.objects.link(cam); scene.camera = cam


def load(path):
    before = set(scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [o for o in set(scene.objects) - before if o.type == 'MESH']
    assert len(meshes) == 1, path
    o = meshes[0]
    attr.layer_name = o.data.color_attributes[0].name
    o.data.materials.clear(); o.data.materials.append(mat)
    bpy.context.view_layer.update()
    return o, set(scene.objects) - before


def corners(o):
    return [o.matrix_world @ Vector(c) for c in o.bound_box]


report = {'renderer': f'Blender {bpy.app.version_string} Cycles {device}', 'size_px': SIZE, 'models': {}}
for family in FAMILIES:
    # Frame the largest level; reuse the camera for all three.
    top, created = load(SRC / f'{family}_level_3.glb')
    pts = corners(top)
    right = (-VIEW).cross(Vector((0, 0, 1))).normalized()
    up = right.cross(-VIEW).normalized()
    xs = [p.dot(right) for p in pts]; ys = [p.dot(up) for p in pts]
    centre = sum(pts, Vector()) / 8
    centre += right * ((max(xs) + min(xs)) / 2 - centre.dot(right)) + up * ((max(ys) + min(ys)) / 2 - centre.dot(up))
    cam_data.ortho_scale = max(max(xs) - min(xs), max(ys) - min(ys)) * 1.04
    cam.location = centre + VIEW * 40
    cam.rotation_euler = (-VIEW).to_track_quat('-Z', 'Y').to_euler()
    bpy.data.batch_remove(list(created))
    for level in (1, 2, 3):
        src = SRC / f'{family}_level_{level}.glb'
        _, created = load(src)
        scene.render.filepath = str(OUT / f'{family}_level_{level}.png')
        bpy.ops.render.render(write_still=True)
        bpy.data.batch_remove(list(created))
        report['models'][f'{family}_level_{level}'] = {
            'source': f'art/runtime_season1_v001/exports/{src.name}',
            'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
            'output': f'art/runtime_season1_v001/thumbnails/{family}_level_{level}.png',
        }
        print('RENDERED', family, level, flush=True)

(ROOT / 'reports').mkdir(exist_ok=True)
(ROOT / 'reports' / 'render_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

