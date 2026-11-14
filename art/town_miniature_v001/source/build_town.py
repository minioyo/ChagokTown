"""ChagokTown miniature set v001. Original procedural meshes, no external assets.

Run with Blender --background --python source/build_town.py
All model coordinates: metres, Z up, front -Y; root at ground centre.
"""
import bpy
import math
import json
import random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
for folder in ('blend', 'exports', 'renders', 'reports'):
    (ROOT / folder).mkdir(parents=True, exist_ok=True)
random.seed(21)

# Only this background process is reset; the user's open Blender is untouched.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = '01 • Chagok Lane'
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
M = {}
COL = None
ROOT_OBJ = None
ASSETS = {}

def material(name, hexcode, rough=.65, metal=0, emission=0):
    c = tuple(int(hexcode[i:i+2],16)/255 for i in (0,2,4))
    linear = tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in c)
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*linear,1)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (*linear,1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*linear,1)
        bsdf.inputs['Emission Strength'].default_value = emission
    M[name] = m
    return m

PALETTE = {
    'Cream':'F5E6C8', 'Warm plaster':'EDB292', 'Butter plaster':'E9CB89',
    'Sage plaster':'A8BCA6', 'Terracotta':'BA6555', 'Clay light':'D18468',
    'Clay shade':'9E5147', 'Teal roof':'427B78', 'Teal tile':'59908A',
    'Teal dark':'315D5B', 'Rose canopy':'CC817B', 'Wood':'966C4E',
    'Wood light':'BB9065', 'Dark wood':'624B3C', 'Ink':'354C4B',
    'Glass':'507D87', 'Glass light':'79A5AA', 'Glass glint':'BFD5CF',
    'Leaf':'78946A', 'Leaf light':'94AC77', 'Leaf dark':'58785C',
    'Flower pink':'DF9BA6', 'Flower coral':'D67C6C', 'Flower cream':'F5DEA6',
    'Flower plum':'AE7FAD', 'Earth':'675644', 'Stone':'D4C7AD',
    'Paving':'E7DAC2', 'Paving warm':'DCC9AA', 'Grass':'A7B591',
    'Brass':'BC945A', 'Lamp glow':'FFE7AA', 'Backdrop':'E5DDD0',
    'Chalk':'F1E5C8', 'Brick':'C68E73'
}
for name, hx in PALETTE.items():
    material(name, hx, .34 if 'Glass' in name else .68,
             .55 if name=='Brass' else 0, .65 if name=='Lamp glow' else 0)

def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c

def register(obj, name, mat=None, smooth=False):
    obj.name = name
    for c in list(obj.users_collection): c.objects.unlink(obj)
    COL.objects.link(obj)
    if ROOT_OBJ: obj.parent = ROOT_OBJ
    if mat: obj.data.materials.append(M[mat])
    if smooth and obj.type == 'MESH':
        for p in obj.data.polygons: p.use_smooth=True
    return obj

def bevel(obj, amount=.04, segments=3):
    mod=obj.modifiers.new('Soft handcrafted edges','BEVEL')
    mod.width=amount; mod.segments=segments
    mod=obj.modifiers.new('Face normals','WEIGHTED_NORMAL')
    mod.keep_sharp=True; mod.weight=50
    return obj

def cube(name, loc, size, mat, radius=.04, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=register(bpy.context.object,name,mat)
    o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if radius: bevel(o, min(radius,min(size)*.43))
    if rot: o.rotation_euler=rot
    return o

def sphere(name, loc, scale, mat, seg=16, rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=1,location=loc)
    o=register(bpy.context.object,name,mat,True)
    o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o

def cylinder(name, loc, radius, depth, mat, top=None, vertices=24, rot=None):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=radius,radius2=radius if top is None else top,depth=depth,location=loc)
    o=register(bpy.context.object,name,mat)
    bevel(o,min(.025,depth*.15,radius*.15),2)
    if rot: o.rotation_euler=rot
    return o

def rod(name,a,b,r,mat,vertices=12):
    d=Vector(b)-Vector(a)
    o=cylinder(name,(Vector(a)+Vector(b))/2,r,d.length,mat,vertices=vertices)
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    return o

def mesh(name,verts,faces,mat,edge=.025):
    me=bpy.data.meshes.new(name+' mesh'); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); COL.objects.link(o)
    if ROOT_OBJ: o.parent=ROOT_OBJ
    me.materials.append(M[mat])
    if edge: bevel(o,edge,3)
    return o

def prism(name,coords,y,depth,mat,edge=.025):
    # Extrude a 2D X/Z polygon along Y.
    n=len(coords)
    verts=[(x,y-depth/2,z) for x,z in coords]+[(x,y+depth/2,z) for x,z in coords]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,verts,faces,mat,edge)

