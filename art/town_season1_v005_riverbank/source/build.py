"""Add sparse riverbank props without changing a v004 environment datablock."""
import bpy, bmesh, math, json, sys
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT.parent
sys.path.insert(0, str(ROOT/'source'))
sys.dont_write_bytecode = True
import scene_checks as C
import glb as F

SOURCE = ART/'town_season1_v004_roof_tones/blend/roof_tones_review.blend'
LABELS = ('beginning', 'middle', 'final')
F.protect()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
originals = {n:bpy.data.scenes['AFTER roof tones • '+n] for n in LABELS}
baseline = {n:C.snapshot(s) for n,s in originals.items()}
scene = originals['final']
bpy.context.window.scene = scene
bpy.context.view_layer.update()

def bvh(obj):
    obj.data.calc_loop_triangles()
    return BVHTree.FromPolygons([obj.matrix_world@v.co for v in obj.data.vertices], [t.vertices[:] for t in obj.data.loop_triangles], all_triangles=True)

terrain = bvh(scene.objects['Integrated • continuous terrain'])
water_z = (scene.objects['Stream • continuous water'].matrix_world@scene.objects['Stream • continuous water'].data.vertices[0].co).z

def ground(x,y):
    hit, normal, _, _ = terrain.ray_cast(Vector((x,y,20)),Vector((0,0,-1)),40)
    assert hit is not None
    return hit.z, normal

def bank_x(y,side):
    # Locate dry ground at the water elevation using the actual saved terrain.
    # This is deliberately independent of the former terrain generator.
    xs = [12+i*.025 for i in range(241)]
    under = [x for x in xs if ground(x,y)[0] < water_z]
    assert under, y
    lo,hi = (min(under)-.05,min(under)+.05) if side<0 else (max(under)-.05,max(under)+.05)
    for _ in range(24):
        mid=(lo+hi)/2
        if (ground(mid,y)[0]>water_z) == (side<0):lo=mid
        else:hi=mid
    return (lo+hi)/2

mat = bpy.data.materials.new('Riverbank • opaque vertex palette')
mat.use_nodes = True
mat.use_backface_culling = True
bsdf = mat.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Roughness'].default_value = .78
bsdf.inputs['Metallic'].default_value = 0
vc = mat.node_tree.nodes.new('ShaderNodeVertexColor')
vc.layer_name = 'Palette'
mat.node_tree.links.new(vc.outputs['Color'],bsdf.inputs['Base Color'])
palette = {name:list(bpy.data.materials[name].diffuse_color) for name in ('Stone shade','Wall stone','Leaf','Leaf light')}

def color_mesh(me,colors):
    me.materials.append(mat)
    attr = me.color_attributes.new(name='Palette',type='FLOAT_COLOR',domain='CORNER')
    for p in me.polygons:
        color = colors[p.index] if isinstance(colors[0],list) else colors
        for li in p.loop_indices:attr.data[li].color=color
    me.color_attributes.active_color = attr
    me.update()

rocks = []
for i in range(3):
    bm=bmesh.new()
    bmesh.ops.create_icosphere(bm,subdivisions=2,radius=1)
    for v in bm.verts:
        x,y,z=v.co
        f=1+.045*math.sin(x*5+y*3+i*1.9)+.025*math.cos(z*7-y*2)
        v.co=(x*f,y*f,z*(1+.045*math.sin(x*4+i)))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    me=bpy.data.meshes.new(f'Riverbank form • rounded stone {i+1}')
    bm.to_mesh(me);bm.free()
    for p in me.polygons:p.use_smooth=True
    color_mesh(me,palette['Stone shade' if i!=1 else 'Wall stone'])
    rocks.append(me)

