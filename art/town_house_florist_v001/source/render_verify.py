"""Render the actual exports and verify normals, palette, pivots, bounds and preservation."""
import bpy, json, hashlib, struct, math, os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
PREVIEW=os.environ.get('TOWN_SET_PREVIEW')=='1'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/chagok_house_florist_v001.blend'))
stats=json.loads((ROOT/'reports/model_stats.json').read_text())
old=json.loads((ROOT/'reports/previous_versions_sha256.json').read_text())
assert all((ROOT.parent/p).exists() and hashlib.sha256((ROOT.parent/p).read_bytes()).hexdigest()==h for p,h in old.items())
assert len(bpy.data.scenes)==15
assert not any(o.type=='FONT' or 'shadow recess' in o.name for o in bpy.data.objects)
report={'blend_reopened':True,'source_scenes':15,'previous_files_unchanged':len(old),'font_objects':0,'brown_window_backings':0,'models':{}}
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    device='GPU' if any(d.type!='CPU' for d in prefs.devices) else 'CPU'
except Exception:device='CPU'
def render(s,name,w,h):
    bpy.context.window.scene=s
    if s.render.engine=='CYCLES':s.cycles.device=device;s.cycles.samples=24 if PREVIEW else 64
    s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(ROOT/'renders'/name)
    bpy.ops.render.render(write_still=True);print('RENDERED',name,flush=True)
rows=[('01 • House upgrades','01_house_levels.png'),('02 • Florist upgrades','02_florist_levels.png'),('03 • Neighborhood style','03_style_with_cafe_v003.png')]
for s,name in rows:render(bpy.data.scenes[s],('preview_'+name) if PREVIEW else name,1650 if PREVIEW else 2400,860 if PREVIEW else 1250)
if PREVIEW:raise SystemExit(0)

def triangle_signature(o):
    me=o.data;me.calc_loop_triangles()
    points=[tuple(round(x,5) for x in o.matrix_world@v.co) for v in me.vertices]
    out=[]
    for t in me.loop_triangles:
        abc=tuple(points[i] for i in t.vertices)
        # Cyclic rotations retain face orientation; reversing the face does not.
        out.append(min(abc,abc[1:]+abc[:1],abc[2:]+abc[:2]))
    return sorted(out)
def colors(o):return {tuple(round(x,3) for x in c.color) for c in o.data.color_attributes[0].data}
studio=bpy.data.collections['STUDIO • lighting']
for key,entry in stats['models'].items():
    path=ROOT/'exports'/f'{key}.glb';raw=path.read_bytes()
    magic,version,length=struct.unpack_from('<4sII',raw,0)
    assert magic==b'glTF' and version==2 and length==len(raw)
    n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n])
    assert len(j['meshes'])==1 and len(j['meshes'][0]['primitives'])==1 and len(j['materials'])==1
    assert j['materials'][0].get('alphaMode','OPAQUE')=='OPAQUE' and not j['materials'][0].get('doubleSided',False)
    assert not j.get('images') and not j.get('textures') and not j.get('cameras') and not j.get('animations')
    primitive=j['meshes'][0]['primitives'][0]
    assert 'COLOR_0' in primitive['attributes'] and 'NORMAL' in primitive['attributes']
    source=bpy.data.scenes['RUNTIME • '+key]
    bpy.context.window.scene=source;bpy.context.view_layer.update()
    original=next(o for o in bpy.data.collections['LOW • '+key].objects if o.type=='MESH')
    source_triangles=triangle_signature(original);source_colors=colors(original)
    s=bpy.data.scenes.new('VERIFY • '+key);bpy.context.window.scene=s
    bpy.ops.import_scene.gltf(filepath=str(path));bpy.context.view_layer.update()
    model_meshes=[o for o in s.objects if o.type=='MESH'];assert len(model_meshes)==1
    o=model_meshes[0];me=o.data;me.calc_loop_triangles()
    assert len(me.materials)==1 and len(me.color_attributes)==1
    assert len(me.loop_triangles)==entry['runtime']['triangles']
    assert all(t.area>1e-12 for t in me.loop_triangles),'Degenerate imported triangle: '+key
    assert triangle_signature(o)==source_triangles,'Triangle coordinates/winding changed: '+key
    assert colors(o)==source_colors,'Vertex palette changed: '+key
    pts=[o.matrix_world@v.co for v in me.vertices]
    assert all(math.isfinite(c) for p in pts for c in p)
    assert all(math.isfinite(c) for n in me.corner_normals for c in n.vector)
    assert all(abs(n.vector.length-1)<.001 for n in me.corner_normals)
    lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
    err=max(abs(a-b) for a,b in zip(lo+hi,entry['runtime']['bounds_min']+entry['runtime']['bounds_max']))
    assert err<1e-5 and abs(lo[2])<1e-5
    assert lo[0]>=-2.4 and lo[1]>=-3.2 and hi[0]<=2.4 and hi[1]<=1.6
    parent=next(o for o in s.objects if o.type=='EMPTY' and o.get('asset_id')==key)
    assert parent.location.length<1e-5 and all(abs(x-1)<1e-5 for x in parent.scale)
    assert entry['runtime']['triangles']<=entry['initial_triangle_target']
    report['models'][key]={'reimport_passed':True,'triangles':len(me.loop_triangles),'mesh_objects':1,'materials':1,'primitives':1,'vertex_colors':len(source_colors),
       'palette_matches_source':True,'triangle_winding_matches_source':True,'normals_finite_and_unit':True,'degenerate_triangles':0,
       'source_outward_closed_components':entry['runtime_source_normals']['closed_outward_components'],
       'bounds_error_m':err,'ground_error_m':abs(lo[2]),'common_lot_passed':True,'root_location':list(parent.location),'dimensions_m':[hi[i]-lo[i] for i in range(3)],'glb_bytes':len(raw)}
    s.collection.children.link(studio);s.world=source.world
    cam=source.camera.copy();cam.data=cam.data.copy();s.collection.objects.link(cam);s.camera=cam
    s.render.engine=source.render.engine;s.cycles.use_denoising=True
    s.view_settings.view_transform=source.view_settings.view_transform;s.view_settings.exposure=.35;s.render.image_settings.file_format='PNG'
    render(s,key+'.png',1200,1200)
    if key.endswith('_3'):
        cam.location=(-8,11,7);cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler()
        render(s,key+'_back.png',1200,1200)
assert all(hashlib.sha256((ROOT.parent/p).read_bytes()).hexdigest()==h for p,h in old.items())
report['all_passed']=True
(ROOT/'reports/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('VALIDATION_COMPLETE',json.dumps(report),flush=True)
