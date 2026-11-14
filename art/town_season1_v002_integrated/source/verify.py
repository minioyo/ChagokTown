"""Fresh-process model, scene, unit, and actual multi-height entry verification."""
import bpy,sys,json,math,struct,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import town as T
import geometry as G
stats=json.loads((ROOT/'reports/model_stats.json').read_text());report={'models':{}}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/integrated_models.blend'))
expected={'cafe':[1.17,3.17],'house':[1.35,3.35],'bakery':[1.15,3.17],'bookshop':[1.18,3.18,5.18],
 'town_hall':[1.28,3.275],'grocer':[1.19,3.19],'workshop':[1.19,3.19]}
for key,row in stats['models'].items():
    scene=bpy.data.scenes['EDIT • '+key];bpy.context.window.scene=scene;bpy.context.view_layer.update();parts=[o for o in scene.objects if o.type=='MESH'];panels=[];glazing=[]
    wall_vs=[];wall_fs=[];dg=bpy.context.evaluated_depsgraph_get()
    for o in parts:
        if not any(word in o.name.lower() for word in ('wall','gable','storeroom','shaft')):continue
        ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();offset=len(wall_vs);wall_vs.extend(ev.matrix_world@v.co for v in me.vertices);wall_fs.extend(tuple(offset+i for i in t.vertices) for t in me.loop_triangles);ev.to_mesh_clear()
    wall=BVHTree.FromPolygons(wall_vs,wall_fs,all_triangles=True);supported_windows=0
    for o in parts:
        points=[o.matrix_world@v.co for v in o.data.vertices]
        lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
        if o.name.startswith(('Door • panel actual size','Balcony • glazed door')):
            value={'width':hi[0]-lo[0],'height':hi[2]-lo[2]};panels.append(value)
            assert abs(value['width']-.8)<1e-5 and abs(value['height']-1.6)<1e-5,(key,value)
        if ('glazing' in o.name.lower() or any(m and m.name=='Glass' for m in o.data.materials)) and not o.name.startswith(('Door','Balcony')):glazing.append((lo[2]+hi[2])/2)
        if o.name.startswith('Window') and any(m and m.name=='Glass' for m in o.data.materials):
            centre=Vector([(lo[i]+hi[i])/2 for i in range(3)]);inward=(o.matrix_world.to_3x3()@Vector((0,1,0))).normalized()
            assert wall.ray_cast(centre,inward,.50)[0] is not None,(key,o.name,'window has no supporting wall within 0.5m',tuple(centre));supported_windows+=1
    assert panels and len(parts)>15
    floors=[]
    if row['level']==3 and row['type'] in expected:
        for z in expected[row['type']]:
            actual=min(glazing,key=lambda v:abs(v-z));assert abs(actual-z)<.025,(key,z,glazing);floors.append(actual)
        assert all(1.8<=b-a<=2.2 for a,b in zip(floors,floors[1:])),(key,floors)
    report['models'][key]={'editable_components':len(parts),'measured_panels_m':panels,'measured_storey_window_centres_m':floors,'rectangular_windows_with_wall_support':supported_windows}
