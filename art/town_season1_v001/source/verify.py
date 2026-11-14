"""Independently reopen originals/map and reimport all twelve delivered GLBs."""
import bpy,sys,json,math,struct,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import geometry as G
import models as M
import scene_common as C
import access as A
stats=json.loads((ROOT/'reports/model_stats.json').read_text())
report={'models':{},'models_blend_reopened':False,'map_blend_reopened':False}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/season1_models.blend'))
for key,model in stats['models'].items():
    scene=bpy.data.scenes['EDIT • '+key];bpy.context.window.scene=scene
    parts=[o for o in scene.objects if o.type=='MESH'];assert len(parts)>10
    panels=[]
    for o in parts:
        if o.name.startswith('Door • panel actual size'):
            zz=[v.co.z for v in o.data.vertices];xx=[v.co.x for v in o.data.vertices]
            panels.append({'width':max(xx)-min(xx),'height':max(zz)-min(zz)})
    assert panels
    if model['type']!='cathedral':assert all(abs(p['width']-.8)<1e-5 and abs(p['height']-1.6)<1e-5 for p in panels),(key,panels)
    report['models'][key]={'named_editable_components':len(parts),'actual_door_panels_m':panels}
report['models_blend_reopened']=True
bpy.ops.wm.read_factory_settings(use_empty=True)
for file in sorted((ROOT/'exports').glob('*.glb')):
    key=file.stem;assert key in stats['models']
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(file));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==1
    obj=meshes[0];me=obj.data;me.calc_loop_triangles();assert len(me.materials)==1
    assert all(math.isfinite(c) for v in me.vertices for c in v.co)
    assert all(t.area>1e-12 for t in me.loop_triangles),(key,'degenerate reimport triangle')
    assert all(math.isfinite(c) for n in me.corner_normals for c in n.vector)
    assert all(abs(n.vector.length-1)<.001 for n in me.corner_normals),(key,'non-unit reimport normal')
    colors=me.color_attributes.active_color;assert colors and len(colors.data)>0
    unique={tuple(round(c,4) for c in value.color[:3]) for value in colors.data};assert len(unique)>4
    assert all(abs(value.color[3]-1)<1e-4 for value in colors.data)
    points=[obj.matrix_world@v.co for v in me.vertices]
    lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
    src=stats['models'][key]['runtime']
    assert max(abs(a-b) for a,b in zip(lo+hi,src['bounds_min']+src['bounds_max']))<1e-4,(key,lo,hi)
    assert abs(lo[2])<1e-5
    assert all(abs(v-1)<1e-5 for v in obj.matrix_world.to_scale())
    data=file.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);mat=doc['materials'][0]
    glb=G.glb_stats(file)
    assert glb['mesh_objects']==glb['primitives']==glb['materials']==1 and glb['textures']==0 and glb['all_primitives_have_vertex_color']
    assert mat.get('alphaMode','OPAQUE')=='OPAQUE' and not mat.get('doubleSided',False)
    pbr=mat.get('pbrMetallicRoughness',{});assert pbr.get('metallicFactor',1)==0 and abs(pbr.get('roughnessFactor',1)-.68)<1e-5
    for primitive in doc['meshes'][0]['primitives']:
        acc=doc['accessors'][primitive['attributes']['NORMAL']];view=doc['bufferViews'][acc['bufferView']]
        assert acc['componentType']==5126 and acc['type']=='VEC3'
        offset=28+size+view.get('byteOffset',0)+acc.get('byteOffset',0);stride=view.get('byteStride',12)
        for i in range(acc['count']):
            normal=struct.unpack_from('<fff',data,offset+i*stride)
            assert all(math.isfinite(c) for c in normal) and abs(math.sqrt(sum(c*c for c in normal))-1)<.001,(key,'raw GLB normal')
    report['models'][key].update({'reimported':True,'bounds_min':lo,'bounds_max':hi,'triangle_count':len(me.loop_triangles),
        'finite_unit_normals':True,'degenerate_triangles':0,'vertex_colour_values':len(unique),'one_mesh_material_primitive':True,'opaque':True,'textures':0,'sha256':hashlib.sha256(data).hexdigest()})
    print('REIMPORT_VERIFIED',key,len(me.loop_triangles),flush=True)
