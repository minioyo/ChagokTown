"""Assemble delivered GLBs into a fixed miniature town; no prior asset is rewritten."""
import sys, math, json, hashlib, struct
from pathlib import Path
import bpy
from mathutils import Vector

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
ART = ROOT.parent
PREVIEW = '--preview' in sys.argv
LAYOUT = json.loads((ROOT/'source/layout.json').read_text(encoding='utf-8'))
for folder in ('blend','exports','renders','reports'):
    (ROOT/folder).mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sys.path.insert(0,str(ART/'town_sol_bakery_bookshop_v001/source'))
import geometry as G
from geometry import box, cyl, rod, ellipsoid, mesh
G.scene = bpy.context.scene
G.scene.name = 'EDIT • environment'
G.LOW = True
palette = json.loads((ART/'town_sol_bakery_bookshop_v001/reports/palette.json').read_text())
palette.update({'Grass':'A7BE8C','Grass edge':'8EA571','Path':'E6D9BC',
                'Path edge':'CABFA6','Water':'81B4B7','Water edge':'719B9F',
                'Soil side':'B8A286','Garden':'A8BC91'})
for name,color in palette.items():
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=G.linear(color)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=G.linear(color);p.inputs['Roughness'].default_value=.8
    G.M[name]=m
m=bpy.data.materials.new('Town environment • vertex color');m.use_nodes=True;m.use_backface_culling=True
p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
p.inputs['Roughness'].default_value=.8
vc=m.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Palette'
m.node_tree.links.new(vc.outputs['Color'],p.inputs['Base Color']);G.runtime_mat=m
G.COL=G.collection('EDIT • terrain paths trees furniture');EDIT=G.COL;G.PARENT=None

def disk(name,x,y,z,rx,ry,depth,color,segments=64):
    o=cyl(name,(x,y,z-depth/2),1,depth,color,thin=True)
    # Replace the 8-sided helper cylinder with a broad rounded oval.
    old=o.data;vs=[]
    for zz in (-depth/2,depth/2):
        vs.extend((rx*math.cos(i*math.tau/segments),ry*math.sin(i*math.tau/segments),zz) for i in range(segments))
    fs=[tuple(range(segments-1,-1,-1)),tuple(range(segments,2*segments))]
    fs.extend((i,(i+1)%segments,(i+1)%segments+segments,i+segments) for i in range(segments))
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();me.materials.append(G.M[color]);o.data=me
    bpy.data.meshes.remove(old)
    for face in me.polygons:face.use_smooth=len(face.vertices)==4
    return o

disk('Island • soil rim',0,.3,-.08,18.6,13.0,1.05,'Soil side')
disk('Island • turf rim',0,.3,0,18.55,12.95,.16,'Grass edge')
disk('Island • grass',0,.3,.008,18.45,12.85,.04,'Grass')

def catmull(points,closed=False,steps=8):
    pp=[Vector((x,y,0)) for x,y in points]
    p=([pp[-1]]+pp+[pp[0],pp[1]]) if closed else ([pp[0]]+pp+[pp[-1]])
    out=[]
    for i in range(1,len(p)-2):
        a,b,c,d=p[i-1:i+3]
        for j in range(steps):
            t=j/steps
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    out.append(out[0] if closed else pp[-1]);return out

def ribbon(name,points,width,color,z=.035):
    pts=catmull(points,closed=points[0]==points[-1]) if points[0]!=points[-1] else catmull(points[:-1],True)
    vs=[]
    for i,p in enumerate(pts):
        tangent=pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]
        if tangent.length<1e-8:tangent=Vector((1,0,0))
        side=Vector((-tangent.y,tangent.x,0)).normalized()*width/2
        vs += [(p.x+side.x,p.y+side.y,z),(p.x-side.x,p.y-side.y,z)]
    faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(pts)-1)]
    return mesh(name,vs,faces,color)

loop=[(-15.6,-6.4),(-15.5,-.7),(-10,-.4),(-4,.45),(2,1.1),(8,1.2),(13.4,1.0),
      (14.5,-4.8),(10.5,-7.9),(4,-9.0),(-3,-8.9),(-10,-9.0),(-15.6,-6.4)]
ribbon('Lane • soft edging',loop,1.95,'Path edge',.020)
ribbon('Lane • walking surface',loop,1.65,'Path',.028)
disk('Square • edge',-1.1,.55,.040,2.65,2.3,.025,'Path edge',48)
disk('Square • paving',-1.1,.55,.045,2.50,2.15,.025,'Path',48)