def arch(name,x,y,bottom,w,h,depth,mat):
    r=w/2; spring=bottom+h-r
    coords=[(x-r,bottom),(x+r,bottom)]
    coords += [(x+r*math.cos(a),spring+r*math.sin(a)) for a in [i*math.pi/16 for i in range(17)]]
    return prism(name,coords,y,depth,mat,.025)

def torus(name,loc,major,minor,mat,rot=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=8,location=loc,major_radius=major,minor_radius=minor)
    o=register(bpy.context.object,name,mat,True)
    if rot: o.rotation_euler=rot
    return o

def text(name,body,loc,size,mat,rot=(math.pi/2,0,0)):
    cu=bpy.data.curves.new(name,'FONT'); cu.body=body; cu.align_x='CENTER'; cu.align_y='CENTER'
    cu.size=size; cu.extrude=.008; cu.bevel_depth=.002; cu.bevel_resolution=2
    o=bpy.data.objects.new(name,cu); COL.objects.link(o)
    if ROOT_OBJ: o.parent=ROOT_OBJ
    o.location=loc; o.rotation_euler=rot; cu.materials.append(M[mat]); return o

def begin_asset(key, title):
    global COL,ROOT_OBJ
    COL=collection('ASSET • '+title)
    ROOT_OBJ=bpy.data.objects.new(key,None); COL.objects.link(ROOT_OBJ)
    ROOT_OBJ.empty_display_size=.35
    ROOT_OBJ['asset_id']=key; ROOT_OBJ['units']='metres'; ROOT_OBJ['front']='-Y'; ROOT_OBJ['pivot']='ground centre'
    ASSETS[key]=(COL,ROOT_OBJ)

def window(name,x,y,z,w,h,trim='Cream',mullions=True):
    cube(name+' recessed shadow',(x,y,z),(w+.18,.12,h+.18),'Dark wood',.04)
    cube(name+' painted glass',(x,y-.075,z),(w,.08,h),'Glass',.03)
    for dx in (-w/2,w/2): cube(name+' vertical jamb',(x+dx,y-.14,z),(.095,.15,h+.15),trim,.025)
    for dz in (-h/2,h/2): cube(name+' cross jamb',(x,y-.14,z+dz),(w+.12,.15,.095),trim,.025)
    if mullions:
        cube(name+' mullion',(x,y-.16,z),(.06,.12,h),trim,.018)
        cube(name+' transom',(x,y-.16,z+.06),(w,.12,.06),trim,.018)
    # Slim reflections are solid geometry, not a billboard or an image texture.
    cube(name+' reflection',(x-w*.25,y-.124,z+h*.12),(.045,.018,h*.55),'Glass glint',.008,rot=(0,-.28,0))
    cube(name+' stone sill',(x,y-.22,z-h/2-.08),(w+.28,.38,.14),'Cream',.04)

def arched_door(x,y,mat='Teal roof'):
    arch('Door • stone arch',x,y,.16,.94,1.72,.20,'Cream')
    arch('Door • inset painted panel',x,y-.115,.17,.73,1.56,.12,mat)
    arch('Door • top glazing',x,y-.185,.90,.52,.67,.035,'Glass')
    cube('Door • lower inset',(x,y-.19,.53),(.49,.035,.38),mat,.045)
    cube('Door • glass divider',(x,y-.215,1.08),(.55,.035,.055),'Cream',.01)
    sphere('Door • brass knob',(x+.24,y-.26,.85),(.055,.055,.055),'Brass',12,8)
    cube('Door • doorstep',(x,y-.30,.10),(1.15,.65,.20),'Stone',.07)

def flower(name,x,y,z,scale=1,color='Flower pink'):
    rod(name+' stem',(x,y,z),(x,y,z+.31*scale),.018*scale,'Leaf dark',8)
    for k in range(5):
        a=k*math.tau/5
        sphere(name+' petal',(x+math.cos(a)*.065*scale,y+math.sin(a)*.065*scale,z+.32*scale),(.067*scale,.067*scale,.045*scale),color,10,6)
    sphere(name+' centre',(x,y,z+.35*scale),(.037*scale,)*3,'Flower cream',10,6)
    leaf=sphere(name+' leaf',(x+.05*scale,y,z+.14*scale),(.10*scale,.035*scale,.045*scale),'Leaf',10,6)
    leaf.rotation_euler[1]=-.4

def pot(name,x,y,z,r=.19,h=.28,flowers=True,color='Flower pink'):
    cylinder(name+' ceramic pot',(x,y,z+h/2),r*.75,h,'Terracotta',top=r)
    torus(name+' rolled rim',(x,y,z+h-.025),r*.94,.034,'Clay light')
    cylinder(name+' earth',(x,y,z+h-.025),r*.8,.035,'Earth',vertices=16)
    if flowers:
        for k in range(4):
            a=k*2.4
            flower(name+str(k),x+math.cos(a)*r*.46,y+math.sin(a)*r*.46,z+h, .65+(k%2)*.25,color)
    else:
        for k in range(5):
            a=k*math.tau/5
            o=sphere(name+' succulent',(x+math.cos(a)*r*.38,y+math.sin(a)*r*.38,z+h+.12),(r*.43,r*.39,.22),'Leaf light',12,8)
            o.rotation_euler=(math.sin(a)*.4,math.cos(a)*.4,0)

