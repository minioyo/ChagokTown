"""Compact-centred season geography, shared by massing and imported-GLB scenes."""
import bpy,bmesh,math,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import geometry as G
import models as M
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent
EXTRA=[{'id':'cathedral','kind':'cathedral','xy':[-.8,14.2],'ground':2.85,'yaw':12,'scale':1},
       {'id':'inn','kind':'inn','xy':[-7.1,-9.5],'ground':-.45,'yaw':-18,'scale':1},
       {'id':'watermill','kind':'watermill','xy':[10,-4.5],'ground':-.45,'yaw':-15,'scale':1},
       {'id':'farmstead','kind':'farmstead','xy':[-13.6,5.5],'ground':.35,'yaw':25,'scale':1},
       {'id':'grocer','kind':'grocer','xy':[-10.3,-1.8],'ground':0,'yaw':62,'scale':1},
       {'id':'town_hall','kind':'town_hall','xy':[7.1,6.9],'ground':1.65,'yaw':-28,'scale':1}]
FOLDERS={'house':'town_house_florist_v001','florist':'town_house_florist_v001','cafe':'town_cafe_v003',
         'bakery':'town_sol_bakery_bookshop_v001','bookshop':'town_sol_bakery_bookshop_v001',
         'grocer':'town_sol_civic_market_workshop_v001','town_hall':'town_sol_civic_market_workshop_v001','workshop':'town_sol_civic_market_workshop_v001'}

def models_in(s):return [o for o in s.objects if o.type=='EMPTY' and o.instance_type=='COLLECTION' and o.get('kind')]
def identity(o):return o.name.split(' • ')[1]
def hull(pp):
    pp=sorted(set(tuple(p) for p in pp));lo=[];hi=[]
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    for p in pp:
        while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(pp):
        while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]
def local_points(col):
    dg=bpy.context.evaluated_depsgraph_get();points=[]
    for obj in col.all_objects:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(dg);me=ev.to_mesh();points.extend(obj.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
    return points
def pose(obj,b):
    obj.location=(*b['xy'],b['ground']-(.065*b['scale'] if b.get('legacy') else 0));obj.rotation_euler=(0,0,math.radians(b['yaw']));obj.scale=(b['scale'],)*3
    obj['kind']=b['kind'];obj['display_level']=b.get('level',3);obj['season_plot_id']=b['id']
def transform_xy(b,p):
    a=math.radians(b['yaw']);c=math.cos(a);s=math.sin(a);return (b['xy'][0]+b['scale']*(c*p[0]-s*p[1]),b['xy'][1]+b['scale']*(s*p[0]+c*p[1]))
def inside(p,poly):
    x,y=p;result=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
    return result
def distance(p,poly):
    result=1e10;p=Vector(p)
    for aa,bb in zip(poly,poly[1:]+poly[:1]):
        a=Vector(aa);d=Vector(bb)-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared));result=min(result,(p-a-d*t).length)
    return result
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)

