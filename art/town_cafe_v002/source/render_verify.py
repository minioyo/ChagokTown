"""Reopen source, reimport GLBs, assert budgets and preservation, render review images."""
import bpy, bmesh, json, hashlib, math, os, struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];V1=ROOT.parent/'town_miniature_v001'
preview=os.environ.get('CAFE_PREVIEW')=='1'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/chagok_cafe_upgrades_v002.blend'))
report=json.loads((ROOT/'reports/optimization.json').read_text())
manifest=json.loads((ROOT/'reports/v001_preservation.json').read_text())
assert manifest=={str(p.relative_to(V1)):hashlib.sha256(p.read_bytes()).hexdigest() for p in V1.rglob('*') if p.is_file()}
assert len(bpy.data.scenes)==7
assert not any(o.type=='FONT' for o in bpy.data.objects)
# Closed arch solids need outward winding for single-sided runtime rendering.
for o in bpy.data.objects:
    if o.type=='MESH' and ('arched' in o.name or 'arch' in o.name):
        bm=bmesh.new();bm.from_mesh(o.data)
        if all(e.is_manifold for e in bm.edges):assert bm.calc_volume(signed=True)>0,o.name
        bm.free()
validation={'source_reopened':True,'scene_count':7,'v001_hashes_unchanged':True,'v001_files_checked':len(manifest),'font_objects':0,'models':{}}
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    device='GPU' if any(d.type!='CPU' for d in prefs.devices) else 'CPU'
except Exception:device='CPU'
def render(s,name,w,h):
    bpy.context.window.scene=s
    if s.render.engine=='CYCLES':s.cycles.device=device;s.cycles.samples=24 if preview else 64
    s.render.resolution_x=w;s.render.resolution_y=h
    s.render.filepath=str(ROOT/'renders'/name)
    bpy.ops.render.render(write_still=True)
    print('RENDERED',name,flush=True)
main=bpy.data.scenes['01 • Cafe upgrades']
render(main,'preview_levels.png' if preview else '01_cafe_levels.png',1650 if preview else 2400,850 if preview else 1250)
if preview:raise SystemExit(0)

studio=bpy.data.collections['STUDIO • lighting']
for level in (1,2,3):
    raw=(ROOT/'exports'/f'cafe_level_{level}.glb').read_bytes()
    n=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+n])
    assert all(m.get('alphaMode','OPAQUE')=='OPAQUE' and not m.get('doubleSided',False) for m in gltf['materials'])
    template=bpy.data.scenes['RUNTIME • level %d'%level]
    s=bpy.data.scenes.new('VERIFY • level %d'%level);bpy.context.window.scene=s
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'exports'/f'cafe_level_{level}.glb'))
    objects=list(s.objects);meshes=[o for o in objects if o.type=='MESH']
    assert len(meshes)==1
    o=meshes[0];me=o.data;me.calc_loop_triangles()
    assert len(me.materials)==1 and len(me.loop_triangles)==report['levels'][str(level)]['after']['triangles']
    assert len(me.color_attributes)==1
    assert not o.modifiers
    bpy.context.view_layer.update()
    verts=[o.matrix_world@v.co for v in me.vertices]
    assert all(math.isfinite(c) for v in verts for c in v)
    lo=[min(v[i] for v in verts) for i in range(3)];hi=[max(v[i] for v in verts) for i in range(3)]
    expected=report['levels'][str(level)]['after']
    delta=max(abs(a-b) for a,b in zip(lo+hi,expected['bounds_min']+expected['bounds_max']))
    assert delta<1e-4 and abs(lo[2])<1e-4
    root=next(o for o in objects if o.type=='EMPTY' and o.get('asset_id'))
    assert root.location.length<1e-4 and all(abs(x-1)<1e-4 for x in root.scale)
    # Verify color variety survived actual glTF import, not just attribute presence.
    colors={tuple(round(x,3) for x in c.color[:3]) for c in me.color_attributes[0].data}
    assert len(colors)>=10
    validation['models'][str(level)]={'reimport_passed':True,'mesh_objects':1,'materials':1,'triangles':len(me.loop_triangles),'vertex_color_count':len(colors),'bounds_max_error_m':delta,'ground_error_m':abs(lo[2]),'root_location':list(root.location),'dimensions_m':[hi[i]-lo[i] for i in range(3)]}
    # This collection contains only the actual imported runtime model for comparison.
    imp=bpy.data.collections.new('IMPORTED • level %d'%level);s.collection.children.link(imp)
    for obj in objects:
        for c in list(obj.users_collection):c.objects.unlink(obj)
        imp.objects.link(obj)
    s.collection.children.link(studio);s.world=template.world
    cam=template.camera.copy();cam.data=cam.data.copy();s.collection.objects.link(cam);s.camera=cam
    s.render.engine=template.render.engine;s.cycles.use_denoising=True
    s.view_settings.view_transform=template.view_settings.view_transform;s.view_settings.exposure=.35
    s.render.image_settings.file_format='PNG'
    render(s,f'cafe_level_{level}.png',1200,1200)
    if level==3:
        # A reverse angle confirms the model is complete away from the hero view.
        cam.location=(-8,11,7);cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler()
        render(s,'04_level_3_back.png',1200,1200)

# Comparison uses the same level-3 design and identical light/material response.
s=main.copy();s.name='VERIFY • same-design optimization';bpy.context.window.scene=s
for c in list(s.collection.children):
    if c!=studio:s.collection.children.unlink(c)
for old in list(s.collection.objects):s.collection.objects.unlink(old)
for col,x,name in [(bpy.data.collections['EDIT • cafe level 3'],-2.9,'Before'),(bpy.data.collections['IMPORTED • level 3'],2.9,'After')]:
    o=bpy.data.objects.new(name,None);s.collection.objects.link(o)
    o.instance_type='COLLECTION';o.instance_collection=col;o.location=Vector((22,6,0)).normalized()*x
cam=main.camera.copy();cam.data=cam.data.copy();s.collection.objects.link(cam);s.camera=cam
cam.location=(6,-22,13);cam.rotation_euler=(Vector((0,-.2,2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=12.2
render(s,'02_before_after_level_3.png',2000,1250)
validation['all_passed']=True
(ROOT/'reports/validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
print('VALIDATION_COMPLETE',json.dumps(validation),flush=True)
