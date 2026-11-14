"""Reopen the saved map and independently inspect the delivered props GLB."""
import bpy, sys, json, numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
import scene_checks as C
manifest=json.loads((ROOT/'reports/manifest.json').read_text())
prior=json.loads((F.ART/manifest['source_manifest']).read_text())
assert manifest['assets']==prior['assets']
assert manifest['layout']==prior['layout']
assert F.sha(F.ART/manifest['source_manifest'])==manifest['source_manifest_sha256']
for e in manifest['assets']:assert F.sha(F.ART/e['path'])==e['sha256']
F.protect()
blend=ROOT/'blend/riverbank_review.blend'
assert F.sha(blend)==manifest['review_blend']['sha256']
bpy.ops.wm.open_mainfile(filepath=str(blend))
baseline=json.loads((ROOT/'reports/environment_baseline.json').read_text())
collection=bpy.data.collections['RIVERBANK v005 • sparse stones and short grass']
props=list(collection.all_objects)
stages={}
for label in ('beginning','middle','final'):
    original=bpy.data.scenes['AFTER roof tones • '+label]
    scene=bpy.data.scenes['RIVERBANK v005 • '+label]
    assert C.digest(C.snapshot(original))==C.digest(baseline[label])
    snap=C.snapshot(scene)
    for o in props:snap['environment'].pop(o.name)
    snap['environment_sha256']=C.digest(snap['environment'])
    assert C.digest(snap)==C.digest(baseline[label])
    assert set(props).issubset(set(scene.objects))
    stages[label]={'original_environment_exact':True,'camera_lighting_exposure_exact':True,'plot_placements_exact':True,
                   'props_objects_same_datablocks':True,'environment_sha256':snap['environment_sha256'],
                   'presentation_sha256':snap['presentation_sha256']}

scene=bpy.data.scenes['RIVERBANK v005 • final']
bpy.context.window.scene=scene;bpy.context.view_layer.update()
terrain_obj=scene.objects['Integrated • continuous terrain'];terrain_obj.data.calc_loop_triangles()
terrain=BVHTree.FromPolygons([terrain_obj.matrix_world@v.co for v in terrain_obj.data.vertices],[t.vertices[:] for t in terrain_obj.data.loop_triangles],all_triangles=True)
water_obj=scene.objects['Stream • continuous water'];water_obj.data.calc_loop_triangles()
water=BVHTree.FromPolygons([water_obj.matrix_world@v.co for v in water_obj.data.vertices],[t.vertices[:] for t in water_obj.data.loop_triangles],all_triangles=True)
water_z=water_obj.data.vertices[0].co.z
def height(point):
    hit=terrain.ray_cast(Vector((point.x,point.y,20)),Vector((0,0,-1)),40)[0]
    assert hit is not None
    return hit.z

def triangles(objects,transform=None):
    rows=[]
    for o in objects:
        if o.type!='MESH':continue
        me=o.data;me.calc_loop_triangles();matrix=o.matrix_world if transform is None else transform@o.matrix_world
        nm=matrix.to_3x3().inverted().transposed()
        color=me.color_attributes.get('Palette') or me.color_attributes.active_color
        for tri in me.loop_triangles:
            corners=[]
            for v,li in zip(tri.vertices,tri.loops):
                pos=matrix@me.vertices[v].co;normal=(nm@me.corner_normals[li].vector).normalized()
                rgba=color.data[li if color.domain=='CORNER' else v].color if color else (0,0,0,0)
                corners.append(list(pos)+list(normal)+list(rgba))
            rows.append(corners)
    return np.asarray(rows,dtype=np.float64)

def compare_geometry(a,b):
    assert a.shape==b.shape
    tree=KDTree(len(b))
    for i,p in enumerate(b[:,:,:3].mean(axis=1)):tree.insert(Vector(p),i)
    tree.balance();used=set();poserr=0.;colorerr=0.;normalerr=0.
    for tri in a:
        _,index,distance=tree.find(Vector(tri[:,:3].mean(axis=0)))
        assert distance<.00001 and index not in used
        used.add(index);other=b[index]
        for corner in tri:
            k=int(np.argmin(np.linalg.norm(other[:,:3]-corner[:3],axis=1)))
            poserr=max(poserr,float(np.max(np.abs(other[k,:3]-corner[:3]))))
            colorerr=max(colorerr,float(np.max(np.abs(other[k,6:]-corner[6:]))))
            normalerr=max(normalerr,float(np.max(np.abs(other[k,3:6]-corner[3:6]))))
    assert poserr<.00001 and colorerr<.00001
    return {'triangles':len(a),'max_position_error_m':poserr,'max_color_error_linear':colorerr,'max_normal_component_difference':normalerr}

original_triangles=triangles(props)
runtime=bpy.data.objects['riverbank_props_v005']
edit_compare=compare_geometry(original_triangles,triangles([runtime]))
contact=[]
for o in props:
    points=[o.matrix_world@v.co for v in o.data.vertices]
    gaps=[p.z-height(p) for p in points]
    if o['riverbank_kind']=='grass':
        roots=[o.matrix_world@o.data.vertices[k].co for k in o.data['root_vertex_indices']]
        roots_gaps=[p.z-height(p) for p in roots]
        assert max(roots_gaps)<0 and min(roots_gaps)>-.12
        assert all(p.z>water_z for p in roots)
        assert all(water.ray_cast(Vector((p.x,p.y,10)),Vector((0,0,-1)),20)[0] is None for p in roots)
        row={'object':o.name,'root_gaps_m':[min(roots_gaps),max(roots_gaps)],'roots_dry':True}
    else:
        assert min(gaps)<-.04 and max(gaps)>.04,(o.name,min(gaps),max(gaps))
        assert max(gaps)<.5
        row={'object':o.name,'terrain_gap_range_m':[min(gaps),max(gaps)],'embedded_and_exposed':True}
    assert not (-8.2<o.location.y<-2)
    contact.append(row)

