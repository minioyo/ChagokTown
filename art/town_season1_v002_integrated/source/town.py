"""Whole-village layout and geography. No legacy central cluster is fixed."""
import bpy,math,json,hashlib,itertools
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent;OLD=ART/'town_season1_v001'
FOLDERS={'cafe':'town_cafe_v003','house':'town_house_florist_v001','florist':'town_house_florist_v001',
 'bakery':'town_sol_bakery_bookshop_v001','bookshop':'town_sol_bakery_bookshop_v001',
 'workshop':'town_sol_civic_market_workshop_v001','grocer':'town_sol_civic_market_workshop_v001','town_hall':'town_sol_civic_market_workshop_v001'}
NEW=('cathedral','inn','watermill','farmstead')
TARGETS=[('cathedral','cathedral',(0,10.2),5,1.2),('inn','inn',(-5,3.3),0,.25),
 ('home_upper_west','house',(-6,9.0),80,.8),('town_hall','town_hall',(7,5.7),-38,.8),
 ('home_upper_east','house',(7.4,10),-18,1.0),('bookshop','bookshop',(3.8,1.0),-30,.35),
 ('cafe','cafe',(-4.4,-2.6),85,0),('bakery','bakery',(.8,-3.8),-8,0),
 ('florist','florist',(7,-1.8),-85,0),('grocer','grocer',(-8.8,-4.8),55,0),
 ('home_entry','house',(-1,-8.8),10,0),('workshop','workshop',(4,-7.5),-80,0),
 ('farmstead','farmstead',(-12,1.5),25,0),('watermill','watermill',(11.8,-4.5),-15,-.15)]
COURTS={'cathedral':[(-1.25,4.15),(1.7,4.0),(2.2,5.15),(1.25,6.0),(-1.25,6.0)],
        'market':[(-1.7,-6.3),(.7,-6.75),(1.85,-5.75),(1.5,-4.75),(-.9,-4.5)]}

def protect():
    inputs=json.loads((ROOT/'reports/protected_art.json').read_text())
    assert all(hashlib.sha256((ART/p).read_bytes()).hexdigest()==h for p,h in inputs.items())
    return len(inputs)
def hull(points):
    pp=sorted(set(tuple(p) for p in points));lo=[];hi=[]
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    for p in pp:
        while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(pp):
        while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]
def local_points(col):
    dg=bpy.context.evaluated_depsgraph_get();result=[]
    for obj in col.all_objects:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(dg);me=ev.to_mesh();result.extend(obj.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
    return result
def world_xy(b,p):
    a=math.radians(b['yaw']);return (b['xy'][0]+math.cos(a)*p[0]-math.sin(a)*p[1],b['xy'][1]+math.sin(a)*p[0]+math.cos(a)*p[1])
def footprint(b,local):return [world_xy(b,p) for p in local[b['kind']]]
def separation(a,b):
    gap=-1e10
    for poly in (a,b):
        for p,q in zip(poly,poly[1:]+poly[:1]):
            dx=q[0]-p[0];dy=q[1]-p[1];ll=math.hypot(dx,dy);axis=(-dy/ll,dx/ll)
            aa=[x*axis[0]+y*axis[1] for x,y in a];bb=[x*axis[0]+y*axis[1] for x,y in b]
            gap=max(gap,min(aa)-max(bb),min(bb)-max(aa))
    return gap
def plan(local):
    offsets=sorted(((i*.15,j*.15) for i in range(-24,25) for j in range(-24,25)),key=lambda p:(p[0]*p[0]+p[1]*p[1],p[1],p[0]))
    placed=[]
    for key,kind,target,yaw,z in TARGETS:
        b={'id':key,'kind':kind,'xy':list(target),'yaw':yaw,'ground':z,'scale':1.0}
        for dx,dy in offsets:
            b['xy']=[round(target[0]+dx,3),round(target[1]+dy,3)];poly=footprint(b,local)
            if any(separation(poly,footprint(o,local))<.40 for o in placed):continue
            if any(separation(poly,poly2)<0 for court,poly2 in COURTS.items() if key!=court):continue
            break
        else:raise AssertionError(('No placement',key))
        placed.append(dict(b))
    return placed
def save_metrics(layout,local,label):
    pairs=[{'a':a['id'],'b':b['id'],'gap_m':separation(footprint(a,local),footprint(b,local))} for a,b in itertools.combinations(layout,2)]
    assert all(p['gap_m']>=-.0001 for p in pairs)
    def area(pp):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(pp,pp[1:]+pp[:1])))/2
    polys=[footprint(b,local) for b in layout];sum_area=sum(area(p) for p in polys);cluster_area=area(hull([p for poly in polys for p in poly]))
    result={'layout':layout,'local_max_stage_hulls':local,'world_max_stage_hulls':{b['id']:footprint(b,local) for b in layout},'pairs':pairs,
            'hull_area_sum_m2':sum_area,'cluster_hull_area_m2':cluster_area,'xy_coverage_percent':100*sum_area/cluster_area}
    (ROOT/'reports'/f'{label}_layout.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
def source_file(kind,level,study=False):
    if kind in NEW:return OLD/'exports'/f'{kind}_level_{level}.glb'
    if not study:return ROOT/'exports'/f'{kind}_level_{level}.glb'
    if kind in ('bakery','bookshop') and level==3:return OLD/'exports/reused_compact'/f'{kind}_level_3.glb'
    return ART/FOLDERS[kind]/'exports'/f'{kind}_level_{level}.glb'

def start_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(OLD/'blend/season1_map.blend'),link=False) as (src,dst):dst.scenes=['Season 1 • final']
    before=dst.scenes[0];before.name='REFERENCE • v001 unchanged'
    bpy.context.window.scene=before;bpy.context.view_layer.update()
    scene=bpy.data.scenes.new('INTEGRATED • final');bpy.context.window.scene=scene
    scene.world=before.world.copy()
    for original in before.objects:
        if original.type not in ('CAMERA','LIGHT'):continue
        obj=original.copy();obj.data=original.data.copy();scene.collection.objects.link(obj)
        if original==before.camera:scene.camera=obj
    for key in ('view_transform','look','exposure','gamma'):setattr(scene.view_settings,key,getattr(before.view_settings,key))
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    library=bpy.data.scenes.new('LIBRARY • imported runtime GLBs');return scene,library,before
def importer(scene,library,study=False):
    assets={}
    def asset(kind,level):
        key=(kind,level)
        if key in assets:return assets[key]
        current=bpy.context.window.scene;bpy.context.window.scene=library;previous=set(library.objects)
        bpy.ops.import_scene.gltf(filepath=str(source_file(kind,level,study)))
        col=bpy.data.collections.new(f'INPUT • {kind}_L{level}');library.collection.children.link(col)
        for obj in set(library.objects)-previous:
            for old in list(obj.users_collection):old.objects.unlink(obj)
            col.objects.link(obj)
        assets[key]=col;bpy.context.window.scene=current;return col
    return asset
