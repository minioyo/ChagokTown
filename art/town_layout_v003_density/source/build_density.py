"""Controlled density study from the exact saved v002 A scene and camera."""
import bpy,sys,json,math,hashlib,heapq
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.geometry import delaunay_2d_cdt
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'town_layout_v002_concepts';ART=ROOT.parent
PREVIEW='--preview' in sys.argv
LAYOUT=json.loads((ROOT/'source/layouts.json').read_text())
METRICS=json.loads((ROOT/'reports/placement_metrics.json').read_text())
for d in ('blend','renders','reports'):(ROOT/d).mkdir(exist_ok=True)
source_paths=[p for p in OLD.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
FOLDERS={'house':'town_house_florist_v001','florist':'town_house_florist_v001','cafe':'town_cafe_v003',
         'bakery':'town_sol_bakery_bookshop_v001','workshop':'town_sol_civic_market_workshop_v001','grocer':'town_sol_civic_market_workshop_v001','bookshop':'town_sol_bakery_bookshop_v001'}
for b in LAYOUT['Dense']:
    source_paths.append(ART/FOLDERS[b['kind']]/'exports'/f"{b['kind']}_level_{b['level']}.glb")
before={str(p.relative_to(ART)):hashlib.sha256(p.read_bytes()).hexdigest() for p in set(source_paths)}
(ROOT/'reports/read_only_sources.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
bpy.ops.wm.open_mainfile(filepath=str(OLD/'blend/chagok_layout_v002_concepts.blend'))
base=bpy.data.scenes['A • composition concept'];base.name='Baseline • v002 A'
if bpy.data.scenes.get('B • composition concept'):bpy.data.scenes.remove(bpy.data.scenes['B • composition concept'])
bpy.context.window.scene=base
def model_objects(s):return [o for o in s.objects if o.type=='EMPTY' and o.instance_type=='COLLECTION' and o.get('kind')]
def id_of(o):return o.name.split(' • ')[1]
BASE_OBJECTS={id_of(o):o for o in model_objects(base)}
assert set(BASE_OBJECTS)=={b['id'] for b in LAYOUT['Baseline']}
CAMERA=base.camera.matrix_world.copy();ORTHO=base.camera.data.ortho_scale
assert abs(ORTHO-28)<1e-6 and not base.camera.data.dof.use_dof
def calibration(s):
    lights=[]
    for o in s.objects:
        if o.type=='LIGHT':
            d=o.data;lights.append((d.type,round(d.energy,6),tuple(round(x,6) for x in d.color),tuple(round(x,6) for row in o.matrix_world for x in row),round(getattr(d,'size',0),6),round(getattr(d,'angle',0),6)))
    world_nodes=[(n.type,[(i.name,str(tuple(i.default_value)) if hasattr(i.default_value,'__len__') else str(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]) for n in s.world.node_tree.nodes]
    return {'camera_matrix':[list(row) for row in s.camera.matrix_world],'ortho':s.camera.data.ortho_scale,'lights':sorted(lights),
            'world':world_nodes,'transform':s.view_settings.view_transform,'look':s.view_settings.look,
            'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'dof':s.camera.data.dof.use_dof}
CALIBRATION=calibration(base)
def yaw(b):
    if 'yaw' in b:return math.radians(b['yaw'])
    x,y=b['xy'];tx,ty=b['toward'];return math.atan2(tx-x,-(ty-y))
def point(b,xy):
    a=yaw(b);c=math.cos(a);s=math.sin(a);sc=b['scale']
    return (b['xy'][0]+sc*(c*xy[0]-s*xy[1]),b['xy'][1]+sc*(s*xy[0]+c*xy[1]))
DOORS={('cafe',2):(1,-1.68),('cafe',1):(.72,-1.60),('bakery',3):(-1.1034,-1.66),('florist',2):(-.65,-1.59),('florist',1):(-.59,-1.49),
       ('house',2):(.67,-1.60),('house',1):(.57,-1.53),('bookshop',3):(.7803,-1.64),('workshop',2):(-.57,-1.54)}
DOORS[('house',3)]=(.67,-1.66);DOORS[('grocer',1)]=(0,-1.58)

def make_warp():
    old=LAYOUT['Baseline'];new={b['id']:b for b in LAYOUT['Compact']}
    anchors=[(tuple(b['xy']),tuple(new[b['id']]['xy'])) for b in old]
    anchors += [((.34,.24),(-.15,-.10)),((-2.55,4.32),(-2.65,2.50)),((-2.55,6.35),(-2.65,4.00))]
    anchors += [((x,y),(x,y)) for x,y in [(-18,-12),(18,-12),(-18,18),(18,18),(0,-12),(0,18),(-18,3),(18,3)]]
    # The ground is triangulated between authored movement anchors. Model meshes
    # never pass through this warp. A positive Jacobian is required on every cell.
    result=delaunay_2d_cdt([Vector(p) for p,q in anchors],[],[],0,1e-6,True)
    vv,edges,faces=result[:3]
    target=[]
    for v in vv:
        i=min(range(len(anchors)),key=lambda i:(v-Vector(anchors[i][0])).length_squared)
        assert (v-Vector(anchors[i][0])).length<1e-4
        target.append(anchors[i][1])
    triangles=[];bad=[]
    for face in faces:
        if len(face)!=3:continue
        src=np.array([tuple(vv[i]) for i in face]);dst=np.array([target[i] for i in face])
        sa=src[1]-src[0];sb=src[2]-src[0];da=dst[1]-dst[0];db=dst[2]-dst[0]
        aa=sa[0]*sb[1]-sa[1]*sb[0];bb=da[0]*db[1]-da[1]*db[0]
        if aa*bb<=0:bad.append((face,float(aa),float(bb)))
        transform=np.linalg.inv(np.vstack((src.T,np.ones(3))))
        triangles.append((src,dst,transform))
    assert not bad,('Ground warp folds',bad)
    def warp(points):
        points=np.asarray(points,dtype=float);out=points.copy();remaining=np.ones(len(points),dtype=bool)
        for src,dst,inv in triangles:
            ids=np.where(remaining & (points[:,0]>=src[:,0].min()-1e-7)&(points[:,0]<=src[:,0].max()+1e-7)&(points[:,1]>=src[:,1].min()-1e-7)&(points[:,1]<=src[:,1].max()+1e-7))[0]
            if not len(ids):continue
            weights=np.column_stack((points[ids,:2],np.ones(len(ids))))@inv.T
            valid=np.min(weights,axis=1)>=-1e-6;ids=ids[valid];weights=weights[valid]
            out[ids,:2]=weights@dst;remaining[ids]=False
        return out
    return warp,len(triangles)
WARP,WARP_TRIANGLES=make_warp()
def warp_xy(x,y):return WARP(np.array([[x,y,0.0]]))[0,:2]

def duplicate_scene(source,name):
    bpy.context.window.scene=source;bpy.ops.scene.new(type='FULL_COPY');s=bpy.context.scene;s.name=name
    # Keep each base building's exact original collection, material and geometry.
    for o in model_objects(s):
        key=id_of(o)
        if key in BASE_OBJECTS:o.instance_collection=BASE_OBJECTS[key].instance_collection
    return s
def baked_world(o):
    evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
    mat=o.matrix_world.copy();coords=np.array([tuple(mat@v.co) for v in me.vertices])
    o.modifiers.clear();o.data=me;o.matrix_world=Matrix.Identity(4)
    return me,coords
def terrain_bvh(s):
    terrain=next(o for o in s.objects if o.type=='MESH' and 'continuous terrain' in o.name)
    terrain.data.calc_loop_triangles()
    return BVHTree.FromPolygons([terrain.matrix_world@v.co for v in terrain.data.vertices],[tuple(t.vertices) for t in terrain.data.loop_triangles],all_triangles=True)
def ground(bvh,x,y):
    p=bvh.ray_cast(Vector((x,y,40)),Vector((0,0,-1)),80)[0]
    return p.z if p else 0.0
def move_group(objects,old_xy,new_xy,bvh):
    if not objects:return
    old_z=min((o.matrix_world@Vector(c)).z for o in objects for c in o.bound_box)
    new_z=ground(bvh,*new_xy)
    for o in objects:o.location+=Vector((new_xy[0]-old_xy[0],new_xy[1]-old_xy[1],new_z-old_z))

def warp_environment(s):
    bpy.context.window.scene=s;bpy.context.view_layer.update()
    meshes=[o for o in s.objects if o.type=='MESH']
    rigid=[o for o in meshes if o.name.startswith(('Tree •','Shrub •','Rock •','Shared bench •','Lane light •')) or any(n in o.name for n in ('low well stone','well water','well coping','tree stone edging'))]
    for o in meshes:
        if o in rigid:continue
        me,coords=baked_world(o);coords=WARP(coords)
        me.vertices.foreach_set('co',coords.astype(np.float32).ravel());me.update()
    bpy.context.view_layer.update();bvh=terrain_bvh(s)
    # Existing forest stays the same population and approximate framing. Only its
    # ground contact is corrected; the old focal tree moves out of the narrow court.
    trunks=[o for o in rigid if o.name.startswith('Tree • warm trunk')]
    for trunk in trunks:
        xy=tuple(trunk.location[:2]);group=[o for o in rigid if o.name.startswith('Tree •') and min(trunks,key=lambda t:math.dist(o.location[:2],t.location[:2]))==trunk]
        new=(-8.8,-1.3) if math.dist(xy,(-1.75,-1.05))<.15 else xy
        move_group(group,xy,new,bvh)
    wells=[o for o in rigid if any(n in o.name for n in ('low well stone','well water','well coping'))]
    move_group(wells,(.34,.24),(-.15,-.10),bvh)
    edge=[o for o in rigid if 'tree stone edging' in o.name];move_group(edge,(-1.75,-1.05),(-8.8,-1.3),bvh)
    benches=[o for o in rigid if o.name.startswith('Shared bench •')];move_group(benches,(-.96,-1.4),(-5.8,3.8),bvh)
    posts=[o for o in rigid if o.name.startswith('Lane light • post')]
    for post in posts:
        xy=tuple(post.location[:2]);group=[o for o in rigid if o.name.startswith('Lane light •') and min(posts,key=lambda p:math.dist(o.location[:2],p.location[:2]))==post]
        move_group(group,xy,warp_xy(*xy),bvh)
    for o in rigid:
        if o.name.startswith(('Shrub •','Rock •')):
            xy=tuple(o.location[:2]);new=warp_xy(*xy);move_group([o],xy,new,bvh)
    return bvh

def asset_collection(kind,level):
    name=f'ASSET • {kind}_level_{level}'
    if bpy.data.collections.get(name):return bpy.data.collections[name]
    library=bpy.data.scenes['LIBRARY • unchanged source GLBs'];current=bpy.context.window.scene;bpy.context.window.scene=library
    previous=set(library.objects)
    bpy.ops.import_scene.gltf(filepath=str(ART/FOLDERS[kind]/'exports'/f'{kind}_level_{level}.glb'))
    col=bpy.data.collections.new(name);library.collection.children.link(col)
    for o in set(library.objects)-previous:
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o)
    bpy.context.window.scene=current;return col
PATH_MAT=next(m for m in bpy.data.materials if m.name=='Path')
def surface_strip(s,name,points,bvh,width=.72,lift=.12):
    samples=[]
    for a,b in zip(points,points[1:]):
        n=max(2,math.ceil(math.dist(a,b)/.18))
        for i in range(n):samples.append(Vector(a).lerp(Vector(b),i/n))
    samples.append(Vector(points[-1]));vs=[];across=4
    for i,p in enumerate(samples):
        d=samples[min(i+1,len(samples)-1)]-samples[max(i-1,0)]
        if d.length<1e-8:d=Vector((1,0))
        d.normalize();side=Vector((-d.y,d.x))
        for j in range(across+1):
            q=p+side*((j/across-.5)*width);vs.append((q.x,q.y,ground(bvh,q.x,q.y)+lift))
    faces=[]
    for i in range(len(samples)-1):
        for j in range(across):
            a=i*(across+1)+j;faces.append((a+across+1,a+across+2,a+1,a))
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],faces);me.materials.append(PATH_MAT)
    o=bpy.data.objects.new(name,me);s.collection.objects.link(o);o.visible_shadow=False
    return o
def pose(o,b):
    o.location=(*b['xy'],b['ground']-.065*b['scale']);o.rotation_euler=(0,0,yaw(b));o.scale=(b['scale'],)*3
def current_model_map(s):return {id_of(o):o for o in model_objects(s)}
ACCESS={}
def road_candidates(s):
    points=[]
    for o in s.objects:
        if o.type=='MESH' and any(m and (m.name=='Path' or m.name.startswith('Path.')) for m in o.data.materials) and any(n in o.name.lower() for n in ('lane','alley','threshold','court','landing','approach')):
            stride=max(1,len(o.data.vertices)//180)
            points += [tuple((o.matrix_world@o.data.vertices[i].co).xy) for i in range(0,len(o.data.vertices),stride)]
    return list(set((round(x,4),round(y,4)) for x,y in points))
def building_bvhs(s):
    bpy.context.window.scene=s;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();result={}
    for instance in model_objects(s):
        vertices=[];faces=[]
        for obj in instance.instance_collection.all_objects:
            if obj.type!='MESH':continue
            ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();offset=len(vertices)
            transform=instance.matrix_world@obj.matrix_world
            vertices += [transform@v.co for v in me.vertices]
            faces += [tuple(offset+i for i in t.vertices) for t in me.loop_triangles];ev.to_mesh_clear()
        result[id_of(instance)]=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
    return result
def clear_walk(points,bvh,obstacles,half_width,height):
    for aa,bb in zip(points,points[1:]):
        a=Vector(aa);b=Vector(bb);delta=b-a
        if delta.length<.03:continue
        normal=Vector((-delta.y,delta.x)).normalized();steps=max(2,math.ceil(delta.length/.25))
        for offset in (-half_width,0,half_width):
            positions=[]
            for i in range(steps+1):
                p=a.lerp(b,i/steps)+normal*offset
                positions.append(Vector((p.x,p.y,ground(bvh,p.x,p.y)+height)))
            for p,q in zip(positions,positions[1:]):
                d=q-p
                if d.length<1e-6:continue
                # A doorstep strip may follow gentle ground, never bridge a
                # retaining-wall drop as an almost vertical paving curtain.
                if abs(d.z)>max(.025,.70*math.hypot(d.x,d.y)):return False
                for collider in obstacles.values():
                    hit=collider.ray_cast(p,d.normalized(),d.length)
                    if hit[0] is not None and hit[3]<d.length-.0001:return False
    return True
def connection(start,candidates,bvh,obstacles,half_width,height,preferred=None,lead=None):
    options=[]
    if preferred is not None:options.append(tuple(preferred))
    options += sorted(candidates,key=lambda p:math.dist(start,p))[:260]
    prefixes=[[start]]+([[start,lead]] if lead else [])
    for prefix in prefixes:
        for end in options:
            points=prefix+[end]
            if clear_walk(points,bvh,obstacles,half_width,height):return points
        origin=prefix[-1]
        for end in options[:100]:
            for middle in ((origin[0],end[1]),(end[0],origin[1])):
                points=prefix+[middle,end]
                if clear_walk(points,bvh,obstacles,half_width,height):return points
    # Infill behind a shop sometimes needs more than one corner. A small local
    # grid traces a walk around the real meshes instead of drawing up a wall.
    for prefix in reversed(prefixes):
        if not clear_walk(prefix,bvh,obstacles,half_width,height):continue
        origin=prefix[-1];step=.38
        def xy(node):return (origin[0]+node[0]*step,origin[1]+node[1]*step)
        def heuristic(p):return min(math.dist(p,q) for q in candidates)
        queue=[(heuristic(origin),0,(0,0))];cost={(0,0):0};previous={};visited=set();serial=0
        while queue and len(visited)<2300:
            _,_,node=heapq.heappop(queue)
            if node in visited:continue
            visited.add(node);p=xy(node)
            nearby=sorted(candidates,key=lambda q:math.dist(p,q))[:8]
            end=next((q for q in nearby if math.dist(p,q)<.72 and clear_walk([p,q],bvh,obstacles,half_width,height)),None)
            if end is not None:
                nodes=[node]
                while nodes[-1] in previous:nodes.append(previous[nodes[-1]])
                path=prefix+[xy(n) for n in reversed(nodes[:-1])]+[end]
                simplified=[path[0]];index=0
                while index<len(path)-1:
                    farthest=next(j for j in range(len(path)-1,index,-1) if clear_walk([path[index],path[j]],bvh,obstacles,half_width,height))
                    simplified.append(path[farthest]);index=farthest
                return simplified
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                nxt=(node[0]+dx,node[1]+dy)
                if max(abs(nxt[0]),abs(nxt[1]))>28 or nxt in visited:continue
                q=xy(nxt);value=cost[node]+math.dist(p,q)
                if value>=cost.get(nxt,float('inf')):continue
                if not clear_walk([p,q],bvh,obstacles,half_width,height):continue
                cost[nxt]=value;previous[nxt]=node;serial+=1
                heapq.heappush(queue,(value+heuristic(q),serial,nxt))
    raise AssertionError(('No clear doorstep connection',start))
compact=duplicate_scene(base,'Compact • same eight models')
for key,o in current_model_map(compact).items():pose(o,next(b for b in LAYOUT['Compact'] if b['id']==key))
compact_bvh=warp_environment(compact)
compact_obstacles=building_bvhs(compact);compact_roads=road_candidates(compact);ACCESS['Compact']={}
# Each unchanged model keeps its entrance connected after a turn of its facade.
for i,b in enumerate(LAYOUT['Compact']):
    original=next(o for o in LAYOUT['Baseline'] if o['id']==b['id'])
    local=DOORS[(b['kind'],b['level'])];start=point(b,local);old_start=point(original,local);end=tuple(warp_xy(*old_start))
    half_width=min(.24,.32*b['scale']);height=min(.55,.85*b['scale'])
    path=connection(start,compact_roads,compact_bvh,compact_obstacles,half_width,height,end)
    ACCESS['Compact'][b['id']]={'points':path,'three_ray_half_width_m':half_width,'height_above_terrain_m':height,'sampled_ground_grade_limit':.70,'clear_of_current_building_meshes':True}
    if math.dist(path[0],path[-1])>.08:surface_strip(compact,'Approach • '+b['id'],path,compact_bvh,2*half_width+.08,.105+i*.002)
dense=duplicate_scene(compact,'Dense • sixteen existing copies');bpy.context.window.scene=dense
dense_bvh=terrain_bvh(dense)
# Collect the shared paving, then add short individual thresholds to it.
road_points=road_candidates(dense)
for i,b in enumerate(LAYOUT['Dense'][8:]):
    obj=bpy.data.objects.new('A • '+b['id']+' • background infill',None);dense.collection.objects.link(obj)
    obj.instance_type='COLLECTION';obj.instance_collection=asset_collection(b['kind'],b['level'])
    # Background houses adopt the existing terrain level; primary eight heights never change.
    b['ground']=ground(dense_bvh,*b['xy']);pose(obj,b);obj['kind']=b['kind'];obj['display_level']=b['level'];obj['background_only']=True
dense_obstacles=building_bvhs(dense);ACCESS['Dense']={}
for i,b in enumerate(LAYOUT['Dense']):
    start=point(b,DOORS[(b['kind'],b['level'])]);half_width=min(.24,.32*b['scale']);height=min(.55,.85*b['scale'])
    local=DOORS[(b['kind'],b['level'])];lead=point(b,(local[0],local[1]-.9))
    path=connection(start,road_points,dense_bvh,dense_obstacles,half_width,height,lead=lead)
    ACCESS['Dense'][b['id']]={'points':path,'three_ray_half_width_m':half_width,'height_above_terrain_m':height,'sampled_ground_grade_limit':.70,'clear_of_current_building_meshes':True}
    if math.dist(path[0],path[-1])>.08:surface_strip(dense,'Connected threshold • '+b['id'],path,dense_bvh,2*half_width+.08,.13+i*.003)
(ROOT/'reports/entrance_checks.json').write_text(json.dumps(ACCESS,indent=2),encoding='utf-8')

def triangles_in_collection(coll):
    total=0;dg=bpy.context.evaluated_depsgraph_get()
    for obj in coll.all_objects:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();total+=len(me.loop_triangles);ev.to_mesh_clear()
    return total
for label,s in [('Baseline',base),('Compact',compact),('Dense',dense)]:
    bpy.context.window.scene=s;bpy.context.view_layer.update()
    assert calibration(s)==CALIBRATION,'Camera/light/colour drift: '+label
    objects=current_model_map(s)
    for b in LAYOUT[label]:
        o=objects[b['id']]
        if b.get('source_id'):
            old=BASE_OBJECTS[b['source_id']];assert o.instance_collection==old.instance_collection
            assert all(abs(x-b['scale'])<1e-6 for x in o.scale)
            assert max(abs(x-y) for x,y in zip(o.scale,old.scale))<1e-6
            assert o.get('display_level')==old.get('display_level') and o.get('kind')==old.get('kind')
    METRICS[label]['building_triangles']=sum(triangles_in_collection(o.instance_collection) for o in model_objects(s))
    environment_triangles=0
    for obj in s.objects:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
        environment_triangles+=len(me.loop_triangles);ev.to_mesh_clear()
    METRICS[label]['environment_triangles']=environment_triangles
    METRICS[label]['total_visible_scene_triangles']=environment_triangles+METRICS[label]['building_triangles']
    METRICS[label]['tree_count']=sum(o.type=='MESH' and o.name.startswith('Tree • warm trunk') for o in s.objects)
    METRICS[label]['calibration_matches_baseline']=True
METRICS['control']={'camera_and_lights_identical':True,'base_eight_collections_identical':True,'base_eight_scales_identical':True,
                    'world_materials_and_colour_management_unchanged':True,'warp_cells_no_folds':WARP_TRIANGLES,
                    'oblique_ortho_m':28,'top_ortho_m':35,'resolution':[1920,1080],'depth_of_field':False}
(ROOT/'reports/calibration.json').write_text(json.dumps(CALIBRATION,indent=2),encoding='utf-8')
(ROOT/'reports/density_metrics.json').write_text(json.dumps(METRICS,indent=2),encoding='utf-8')
(ROOT/'reports/display_layouts.json').write_text(json.dumps(LAYOUT,indent=2),encoding='utf-8')
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    device='GPU' if any(d.type!='CPU' for d in prefs.devices) else 'CPU'
except Exception:device='CPU'
for s in (base,compact,dense):
    s.camera.matrix_world=CAMERA;s.camera.data.ortho_scale=28;s.camera.data.dof.use_dof=False
    s.render.resolution_x=1440 if PREVIEW else 1920;s.render.resolution_y=810 if PREVIEW else 1080;s.render.resolution_percentage=100
    s.cycles.samples=24 if PREVIEW else 64;s.cycles.device=device
bpy.context.window.scene=compact;bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/chagok_density_comparison.blend'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/chagok_density_comparison.blend'))
for label,name in [('Compact','Compact • same eight models'),('Dense','Dense • sixteen existing copies')]:
    s=bpy.data.scenes[name];bpy.context.window.scene=s
    for top in (False,True):
        if top:s.camera.location=(0,3,45);s.camera.rotation_euler=(0,0,0);s.camera.data.ortho_scale=35
        else:s.camera.matrix_world=CAMERA;s.camera.data.ortho_scale=28
        filename=label.lower()+('_top' if top else '_oblique')+'.png'
        s.render.filepath=str(ROOT/'renders'/(('preview_' if PREVIEW else '')+filename))
        bpy.ops.render.render(write_still=True);print('RENDERED',filename,flush=True)
for view in ('oblique','top'):
    src=OLD/'renders'/f'A_{view}.png';dst=ROOT/'renders'/f'baseline_{view}.png';dst.write_bytes(src.read_bytes())
assert all(hashlib.sha256((ART/p).read_bytes()).hexdigest()==h for p,h in before.items())
(ROOT/'reports/completion.json').write_text(json.dumps({'blend_reopened':True,'previous_files_unchanged':len(before),
    'baseline_pngs_copied_byte_exact':True,'preview':PREVIEW,'render_device':device,'scope':'density comparison only'},indent=2),encoding='utf-8')
print('DENSITY_COMPARISON_COMPLETE',flush=True)