tufts=[]
for form,count in enumerate((3,4,4)):
    vertices=[];faces=[];colors=[];root_ids=[]
    for j in range(count):
        a=j*2.399+form*.7
        height=(.23,.31,.265,.285)[j]*(1+form*.025)
        lean=Vector((math.cos(a)*.115,math.sin(a)*.115,0))
        root=Vector((math.cos(a)*.033,math.sin(a)*.033,0))
        start=len(vertices)
        for ring in range(2):
            center=root+lean*(.38 if ring else 0)+Vector((0,0,height*.55 if ring else 0))
            radius=.019 if ring==0 else .025
            for k in range(3):
                t=a+k*math.tau/3
                vertices.append(tuple(center+Vector((math.cos(t)*radius,math.sin(t)*radius,0))))
        vertices.append(tuple(root+lean+Vector((0,0,height))))
        root_ids.extend(range(start,start+3))
        local=[(0,2,1)]
        for k in range(3):
            n=(k+1)%3
            local.extend([(k,n,n+3),(k,n+3,k+3),(k+3,n+3,6)])
        faces.extend(tuple(start+k for k in f) for f in local)
        colors.extend([palette['Leaf light' if (j+form)%3==0 else 'Leaf']]*len(local))
    me=bpy.data.meshes.new(f'Riverbank form • short grass {form+1}')
    me.from_pydata(vertices,[],faces)
    color_mesh(me,colors)
    me['root_vertex_indices']=root_ids
    tufts.append(me)

collection=bpy.data.collections.new('RIVERBANK v005 • sparse stones and short grass')
specs=[('01 downstream inner',-13.0,-1,3,2,.96),('02 downstream outer',-9.4,1,2,1,.90),
       ('03 upstream inner',-.1,-1,2,3,1.04),('04 upper outer',5.2,1,3,2,.86),('05 upper inner',11.2,-1,2,2,.94)]
placements=[]
for group_index,(group,y,side,count,grass_count,stone_size) in enumerate(specs):
    col=bpy.data.collections.new('Riverbank cluster • '+group)
    collection.children.link(col)
    stone_specs=[(-.24,.045,(.35,.255,.205),17),(.31,.16,(.245,.185,.15),-29),(.02,.43,(.17,.14,.11),54)]
    for j,(dy,dry,scale,yaw) in enumerate(stone_specs[:count]):
        yy=y+dy;xx=bank_x(yy,side)+side*dry
        z,normal=ground(xx,yy)
        o=bpy.data.objects.new(f'Riverbank • {group} • stone {j+1}',rocks[(j+len(placements))%3])
        col.objects.link(o)
        o.location=(xx,yy,z-.035)
        o.rotation_mode='QUATERNION'
        o.rotation_quaternion=normal.to_track_quat('Z','Y')@Quaternion(Vector((0,0,1)),math.radians(yaw+side*13+group_index*19))
        o.scale=tuple(s*stone_size for s in scale);o['riverbank_kind']='stone';o['cluster']=group
        placements.append({'object':o.name,'kind':'stone','cluster':group,'ground_z':z,'bank_side':side,'shape':o.data.name})
    grass_specs=[(-.38,.60,.83,18),(.43,.56,1.0,113)]
    if grass_count==1:grass_specs=[(.30,.52,.91,77)]
    elif grass_count==3:grass_specs.append((.06,.85,.73,218))
    for j,(dy,dry,size,yaw) in enumerate(grass_specs):
        size*=.93+(group_index%3)*.055
        yy=y+dy;xx=bank_x(yy,side)+side*dry
        z,_=ground(xx,yy)
        me=tufts[(j+len(placements))%3]
        o=bpy.data.objects.new(f'Riverbank • {group} • short grass {j+1}',me)
        col.objects.link(o);o.location=(xx,yy,z-.035);o.rotation_euler.z=math.radians(yaw+int(y*3));o.scale=(size,)*3
        # Every basal triangle is placed below the sampled ground, without floating roots.
        matrix=Matrix.LocRotScale(o.location,o.rotation_euler.to_quaternion(),o.scale)
        root_z=[(matrix@me.vertices[k].co).z-ground(*(matrix@me.vertices[k].co)[:2])[0] for k in me['root_vertex_indices']]
        o.location.z-=max(0,max(root_z)+.008)
        o['riverbank_kind']='grass';o['cluster']=group
        placements.append({'object':o.name,'kind':'grass','cluster':group,'ground_z':z,'bank_side':side,'shape':me.name})

props=list(collection.all_objects)
for label,source in originals.items():
    new=source.copy();new.name='RIVERBANK v005 • '+label;new.use_fake_user=True
    new.collection.children.link(collection)
    snap=C.snapshot(new)
    for o in props:snap['environment'].pop(o.name)
    snap['environment_sha256']=C.digest(snap['environment'])
    assert C.digest(snap)==C.digest(baseline[label]),label
    assert C.digest(C.snapshot(source))==C.digest(baseline[label]),label

