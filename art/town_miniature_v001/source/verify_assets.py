"""Reopen source and independently reimport every GLB, comparing evaluated geometry."""
import bpy, json, math, struct
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
expected=json.loads((ROOT/'reports/model_stats.json').read_text())
source=ROOT/'blend/chagok_town_miniature_v001.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
report={'blender':bpy.app.version_string,'source_reopened':True,
        'source_file_bytes':source.stat().st_size,'source_scenes':[s.name for s in bpy.data.scenes],
        'source_objects':len(bpy.data.objects),'models':{}}
assert len(bpy.data.scenes)==7
assert len([o for o in bpy.data.objects if 'asset_id' in o])==6
report['source_meshes']=len([o for o in bpy.data.objects if o.type=='MESH'])
report['source_editable_text_objects']=len([o for o in bpy.data.objects if o.type=='FONT'])

for key,exp in expected.items():
    path=ROOT/'exports'/f'{key}.glb'
    raw=path.read_bytes()
    magic,version,length=struct.unpack_from('<4sII',raw,0)
    assert magic==b'glTF' and version==2 and length==len(raw)
    json_len,kind=struct.unpack_from('<II',raw,12)
    gltf=json.loads(raw[20:20+json_len])
    assert not gltf.get('images'), 'Unexpected image dependency'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    bpy.context.view_layer.update()
    verts=[]; triangles=0; objects=[]; mats=set()
    for o in bpy.context.scene.objects:
        if o.type!='MESH': continue
        objects.append(o)
        o.data.calc_loop_triangles(); triangles+=len(o.data.loop_triangles)
        verts += [o.matrix_world@v.co for v in o.data.vertices]
        mats.update(m.name for m in o.data.materials if m)
    assert verts and all(math.isfinite(c) for v in verts for c in v)
    low=[min(v[i] for v in verts) for i in range(3)]
    high=[max(v[i] for v in verts) for i in range(3)]
    assert len(objects)==exp['mesh_objects'], (key,'objects',len(objects),exp['mesh_objects'])
    assert triangles==exp['triangles'], (key,'triangles',triangles,exp['triangles'])
    assert len(mats)==exp['materials'], (key,'materials',len(mats),exp['materials'])
    err=max(abs(a-b) for a,b in zip(low+high,exp['bounds_min']+exp['bounds_max']))
    assert err<.0001, (key,'bounds error',err)
    assert abs(low[2])<.0001, (key,'ground',low[2])
    root=next(o for o in bpy.context.scene.objects if o.get('asset_id')==key)
    assert root.location.length<.0001
    assert all(abs(v-1)<.0001 for v in root.scale)
    report['models'][key]={
        'glb_header_valid':True,'reimport_passed':True,'file_bytes':len(raw),
        'mesh_objects':len(objects),'triangles':triangles,'materials':len(mats),
        'bounds_min':low,'bounds_max':high,'max_bounds_error_m':err,
        'ground_error_m':abs(low[2]),'root_location':list(root.location),
        'image_textures':len(gltf.get('images',[])),
    }
    print('VERIFIED',key,triangles,'triangles',flush=True)
report['all_passed']=True
(ROOT/'reports/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('VALIDATION_COMPLETE',flush=True)