# Short footpaths connect the reserved maximum-size lots to the continuous lane.
lane_points=catmull(loop[:-1],True,steps=16)
for slot in LAYOUT['slots']:
    x,y=slot['xy'];a=math.radians(slot['yaw_deg'])
    start=(x+1.25*math.sin(a),y-1.25*math.cos(a))
    outer=Vector((x+3.3*math.sin(a),y-3.3*math.cos(a),0))
    nearest=min(lane_points,key=lambda p:(p-outer).length_squared)
    end=(nearest.x,nearest.y)
    ribbon('Approach • '+slot['id'],[start,((start[0]+end[0])/2,(start[1]+end[1])/2),end],.82,'Path',.030)

# A restrained pond on the right and an actual bridge at the end of a side walk.
disk('Pond • soft stone bank',14.6,3.1,.030,2.35,4.15,.035,'Path edge',48)
disk('Pond • water',14.6,3.1,.035,2.08,3.88,.018,'Water edge',48)
disk('Pond • soft water center',14.6,3.1,.039,1.92,3.71,.018,'Water',48)
ribbon('Pond approach',[(11.5,.2),(13.0,.2),(17.0,.2)],1.0,'Path',.042)
for i in range(15):
    x=12.7+i*.265;z=.20+.25*math.sin(i/14*math.pi)
    box('Bridge • plank %02d'%i,(x,.2,z),(.25,1.12,.12),'Wood light',.015)
for side in (-1,1):
    for x in (12.7,14.55,16.4):
        z=.20+.25*math.sin((x-12.7)/3.7*math.pi)
        cyl('Bridge • post',(x,.2+side*.52,z+.34),.055,.7,'Cream',thin=True)
    rod('Bridge • handrail left',(12.7,.2+side*.52,.85),(14.55,.2+side*.52,1.05),.045,'Wood light')
    rod('Bridge • handrail right',(14.55,.2+side*.52,1.05),(16.4,.2+side*.52,.85),.045,'Wood light')

# Low fountain leaves the rear landmark visible from the fixed game camera.
disk('Fountain • stone base',-1.1,.6,.14,.89,.89,.13,'Stone',24)
cyl('Fountain • bowl',(-1.1,.6,.32),.78,.35,'Cream',top=.90)
disk('Fountain • opaque water',-1.1,.6,.505,.77,.77,.02,'Water',24)
cyl('Fountain • stem',(-1.1,.6,.76),.13,.52,'Stone')
cyl('Fountain • upper bowl',(-1.1,.6,1.05),.33,.15,'Cream',top=.43)
ellipsoid('Fountain • finial',(-1.1,.6,1.22),(.12,.12,.15),'Water')

def tree(x,y,s=1):
    cyl('Tree • trunk',(x,y,.82*s),.13*s,1.65*s,'Wood',thin=True)
    rod('Tree • branch',(x,y,1.1*s),(x+.4*s,y+.04*s,1.75*s),.07*s,'Wood')
    for dx,dy,z,rx,ry,rz,col in [(-.33,0,1.95,.73,.72,.95,'Leaf light'),(.37,.03,2.12,.78,.72,1.0,'Sage'),(0,.05,2.65,.65,.67,.75,'Leaf light')]:
        ellipsoid('Tree • rounded canopy',(x+dx*s,y+dy*s,z*s),(rx*s,ry*s,rz*s),col)
    disk('Tree • grass collar',x,y,.018,.75*s,.65*s,.02,'Garden',20)

for x,y,s in [(-16.3,3.4,1.05),(-13.2,8.5,.92),(-8.8,10.0,.83),(-2.7,10.8,.9),
              (5.1,10.2,.96),(11.3,8.0,.9),(16,6.3,.73),(-16.5,-3.6,.78),
              (-12.5,-10,.72),(-6.5,-11,.72),(.2,-11,.7),(7,-10.2,.8),(13.5,-8,.8),(-7.9,1.3,.80)]:
    tree(x,y,s)