edit_scene=bpy.data.scenes['RIVERBANK v005 • final']
bpy.context.window.scene=edit_scene
bpy.context.view_layer.update()
for row in placements:
    o=bpy.data.objects[row['object']]
    row.update(matrix=[list(r) for r in o.matrix_world],origin=list(o.location),scale=list(o.scale))
    if row['kind']=='grass':
        gaps=[(o.matrix_world@o.data.vertices[k].co).z-ground(*(o.matrix_world@o.data.vertices[k].co)[:2])[0] for k in o.data['root_vertex_indices']]
        row['root_gap_range_m']=[min(gaps),max(gaps)]
        assert max(gaps)<0 and min(gaps)>-.12,(o.name,gaps)
    else:
        center=o.location;row['center_ground_gap_m']=center.z-ground(center.x,center.y)[0]
    # Avoid the wheel and the existing mill entrance in every growth scene.
    row['outside_mill_keepout_y']=not (-8.2<o.location.y<-2.0)
    assert row['outside_mill_keepout_y']

# Export a separate, single-mesh props asset at the unchanged town origin.
runtime=bpy.data.scenes.new('LIBRARY • riverbank props GLB');runtime.use_fake_user=True
bpy.context.window.scene=runtime
merged=bpy.data.meshes.new('Riverbank • combined props mesh')
asset=bpy.data.objects.new('riverbank_props_v005',merged);runtime.collection.objects.link(asset)
merged.materials.append(mat)
for o in props:
    clone=o.copy();clone.data=o.data.copy();runtime.collection.objects.link(clone);clone.select_set(True)
asset.select_set(True);bpy.context.view_layer.objects.active=asset
bpy.ops.object.join()
tri=asset.modifiers.new('Explicit triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name)
asset['units']='metres';asset['placement']='town world origin (0,0,0), rotation identity, scale 1'
asset['source_collection']=collection.name
path=ROOT/'exports/riverbank_props_v005.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_yup=True,export_extras=True,export_cameras=False,export_lights=False)
asset.select_set(False)
doc,blob,_=F.read(path);p=F.primitive(doc)
stats={'triangles':doc['accessors'][p['indices']]['count']//3,'exported_vertices':doc['accessors'][p['attributes']['POSITION']]['count'],
       'mesh_vertices':len(asset.data.vertices),'meshes':len(doc['meshes']),'materials':len(doc['materials']),'primitives':1,'textures':len(doc.get('textures',[])),
       'bytes':path.stat().st_size,'edit_objects':len(props),'edit_unique_meshes':len({o.data.name for o in props}),'stone_objects':12,'grass_tufts':10}
assert stats['triangles']<=1500,stats
assert len(doc.get('cameras',[]))==0 and len(doc['nodes'])==1

bpy.context.window.scene=edit_scene;bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/riverbank_review.blend'))
(ROOT/'reports/environment_baseline.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
(ROOT/'reports/placements.json').write_text(json.dumps({'coordinate_system':'Blender XY, +Z up, metres; town origin unchanged','runtime_placement':{'translation':[0,0,0],'rotation_xyzw':[0,0,0,1],'scale':[1,1,1]},'water_z':water_z,'clusters':5,'objects':placements},indent=2),encoding='utf-8')
(ROOT/'reports/model_stats.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
(ROOT/'reports/palette.json').write_text(json.dumps({'linear_rgba':palette,'roughness':.78,'metallic':0,'opaque':True,'source':'Exact existing v004 Stone shade, Wall stone, Leaf and Leaf light material diffuse colors'},indent=2),encoding='utf-8')
manifest=json.loads((ART/'town_season1_v004_roof_tones/reports/manifest.json').read_text())
manifest['revision']='town_season1_v005_riverbank'
manifest['source_manifest']='town_season1_v004_roof_tones/reports/manifest.json'
manifest['source_manifest_sha256']=F.sha(ART/manifest['source_manifest'])
manifest['buildings_unchanged']=True
manifest['riverbank']={'path':'town_season1_v005_riverbank/exports/riverbank_props_v005.glb','sha256':F.sha(path),'placement':'Identity at town origin; positions baked into mesh','placements':'reports/placements.json','stats':stats}
manifest['review_blend']={'path':'town_season1_v005_riverbank/blend/riverbank_review.blend','sha256':F.sha(ROOT/'blend/riverbank_review.blend'),'scenes':['RIVERBANK v005 • '+n for n in LABELS]}
(ROOT/'reports/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
F.protect()
print('RIVERBANK_BUILD_COMPLETE',json.dumps(stats),flush=True)