report['component_blend_reopened']=True
bpy.ops.wm.read_factory_settings(use_empty=True)
for path in sorted((ROOT/'exports').glob('*.glb')):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(path))
    key=path.stem;meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==1
    obj=meshes[0];me=obj.data;me.calc_loop_triangles();assert len(me.materials)==1
    assert all(math.isfinite(c) for v in me.vertices for c in v.co)
    assert all(t.area>1e-12 for t in me.loop_triangles),(key,'degenerate reimport')
    assert all(math.isfinite(c) and abs(n.vector.length-1)<.001 for n in me.corner_normals for c in n.vector),(key,'reimport normal')
    colors=me.color_attributes.active_color;assert colors and len(colors.data)>0
    unique={tuple(round(c,4) for c in v.color[:3]) for v in colors.data};assert len(unique)>4 and all(abs(v.color[3]-1)<1e-4 for v in colors.data)
    points=[obj.matrix_world@v.co for v in me.vertices];lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)];src=stats['models'][key]['runtime']
    assert max(abs(a-b) for a,b in zip(lo+hi,src['bounds_min']+src['bounds_max']))<1e-4 and abs(lo[2])<1e-5
    assert all(abs(v-1)<1e-5 for v in obj.matrix_world.to_scale())
    data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);mat=doc['materials'][0];glb=G.glb_stats(path)
    assert glb['mesh_objects']==glb['primitives']==glb['materials']==1 and glb['textures']==0 and glb['all_primitives_have_vertex_color']
    assert mat.get('alphaMode','OPAQUE')=='OPAQUE' and not mat.get('doubleSided',False)
    pbr=mat.get('pbrMetallicRoughness',{});assert pbr.get('metallicFactor',1)==0 and abs(pbr.get('roughnessFactor',1)-.68)<1e-5
    for primitive in doc['meshes'][0]['primitives']:
        acc=doc['accessors'][primitive['attributes']['NORMAL']];view=doc['bufferViews'][acc['bufferView']];offset=28+size+view.get('byteOffset',0)+acc.get('byteOffset',0);stride=view.get('byteStride',12)
        for i in range(acc['count']):
            normal=struct.unpack_from('<fff',data,offset+i*stride);assert all(math.isfinite(c) for c in normal) and abs(math.sqrt(sum(c*c for c in normal))-1)<.001
    report['models'][key].update({'reimported':True,'triangles':len(me.loop_triangles),'finite_unit_normals':True,'degenerate_triangles':0,'vertex_colours':len(unique),'ground_z':lo[2],'world_scale':list(obj.matrix_world.to_scale()),'sha256':hashlib.sha256(data).hexdigest()})
    print('VERIFIED_GLB',key,flush=True)
assert len(report['models'])==24
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/integrated_village.blend'))
final=bpy.data.scenes['INTEGRATED • final'];bpy.context.window.scene=final;bpy.context.view_layer.update();layout=json.loads((ROOT/'source/layout.json').read_text())
plots=[o for o in final.objects if 'plot_id' in o];assert len(plots)==14
reference=bpy.data.scenes['REFERENCE • v001 unchanged'];bpy.context.window.scene=reference;bpy.context.view_layer.update();ref_matrix=reference.camera.matrix_world.copy()
bpy.context.window.scene=final;bpy.context.view_layer.update()
assert final.camera.matrix_world==ref_matrix and final.camera.data.ortho_scale==reference.camera.data.ortho_scale==48,('Camera mismatch',list(final.camera.location),list(reference.camera.location),final.camera.data.ortho_scale,reference.camera.data.ortho_scale)
assert all(getattr(final.view_settings,k)==getattr(reference.view_settings,k) for k in ('view_transform','look','exposure','gamma'))
lights=lambda s:sorted((o.type,tuple(o.location),tuple(o.rotation_euler),o.data.type,o.data.energy,tuple(o.data.color),o.data.size if o.data.type=='AREA' else 0) for o in s.objects if o.type=='LIGHT')
assert lights(final)==lights(reference)
terrain=next(o for o in final.objects if o.name=='Integrated • continuous terrain');terrain.data.calc_loop_triangles()
ground=BVHTree.FromPolygons([v.co for v in terrain.data.vertices],[tuple(t.vertices) for t in terrain.data.loop_triangles],all_triangles=True)
def gz(x,y):return ground.ray_cast(Vector((x,y,30)),Vector((0,0,-1)),60)[0].z
contacts={};frames={};assets={}
tree_contacts={}
for obj in final.objects:
    if obj.name.startswith('REUSED • Tree • warm trunk'):
        bottom=min((obj.matrix_world@Vector(c)).z for c in obj.bound_box);delta=bottom-gz(obj.location.x,obj.location.y)
        assert abs(delta)<.03,(obj.name,'tree ground contact',delta);tree_contacts[obj.name]=delta