def window_box(x,y,z,w=1):
    cube('Windowbox • timber trough',(x,y,z),(w,.31,.24),'Wood light',.045)
    cube('Windowbox • top earth',(x,y,z+.115),(w-.09,.22,.025),'Earth',.01)
    for dx in (-w*.38,w*.38): cube('Windowbox • brass strap',(x+dx,y-.165,z),(.055,.025,.22),'Brass',.008)
    for k in range(5): flower('Windowbox bloom',x-w*.37+k*w*.185,y,z+.14,.55,['Flower pink','Flower cream'][k%2])

def gable_roof(w,d,eave,rise,mat='Terracotta',tile='Clay light'):
    # Real gable wall and thick roof panels; discrete staggered rows add miniature relief.
    prism('Gable • plaster triangle',[(-w/2+.2,eave-.12),(w/2-.2,eave-.12),(0,eave+rise-.12)],0,d-.35,'Warm plaster' if mat=='Terracotta' else 'Sage plaster',.035)
    angle=math.atan2(rise,w/2)
    length=math.hypot(w/2,rise)
    for side in (-1,1):
        cube('Roof • thick slope',(side*w/4,0,eave+rise/2),(length+.13,d,.19),mat,.055,rot=(0,side*angle,0))
        # Individual rounded shingles, kept as editable parts.
        for row in range(5):
            t=(row+.5)/5
            x=side*w/2*t; z=eave+rise*(1-t)+.115
            for col in range(7):
                y=-d/2+(col+.5)*d/7
                c=tile if (row+col)%4==0 else mat
                cube('Roof • shingle %s %s %s'%(side,row,col),(x,y,z),(length/5+.055,d/7-.025,.065),c,.023,rot=(0,side*angle,0))
        for y in (-d/2-.015,d/2+.015):
            cube('Roof • cream bargeboard',(side*w/4,y,eave+rise/2-.045),(length+.22,.15,.20),'Cream',.035,rot=(0,side*angle,0))
        cube('Roof • eave fascia',(side*w/2,0,eave-.045),(.14,d+.12,.22),'Cream',.035)
    for k in range(8):
        cylinder('Roof • ridge cap',(0,-d/2+(k+.5)*d/8,eave+rise+.13),.14,d/8+.035,mat,vertices=12,rot=(math.pi/2,0,0))

def foundation(w,d,mat):
    cube('Foundation • rounded stone plinth',(0,0,.095),(w+.22,d+.20,.19),'Stone',.075)
    cube('Wall • plaster shell',(0,0,1.38),(w,d,2.56),mat,.10)
    cube('Wall • lower skirting',(0,0,.29),(w+.07,d+.07,.23),'Cream',.04)

# 01 — a tall, warm little house with red tiled gable and a tiny porch.
begin_asset('house','01 Apricot House')
foundation(2.55,2.30,'Warm plaster')
gable_roof(3.08,2.85,2.67,1.07)
arched_door(.56,-1.22)
window('House front window',-.67,-1.20,1.45,.83,.88)
window_box(-.67,-1.49,.86,.98)
# Circular attic window, layered rim and crossed bars.
cylinder('Attic • circular frame',(0,-1.28,3.02),.30,.13,'Cream',rot=(math.pi/2,0,0))
cylinder('Attic • circular glass',(0,-1.36,3.02),.22,.04,'Glass',rot=(math.pi/2,0,0))
cube('Attic • vertical bar',(0,-1.39,3.02),(.045,.04,.43),'Cream',.01)
cube('Attic • horizontal bar',(0,-1.39,3.02),(.43,.04,.045),'Cream',.01)
# A complete side window is made at front then rotated around the house.
before=set(COL.objects)
window('House side window',0,-1.30,1.53,.84,.95)
for o in set(COL.objects)-before:
    o.location=Vector((-o.location.y,o.location.x,o.location.z)); o.rotation_euler[2]+=math.pi/2
