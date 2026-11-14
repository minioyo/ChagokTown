"""Independent source proof, raw-byte mapping, 36 reimports and unchanged-map checks."""
import bpy,sys,json,gzip,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
import solids
import spatial as S
import scene_checks as C
manifest=json.loads((ROOT/'reports/manifest.json').read_text());baseline=json.loads((ROOT/'reports/environment_baseline.json').read_text());report={'models':{}}
original_points={};output_points={};loaded=None
for entry in manifest['assets']:
    key=f"{entry['type']}_level_{entry['level']}";src=F.ART/entry['source_path'];dst=F.ART/entry['path']
    assert F.sha(src)==entry['source_sha256'] and F.sha(dst)==entry['sha256']
    a,ab,_=F.read(src);b,bb,_=F.read(dst);ap=F.primitive(a);bp=F.primitive(b)
    with gzip.open(ROOT/entry['mapping'],'rt',encoding='utf-8') as stream:proof=json.load(stream)
    assert proof['source_glb_sha256']==F.sha(src) and proof['output_glb_sha256']==F.sha(dst)
    used=proof['new_to_old_vertex'];kept=proof['kept_original_triangle_ids'];removed=proof['removed_triangles'];assert used==sorted(set(used))
    old_indices=np.array(F.accessor(a,ab,ap['indices']),dtype=np.int64).reshape(-1,3);new_indices=np.array(F.accessor(b,bb,bp['indices']),dtype=np.int64).reshape(-1,3)
    assert sorted(kept+[i for i,_ in removed])==list(range(len(old_indices))) and len(kept)==len(new_indices)
    reverse={old:new for new,old in enumerate(used)};expected=np.array([[reverse[int(i)] for i in old_indices[t]] for t in kept])
    assert np.array_equal(new_indices,expected)
    assert ap['attributes'].keys()==bp['attributes'].keys()
    for semantic,ai in ap['attributes'].items():
        old=F.accessor(a,ab,ai,True);new=F.accessor(b,bb,bp['attributes'][semantic],True);assert new==[old[i] for i in used],(key,semantic)
    for field in set(a)|set(b):
        if field in ('bufferViews','buffers','accessors','meshes'):continue
        assert a.get(field)==b.get(field),(key,field)
    def mesh_metadata(d):
        import copy
        mesh=copy.deepcopy(d['meshes'][0]);p=mesh['primitives'][0];p.pop('attributes');p.pop('indices');return mesh
    assert mesh_metadata(a)==mesh_metadata(b)
    positions=np.array(F.accessor(a,ab,ap['attributes']['POSITION']),dtype=np.float64);pa=F.blender_points(a,positions)
    pb=F.blender_points(b,F.accessor(b,bb,bp['attributes']['POSITION']));original_points[entry['type'],entry['level']]=pa;output_points[entry['type'],entry['level']]=pb
    assert np.isfinite(pa).all() and np.isfinite(pb).all()
    assert np.array_equal(pa.min(axis=0),pb.min(axis=0)) and np.array_equal(pa.max(axis=0),pb.max(axis=0)),(key,'changed bounds')
    assert abs(pb[:,2].min())<1e-5 and all(abs(v-1)<1e-6 for v in F.mesh_world(b).to_scale())
    normals=np.array(F.accessor(b,bb,bp['attributes']['NORMAL']));assert np.isfinite(normals).all() and np.max(np.abs(np.linalg.norm(normals,axis=1)-1))<.001
    colors=np.array(F.accessor(b,bb,bp['attributes']['COLOR_0']));assert np.isfinite(colors).all() and len(np.unique(colors,axis=0))>4
    color_accessor=b['accessors'][bp['attributes']['COLOR_0']];alpha=1 if color_accessor['componentType']==5126 else {5121:255,5123:65535}[color_accessor['componentType']]
    assert colors.shape[1] in (3,4)
    if colors.shape[1]==4:assert np.all(colors[:,3]==alpha)
    blend=F.ART/entry['editable_blend'];assert F.sha(blend)==proof['source_blend_sha256']
    if loaded!=blend:bpy.ops.wm.open_mainfile(filepath=str(blend));loaded=blend
    current,_=solids.collect(bpy.data.scenes[entry['editable_scene']],pa);current={o['name']:o for o in current}
    for o in proof['occluders']:assert current[o['name']]['geometry_sha256']==o['geometry_sha256']
    for i,owner in removed:
        o=proof['occluders'][owner];tri=pa[old_indices[i]]
        assert np.all(tri@np.array(o['normals']).T < np.array(o['offsets'])-5e-5),(key,i,'unproven removal')
    report['models'][key]={'raw_attribute_bytes_preserved':True,'exact_triangle_index_correspondence':True,'all_removed_triangles_independently_proven':len(removed),
                           'opaque_closed_outward_convex_same_stage_occluders':len(current),'nodes_materials_extras_unchanged':True,
                           'source_sha256':F.sha(src),'output_sha256':F.sha(dst),'triangles':len(new_indices),'exported_vertices':len(pb),'bounds_min':pb.min(axis=0).tolist(),'bounds_max':pb.max(axis=0).tolist()}
    print('RAW_AND_SOLID_PROOF',key,flush=True)