def bench(x,y,a=0):
    before=set(G.COL.objects)
    for dx in (-.50,.50):
        box('Bench • legs',(x+dx,y,.23),(.08,.4,.44),'Teal',.012)
    for yy in (-.12,.04,.2):box('Bench • seat',(x,y+yy,.47),(1.22,.14,.075),'Wood light',.012)
    box('Bench • back',(x,y+.26,.79),(1.25,.075,.27),'Wood light',.02)
    for dx in (-.5,.5):box('Bench • back stay',(x+dx,y+.25,.66),(.055,.07,.60),'Teal',.01)
    for o in set(G.COL.objects)-before:
        px,py=o.location.x-x,o.location.y-y
        o.location.x=x+px*math.cos(a)-py*math.sin(a);o.location.y=y+px*math.sin(a)+py*math.cos(a);o.rotation_euler.z+=a
bench(-3.0,2.7,-.25);bench(1.2,2.8,.25);bench(16.0,-1.9,math.pi/2)
for x,y in [(-13.2,-7),(6.6,-7.1),(-8.2,2.8),(10.5,2.5)]:
    cyl('Lamp • stem',(x,y,1.08),.045,2.16,'Teal',thin=True)
    box('Lamp • shade',(x,y,2.23),(.25,.25,.31),'Cream',.045)
    cyl('Lamp • cap',(x,y,2.44),.21,.12,'Teal',top=.03)

# A handful of broad shrub clusters; never fill every gap with small repeated props.
for x,y in [(-16.0,-7.3),(-10,9.6),(-4,10.6),(8.5,9.5),(12.2,5.5),(16.4,2.8),
            (13.2,-6.3),(5.8,-10),(-3.5,-10.9),(-14.5,.7)]:
    for dx,dy,s in [(-.28,0,.48),(.22,.13,.57)]:
        ellipsoid('Shrub • round',(x+dx,y+dy,s*.65),(s,s*.82,s*.7),'Sage')

bpy.context.view_layer.update()
environment_edit_stats=G.stats(EDIT)
ENV=G.collection('RUNTIME • environment')
root=bpy.data.objects.new('environment_root',None);ENV.objects.link(root)
for obj in list(EDIT.objects):
    o=obj.copy();o.data=obj.data.copy();o.parent=root;ENV.objects.link(o)
G.consolidate(ENV,root,'town_environment',0)
env_mesh=next(o for o in ENV.objects if o.type=='MESH')
for key in ('placement_lot_m','placement_xy_min','placement_xy_max'):
    if key in env_mesh:del env_mesh[key]
G.export(ENV,ROOT/'exports/town_environment.glb')
G.scene.collection.children.unlink(ENV)

