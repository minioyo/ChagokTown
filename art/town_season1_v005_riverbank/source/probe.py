"""Read-only inspection of the v004 source scene."""
import bpy, json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT.parent
bpy.ops.wm.open_mainfile(filepath=str(ART/'town_season1_v004_roof_tones/blend/roof_tones_review.blend'))
scene = bpy.data.scenes['AFTER roof tones • final']
bpy.context.window.scene = scene
bpy.context.view_layer.update()
objects = []
for o in scene.objects:
    row = {'name': o.name, 'type': o.type, 'location': list(o.location)}
    if o.type == 'MESH':
        row.update(vertices=len(o.data.vertices), materials=[m.name for m in o.data.materials],
                   bounds=[[min((o.matrix_world@v.co)[a] for v in o.data.vertices), max((o.matrix_world@v.co)[a] for v in o.data.vertices)] for a in range(3)])
    if o.get('plot_id'):
        row['plot_id'] = o['plot_id']
    objects.append(row)
terrain = scene.objects['Integrated • continuous terrain']
terrain.data.calc_loop_triangles()
bvh = BVHTree.FromPolygons([terrain.matrix_world@v.co for v in terrain.data.vertices], [t.vertices[:] for t in terrain.data.loop_triangles], all_triangles=True)
heights = []
for y in (-15,-11,-8,-4,0,4,8,12,16):
    row = {'y':y,'samples':[]}
    for i in range(21):
        x = 13+i*.2
        hit = bvh.ray_cast(Vector((x,y,20)), Vector((0,0,-1)), 40)[0]
        row['samples'].append([round(x,3), round(hit.z,4)])
    heights.append(row)
water = scene.objects['Stream • continuous water']
report = {'scenes':[s.name for s in bpy.data.scenes], 'objects':objects,
          'camera': {'location':list(scene.camera.location),'rotation':list(scene.camera.rotation_euler),'scale':scene.camera.data.ortho_scale},
          'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],
          'water_first_vertices':[list(v.co) for v in list(water.data.vertices)[:15]],
          'terrain_heights':heights,
          'materials':{m.name:list(m.diffuse_color) for m in bpy.data.materials if m.name in ['Grass','Stone','Leaf','Leaf light','Sage'] or 'grass' in m.name.lower() or 'stone' in m.name.lower() or 'leaf' in m.name.lower()}}
(ROOT/'reports/probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PROBE_COMPLETE', flush=True)