cube('Chimney • plaster stack',(.78,.62,3.57),(.43,.46,1.05),'Warm plaster',.055)
cube('Chimney • cap',(.78,.62,4.10),(.58,.59,.14),'Cream',.035)
cube('Chimney • dark opening',(.78,.62,4.176),(.30,.32,.018),'Dark wood',.018)
for i in range(3): cube('Chimney • little brick',(.78+(.08 if i%2 else -.08),.379,3.35+i*.21),(.22,.022,.075),'Brick',.018)
cube('Porch • little canopy',(.57,-1.54,1.93),(1.17,.77,.13),'Teal roof',.05,rot=(.12,0,0))
for x in (.10,1.04): rod('Porch • bracket',(x,-1.22,1.55),(x,-1.79,1.92),.035,'Wood')
cube('House • number plaque',(.99,-1.25,1.36),(.22,.06,.21),'Cream',.035)
text('House • 03','03',(.99,-1.291,1.36),.11,'Ink')
pot('House • porch pot',1.17,-1.53,0,.17,.26,False)
cube('House • mailbox',(-1.09,-1.27,.70),(.29,.16,.36),'Teal roof',.045)
cube('House • letter slot',(-1.09,-1.365,.78),(.19,.022,.035),'Brass',.008)

# 02 — a butter-yellow café: rounded parapet, broad shopfront, striped awning.
begin_asset('cafe','02 Butter Cafe')
foundation(3.0,2.40,'Butter plaster')
cube('Cafe • upper cornice',(0,0,2.63),(3.24,2.64,.23),'Cream',.08)
# Low hipped roof, with the back matching the visible front.
verts=[(-1.69,-1.43,2.75),(1.69,-1.43,2.75),(1.69,1.43,2.75),(-1.69,1.43,2.75),(-1.22,-.97,3.25),(1.22,-.97,3.25),(1.22,.97,3.25),(-1.22,.97,3.25)]
mesh('Cafe • hipped teal roof',verts,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'Teal roof',.08)
cube('Cafe • roof crown',(0,0,3.24),(2.50,2.02,.14),'Teal tile',.08)
for x in (-1.22,-.82,-.41,0,.41,.82,1.22):
    rod('Cafe • raised roof seam',(x,-1.40,2.80),(x*.73,-.98,3.28),.022,'Teal tile')
window('Cafe display',-.57,-1.25,1.17,1.34,1.39,trim='Teal dark')
arched_door(.99,-1.25,'Teal roof')
cube('Cafe • fascia sign',(0,-1.29,2.32),(2.54,.16,.42),'Teal dark',.08)
text('Cafe • raised lettering','BUTTER',(-.08,-1.389,2.33),.25,'Cream')
# Segmented fabric over a quarter-curve profile, alternating stripes.
for k in range(10):
    x=-1.49+(k+.5)*2.98/10; width=2.98/10+.008
    coords=[]
    for j in range(9):
        t=j/8
        coords.append((-1.29-.71*t,2.08-.12*t-.25*t*t))
    vs=[]
    for xx in (x-width/2,x+width/2): vs += [(xx,yy,zz) for yy,zz in coords]
    fs=[(j,j+1,9+j+1,9+j) for j in range(8)]
    o=mesh('Cafe • awning stripe %02d'%k,vs,fs,'Cream' if k%2==0 else 'Teal roof',0)
    solid=o.modifiers.new('Canvas thickness','SOLIDIFY'); solid.thickness=.045
    bevel(o,.018,2)
    cube('Cafe • scalloped valance',(x,-2.006,1.65),(width,.07,.23),'Cream' if k%2==0 else 'Teal roof',.075)
for x in (-1.47,1.47): rod('Cafe • awning support',(x,-1.28,1.58),(x,-1.98,1.76),.025,'Brass')
# Raised cup icon on a projecting wooden sign.
rod('Cafe • sign arm',(1.45,-1.2,2.49),(1.95,-1.6,2.49),.04,'Dark wood')
cylinder('Cafe • round cup sign',(1.88,-1.64,2.19),.31,.12,'Cream',rot=(math.pi/2,0,0))
cube('Cafe • cup relief',(1.84,-1.719,2.19),(.25,.04,.22),'Teal roof',.055)
torus('Cafe • cup handle',(2.00,-1.72,2.21),.072,.023,'Teal roof',rot=(math.pi/2,0,0))
cube('Cafe • saucer relief',(1.84,-1.72,2.04),(.35,.04,.045),'Teal roof',.018)
# Side window and a small exterior café table.
before=set(COL.objects)
window('Cafe side window',.15,-1.54,1.44,1.16,1.12,trim='Cream')
for o in set(COL.objects)-before:
    o.location=Vector((-o.location.y,o.location.x,o.location.z)); o.rotation_euler[2]+=math.pi/2
cylinder('Cafe • pavement table',(-.92,-2.02,.63),.36,.10,'Wood light')
rod('Cafe • table pedestal',(-.92,-2.02,.08),(-.92,-2.02,.62),.055,'Ink')
cylinder('Cafe • table base',(-.92,-2.02,.045),.23,.09,'Ink')
for x,y in [(-1.45,-2.08),(-.39,-2.16)]:
    cylinder('Cafe • stool seat',(x,y,.36),.18,.09,'Wood light')
    for dx,dy in [(-.10,-.08),(.10,-.08),(0,.11)]: rod('Cafe • stool leg',(x+dx,y+dy,.02),(x+dx*.7,y+dy*.7,.34),.025,'Ink')