assert len(report['models'])==12 and all(r['reimported'] for r in report['models'].values())
report['reused_compact_variants']={}
variant_stats=json.loads((ROOT/'reports/reused_compact_variants.json').read_text())
for file in sorted((ROOT/'exports/reused_compact').glob('*.glb')):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(file))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==1
    obj=meshes[0];me=obj.data;me.calc_loop_triangles()
    assert all(t.area>1e-12 for t in me.loop_triangles) and all(math.isfinite(c) for n in me.corner_normals for c in n.vector)
    assert all(abs(n.vector.length-1)<.001 for n in me.corner_normals)
    kind=file.stem.split('_level_')[0];assert len(me.loop_triangles)==variant_stats[kind]['source']['triangles']
    points=[obj.matrix_world@v.co for v in me.vertices];bounds=[min(p[i] for p in points) for i in range(3)]+[max(p[i] for p in points) for i in range(3)]
    expected=variant_stats[kind]['source']['bounds_min']+variant_stats[kind]['source']['bounds_max']
    assert max(abs(a-b) for a,b in zip(bounds,expected))<1e-4
    colors=me.color_attributes.active_color;assert colors and len({tuple(round(c,3) for c in value.color[:3]) for value in colors.data})>4
    report['reused_compact_variants'][kind]={'reimported':True,'geometry_matches_compact':True,'triangles':len(me.loop_triangles),'finite_unit_normals':True,'degenerate_triangles':0}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/season1_map.blend'))
scene_stats={};camera_reference=None
for name,count in [('Season 1 • beginning',8),('Season 1 • middle',12),('Season 1 • final',14)]:
    scene=bpy.data.scenes[name];bpy.context.window.scene=scene;bpy.context.view_layer.update();objects=C.models_in(scene)
    assert len(objects)==count
    matrix=[list(row) for row in scene.camera.matrix_world]
    if camera_reference is None:camera_reference=matrix
    assert matrix==camera_reference and scene.camera.data.ortho_scale==48 and not scene.camera.data.dof.use_dof
    assert (scene.render.resolution_x,scene.render.resolution_y)==(2400,1500)
    scene_stats[name]={'count':count,'camera_matrix_matches':True,'ortho':48,'unit_scale':scene.unit_settings.scale_length}
final=bpy.data.scenes['Season 1 • final'];bpy.context.window.scene=final;bpy.context.view_layer.update()
layout=json.loads((ROOT/'source/layout.json').read_text());footprints=json.loads((ROOT/'reports/final_layout.json').read_text())['maximum_local_hulls']
assert not C.check_layout(final,layout,footprints,'verified_final')
bvh=A.terrain_bvh(final);contacts={};frames={}
for obj in C.models_in(final):
    key=C.identity(obj);b=next(b for b in layout if b['id']==key)
    assert math.dist(obj.location[:2],b['xy'])<1e-5 and all(abs(v-b['scale'])<1e-6 for v in obj.scale)
    if not b.get('legacy'):assert all(abs(v-1)<1e-6 for v in obj.scale)
    z=A.ground(bvh,*b['xy']);contacts[key]={'ground_at_root':z,'declared_ground':b['ground'],'difference':z-b['ground']}
    assert abs(z-b['ground'])<.025,(key,'root/terrain height',z,b['ground'])
    points=[obj.matrix_world@p for p in C.local_points(obj.instance_collection)]
    camera_points=[world_to_camera_view(final,final.camera,p) for p in points[::max(1,len(points)//700)]]
    frames[key]={'x':[min(p.x for p in camera_points),max(p.x for p in camera_points)],'y':[min(p.y for p in camera_points),max(p.y for p in camera_points)]}
    assert all(0<=p.x<=1 and 0<=p.y<=1 for p in camera_points),(key,'cropped building')
assert not any(o.type=='FONT' for o in final.objects)
report.update({'map_blend_reopened':True,'scene_counts_and_cameras':scene_stats,'ground_contacts':contacts,'wide_frame_projection':frames,
               'max_stage_overlap_pairs':0,'new_building_scale':[1,1,1],'protected_art_files_unchanged':C.protect(),'passed':True})
(ROOT/'reports/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('SEASON_VALIDATION_COMPLETE',flush=True)