# Every output is imported independently into an empty scene in this new process.
bpy.ops.wm.read_factory_settings(use_empty=True)
for entry in manifest['assets']:
    key=f"{entry['type']}_level_{entry['level']}";bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(F.ART/entry['path']));bpy.context.view_layer.update();meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==1
    obj=meshes[0];me=obj.data;me.calc_loop_triangles();assert len(me.materials)==1
    assert all(t.area>1e-12 for t in me.loop_triangles),(key,'degenerate reimport triangle')
    assert all(math.isfinite(c) and abs(n.vector.length-1)<.001 for n in me.corner_normals for c in n.vector),(key,'reimport normal')
    assert all(abs(v-1)<1e-6 for v in obj.matrix_world.to_scale())
    points=np.array([tuple(obj.matrix_world@v.co) for v in me.vertices]);source_points=original_points[entry['type'],entry['level']]
    assert max(np.max(np.abs(points.min(axis=0)-source_points.min(axis=0))),np.max(np.abs(points.max(axis=0)-source_points.max(axis=0))))<1e-4
    colors=me.color_attributes.active_color;assert colors and len({tuple(round(c,4) for c in v.color[:3]) for v in colors.data})>4
    assert all(abs(c.color[3]-1)<1e-5 for c in colors.data)
    assert len(me.loop_triangles)==report['models'][key]['triangles']
    report['models'][key].update({'independently_reimported':True,'finite_unit_corner_normals':True,'degenerate_triangles':0,'vertex_color_preserved':True,'world_scale':[1,1,1],'ground_pivot_preserved':True})
    print('REIMPORT_OK',key,flush=True)
# The original map is reopened now, not substituted with a previous run's verdict.
bpy.ops.wm.open_mainfile(filepath=str(F.ART/'town_season1_v002_integrated/blend/integrated_village.blend'))
for label in ('beginning','middle','final'):assert C.digest(C.snapshot(bpy.data.scenes['INTEGRATED • '+label]))==C.digest(baseline[label]),('Original baseline drift',label)
review=ROOT/'blend/hiddenfaces_review.blend';bpy.ops.wm.open_mainfile(filepath=str(review));environment={}
for label,count in [('beginning',8),('middle',12),('final',14)]:
    for variant in ('ORIGINAL','OPTIMIZED'):
        scene=bpy.data.scenes[variant+' • '+label];snap=C.snapshot(scene);assert C.digest(snap)==C.digest(baseline[label]),('Review map drift',variant,label)
        plots=[o for o in scene.objects if o.get('plot_id')];assert len(plots)==count
        assert all(all(abs(s-1)<1e-6 for s in o.scale) for o in plots)
    environment[label]={'environment_sha256':baseline[label]['environment_sha256'],'presentation_sha256':baseline[label]['presentation_sha256'],'plot_count':count,'exact_original_environment_and_placements':True}