cylinder('Cafe • cup on table',(-.96,-2.04,.74),.07,.13,'Cream',top=.085)
cylinder('Cafe • coffee',(-.96,-2.04,.808),.069,.008,'Dark wood',vertices=16)
pot('Cafe • succulent',-.77,-1.92,.685,.075,.10,False)
# Sandwich board is an actual A-frame, with raised chalk motifs.
for y,angle in [(-1.73,-.16),(-1.44,.16)]:
    cube('Cafe • A board wood frame',(.26,y,.50),(.49,.07,.89),'Wood light',.035,rot=(angle,0,0))
cube('Cafe • A board writing surface',(.26,-1.817,.54),(.37,.026,.62),'Ink',.025,rot=(-.16,0,0))
text('Cafe • menu title','MENU',(.26,-1.87,.70),.09,'Chalk')
for z,w in [(.56,.23),(.46,.19),(.36,.24)]: cube('Cafe • chalk menu line',(.26,-1.86,z),(w,.016,.016),'Chalk',.005)

# 03 — a narrow flower shop with a taller mint gable and greenhouse bay.
begin_asset('flower_shop','03 Petal Florist')
foundation(2.58,2.28,'Sage plaster')
gable_roof(3.04,2.77,2.65,.88,'Teal roof','Teal tile')
arched_door(-.64,-1.21,'Rose canopy')
window('Florist display',.56,-1.21,1.36,.83,1.18,trim='Cream')
cube('Florist • sign backing',(0,-1.29,2.33),(2.10,.18,.40),'Cream',.085)
text('Florist • raised lettering','PETAL',(0,-1.402,2.33),.245,'Teal dark')
# Little flower emblem in the gable.
for k in range(6):
    a=k*math.tau/6
    sphere('Florist • gable petal',(math.sin(a)*.15,-1.23,2.98+math.cos(a)*.15),(.10,.05,.13),'Flower cream',12,8)
sphere('Florist • gable flower centre',(0,-1.29,2.98),(.085,.04,.085),'Clay light',12,8)
for k in range(7):
    x=.56-.70+(k+.5)*1.40/7
    cube('Florist • canvas stripe',(x,-1.49,2.02),(1.4/7+.006,.73,.075),'Rose canopy' if k%2==0 else 'Cream',.025,rot=(.24,0,0))
    cube('Florist • canvas scallop',(x,-1.84,1.88),(1.4/7+.006,.07,.20),'Rose canopy' if k%2==0 else 'Cream',.065)
# Small faceted glazed conservatory attached to the right wall.
cube('Florist • greenhouse base',(1.57,.14,.25),(.70,1.81,.50),'Cream',.07)
cube('Florist • greenhouse glass',(1.57,.14,1.11),(.61,1.72,1.27),'Glass light',.035)
for x in (1.30,1.90):
    for y in (-.74,.14,1.02): cube('Florist • greenhouse upright',(x,y,1.13),(.065,.075,1.43),'Cream',.015)
for z in (.55,1.02,1.76): cube('Florist • greenhouse side rail',(1.92,.14,z),(.07,1.85,.065),'Cream',.012)
cube('Florist • greenhouse roof',(1.59,.14,1.91),(.79,1.90,.08),'Glass',.022,rot=(0,.32,0))
for y in (-.77,-.14,.46,1.06): cube('Florist • greenhouse roof rafter',(1.59,y,1.96),(.83,.065,.08),'Cream',.015,rot=(0,.32,0))
for x,z in [(1.22,2.08),(1.97,1.83)]: cube('Florist • greenhouse roof edge',(x,.14,z),(.08,1.96,.09),'Cream',.02)
cube('Florist • flower stand',(.65,-1.63,.47),(1.17,.44,.13),'Wood light',.035)
for x in (.14,1.16):
    for y in (-1.79,-1.49): cube('Florist • stand leg',(x,y,.23),(.075,.075,.46),'Wood',.018)
for i,color in enumerate(('Flower pink','Flower cream','Flower plum')):
    pot('Florist • display bouquet',.23+i*.41,-1.63,.535,.16,.22,True,color)
pot('Florist • tall front bouquet',-1.13,-1.59,0,.22,.42,True,'Flower cream')
pot('Florist • side succulent',1.53,-1.23,0,.23,.30,False)
cube('Florist • door hanging sign',(-.64,-1.44,1.10),(.37,.05,.18),'Cream',.03)
text('Florist • OPEN','OPEN',(-.64,-1.477,1.10),.09,'Teal dark')