def init(blockout=False):
    bpy.ops.wm.open_mainfile(filepath=str(ART/'town_layout_v003_density/blend/chagok_density_comparison.blend'))
    scene=bpy.data.scenes['Compact • same eight models'];scene.name='Season 1 • final'
    for s in list(bpy.data.scenes):
        if s!=scene and s.name!='LIBRARY • unchanged source GLBs':bpy.data.scenes.remove(s)
    bpy.context.window.scene=scene
    library=bpy.data.scenes['LIBRARY • unchanged source GLBs'];library.name='LIBRARY • actual GLB inputs'
    palette=M.materials();(ROOT/'reports/palette.json').write_text(json.dumps(palette,indent=2),encoding='utf-8')
    originals={identity(o):o for o in models_in(scene)}
    compact=json.loads((ART/'town_layout_v003_density/source/layouts.json').read_text())['Compact']
    layout=[dict(b,legacy=True,level=3) for b in compact]+[dict(b,level=3) for b in EXTRA]
    assets={}
    def asset(kind,level):
        key=(kind,level)
        if key in assets:return assets[key]
        if blockout and kind in M.BUILDERS:
            bpy.context.window.scene=library;col,_=M.BUILDERS[kind](3,False);assets[key]=col
        else:
            # Preserve the user-selected Compact's authored bakery and bookshop variant.
            matching=next((o for o in originals.values() if o.get('kind')==kind and o.get('display_level')==level),None) if blockout else None
            if matching:assets[key]=matching.instance_collection
            else:
                bpy.context.window.scene=library;previous=set(library.objects)
                file=(ROOT/'exports'/f'{kind}_level_{level}.glb') if kind in M.BUILDERS else (ART/FOLDERS[kind]/'exports'/f'{kind}_level_{level}.glb')
                if not blockout and kind in ('bakery','bookshop') and level==3:file=ROOT/'exports/reused_compact'/f'{kind}_level_3.glb'
                bpy.ops.import_scene.gltf(filepath=str(file));col=bpy.data.collections.new(f'S1 INPUT • {kind}_level_{level}');library.collection.children.link(col)
                for obj in set(library.objects)-previous:
                    for c in list(obj.users_collection):c.objects.unlink(obj)
                    col.objects.link(obj)
                assets[key]=col
        bpy.context.window.scene=scene;return assets[key]
    for b in layout:
        col=asset(b['kind'],3)
        if b['id'] in originals:obj=originals[b['id']]
        else:obj=bpy.data.objects.new('SEASON • '+b['id']+' • fixed plot',None);scene.collection.objects.link(obj)
        obj.instance_type='COLLECTION';obj.instance_collection=col;pose(obj,b)
    bpy.context.view_layer.update()
    # Real maximum-stage XY hulls, with the background stage's source solids.
    footprints={b['id']:hull([(p.x,p.y) for p in local_points(asset(b['kind'],3))]) for b in layout}
    if blockout:
        # Reserve garden/courtyard details before those are produced.
        for b in layout:
            if b['kind'] in M.LOTS:
                (x0,y0),(x1,y1)=M.LOTS[b['kind']];footprints[b['id']]=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    return scene,library,layout,asset,footprints

