"""Reopen editable blend, inspect real GLB bytes, reimport and render delivered models."""
import sys, bpy, json, struct, hashlib, math
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
PREVIEW='--preview' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/chagok_sol_bakery_bookshop_v001.blend'))
stats=json.loads((ROOT/'reports/model_stats.json').read_text())
old=json.loads((ROOT/'reports/protected_files_sha256.json').read_text())
def preserve():
    assert all((ROOT.parents[1]/p).is_file() and hashlib.sha256((ROOT.parents[1]/p).read_bytes()).hexdigest()==h for p,h in old.items())
preserve()
assert len(bpy.data.scenes)==15
assert not any(o.type=='FONT' or 'shadow recess' in o.name for o in bpy.data.objects)
report={'blend_reopened':True,'source_scenes':15,'protected_files_unchanged':len(old),
        'font_objects':0,'brown_window_backing_objects':0,'models':{},'renders_use_delivered_glbs':True}
def signature(o):
    me=o.data;me.calc_loop_triangles()
    pts=[tuple(round(c,5) for c in o.matrix_world@v.co) for v in me.vertices]
    out=[]
    for t in me.loop_triangles:
        abc=tuple(pts[i] for i in t.vertices)
        out.append(min(abc,abc[1:]+abc[:1],abc[2:]+abc[:2]))
    return sorted(out)
def palette_colors(o):
    return {tuple(round(c,3) for c in datum.color) for datum in o.data.color_attributes[0].data}