# 04 — a sculpted canopy on a branching trunk, roots anchored at ground level.
begin_asset('round_tree','04 Round Tree')
cylinder('Tree • soil mound',(0,0,.065),.52,.13,'Grass',top=.45)
cylinder('Tree • trunk',(0,0,.91),.15,1.72,'Wood',top=.10,vertices=12)
for a in (.3,2.3,4.4):
    rod('Tree • root',(0,0,.20),(.38*math.cos(a),.38*math.sin(a),.055),.075,'Wood',10)
for a,z in [(0,1.4),(2.1,1.55),(4.2,1.7)]:
    rod('Tree • branch',(0,0,.85),(.47*math.cos(a),.47*math.sin(a),z),.07,'Wood',10)
for i,(x,y,z,sx,sy,sz) in enumerate([(-.46,-.10,1.90,.65,.61,.68),(.42,-.21,2.03,.67,.63,.72),(.0,.42,2.15,.70,.66,.69),(-.12,-.14,2.51,.70,.65,.67),(.43,.32,2.44,.53,.51,.58)]):
    o=sphere('Tree • sculpted foliage %02d'%i,(x,y,z),(sx,sy,sz),['Leaf','Leaf light','Leaf dark','Leaf light','Leaf'][i],20,12)
    # Tiny, deterministic silhouette irregularities keep the canopy from perfect bubbles.
    for v in o.data.vertices:
        q=v.co
        q*=1+.025*math.sin(q.x*13+q.y*9)*math.cos(q.z*11)
for x,y in [(-.31,-.24),(.27,.25)]:
    sphere('Tree • ground leaf',(x,y,.13),(.16,.08,.065),'Leaf light',12,8)

# 05 — bent metal frame and individual timber slats, visible pegs and rounded ends.
begin_asset('wood_bench','05 Timber Bench')
for y in (-.23,-.075,.08,.235): cube('Bench • seat slat',(0,y,.47),(1.65,.13,.105),'Wood light',.035)
for z in (.71,.89,1.07): cube('Bench • back slat',(0,.31+(z-.7)*.12,z),(1.65,.105,.14),'Wood light',.035,rot=(.12,0,0))
for x in (-.62,.62):
    for y in (-.20,.23): rod('Bench • splayed leg',(x,y*1.2,.025),(x,y,.43),.045,'Teal dark')
    rod('Bench • seat support',(x,-.30,.40),(x,.35,.40),.045,'Teal dark')
    rod('Bench • back support',(x,.26,.40),(x,.38,1.15),.04,'Teal dark')
    rod('Bench • arm front',(x,-.18,.46),(x,-.18,.72),.035,'Teal dark')
    cube('Bench • wooden armrest',(x,.03,.74),(.13,.54,.085),'Wood',.04)
    for z in (.71,.89,1.07): sphere('Bench • brass peg',(x,.246+(z-.7)*.12,z),(.018,.012,.018),'Brass',10,6)
rod('Bench • lower stretcher',(-.65,.16,.23),(.65,.16,.23),.035,'Teal dark')

# 06 — a softly lit little lantern with an actual frame and four glowing panes.
begin_asset('street_lamp','06 Lantern')
cylinder('Lamp • foot',(0,0,.055),.24,.11,'Teal dark')
cylinder('Lamp • flared base',(0,0,.24),.145,.30,'Teal dark',top=.085)
cylinder('Lamp • post',(0,0,1.19),.055,1.68,'Teal dark')
for z in (.44,1.84): cylinder('Lamp • brass collar',(0,0,z),.076,.07,'Brass')
cylinder('Lamp • lantern foot',(0,0,1.99),.22,.12,'Teal dark',vertices=4,rot=(0,0,math.pi/4))
cube('Lamp • warm glass',(0,0,2.22),(.28,.28,.40),'Lamp glow',.035)
for x in (-.17,.17):
    for y in (-.17,.17): rod('Lamp • lantern corner',(x,y,2.0),(x,y,2.46),.024,'Teal dark')
cube('Lamp • top frame',(0,0,2.46),(.40,.40,.09),'Teal dark',.025)
cylinder('Lamp • pyramidal cap',(0,0,2.60),.37,.25,'Teal roof',top=.06,vertices=4,rot=(0,0,math.pi/4))
sphere('Lamp • finial',(0,0,2.76),(.06,.06,.09),'Brass',12,8)