def terrain(scene,layout,footprints):
    bpy.context.window.scene=scene;G.scene=scene;G.PARENT=None;G.COL=G.collection('SEASON • geography and shared paths')
    old=next(o for o in scene.objects if o.type=='MESH' and 'continuous terrain' in o.name)
    # Saved Compact's centre terrain is retained. New pads are local to six new destinations.
    old.data=old.data.copy();pads=[(b,[transform_xy(b,p) for p in footprints[b['id']]]) for b in layout if not b.get('legacy')]
    legacy_pads=[(b,[transform_xy(b,p) for p in footprints[b['id']]]) for b in layout if b.get('legacy')]
    channel=[(11.0,20),(13.0,13),(14.0,5),(13.27,-2.27),(12.53,-5.02),(11.77,-7.9),(10.4,-14),(12,-20)]
    def stream_distance(x,y):return min(distance((x,y),[a,b]) for a,b in zip(channel,channel[1:]))
    for vertex in old.data.vertices:
        p=old.matrix_world@vertex.co;x,y=p.x,p.y;z=p.z
        for b,poly in pads:
            d=distance((x,y),poly)
            if inside((x,y),poly):z=b['ground']
            elif d<1.30:z=b['ground']+(z-b['ground'])*smooth(d/1.30)
        for b,poly in legacy_pads:
            if inside((x,y),poly):z=b['ground']
        dd=stream_distance(x,y)
        if dd<1.7:z=-.77+(max(z,0)+.77)*smooth((dd-.30)/1.4)
        elif dd<2.3:z=max(z,0)+(z-max(z,0))*smooth((dd-1.7)/.6)
        vertex.co.z=z
        if abs(x)>20:vertex.co.x=x+(x-math.copysign(20,x))*8
        if abs(y)>21:vertex.co.y=y+(y-math.copysign(21,y))*8
    old.data.update();old.name='Season • continuous Compact-derived terrain'
    # Trim only the duplicated lower tail of Compact's old entry alley. Its
    # centre junction remains, and the longer season entry takes over below it.
    for obj in scene.objects:
        if obj.type=='MESH' and 'downhill entry alley' in obj.name:
            obj.data=obj.data.copy();bm=bmesh.new();bm.from_mesh(obj.data)
            remove=[f for f in bm.faces if (obj.matrix_world@f.calc_center_median()).y< -4.6]
            bmesh.ops.delete(bm,geom=remove,context='FACES')
            loose=[v for v in bm.verts if not v.link_faces]
            if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
            bm.to_mesh(obj.data);bm.free()
    old.data.calc_loop_triangles();bvh=BVHTree.FromPolygons([old.matrix_world@v.co for v in old.data.vertices],[tuple(t.vertices) for t in old.data.loop_triangles],all_triangles=True)
    def ground(x,y):
        hit=bvh.ray_cast(Vector((x,y,50)),Vector((0,0,-1)),100)[0];return hit.z if hit else 0
    # Move existing trees as rigid groups out of new building envelopes, never shrink buildings to fit them.
    trunks=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('Tree • warm trunk')]
    forest=[(-18,10),(-17,13),(-14,13),(-8,18),(3,21),(7,18),(16,10),(18,6),(18,1),(16,-4),(18,-12),(-17,-8),(-16,-13),(-4,-17),(4,-15)]
    trees=[o for o in scene.objects if o.name.startswith('Tree •') and o.type=='MESH']
    groups={trunk:[o for o in trees if min(trunks,key=lambda t:math.dist(o.location[:2],t.location[:2]))==trunk] for trunk in trunks}
    for i,(trunk,group) in enumerate(groups.items()):
        x,y=trunk.location[:2];target=forest[i%len(forest)];bottom=min((o.matrix_world@Vector(c)).z for o in group for c in o.bound_box)
        delta=Vector((target[0]-x,target[1]-y,ground(*target)-bottom))
        for o in group:o.location+=delta
    # Remove the old ring of a moved centre tree only in this derived scene.
    for o in list(scene.objects):
        if o.type=='MESH' and 'tree stone edging' in o.name:bpy.data.objects.remove(o,do_unlink=True)
    for o in scene.objects:
        if o.type=='MESH' and o.name.startswith(('Shrub •','Rock •')):
            xy=tuple(o.location[:2]);bottom=min((o.matrix_world@Vector(c)).z for c in o.bound_box);o.location.z+=ground(*xy)-bottom
    # New routes are authored as destinations, not a uniform outer loop.
    roads=[('Entry lane',[(-3,-42),(-3,-18),(-3.4,-13),(-2.9,-8),(-2.5,-4.2)],1.35),
           ('Inn courtyard',[(-3.4,-12),(-5.0,-12.0),transform_xy(next(b for b in layout if b['id']=='inn'),M.DOORS['inn'])],1.15),
           ('West grocer lane',[(-3.8,-3.0),(-7.4,-4.5),(-9.5,-3.5),(-9.5,-1.8)],1.05),
           ('Farm lane',[(-9.5,-1.8),(-11.1,.4),(-13.0,1.5),transform_xy(next(b for b in layout if b['id']=='farmstead'),M.DOORS['farmstead'])],1.0),
           ('Mill lane',[(1.6,-.4),(4.6,-2.1),(6.8,-5.6),transform_xy(next(b for b in layout if b['id']=='watermill'),M.DOORS['watermill'])],1.05),
           ('Upper civic lane',[(3.9,1.9),(5.0,3.3),(5.1,5.2),(5.1,7.5),(4.5,9.7),transform_xy(next(b for b in layout if b['id']=='cathedral'),M.DOORS['cathedral'])],1.15),
           ('Civic bridge approach',[(8.5,4.3),(10.7,5.0),(12.0,7.0)],.85),
           ('East woodland walk',[(15.5,7.0),(16.5,6.0)],.8),
           ('Mill bridge approach',[(8.9,-6.6),(9.3,-8.3),(9.8,-9.2)],.9),
           ('Lower streamside walk',[(13.2,-9.2),(15.5,-11),(16,-14)],.8)]
    def strip(name,points,width,z_override=None,color='Path'):
        samples=[]
        for a,b in zip(points,points[1:]):
            n=max(2,math.ceil(math.dist(a,b)/.16))
            samples += [Vector(a).lerp(Vector(b),i/n) for i in range(n)]
        samples.append(Vector(points[-1]));vs=[]
        for i,p in enumerate(samples):
            d=samples[min(i+1,len(samples)-1)]-samples[max(i-1,0)];side=Vector((-d.y,d.x)).normalized()
            for j in range(5):
                q=p+side*((j/4-.5)*width);vs.append((q.x,q.y,z_override if z_override is not None else ground(q.x,q.y)+.075))
        fs=[]
        for i in range(len(samples)-1):
            for j in range(4):a=i*5+j;fs.append((a,a+1,a+6,a+5))
        o=G.mesh(name,vs,fs,color);o.visible_shadow=False
        if name in ('Season lane • Upper civic lane','Season lane • Entry lane') and z_override is None:
            for aa,bb in zip(points,points[1:]):
                a=Vector(aa);b=Vector(bb);d=b-a;n=max(2,math.ceil(d.length/.24));length=d.length/n
                for i in range(n):
                    p=a.lerp(b,(i+.5)/n);z0=ground(*a.lerp(b,i/n));z1=ground(*a.lerp(b,(i+1)/n))
                    if .18*length<abs(z1-z0)<1.2*length:
                        depth=abs(z1-z0)+.17
                        G.box('Stair • season lane tread',(p.x,p.y,max(z0,z1)+.10-depth/2),(width+.08,length+.035,depth),'Stone light',.008,rot=(0,0,math.atan2(d.y,d.x)-math.pi/2))
        return o
    for i,(name,points,width) in enumerate(roads):strip('Season lane • '+name,points,width)
    strip('Season • continuous water channel',channel,2.0,-.40,'Water')
    # A modest mill-side bridge across the channel; water is visible beneath it.
    for y in (-9.2,7.0):
        x=11.45 if y<0 else 13.75
        G.box('Bridge • stone deck',(x,y,.10),(3.5,1.25,.23),'Old stone',.045)
        for xx in (x-1.45,x+1.45):G.box('Bridge • bank support',(xx,y,-.25),(.48,1.40,.72),'Stone shade',.035)
        for yy in (y-.60,y+.60):
            G.box('Bridge • low parapet',(x,yy,.47),(3.55,.19,.57),'Old stone',.035)
            G.box('Bridge • pale coping',(x,yy,.78),(3.64,.25,.12),'Stone light',.02)
    return ground,roads,strip