STUDIO=bpy.data.collections.new('STUDIO • camera and lights')
G.scene.collection.children.link(STUDIO)
G.COL=STUDIO;G.PARENT=None
box('Studio • background',(0,0,-1.18),(200,200,.08),'Backdrop',0)
for name,loc,power,size,color in [('Sun softbox',(-14,-18,28),8500,15,(1,.9,.78)),('Sky fill',(15,0,23),4500,14,(.82,.91,1)),('Rim',(0,20,25),6500,14,(1,.96,.85))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    o=bpy.data.objects.new(name,data);STUDIO.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Town • soft sky');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.7,.8,.9,1);bg.inputs['Strength'].default_value=.35
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    DEVICE='GPU' if any(d.type!='CPU' for d in prefs.devices) else 'CPU'
except Exception:DEVICE='CPU'

def setup_scene(name,top=False):
    s=bpy.data.scenes.new(name);bpy.context.window.scene=s
    s.collection.children.link(ENV);s.collection.children.link(STUDIO);s.world=world
    s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
    s.render.engine='CYCLES';s.cycles.device=DEVICE;s.cycles.samples=20 if PREVIEW else 64;s.cycles.use_denoising=True
    s.render.resolution_x=1440 if PREVIEW else 2240;s.render.resolution_y=810 if PREVIEW else 1260;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
    s.view_settings.view_transform='AgX';s.view_settings.exposure=.20
    camdata=bpy.data.cameras.new(name+' camera');cam=bpy.data.objects.new(name+' camera',camdata);s.collection.objects.link(cam)
    cam.location=(0,0,50) if top else LAYOUT['camera']['location'];target=Vector((0,0,0) if top else LAYOUT['camera']['target'])
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=43 if top else LAYOUT['camera']['ortho_scale'];s.camera=cam
    return s

TEMPLATES={};INPUTS={};MISSING=[]
def load_model(slot,level):
    key=(slot['kind'],level)
    if key in TEMPLATES:return TEMPLATES[key]
    path=ART/slot['source']/'exports'/f"{slot['kind']}_level_{level}.glb"
    if not path.exists():
        MISSING.append(str(path.relative_to(ART)));return None
    INPUTS[str(path.relative_to(ART))]=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.import_scene.gltf(filepath=str(path))
    objs=list(bpy.context.selected_objects);model=next(o for o in objs if o.type=='MESH')
    bpy.context.view_layer.update();matrix=model.matrix_world.copy();model.parent=None;model.matrix_world=matrix
    for c in list(model.users_collection):c.objects.unlink(model)
    for o in objs:
        if o!=model:bpy.data.objects.remove(o,do_unlink=True)
    TEMPLATES[key]=model;return model

STATS={};SCENES={}
for stage,levels in LAYOUT['stages'].items():
    s=setup_scene(stage);SCENES[stage]=s
    G.scene=s;G.COL=G.collection('BUILDINGS • '+stage);G.PARENT=None
    building_coll=G.COL
    for slot in LAYOUT['slots']:
        x,y=slot['xy'];level=levels.get(slot['id'],0)
        if level:
            template=load_model(slot,level)
            if template:
                o=template.copy();o.name=slot['id']+' • '+str(level);building_coll.objects.link(o)
                o.location=(x,y,0);o.rotation_euler.z=math.radians(slot['yaw_deg']);o['slot_id']=slot['id'];o['level']=level
                continue
        # Empty future lots are low meadow patches, not neon construction labels.
        disk('Reserved garden • '+slot['id'],x,y-.8,.021,1.8,1.7,.02,'Garden',24)
        for dx,dy in [(-1.15,.4),(1.1,.2)]:
            ellipsoid('Reserved garden • shrub',(x+dx,y+dy,.24),(.45,.36,.25),'Sage')
        for j,(dx,dy) in enumerate([(-.7,-1.65),(-.3,-1.9),(.15,-1.75)]):
            cyl('Reserved garden • flower stem',(x+dx,y+dy,.18),.024,.34,'Leaf dark',thin=True)
            for k in range(4):
                a=k*math.pi/2
                ellipsoid('Reserved garden • petal',(x+dx+.085*math.cos(a),y+dy+.085*math.sin(a),.36),(.095,.095,.055),'Flower' if j%2 else 'Pink')
    bpy.context.view_layer.update()
    STATS[stage]={'building_and_garden':G.stats(building_coll),'environment':G.stats(ENV),'slots':levels}
    s['layout_manifest']='source/layout.json';s['stage']=stage;s['fixed_layout']=True

top=setup_scene('mature • plan view',True);top.collection.children.link(bpy.data.collections['BUILDINGS • mature']);SCENES['top']=top
top.render.resolution_y=1500 if not PREVIEW else 1000
focus=setup_scene('early • close view');focus.collection.children.link(bpy.data.collections['BUILDINGS • early']);SCENES['early_focus']=focus
focus.camera.location+=Vector((-7.7,-.2,0));focus.camera.data.ortho_scale=25
focus['note']='Optional starter framing only; the three stage overview cameras remain identical.'

# Scene-level exports retain per-building objects so slots can be selected and upgraded.
for stage in LAYOUT['stages']:
    s=SCENES[stage];bpy.context.window.scene=s
    bpy.ops.object.select_all(action='DESELECT')
    for o in s.objects:
        if o.type=='MESH' and o.name!='Studio • background':o.select_set(True)
    bpy.context.view_layer.objects.active=env_mesh
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports'/f'town_{stage}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True,export_cameras=False,export_lights=False)

bpy.context.window.scene=SCENES['mature']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/chagok_fixed_town_v001.blend'))
for stage,s in SCENES.items():
    bpy.context.window.scene=s;s.render.filepath=str(ROOT/'renders'/f"{'preview_' if PREVIEW else ''}town_{stage}.png")
    bpy.ops.render.render(write_still=True);print('RENDERED',stage,flush=True)
assert all(hashlib.sha256((ART/p).read_bytes()).hexdigest()==h for p,h in INPUTS.items()),'Source assets changed during town assembly'
report={'preview':PREVIEW,'source_glbs_unchanged':INPUTS,'missing_models':sorted(set(MISSING)),
        'render_device':DEVICE,'stages':STATS,'environment_edit':environment_edit_stats,
        'environment_glb':G.glb_stats(ROOT/'exports/town_environment.glb'),
        'note':'Offline scene and geometry only. Android, Pleos and vehicle performance untested.'}
(ROOT/'reports'/('preview.json' if PREVIEW else 'assembly.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
print('ASSEMBLY_COMPLETE',len(MISSING),'missing stage requests',flush=True)