def place(scene,layout,asset,level=3):
    for b in layout:
        obj=bpy.data.objects.new('PLOT • '+b['id'],None);scene.collection.objects.link(obj);obj.instance_type='COLLECTION';obj.instance_collection=asset(b['kind'],level)
        obj.location=(*b['xy'],b['ground']);obj.rotation_euler=(0,0,math.radians(b['yaw']));obj.scale=(1,1,1);obj['kind']=b['kind'];obj['plot_id']=b['id'];obj['level']=level
    bpy.context.window.scene=scene;bpy.context.view_layer.update()
def configure(scene,preview=False):
    prefs=bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type='OPTIX';prefs.get_devices()
        for device in prefs.devices:device.use=device.type!='CPU'
        gpu=any(d.type!='CPU' for d in prefs.devices)
    except Exception:gpu=False
    scene.render.engine='CYCLES';scene.cycles.device='GPU' if gpu else 'CPU';scene.cycles.samples=24 if preview else 64;scene.cycles.use_denoising=True
    scene.render.resolution_x=1600 if preview else 2400;scene.render.resolution_y=1000 if preview else 1500;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.camera.data.dof.use_dof=False
def top_camera(scene):scene.camera.location=(-1.5,2,55);scene.camera.rotation_euler=(0,0,0);scene.camera.data.ortho_scale=58
def ground_scene(scene,layout,local,make_routes=True):
    import geometry as G
    import standards as S
    G.scene=scene;G.PARENT=None;G.LOW=True;G.COL=G.collection('ENVIRONMENT • continuous village ground');S.materials()
    pads=[(b,footprint(b,local)) for b in layout]
    def inside(p,poly):
        x,y=p;result=False
        for a,b in zip(poly,poly[1:]+poly[:1]):
            if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
        return result
    def distance(p,poly):
        p=Vector(p);result=1e10
        for aa,bb in zip(poly,poly[1:]+poly[:1]):
            a=Vector(aa);delta=Vector(bb)-a;t=max(0,min(1,(p-a).dot(delta)/delta.length_squared));result=min(result,(p-a-delta*t).length)
        return result
    def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
    mill=next(b for b in layout if b['kind']=='watermill');wheel=world_xy(mill,(2.58,.15))
    channel=[(wheel[0]-.8,22),(wheel[0]-1.3,12),(wheel[0]-.2,5),(wheel[0]+.4,0),wheel,(wheel[0]-1.1,-10),(wheel[0]-2,-22)]
    def height(x,y):
        natural=.85*smooth((y+1)/9);best=(1e10,None)
        for b,poly in pads:
            if inside((x,y),poly):
                natural=b['ground'];best=(0,b);break
            d=distance((x,y),poly)
            if d<best[0]:best=(d,b)
        if best[0]<1.2:natural=best[1]['ground']+(natural-best[1]['ground'])*smooth(best[0]/1.2)
        dd=min(distance((x,y),[a,b]) for a,b in zip(channel,channel[1:]))
        # Preserve the mill's stone footing; the cut starts beyond its wall, under the wheel.
        a=math.radians(-mill['yaw']);dx=x-mill['xy'][0];dy=y-mill['xy'][1];mx=math.cos(a)*dx-math.sin(a)*dy;my=math.sin(a)*dx+math.cos(a)*dy
        footing=(-3.25<mx<2.04 and -1.65<my<2.35)
        if dd<1.6 and not footing:natural=min(natural,-.60+(max(natural,0)+.60)*smooth((dd-.30)/1.3))
        return natural
    step=.4;nx=120;ny=110;vs=[]
    for iy in range(ny+1):
        y=-22+iy*step
        for ix in range(nx+1):
            x=-24+ix*step;xx=x+(x-math.copysign(20,x))*8 if abs(x)>20 else x;yy=y+(y-math.copysign(18,y))*8 if abs(y)>18 else y
            vs.append((xx,yy,height(x,y)))
    faces=[]
    for iy in range(ny):
        for ix in range(nx):a=iy*(nx+1)+ix;faces.append((a,a+1,a+nx+2,a+nx+1))
    terrain=G.mesh('Integrated • continuous terrain',vs,faces,'Grass')
    for p in terrain.data.polygons:p.use_smooth=True
    from mathutils.bvhtree import BVHTree
    terrain.data.calc_loop_triangles()
    terrain_bvh=BVHTree.FromPolygons(vs,[tuple(t.vertices) for t in terrain.data.loop_triangles],all_triangles=True)
    def mesh_height(x,y):
        hit=terrain_bvh.ray_cast(Vector((x,y,30)),Vector((0,0,-1)),60)[0]
        return hit.z if hit else height(x,y)
    def paving(name,points,width=1.1,z=None):
        samples=[]
        for aa,bb in zip(points,points[1:]):
            a=Vector(aa);b=Vector(bb);n=max(2,math.ceil((b-a).length/.16));samples += [a.lerp(b,i/n) for i in range(n)]
        samples.append(Vector(points[-1]));vertices=[]
        for i,p in enumerate(samples):
            delta=samples[min(i+1,len(samples)-1)]-samples[max(0,i-1)];side=Vector((-delta.y,delta.x)).normalized()
            for j in range(5):
                q=p+side*((j/4-.5)*width);vertices.append((q.x,q.y,z if z is not None else mesh_height(q.x,q.y)+.025))
        fs=[]
        for i in range(len(samples)-1):
            for j in range(4):a=i*5+j;fs.append((a,a+1,a+6,a+5))
        o=G.mesh(name,vertices,fs,'Water' if z is not None else 'Path');o.visible_shadow=False;return o
    # The shared spine turns through two small courts; it does not radiate from a copied centre.
    routes=[('South shared street',[(-.2,-30),(-.2,-12),(1.4,-9),(1.0,-6.5),(3.0,-4.8),(4.7,-1.7),(2.0,.8),(0,3),(0,5.6)],1.1),
            ('West shared lane',[(-15,-4.8),(-10.0,-5.8),(-7.1,-5.7),(-4.9,-5.0),(-2.0,-5.8),(.4,-6)],1.05),
            ('Inn and north lane',[(-2.4,-1.6),(-1.5,.5),(-3.4,1.6),(-4.2,2.3),(-2.0,4.3),(.1,5.4),(4.3,4.1),(6.2,4.1)],1.0),
            ('Mill-side working lane',[(1.5,-8.1),(4.9,-8.1),(7.8,-6.9),(9.4,-5.8)],1.1),
            ('Farm shared yard',[(-10.0,-5.8),(-12.3,-3.3),(-13.2,-1.0),(-10.8,-.1),(-8.5,.1)],1.0)]
    if make_routes:
        for name,points,width in routes:paving('Shared paving • '+name,points,width)
    for name,poly in COURTS.items():
        # Clip small grid cells to the convex court. Every vertex samples the actual ground.
        vertices=[];fs=[];spacing=.22
        for ix in range(math.floor(min(p[0] for p in poly)/spacing),math.ceil(max(p[0] for p in poly)/spacing)):
            for iy in range(math.floor(min(p[1] for p in poly)/spacing),math.ceil(max(p[1] for p in poly)/spacing)):
                cell=[(ix*spacing,iy*spacing),((ix+1)*spacing,iy*spacing),((ix+1)*spacing,(iy+1)*spacing),(ix*spacing,(iy+1)*spacing)]
                for a,b in zip(poly,poly[1:]+poly[:1]):
                    def side(p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
                    out=[]
                    for p,q in zip(cell,cell[1:]+cell[:1]):
                        sp=side(p);sq=side(q)
                        if sp>=0:out.append(p)
                        if (sp>=0)!=(sq>=0):
                            t=sp/(sp-sq);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
                    cell=out
                    if not cell:break
                if len(cell)<3:continue
                base=len(vertices);vertices.extend((x,y,mesh_height(x,y)+.026) for x,y in cell);fs.append(tuple(range(base,base+len(cell))))
        obj=G.mesh('Shared court • '+name,vertices,fs,'Path');obj.visible_shadow=False
    # The wheel reaches the water; the stream has a continuous bed, not a blue display plinth.
    paving('Stream • continuous water',channel,1.65,mill['ground']+.035)
    return mesh_height,paving,routes