def decoded(j,bin_data,index):
    a=j['accessors'][index];v=j['bufferViews'][a['bufferView']]
    ctype={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']]
    width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    fmt='<'+ctype*width;stride=v.get('byteStride',struct.calcsize(fmt))
    offset=v.get('byteOffset',0)+a.get('byteOffset',0)
    return [struct.unpack_from(fmt,bin_data,offset+i*stride) for i in range(a['count'])]
IMPORTED={};VERIFICATION={}
studio=bpy.data.collections['STUDIO • lighting']
for key,entry in stats['models'].items():
    source=bpy.data.scenes['RUNTIME • '+key];bpy.context.window.scene=source;bpy.context.view_layer.update()
    original=next(o for o in bpy.data.collections['LOW • '+key].objects if o.type=='MESH')
    original_sig=signature(original);original_colors=palette_colors(original)
    raw=(ROOT/'exports'/f'{key}.glb').read_bytes()
    magic,version,length=struct.unpack_from('<4sII',raw,0)
    assert magic==b'glTF' and version==2 and length==len(raw)
    n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);bin_data=raw[28+n:]
    assert len(j['meshes'])==len(j['materials'])==1 and len(j['meshes'][0]['primitives'])==1
    assert not j.get('images') and not j.get('textures') and not j.get('cameras') and not j.get('animations')
    mat=j['materials'][0];pbr=mat['pbrMetallicRoughness']
    assert mat.get('alphaMode','OPAQUE')=='OPAQUE' and not mat.get('doubleSided',False)
    assert pbr.get('metallicFactor',1)==0 and abs(pbr['roughnessFactor']-.68)<1e-5
    primitive=j['meshes'][0]['primitives'][0]
    assert primitive.get('mode',4)==4
    assert 'COLOR_0' in primitive['attributes'] and 'NORMAL' in primitive['attributes']
    normals=decoded(j,bin_data,primitive['attributes']['NORMAL'])
    normal_lengths=[math.sqrt(sum(c*c for c in v)) for v in normals]
    assert all(math.isfinite(c) for v in normals for c in v)
    assert all(abs(v-1)<.001 for v in normal_lengths),'Invalid GLB NORMAL data'
    color_data=decoded(j,bin_data,primitive['attributes']['COLOR_0'])
    assert len(set(color_data))>5 and all(c[-1] in (1,255,65535) for c in color_data if len(c)==4)
    s=bpy.data.scenes.new('VERIFY • '+key);bpy.context.window.scene=s
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'exports'/f'{key}.glb'));bpy.context.view_layer.update()
    coll=bpy.data.collections.new('IMPORTED • '+key);s.collection.children.link(coll)
    for obj in list(s.objects):
        for c in list(obj.users_collection):c.objects.unlink(obj)
        coll.objects.link(obj)
    model_meshes=[o for o in coll.objects if o.type=='MESH'];assert len(model_meshes)==1
    o=model_meshes[0];me=o.data;me.calc_loop_triangles()
    assert len(me.materials)==len(me.color_attributes)==1
    assert len(me.loop_triangles)==entry['runtime']['triangles']
    assert all(t.area>1e-12 for t in me.loop_triangles),'Degenerate GLB triangle: '+key
    assert signature(o)==original_sig,'Geometry or oriented triangle winding changed: '+key
    assert palette_colors(o)==original_colors,'Palette changed: '+key
    pts=[o.matrix_world@v.co for v in me.vertices]
    assert all(math.isfinite(c) for v in pts for c in v)
    assert all(math.isfinite(c) for n in me.corner_normals for c in n.vector)
    assert all(abs(n.vector.length-1)<.001 for n in me.corner_normals)
    lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
    error=max(abs(a-b) for a,b in zip(lo+hi,entry['runtime']['bounds_min']+entry['runtime']['bounds_max']))
    assert error<1e-5 and abs(lo[2])<1e-5
    assert lo[0]>=-2.4 and lo[1]>=-3.2 and hi[0]<=2.4 and hi[1]<=1.6
    root=next(o for o in coll.objects if o.type=='EMPTY' and o.get('asset_id')==key)
    assert root.location.length<1e-5 and all(abs(c-1)<1e-5 for c in root.scale)
    assert o.location.length<1e-5 and all(abs(c-1)<1e-5 for c in o.scale)
    assert all(abs(c)<1e-5 for c in root.rotation_euler)
    assert len(me.loop_triangles)<=entry['initial_triangle_target']
    # Reopened editable components have the same exact dimensions and positive source solids.
    edit=entry['editable'];assert all(abs(a-b)<1e-5 for a,b in zip(edit['bounds_min']+edit['bounds_max'],lo+hi))
    s.collection.children.link(studio);s.world=source.world
    cam=source.camera.copy();cam.data=cam.data.copy();s.collection.objects.link(cam);s.camera=cam
    s.render.engine='CYCLES';s.cycles.use_denoising=True
    s.view_settings.view_transform=source.view_settings.view_transform;s.view_settings.exposure=.35
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
    s.render.resolution_percentage=100
    IMPORTED[key]=coll;VERIFICATION[key]=s
    report['models'][key]={'reimport_passed':True,'triangles':len(me.loop_triangles),'meshes':1,'materials':1,'primitives':1,
        'vertex_color_count':len(original_colors),'palette_matches_source':True,'geometry_and_winding_match_source':True,
        'raw_glb_normals_finite_and_unit':True,'normal_length_min':min(normal_lengths),'normal_length_max':max(normal_lengths),
        'imported_normals_finite_and_unit':True,'degenerate_triangles':0,'source_outward_closed_components':entry['source_geometry']['closed_outward_components'],
        'bounds_error_m':error,'ground_error_m':abs(lo[2]),'bounds_min':lo,'bounds_max':hi,'common_lot_passed':True,
        'root_location':list(root.location),'root_scale':list(root.scale),'dimensions_m':[hi[i]-lo[i] for i in range(3)],
        'opaque':True,'backface_culling':True,'textures':0,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    print('VERIFIED',key,flush=True)

# Every new building visible in the comparison renders comes from the final .glb reimport.
for sname in ('01 • Bakery upgrades','02 • Bookshop upgrades','03 • Neighborhood style'):
    for o in bpy.data.scenes[sname].objects:
        if o.instance_type=='COLLECTION' and o.instance_collection.name.startswith('LOW • '):
            o.instance_collection=IMPORTED[o.instance_collection.name.split(' • ')[1]]
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    device='GPU' if any(d.type!='CPU' for d in prefs.devices) else 'CPU'
except Exception:device='CPU'
def render(s,name,w,h):
    bpy.context.window.scene=s;s.cycles.device=device;s.cycles.samples=24 if PREVIEW else 64
    s.render.resolution_x=w;s.render.resolution_y=h;s.render.filepath=str(ROOT/'renders'/name)
    bpy.ops.render.render(write_still=True);print('RENDERED',name,flush=True)
rows=[('01 • Bakery upgrades','01_bakery_levels.png'),('02 • Bookshop upgrades','02_bookshop_levels.png'),('03 • Neighborhood style','03_style_with_cafe_v003.png')]
for sname,name in rows:
    render(bpy.data.scenes[sname],('preview_'+name) if PREVIEW else name,1500 if PREVIEW else 2400,781 if PREVIEW else 1250)
if not PREVIEW:
    for key,s in VERIFICATION.items():
        render(s,key+'.png',1200,1200)
        if key.endswith('_3'):
            s.camera.location=(-8,11,7)
            s.camera.rotation_euler=(Vector((0,0,2))-s.camera.location).to_track_quat('-Z','Y').to_euler()
            render(s,key+'_back.png',1200,1200)
preserve();report['all_passed']=True;report['render_device']=device;report['preview_only']=PREVIEW
(ROOT/'reports'/('validation_preview.json' if PREVIEW else 'validation.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
print('VALIDATION_COMPLETE',flush=True)
