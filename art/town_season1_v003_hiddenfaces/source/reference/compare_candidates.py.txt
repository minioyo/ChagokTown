"""Render audit variants and measure terrain reduction without saving production blend."""
from pathlib import Path
import bpy, json, math, hashlib, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path(__file__).resolve().parent;ART=OUT.parents[2]/'art'
source=ART/'town_season1_v002_integrated/blend/integrated_village.blend'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
s=bpy.data.scenes['INTEGRATED • final'];bpy.context.window.scene=s
s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True
s.render.resolution_x=1440;s.render.resolution_y=900;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    s.cycles.device='GPU' if any(d.type!='CPU' for d in prefs.devices) else 'CPU'
except Exception:s.cycles.device='CPU'

def render(name):
    if (OUT/(name+'.png')).exists():
        print('REUSED_UNCHANGED_RENDER',name,flush=True);return
    bpy.context.window.scene=s;s.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True);print('RENDERED',name,flush=True)

render('01_original')
imports=bpy.data.scenes.new('AUDIT imports');collections={};checks={}
manifest=json.loads((ART/'town_season1_v002_integrated/reports/manifest.json').read_text())
original_collections={}
for entry in manifest['assets']:
    if entry['level']!=3:continue
    bpy.context.window.scene=imports
    bpy.ops.import_scene.gltf(filepath=str(ART/entry['path']));bpy.context.view_layer.update()
    coll=bpy.data.collections.new('AUDIT original '+entry['type'])
    for o in list(bpy.context.selected_objects):
        for c in list(o.users_collection):c.objects.unlink(o)
        coll.objects.link(o)
    original_collections[entry['type']]=coll
bpy.context.window.scene=s
for o in s.objects:
    if o.instance_type=='COLLECTION' and o.get('kind') in original_collections:
        o.instance_collection=original_collections[o['kind']]
bpy.context.view_layer.update()
render('01b_original_glbs_reimported')
for path in sorted((OUT/'hidden_face_candidates').glob('*.glb')):
    bpy.context.window.scene=imports
    bpy.ops.import_scene.gltf(filepath=str(path));bpy.context.view_layer.update()
    objs=list(bpy.context.selected_objects);coll=bpy.data.collections.new('AUDIT '+path.stem)
    for o in objs:
        for c in list(o.users_collection):c.objects.unlink(o)
        coll.objects.link(o)
    meshes=[o for o in objs if o.type=='MESH'];assert len(meshes)==1
    me=meshes[0].data;me.calc_loop_triangles()
    assert len(me.color_attributes)==1 and all(t.area>1e-12 for t in me.loop_triangles)
    assert all(math.isfinite(c) for n in me.corner_normals for c in n.vector)
    assert all(abs(n.vector.length-1)<.001 for n in me.corner_normals)
    checks[path.stem]={'reimport_passed':True,'triangles':len(me.loop_triangles),'color_attributes':1,
                       'finite_unit_normals':True,'degenerate_triangles':0}
    collections[path.stem.removesuffix('_level_3')]=coll
bpy.context.window.scene=s
for o in s.objects:
    if o.instance_type=='COLLECTION' and o.get('kind') in collections:
        o.instance_collection=collections[o['kind']]
bpy.context.view_layer.update()
render('02_hidden_faces_removed')

terrain=s.objects['Integrated • continuous terrain']
dg=bpy.context.evaluated_depsgraph_get();evaluated=terrain.evaluated_get(dg);base=evaluated.to_mesh();base.calc_loop_triangles()
coords=[v.co.copy() for v in base.vertices]
sample_points=coords+[sum((base.vertices[i].co for i in t.vertices),Vector())/3 for t in base.loop_triangles]
original_triangles=len(base.loop_triangles)
original_bvh=BVHTree.FromPolygons(coords,[tuple(t.vertices) for t in base.loop_triangles],all_triangles=True)
evaluated.to_mesh_clear()
reference_points=[];reference_misses=0
for point in sample_points:
    hit=original_bvh.ray_cast(Vector((point.x,point.y,50)),Vector((0,0,-1)),100)[0]
    if hit is None:reference_misses+=1
    else:reference_points.append(hit)
mod=terrain.modifiers.new('AUDIT terrain simplification','DECIMATE');mod.decimate_type='COLLAPSE'
terrain_results={}
for ratio in (.5,.25,.1):
    mod.ratio=ratio;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    e=terrain.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles()
    bvh=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[tuple(t.vertices) for t in me.loop_triangles],all_triangles=True)
    errors=[];misses=0
    for point in reference_points:
        hit=bvh.ray_cast(Vector((point.x,point.y,50)),Vector((0,0,-1)),100)[0]
        if hit is None:misses+=1
        else:errors.append(hit.z-point.z)
    absolute=sorted(abs(x) for x in errors)
    terrain_results[str(ratio)]={'before_triangles':original_triangles,'after_triangles':len(me.loop_triangles),
                                'sample_count':len(reference_points),'reference_ray_misses':reference_misses,'ray_misses':misses,
                                'max_abs_height_error_m':max(absolute),'p99_abs_height_error_m':absolute[int(.99*(len(absolute)-1))],
                                'max_upward_height_error_m':max(errors),'max_downward_height_error_m':min(errors)}
    e.to_mesh_clear();print('TERRAIN',ratio,terrain_results[str(ratio)],flush=True)
mod.ratio=.25;bpy.context.view_layer.update()
render('03_hidden_faces_and_quarter_terrain')
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
pixel_metrics={}
for before,after in [('01_original','01b_original_glbs_reimported'),('01b_original_glbs_reimported','02_hidden_faces_removed'),('02_hidden_faces_removed','03_hidden_faces_and_quarter_terrain')]:
    aa=bpy.data.images.load(str(OUT/(before+'.png')),check_existing=False)
    bb=bpy.data.images.load(str(OUT/(after+'.png')),check_existing=False)
    a=np.empty(len(aa.pixels),dtype=np.float32);b=np.empty(len(bb.pixels),dtype=np.float32)
    aa.pixels.foreach_get(a);bb.pixels.foreach_get(b)
    diff=np.abs(a.reshape(-1,4)[:,:3]-b.reshape(-1,4)[:,:3])
    pixel_metrics[before+' -> '+after]={'mean_linear_rgb_abs_error':float(diff.mean()),
        'percent_pixels_with_any_channel_difference_over_0_01':float(np.mean(np.max(diff,axis=1)>.01)*100)}
    bpy.data.images.remove(aa);bpy.data.images.remove(bb)
(OUT/'comparison.json').write_text(json.dumps({'source_blend_unchanged':True,'candidate_glb_checks':checks,
                                             'terrain_trials':terrain_results,'terrain_render_ratio':.25,
                                             'render_resolution':[1440,900],'render_samples':64,
                                             'pixel_differences':pixel_metrics,
                                             'limits':'Visual candidate and sampled height checks; all-stage and runtime performance untested.'},indent=2),encoding='utf-8')
print('COMPARISON_COMPLETE',flush=True)