def object_bvh(objects,matrix=None):
    vertices=[];faces=[]
    for o in objects:
        if o.type!='MESH':continue
        me=o.data;me.calc_loop_triangles();n=len(vertices)
        world=o.matrix_world if matrix is None else matrix@o.matrix_world
        vertices.extend(world@v.co for v in me.vertices)
        faces.extend(tuple(n+k for k in t.vertices) for t in me.loop_triangles)
    return BVHTree.FromPolygons(vertices,faces,all_triangles=True)

props_bvh=object_bvh(props)
intersections=[];building_checks=0
for label in ('beginning','middle','final'):
    s=bpy.data.scenes['RIVERBANK v005 • '+label]
    bpy.context.window.scene=s;bpy.context.view_layer.update()
    for plot in s.objects:
        if not plot.get('plot_id'):continue
        building_checks+=1
        overlaps=props_bvh.overlap(object_bvh(plot.instance_collection.all_objects,plot.matrix_world))
        if overlaps:intersections.append([label,plot['plot_id'],len(overlaps)])
assert not intersections,intersections
path_checks=0
for o in scene.objects:
    if o.type=='MESH' and o.name.startswith(('Shared alley','Shared paving','Shared court')):
        path_checks+=1
        assert not props_bvh.overlap(object_bvh([o])),o.name

path=F.ART/manifest['riverbank']['path']
assert F.sha(path)==manifest['riverbank']['sha256']
doc,blob,_=F.read(path);p=F.primitive(doc)
positions=np.asarray(F.accessor(doc,blob,p['attributes']['POSITION']))
normals=np.asarray(F.accessor(doc,blob,p['attributes']['NORMAL']))
colors=np.asarray(F.accessor(doc,blob,p['attributes']['COLOR_0']))
indices=np.asarray(F.accessor(doc,blob,p['indices']),dtype=np.int64).reshape(-1,3)
assert np.isfinite(positions).all() and np.isfinite(normals).all() and np.isfinite(colors).all()
lengths=np.linalg.norm(normals,axis=1)
assert np.max(np.abs(lengths-1))<.0001
assert indices.min()>=0 and indices.max()<len(positions)
cross=np.cross(positions[indices[:,1]]-positions[indices[:,0]],positions[indices[:,2]]-positions[indices[:,0]])
areas=np.linalg.norm(cross,axis=1)/2
assert areas.min()>1e-10
face_normals=cross/np.linalg.norm(cross,axis=1)[:,None]
alignment=np.einsum('ij,ij->i',face_normals,normals[indices].mean(axis=1))
assert alignment.min()>.1
assert colors.shape[1]==3 or (colors[:,3]==1).all()
assert not doc['materials'][0].get('doubleSided',False)
assert not doc.get('textures') and not doc.get('images') and not doc.get('cameras') and len(doc['nodes'])==1
assert np.allclose(F.mesh_world(doc),np.eye(4),atol=1e-7)

qa=bpy.data.scenes.new('QA • props reimport')
col=C.import_asset(path,qa,'QA • props reimport')
reimport_compare=compare_geometry(triangles([runtime]),triangles(col.all_objects))
all_compare=compare_geometry(original_triangles,triangles(col.all_objects))
assert reimport_compare['max_normal_component_difference']<.0001
for o in col.all_objects:
    if o.type=='MESH':assert np.allclose(o.matrix_world,np.eye(4),atol=1e-7)
report={'passed':True,'reopened_blend_sha256':F.sha(blend),'delivered_glb_sha256':F.sha(path),'source_blend_sha256':F.sha(F.ART/'town_season1_v004_roof_tones/blend/roof_tones_review.blend'),
        'protected_inputs_checked':F.protect(),'building_glb_paths_and_hashes_unchanged':36,'layout_unchanged':True,'stages':stages,
        'glb_static':{'triangles':len(indices),'vertices':len(positions),'materials':len(doc['materials']),'meshes':len(doc['meshes']),'primitives':1,'textures':0,
                      'bytes':path.stat().st_size,'degenerate_triangles':0,'minimum_triangle_area_m2':float(areas.min()),
                      'minimum_normal_face_alignment':float(alignment.min()),'finite_unit_normals':True,'opaque_color_alpha':True,'backface_culling':True,'identity_origin_and_scale':True},
        'edit_to_runtime':edit_compare,'runtime_to_reimport':reimport_compare,'edit_to_reimport':all_compare,'ground_contacts':contact,
        'building_intersection_checks':building_checks,'building_intersections':intersections,'existing_path_checks':path_checks,'existing_path_intersections':0,
        'mill_keepout_blender_y_m':[-8.2,-2.0],
        'limits':'Geometry, scene and rendered art validation only. No Android, Pleos, vehicle or gameplay performance validation.'}
(ROOT/'reports/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('RIVERBANK_VERIFICATION_PASSED',json.dumps({'triangles':len(indices),'building_checks':building_checks,'protected_inputs':report['protected_inputs_checked']}),flush=True)