def configure(scene,preview=False):
    prefs=bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type='OPTIX';prefs.get_devices()
        for d in prefs.devices:d.use=d.type!='CPU'
        device='GPU' if any(d.type!='CPU' for d in prefs.devices) else 'CPU'
    except Exception:device='CPU'
    scene.render.engine='CYCLES';scene.cycles.device=device;scene.cycles.samples=24 if preview else 64;scene.cycles.use_denoising=True
    scene.render.resolution_x=1600 if preview else 2400;scene.render.resolution_y=1000 if preview else 1500;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.camera.data.dof.use_dof=False
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.15;scene.view_settings.gamma=1

def camera(scene,close=False,top=False):
    cam=scene.camera;cam.data.type='ORTHO'
    if top:cam.location=(-1.5,2,55);cam.rotation_euler=(0,0,0);cam.data.ortho_scale=58
    else:
        target=Vector((-1.7,3.4,2.9)) if not close else Vector((-1.5,3.0,2.1))
        cam.location=target+Vector((28,-40,32));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=48 if not close else 24
    cam.data.dof.use_dof=False

def protect():
    before=json.loads((ROOT/'reports/protected_art_sha256.json').read_text())
    assert all(hashlib.sha256((ART/p).read_bytes()).hexdigest()==h for p,h in before.items()),'Protected art changed'
    return len(before)

def check_layout(scene,layout,footprints,label):
    transformed={b['id']:[transform_xy(b,p) for p in footprints[b['id']]] for b in layout}
    def separation(a,b):
        gap=-1e10
        for poly in (a,b):
            for p,q in zip(poly,poly[1:]+poly[:1]):
                dx=q[0]-p[0];dy=q[1]-p[1];length=math.hypot(dx,dy);ax=(-dy/length,dx/length)
                aa=[x*ax[0]+y*ax[1] for x,y in a];bb=[x*ax[0]+y*ax[1] for x,y in b]
                gap=max(gap,min(aa)-max(bb),min(bb)-max(aa))
        return gap
    pairs=[]
    for i,a in enumerate(layout):
        for b in layout[i+1:]:pairs.append({'a':a['id'],'b':b['id'],'gap':separation(transformed[a['id']],transformed[b['id']])})
    collisions=[p for p in pairs if p['gap']<-.0001]
    (ROOT/'reports'/f'{label}_layout.json').write_text(json.dumps({'layout':layout,'maximum_local_hulls':footprints,'world_hulls':transformed,'pairs':pairs,'collisions':collisions},indent=2),encoding='utf-8')
    print('LAYOUT',label,'collisions',collisions,flush=True)
    return collisions