layout=manifest['layout'];kinds={b['kind'] for b in layout};local={}
for kind in kinds:
    before=S.hull([tuple(p[:2]) for n in (1,2,3) for p in original_points[kind,n]])
    after=S.hull([tuple(p[:2]) for n in (1,2,3) for p in output_points[kind,n]])
    assert before==after,(kind,'changed maximum-stage hull');local[kind]=after
pairs=[]
for i,a in enumerate(layout):
    for b in layout[i+1:]:
        gap=S.separation(S.footprint(a,local),S.footprint(b,local));assert gap>=.4-1e-5;pairs.append({'a':a['id'],'b':b['id'],'gap_m':gap})
assert len(pairs)==91
final=bpy.data.scenes['OPTIMIZED • final'];bpy.context.window.scene=final;bpy.context.view_layer.update();terrain=final.objects['Integrated • continuous terrain'];terrain.data.calc_loop_triangles()
ground=BVHTree.FromPolygons([terrain.matrix_world@v.co for v in terrain.data.vertices],[tuple(t.vertices) for t in terrain.data.loop_triangles],all_triangles=True)
def gz(x,y):return ground.ray_cast(Vector((x,y,30)),Vector((0,0,-1)),60)[0].z
contacts={}
for b in layout:
    d=gz(*b['xy'])-b['ground'];assert abs(d)<.025,(b['id'],'ground contact');contacts[b['id']]=d
colliders={}
for b in layout:
    for n in (1,2,3):
        entry=next(e for e in manifest['assets'] if e['type']==b['kind'] and e['level']==n);doc,blob,_=F.read(F.ART/entry['path']);p=F.primitive(doc);points=output_points[b['kind'],n]
        world=[(*S.world_xy(b,point),point[2]+b['ground']) for point in points];faces=np.array(F.accessor(doc,blob,p['indices']),dtype=np.int64).reshape(-1,3).tolist()
        colliders[b['id'],n]=BVHTree.FromPolygons(world,faces,all_triangles=True)
access=json.loads((F.ART/'town_season1_v002_integrated/reports/access.json').read_text());assert len(access['primary_doors'])==42;failures=[];segments=0
for row in access['primary_doors']:
    others=[bv for (key,n),bv in colliders.items() if key!=row['plot'] or n==row['level']]
    for aa,bb in zip(row['points'],row['points'][1:]):
        a=Vector(aa);b=Vector(bb);d=b-a
        if d.length<1e-5:continue
        side=Vector((-d.y,d.x)).normalized();steps=max(2,math.ceil(d.length/.12))
        for off in (-.30,0,.30):
            pp=[a.lerp(b,i/steps)+side*off for i in range(steps+1)]
            for height in (.3,.85,1.5):
                world=[Vector((p.x,p.y,gz(p.x,p.y)+height)) for p in pp]
                for p,q in zip(world,world[1:]):
                    dd=q-p
                    if dd.length<1e-6:continue
                    segments+=1
                    if any(bv.ray_cast(p,dd.normalized(),dd.length-.00001)[0] is not None for bv in others):failures.append((row['plot'],row['level'],height,off,tuple(p)));break
assert not failures,failures[:12]
report.update({'review_map_reopened':True,'original_component_blends_reopened':True,'all_36_reimports_passed':True,'environment':environment,
 'ground_contacts_m':contacts,'maximum_stage_hulls_unchanged':True,'maximum_stage_pairs':pairs,'overlap_pairs':0,
 'primary_entry_stage_cases':42,'walk_ray_heights_m':[.3,.85,1.5],'walk_ray_offsets_m':[-.3,0,.3],'tested_ray_segments':segments,'entry_collisions':0,
 'review_blend_sha256':F.sha(review),'manifest_sha256':F.sha(ROOT/'reports/manifest.json'),'protected_original_files_unchanged':F.protect(),'passed':True})
(ROOT/'reports/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('ALL_36_INDEPENDENT_VALIDATION_COMPLETE',flush=True)