for b in layout:
    obj=next(o for o in plots if o['plot_id']==b['id']);assert all(abs(v-1)<1e-6 for v in obj.scale)
    delta=gz(*b['xy'])-b['ground'];assert abs(delta)<.025,(b['id'],delta);contacts[b['id']]=delta
    pp=[obj.matrix_world@p for p in T.local_points(obj.instance_collection)];screen=[world_to_camera_view(final,final.camera,p) for p in pp]
    assert all(0<p.x<1 and 0<p.y<1 for p in screen),(b['id'],'cropped')
    frames[b['id']]={'x':[min(p.x for p in screen),max(p.x for p in screen)],'y':[min(p.y for p in screen),max(p.y for p in screen)]}
    for n in (1,2,3):assets[b['kind'],n]=bpy.data.collections[f"INPUT • {b['kind']}_L{n}"]
local={k:T.hull([(p.x,p.y) for n in (1,2,3) for p in T.local_points(assets[k,n])]) for k in {b['kind'] for b in layout}}
metrics=T.save_metrics(layout,local,'verified');assert len(metrics['pairs'])==91 and min(p['gap_m'] for p in metrics['pairs'])>=.4-1e-5
scene_counts={}
for label,count in [('beginning',8),('middle',12),('final',14)]:
    scene=bpy.data.scenes['INTEGRATED • '+label];assert len([o for o in scene.objects if 'plot_id' in o])==count
    bpy.context.window.scene=scene;bpy.context.view_layer.update()
    assert scene.camera.matrix_world==ref_matrix and scene.camera.data.ortho_scale==48 and not scene.camera.data.dof.use_dof
    scene_counts[label]=count
# Re-test saved paths against real imported triangles at three heights and three offsets.
access=json.loads((ROOT/'reports/access.json').read_text());colliders={}
for b in layout:
    for n in (1,2,3):
        vs=[];fs=[]
        for obj in assets[b['kind'],n].all_objects:
            if obj.type!='MESH':continue
            obj.data.calc_loop_triangles();offset=len(vs)
            for v in obj.data.vertices:
                p=obj.matrix_world@v.co;xy=T.world_xy(b,p);vs.append((xy[0],xy[1],p.z+b['ground']))
            fs.extend(tuple(offset+i for i in t.vertices) for t in obj.data.loop_triangles)
        colliders[b['id'],n]=BVHTree.FromPolygons(vs,fs,all_triangles=True)
failures=[]
for row in access['primary_doors']:
    others=[bv for (key,n),bv in colliders.items() if key!=row['plot'] or n==row['level']]
    for aa,bb in zip(row['points'],row['points'][1:]):
        a=Vector(aa);b=Vector(bb);d=b-a
        if d.length<1e-5:continue
        side=Vector((-d.y,d.x)).normalized();steps=max(2,math.ceil(d.length/.12))
        for off in (-.30,0,.30):
            pp=[a.lerp(b,i/steps)+side*off for i in range(steps+1)]
            for h in (.3,.85,1.5):
                world=[Vector((p.x,p.y,gz(p.x,p.y)+h)) for p in pp]
                for p,q in zip(world,world[1:]):
                    dd=q-p
                    if dd.length<1e-6:continue
                    if any(bv.ray_cast(p,dd.normalized(),dd.length-.00001)[0] is not None for bv in others):failures.append((row['plot'],row['level'],h,off,tuple(p)));break
assert not failures,failures[:20]
manifest=json.loads((ROOT/'reports/manifest.json').read_text());assert len(manifest['assets'])==36
assert all(hashlib.sha256((T.ART/a['path']).read_bytes()).hexdigest()==a['sha256'] for a in manifest['assets'])
report.update({'map_blend_reopened':True,'scene_counts':scene_counts,'exact_before_camera_lights_exposure':True,'all_instances_world_scale':[1,1,1],
 'ground_contact_differences_m':contacts,'reused_tree_contacts_m':tree_contacts,'whole_frame_projection':frames,'max_stage_pairs':91,'overlaps':0,'minimum_max_hull_gap_m':min(p['gap_m'] for p in metrics['pairs']),
 'primary_doors_tested':42,'walk_ray_heights_m':[.3,.85,1.5],'walk_ray_offsets_m':[-.30,0,.30],'entry_triangle_collisions':0,'protected_art_files_unchanged':T.protect(),'passed':True})
report['validated_files']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'blend/integrated_models.blend',ROOT/'blend/integrated_village.blend']}
(ROOT/'reports/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('INTEGRATED_VALIDATION_COMPLETE',flush=True)