# Keep all fonts editable in .blend. Exporter receives evaluated mesh copies later.
def evaluated_stats(objs):
    dg=bpy.context.evaluated_depsgraph_get(); triangles=0; vertices=0; meshes=0; materials=set(); bounds=[]
    for o in objs:
        if o.type not in {'MESH','FONT','CURVE','SURFACE'}: continue
        e=o.evaluated_get(dg); me=e.to_mesh()
        me.calc_loop_triangles(); triangles+=len(me.loop_triangles); vertices+=len(me.vertices); meshes+=1
        materials.update(m.name for m in me.materials if m)
        bounds.extend(e.matrix_world@v.co for v in me.vertices)
        e.to_mesh_clear()
    lo=[min(v[i] for v in bounds) for i in range(3)]
    hi=[max(v[i] for v in bounds) for i in range(3)]
    return dict(mesh_objects=meshes,evaluated_vertices=vertices,triangles=triangles,materials=len(materials),material_names=sorted(materials),bounds_min=lo,bounds_max=hi,dimensions=[hi[i]-lo[i] for i in range(3)])

bpy.context.view_layer.update()
# Normalize the actual evaluated lowest vertex, including bevels and tilted legs.
for key,(c,r) in ASSETS.items():
    dz=evaluated_stats(c.objects)['bounds_min'][2]
    for o in c.objects:
        if o != r: o.location.z-=dz
bpy.context.view_layer.update()
stats={key:evaluated_stats(c.objects) for key,(c,r) in ASSETS.items()}
(ROOT/'reports/model_stats.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
(ROOT/'reports/palette.json').write_text(json.dumps(PALETTE,indent=2),encoding='utf-8')

# Export each asset at the shared ground pivot. Evaluate modifiers but retain component names.
for key,(c,r) in ASSETS.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in c.objects: o.select_set(True)
    bpy.context.view_layer.objects.active=r
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'exports'/f'{key}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True,export_cameras=False,export_lights=False)
    print('EXPORTED',key,flush=True)

# Hide originals from camera using collection.hide_render. Display instances in the diorama.
for c,r in ASSETS.values():
    scene.collection.children.unlink(c)
    c.use_fake_user=True
COL=collection('DIORAMA • lane and landscaping'); ROOT_OBJ=None

def instance(key,name,loc,angle=0,scale=1):
    o=bpy.data.objects.new(name,None); COL.objects.link(o)
    o.instance_type='COLLECTION'; o.instance_collection=ASSETS[key][0]
    o.location=loc; o.rotation_euler[2]=angle; o.scale=(scale,)*3
    return o

cube('Diorama • rounded display island',(0,0,-.30),(11.9,7.8,.56),'Stone',.23)
cube('Diorama • garden surface',(0,0,-.045),(11.65,7.55,.09),'Grass',.16)
cube('Diorama • warm pedestrian lane',(0,-1.90,.007),(11.54,2.55,.075),'Paving',.18)
cube('Diorama • rear pavement',(0,1.17,.025),(11.40,3.28,.11),'Paving warm',.10)
# A slim border and small individual pavers catch soft contact shadows.
for x in [i*.46-5.52 for i in range(25)]:
    for y in (-3.20,-.58): cube('Lane • rounded kerbstone',(x,y,.078),(.43,.18,.16),'Cream',.035)
for row in range(4):
    for j in range(23):
        x=-5.35+j*.48+(.22 if row%2 else 0)
        if x>5.4: continue
        cube('Lane • setts',(x,-2.90+row*.56,.054),(.44,.51,.035),'Paving warm' if (j+row)%7==0 else 'Paving',.035)
instance('house','House on Apricot Lane',(-3.73,1.13,.085),-.035)
instance('cafe','Butter Cafe on the corner',(-.20,1.23,.085),0)
instance('flower_shop','Petal florist',(3.38,1.30,.085),.025)
instance('round_tree','Tree • left corner',(-5.05,-1.32,.03),0,.88)
instance('round_tree','Tree • back garden',(5.03,2.54,.03),1.7,.82)
instance('wood_bench','Bench • foreground',(2.32,-2.85,.075),-.08)
instance('street_lamp','Lamp • by cafe',(-1.86,-.90,.09))
instance('street_lamp','Lamp • by flower shop',(4.79,-1.06,.09))
# Small planted corners, stones, and stepping slabs create a cared-for lane.
for x,y in [(-4.48,2.98),(-2.13,2.97),(1.52,2.96),(5.0,1.56)]:
    for k in range(3): sphere('Garden • low shrub',(x+.24*(k-1),y,.30),(.35,.31,.30),'Leaf' if k%2 else 'Leaf light',14,8)
for x,y in [(-4.0,-3.57),(-3.2,-3.49),(4.47,-3.48),(.2,-3.52)]:
    for k in range(3):
        a=k*2.2
        sphere('Garden • tiny clover',(x+.08*math.sin(a),y+.08*math.cos(a),.04),(.065,.10,.035),'Leaf',10,6)
for x in (-3.65,-3.15): cube('Garden • stepping stone',(x,-.35,.08),(.42,.30,.10),'Cream',.08,rot=(0,0,.06))
# Inset brass title at the front of the physical base.
cube('Diorama • title plate',(0,-3.913,-.28),(2.45,.035,.24),'Brass',.035)
text('Diorama • title','C H A G O K   L A N E',(0,-3.94,-.28),.115,'Dark wood')

COL=collection('STUDIO • camera and lights')
cube('Studio floor',(0,0,-.66),(200,200,.10),'Backdrop',.02)

def camera(name,loc,target,ortho):
    data=bpy.data.cameras.new(name); o=bpy.data.objects.new(name,data); COL.objects.link(o)
    o.location=loc; o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO'; data.ortho_scale=ortho; data.lens=50
    return o

cam=camera('Camera • hero',(11,-17,13),(0,.05,1.0),15.9); scene.camera=cam
def area(name,loc,power,size,color,target=(0,0,0)):
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.shape='DISK'; data.size=size; data.color=color
    o=bpy.data.objects.new(name,data); COL.objects.link(o); o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

area('Large warm window',(-6,-8,13),1800,8,(1,.86,.72))
area('Cool sky fill',(7,-1,10),1100,7,(.77,.87,1))
area('Soft back rim',(0,7,10),1400,6,(1,.94,.80))
scene.world=bpy.data.worlds.new('Warm studio world'); scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs['Color'].default_value=(.65,.72,.78,1); bg.inputs['Strength'].default_value=.35

# Enum choices are inspected before assigning, except engines (Blender may under-report them).
try: scene.render.engine='CYCLES'
except TypeError: scene.render.engine='BLENDER_EEVEE'
if scene.render.engine=='CYCLES':
    scene.cycles.samples=48
    scene.cycles.use_denoising=True
    scene.cycles.max_bounces=6
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences
        prefs.get_devices()
        available=[i.identifier for i in prefs.bl_rna.properties['compute_device_type'].enum_items]
        for backend in ('OPTIX','CUDA','HIP','ONEAPI','METAL'):
            if backend not in available: continue
            try:
                prefs.compute_device_type=backend; prefs.get_devices()
                gpu=[d for d in prefs.devices if d.type!='CPU']
                if gpu:
                    for d in prefs.devices: d.use=d.type!='CPU'
                    scene.cycles.device='GPU'; break
            except Exception: pass
    except Exception: pass
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.resolution_x=1800; scene.render.resolution_y=1400; scene.render.resolution_percentage=100
scene.render.film_transparent=False
view_options=[v.identifier for v in scene.view_settings.bl_rna.properties['view_transform'].enum_items]
if 'AgX' in view_options: scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=.35
scene.render.filepath=str(ROOT/'renders/01_diorama.png')
# Saved camera view opens directly as a useful overview, not a random object close-up.
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_perspective='CAMERA'
            a.spaces.active.clip_end=500
bpy.ops.object.select_all(action='DESELECT')
scene['art_direction']='Warm cartoon miniature; separate editable solid parts; no image cards.'
scene['validation_scope']='3D assets and rendered stills; not Android/Pleos/device performance.'
# Each source collection also has an ordinary editing scene. Collection instances in
# the lane update immediately when a component is edited in one of these six scenes.
library_studio=bpy.data.collections.new('LIBRARY • shared studio')
for o in COL.objects:
    if o.type=='LIGHT': library_studio.objects.link(o)
floor=bpy.data.objects['Studio floor'].copy()
floor.data=floor.data.copy(); floor.name='Library floor'; floor.location.z=-.06
library_studio.objects.link(floor)
for index,(key,(c,r)) in enumerate(ASSETS.items(),2):
    s=bpy.data.scenes.new('%02d • Edit %s'%(index,key))
    s.collection.children.link(c); s.collection.children.link(library_studio)
    s.world=scene.world; s.unit_settings.system='METRIC'; s.unit_settings.scale_length=1
    cd=bpy.data.cameras.new('Edit camera '+key); co=bpy.data.objects.new('Edit camera '+key,cd)
    s.collection.objects.link(co); s.camera=co
    height=stats[key]['dimensions'][2]
    co.location=(height*1.9,-height*2.5,height*2.0)
    co.rotation_euler=(Vector((0,0,height*.46))-co.location).to_track_quat('-Z','Y').to_euler()
    cd.type='ORTHO'; cd.ortho_scale=max(height*1.45,stats[key]['dimensions'][0]*1.7)
    s.render.engine=scene.render.engine
    if s.render.engine=='CYCLES': s.cycles.samples=48; s.cycles.use_denoising=True
    s.render.resolution_x=1100; s.render.resolution_y=1100; s.render.resolution_percentage=100
    s.view_settings.view_transform=scene.view_settings.view_transform; s.view_settings.exposure=.35
    s['edit_help']='Expand ASSET collection. All components and material slots are editable; lane uses this same collection.'
bpy.context.window.scene=scene
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/chagok_town_miniature_v001.blend'))
print('BUILD_COMPLETE',str(ROOT),flush=True)
