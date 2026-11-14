"""Two composition studies; existing GLBs stay read-only. No equal lots or loop road."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];ART=ROOT.parent
for d in ('blend','renders','reports'):(ROOT/d).mkdir(exist_ok=True)
PREVIEW='--preview' in sys.argv;CHECK_ONLY='--layout-check' in sys.argv
LAYOUTS=json.loads((ROOT/'source/layouts.json').read_text())
FOLDERS={'cafe':'town_cafe_v003','house':'town_house_florist_v001','florist':'town_house_florist_v001',
         'bakery':'town_sol_bakery_bookshop_v001','bookshop':'town_sol_bakery_bookshop_v001',
         'grocer':'town_sol_civic_market_workshop_v001','workshop':'town_sol_civic_market_workshop_v001'}
def asset(kind,level):return ART/FOLDERS[kind]/'exports'/f'{kind}_level_{level}.glb'
inputs={asset(b['kind'],l) for data in LAYOUTS.values() for b in data['buildings'] for l in (b['level'],3)}
inputs|={p for p in (ART/'town_layout_v001').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
hashes={str(p.relative_to(ART)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
(ROOT/'reports/read_only_inputs.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
sys.path.insert(0,str(ROOT/'source'));import geometry as G
from geometry import box,cyl,rod,ellipsoid,ring,mesh
library=bpy.context.scene;library.name='LIBRARY • unchanged source GLBs'
G.scene=library;G.LOW=True;G.PARENT=None
palette=json.loads((ART/'town_sol_bakery_bookshop_v001/reports/palette.json').read_text())
palette.update({'Grass':'9BAA79','Grass light':'A8B586','Grass dark':'829567','Path':'D9C8A6',
                'Path edge':'B6A382','Bank':'A49273','Water':'80B6B8','Water deep':'679CA7','Wall stone':'B7AA92',
                'Warm plaster':'D8C6A6','Deep teal roof':'376C67','Olive roof':'79754F','Olive roof light':'938B62'})
for name,h in palette.items():
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=G.linear(h)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=G.linear(h);p.inputs['Roughness'].default_value=.85
    G.M[name]=m
CACHE={};VERTS={}
def load(kind,level):
    key=f'{kind}_level_{level}'
    if key in CACHE:return CACHE[key]
    bpy.context.window.scene=library;before=set(library.objects)
    bpy.ops.import_scene.gltf(filepath=str(asset(kind,level)));bpy.context.view_layer.update()
    objects=set(library.objects)-before;c=bpy.data.collections.new('ASSET • '+key);library.collection.children.link(c)
    for o in objects:
        for col in list(o.users_collection):col.objects.unlink(o)
        c.objects.link(o)
    VERTS[key]=[o.matrix_world@v.co for o in objects if o.type=='MESH' for v in o.data.vertices]
    CACHE[key]=c;return c
def hull(points):
    pp=sorted(set((round(x,5),round(y,5)) for x,y in points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];hi=[]
    for p in pp:
        while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(pp):
        while len(hi)>=2 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]
def angle(b):
    x,y=b['xy'];tx,ty=b['toward'];return math.atan2(tx-x,-(ty-y))
def transform(b,p):
    a=angle(b);s=b['scale'];x,y=b['xy']
    return (x+s*(math.cos(a)*p[0]-math.sin(a)*p[1]),y+s*(math.sin(a)*p[0]+math.cos(a)*p[1]))
def polygon_gap(a,b):
    # SAT on actual maximum-stage projected convex hulls, not 4.8 m slot rectangles.
    max_sep=-1e9
    for poly in (a,b):
        for p,q in zip(poly,poly[1:]+poly[:1]):
            dx=q[0]-p[0];dy=q[1]-p[1];length=math.hypot(dx,dy);axis=(-dy/length,dx/length)
            aa=[x*axis[0]+y*axis[1] for x,y in a];bb=[x*axis[0]+y*axis[1] for x,y in b]
            max_sep=max(max_sep,max(min(aa)-max(bb),min(bb)-max(aa)))
    return max_sep
REPORT={'scope':'composition-only; no runtime packaging or full asset recertification','concepts':{}}
for label,data in LAYOUTS.items():
    footprints={}
    for b in data['buildings']:
        load(b['kind'],b['level']);load(b['kind'],3)
        key=b['kind']+'_level_3';footprints[b['id']]=hull([transform(b,v) for v in VERTS[key]])
        b['yaw_degrees']=math.degrees(angle(b))
    pairs=[]
    for i,a in enumerate(data['buildings']):
        for b in data['buildings'][i+1:]:
            gap=polygon_gap(footprints[a['id']],footprints[b['id']])
            pairs.append({'a':a['id'],'b':b['id'],'separating_gap_m':round(gap,4),'overlap':gap<-.0001})
    REPORT['concepts'][label]={'buildings':data['buildings'],'maximum_stage_xy_hulls':footprints,'pairs':pairs}
    bad=[p for p in pairs if p['overlap']]
    print('PLACEMENT_CHECK',label,json.dumps(bad),flush=True)
(ROOT/'reports/layout_checks.json').write_text(json.dumps(REPORT,indent=2),encoding='utf-8')
if CHECK_ONLY:raise SystemExit(0)
assert not any(p['overlap'] for c in REPORT['concepts'].values() for p in c['pairs']),'Maximum-stage hull collision; inspect layout_checks.json'

def inside(p,poly):
    x,y=p;result=False
    for (ax,ay),(bx,by) in zip(poly,poly[1:]+poly[:1]):
        if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:result=not result
    return result
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def segment_distance(p,a,b):
    dx=b[0]-a[0];dy=b[1]-a[1];dd=dx*dx+dy*dy
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/dd)) if dd else 0
    return math.hypot(p[0]-a[0]-dx*t,p[1]-a[1]-dy*t)
def boundary_distance(p,poly):return min(segment_distance(p,a,b) for a,b in zip(poly,poly[1:]+poly[:1]))
def spline(points,steps=9):
    # x,y,z,width samples; hand-authored nodes control routes, not random placement.
    pp=[Vector(p) for p in points];p=[pp[0]]+pp+[pp[-1]];out=[]
    for i in range(1,len(p)-2):
        a,b,c,d=p[i-1:i+3]
        for j in range(steps):
            t=j/steps;out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    out.append(pp[-1]);return out
STREAM=spline([(-10,-11,-.32,2.3),(-7.0,-6.0,-.32,2.0),(-3,-3,-.32,2.05),(0,-1,-.32,1.9),(2.3,1.7,-.32,1.8),(3,5,-.32,2.0),(5.5,9,-.32,1.95),(5.3,14,-.32,2.1)],10)
TERRACE=[(-8.1,5.05),(-5.4,4.85),(-3.4,5.40),(-1.7,6.25),(3.4,7.15),(4.2,11.5),(-1.2,12.9),(-8.3,10.1)]
def stream_dist(x,y):return min(segment_distance((x,y),(a.x,a.y),(b.x,b.y)) for a,b in zip(STREAM,STREAM[1:]))
def height(label,x,y):
    if label=='A':
        h=.10+1.75*smooth((y-5.2)/6)+.42*math.exp(-((x+10)**2+(y-5)**2)/22)
        h-=.55*math.exp(-((x+6.5)**2+(y+5)**2)/15)
        if inside((x,y),TERRACE):h=1.65
        elif y>6:
            dist=boundary_distance((x,y),TERRACE)
            h=h*smooth(dist/1.3)+1.65*(1-smooth(dist/1.3))
    else:
        h=.03+.48*smooth((x-2)/6)+.25*smooth((y-5)/5)
        dist=stream_dist(x,y)
        if dist<1.7:h=-.53+(h+.53)*smooth((dist-.78)/.92)
    # Compact pads conform to actual hulls. They are blended into terrain, not visible lots.
    for b in LAYOUTS[label]['buildings']:
        poly=REPORT['concepts'][label]['maximum_stage_xy_hulls'][b['id']]
        isin=inside((x,y),poly);dist=boundary_distance((x,y),poly)
        if isin:h=b['ground']
        elif dist<.75:h=b['ground']+(h-b['ground'])*smooth(dist/.75)
    if label=='A':
        plaza=[(-4.1,.2),(-3.30,-1.25),(-1.35,-2.30),(1.24,-1.64),(2.60,.45),(1.83,2.54),(-.52,3.15),(-2.56,2.35),(-3.89,1.47)]
        if inside((x,y),plaza):h=0.0
        else:
            dist=boundary_distance((x,y),plaza)
            if dist<.55:h*=smooth(dist/.55)
    else:
        # Keep the real channel continuous even where a conservative future-stage
        # ground pad extends beyond the smaller displayed shop's current foundation.
        dist=stream_dist(x,y)
        if dist<1.65:
            natural=.03+.48*smooth((x-2)/6)+.25*smooth((y-5)/5)
            bed=-.53+(natural+.53)*smooth((dist-.78)/.92)
            h=min(h,bed)
    return h

def polygon(name,poly,z,color,depth=.10):
    n=len(poly);vs=[(x,y,z-depth) for x,y in poly]+[(x,y,z) for x,y in poly]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,vs,faces,color,.018)
CURRENT_LABEL=None
TERRAIN_BVH={}
RIBBON_ORDINAL=0
def surface_height(label,x,y):
    if label not in TERRAIN_BVH:return height(label,x,y)
    hit=TERRAIN_BVH[label].ray_cast(Vector((x,y,40)),Vector((0,0,-1)),80)[0]
    return hit.z if hit is not None else height(label,x,y)
def ribbon(name,nodes,color,edge=True,lift=None):
    global RIBBON_ORDINAL
    if lift is None:
        RIBBON_ORDINAL+=1;lift=RIBBON_ORDINAL*.003
    pp=spline(nodes,steps=14);vs=[];across=6
    for i,p in enumerate(pp):
        a=pp[max(i-1,0)];b=pp[min(i+1,len(pp)-1)];d=Vector((b.x-a.x,b.y-a.y,0)).normalized();side=Vector((-d.y,d.x,0))
        for j in range(across+1):
            sign=j/across*2-1;xx=p.x+sign*side.x*p.w/2;yy=p.y+sign*side.y*p.w/2
            zz=p.z if color in ('Water','Water deep') else surface_height(CURRENT_LABEL,xx,yy)+(.045 if edge else .027)+lift
            vs.append((xx,yy,zz))
    fs=[]
    for i in range(len(pp)-1):
        for j in range(across):
            a=i*(across+1)+j;fs.append((a+across+1,a+across+2,a+1,a))
    if edge:
        outer=[(p[0],p[1],p[2]-.018,p[3]+.18) for p in nodes]
        ribbon(name+' • worn margin',outer,'Path edge',False,lift)
    o=mesh(name,vs,fs,color)
    # Roads are fused surface colour in this study. Overlapping route junctions
    # should receive building shadows, but must not cast near-coplanar self shadows.
    o.visible_shadow=False
    return o
def terrain(label):
    # Broad continuous ground extends beyond the camera; no island rim or display plinth.
    step=.40;count=130;vs=[]
    for iy in range(count+1):
        y=-24+iy*step
        for ix in range(count+1):
            x=-26+ix*step;vs.append((x,y,height(label,x,y)))
    fs=[]
    for iy in range(count):
        for ix in range(count):
            a=iy*(count+1)+ix;fs.append((a,a+1,a+count+2,a+count+1))
    o=mesh(label+' • continuous terrain',vs,fs,'Grass')
    for p in o.data.polygons:p.use_smooth=True
    # Vertex blends remove grid-stepped banks and hard polygons under the woodland.
    attr=o.data.color_attributes.new(name='Ground palette',type='FLOAT_COLOR',domain='POINT')
    for i,vert in enumerate(o.data.vertices):
        xx,yy=vert.co.x,vert.co.y
        forest=max(math.exp(-((xx-cx)**2+(yy-cy)**2)/rr**2) for cx,cy,rr in ([(-9,8,4.2),(7,8,4.0),(-10,-4,3.5)] if label=='A' else [(-8,9,4.0),(10,4,4.5),(9,-7,3.2),(-11,-4,3.2)]))
        c1=G.linear(palette['Grass']);c2=G.linear(palette['Grass dark']);blend=forest*.55
        color=tuple(a*(1-blend)+b*blend for a,b in zip(c1,c2))
        if label=='B':
            bank=1-smooth((stream_dist(xx,yy)-.95)/.95);bb=G.linear(palette['Bank'])
            color=tuple(a*(1-bank)+b*bank for a,b in zip(color,bb))
        attr.data[i].color=color
    mat=bpy.data.materials.new(label+' • blended ground');mat.use_nodes=True
    bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Roughness'].default_value=.94
    vc=mat.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Ground palette';mat.node_tree.links.new(vc.outputs['Color'],bsdf.inputs['Base Color'])
    o.data.materials.clear();o.data.materials.append(mat)
    o.data.calc_loop_triangles()
    TERRAIN_BVH[label]=BVHTree.FromPolygons([v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)

def tree(x,y,h,label,variant=0,hero=False):
    z=surface_height(label,x,y)
    cyl('Tree • warm trunk',(x,y,z+h*.28),.12 if hero else .095,h*.56,'Wood',top=.07)
    rod('Tree • branch',(x,y,z+h*.35),(x+.45,y+.07,z+h*.65),.065,'Wood')
    colors=['Leaf','Leaf dark','Leaf light']
    crown=[(-.34,-.04,.72,.92),(.44,.12,.77,.80),(.02,.02,.92,.70)]
    for i,(dx,dy,hh,ss) in enumerate(crown):
        o=ellipsoid('Tree • rounded canopy',(x+dx,y+dy,z+h*hh),(h*.28*ss,h*.25*ss,h*.30*ss),colors[(i+variant)%3])
        o.rotation_euler[2]=variant*.37+i*.23
def shrub(x,y,label,s=.7):
    z=surface_height(label,x,y)
    for dx,dy,k in [(-.25,0,.8),(.22,.05,1),(.03,-.22,.7)]:
        ellipsoid('Shrub • leaf mound',(x+dx*s,y+dy*s,z+.30*s*k),(.50*s*k,.40*s*k,.38*s*k),'Leaf')
def rock(x,y,label,s=1):
    z=surface_height(label,x,y)
    o=ellipsoid('Rock • soft outcrop',(x,y,z+.25*s),(.63*s,.43*s,.40*s),'Wall stone');o.rotation_euler=(.1,.17,x*.17)
def wall(name,points,zbottom,ztop):
    for a,b in zip(points,points[1:]):
        d=Vector((b[0]-a[0],b[1]-a[1],0));length=d.length;n=max(1,math.ceil(length/.77))
        for i in range(n):
            t=(i+.5)/n;x=a[0]+d.x*t;y=a[1]+d.y*t
            for row in range(3):
                hh=(ztop-zbottom)/3
                box(name,(x,y,zbottom+(row+.5)*hh),(length/n-.025,.32,hh-.023),'Wall stone',.045,rot=(0,0,math.atan2(d.y,d.x)))
        box(name+' • coping',((a[0]+b[0])/2,(a[1]+b[1])/2,ztop+.035),(length+.03,.43,.13),'Stone',.035,rot=(0,0,math.atan2(d.y,d.x)))
def bench(x,y,z,theta=0):
    before=set(G.COL.objects)
    box('Shared bench • timber seat',(0,0,z+.44),(1.15,.39,.10),'Wood light',.03)
    box('Shared bench • back',(0,.18,z+.66),(1.15,.07,.24),'Wood light',.025)
    for dx in (-.41,.41):
        for dy in (-.12,.12):rod('Shared bench • leg',(dx,dy,z),(dx,dy,z+.40),.027,'Teal dark')
        rod('Shared bench • back support',(dx,.16,z+.40),(dx,.16,z+.74),.023,'Teal dark')
    for o in set(G.COL.objects)-before:
        xx,yy=o.location.x,o.location.y;o.location.x=x+math.cos(theta)*xx-math.sin(theta)*yy;o.location.y=y+math.sin(theta)*xx+math.cos(theta)*yy;o.rotation_euler[2]+=theta
def lantern(x,y,z):
    rod('Lane light • post',(x,y,z),(x,y,z+1.74),.035,'Teal dark')
    box('Lane light • warm glass',(x,y,z+1.68),(.21,.21,.26),'Butter',.035)
    box('Lane light • small cap',(x,y,z+1.85),(.29,.29,.07),'Teal dark',.025)
def steps():
    for i in range(8):
        zz=(i+1)*1.65/8
        box('Terrace stair • stone tread',(-2.55,4.32+i*.29,zz/2),(1.39,.34,zz),'Stone',.025)
    # The path at each end widens into a shared landing, not a straight parade axis.
    polygon('Terrace stair • lower landing',[(-3.55,3.7),(-1.84,3.88),(-1.81,4.4),(-3.35,4.5)],.055,'Path')
    polygon('Terrace stair • upper landing',[(-3.45,6.35),(-1.55,6.22),(-1.13,7.02),(-3.31,7.26)],1.70,'Path')
    # A small open stone arch marks the change of level, using one broad band.
    x,y,z=-2.55,6.18,1.58
    for dx in (-.78,.78):box('Terrace stair • arch pier',(x+dx,y,z+.53),(.28,.36,1.06),'Wall stone',.035)
    n=10;outer=.92;inner=.64;center=z+1.03;vs=[]
    for yy in (y-.18,y+.18):
        for radius in (outer,inner):
            vs.extend((x+radius*math.cos(i*math.pi/n),yy,center+radius*math.sin(i*math.pi/n)) for i in range(n+1))
    k=n+1;faces=[]
    for i in range(n):
        faces.extend([(i,i+1,k+i+1,k+i),(2*k+i,3*k+i,3*k+i+1,2*k+i+1),(i,2*k+i,2*k+i+1,i+1),(k+i,k+i+1,3*k+i+1,3*k+i)])
    faces.extend([(0,k,3*k,2*k),(n,2*k+n,3*k+n,k+n)])
    mesh('Terrace stair • broad open arch',vs,faces,'Wall stone')
def creek_bridge():
    a=Vector((-1.48,.48,0));b=Vector((1.43,-2.43,0));d=b-a;side=Vector((-d.y,d.x,0)).normalized();yaw=math.atan2(d.y,d.x)
    for i in range(17):
        t=i/16;p=a+d*t;z=.13+.20*math.sin(t*math.pi)
        box('Bridge • timber deck',(p.x,p.y,z),(.27,1.43,.11),'Wood light',.025,rot=(0,0,yaw))
    for sign in (-1,1):
        pp=[]
        for t in (0,.25,.5,.75,1):
            p=a+d*t+side*(sign*.70);z=.13+.20*math.sin(t*math.pi)
            rod('Bridge • railing post',(p.x,p.y,z),(p.x,p.y,z+.62),.042,'Wood')
            pp.append((p.x,p.y,z+.64))
        for p,q in zip(pp,pp[1:]):rod('Bridge • handrail',p,q,.043,'Wood light')

VARIANTS={}
def composition_asset(kind,level):
    source=load(kind,level)
    if kind not in ('bookshop','bakery'):return source
    key=f'{kind}_level_{level}'
    if key in VARIANTS:return VARIANTS[key]
    coll=bpy.data.collections.new('CONCEPT COPY • '+key);library.collection.children.link(coll)
    copies={}
    for old in source.objects:
        obj=old.copy()
        if old.type=='MESH':obj.data=old.data.copy()
        coll.objects.link(obj);copies[old]=obj
    for old,obj in copies.items():obj.parent=copies.get(old.parent)
    def matches(rgba,name):return max(abs(a-b) for a,b in zip(rgba,G.linear(palette[name])))<.006
    for obj in copies.values():
        if obj.type!='MESH':continue
        me=obj.data;attr=me.color_attributes[0]
        for i,c in enumerate(attr.data):
            vi=i if attr.domain=='POINT' else me.loops[i].vertex_index;z=me.vertices[vi].co.z
            if kind=='bookshop':
                if matches(c.color,'Sage'):c.color=G.linear(palette['Warm plaster'])
                elif z>3.0 and any(matches(c.color,n) for n in ('Teal dark','Teal','Teal light')):c.color=G.linear(palette['Deep teal roof'])
            elif z>1.75:
                if matches(c.color,'Clay'):c.color=G.linear(palette['Olive roof'])
                elif matches(c.color,'Clay light'):c.color=G.linear(palette['Olive roof light'])
        if kind=='bookshop':
            for vert in me.vertices:
                if vert.co.z>2.5:vert.co.z=2.5+(vert.co.z-2.5)*1.30
            me.update()
    if kind=='bookshop':
        previous=G.COL;G.COL=coll
        x,y=.74,.20
        box('Concept bookshop • slender upper lookout',(x,y,5.43),(.75,.77,2.22),'Warm plaster',.04)
        box('Concept bookshop • tower ivory belt',(x,y,6.49),(.87,.89,.13),'Cream',.025)
        box('Concept bookshop • tower glass',(x,y-.395,5.92),(.30,.035,.48),'Glass',.01)
        for dx in (-.19,.19):box('Concept bookshop • ivory window jamb',(x+dx,y-.425,5.92),(.065,.065,.57),'Cream',.014)
        for dz in (-.265,.265):box('Concept bookshop • ivory window head',(x,y-.435,5.92+dz),(.44,.07,.065),'Cream',.014)
        box('Concept bookshop • side tower glass',(x+.39,y,5.92),(.035,.30,.48),'Glass',.01)
        for dy in (-.19,.19):box('Concept bookshop • side ivory jamb',(x+.425,y+dy,5.92),(.065,.065,.57),'Cream',.014)
        for dz in (-.265,.265):box('Concept bookshop • side ivory head',(x+.435,y,5.92+dz),(.07,.44,.065),'Cream',.014)
        r=.51;zz=6.57
        vs=[(x-r,y-r,zz),(x+r,y-r,zz),(x+r,y+r,zz),(x-r,y+r,zz),(x,y,7.49)]
        mesh('Concept bookshop • pointed teal roof',vs,[(3,2,1,0),(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'Deep teal roof',.018)
        box('Concept bookshop • thick tower eave',(x,y,6.56),(1.07,1.07,.12),'Deep teal roof',.035)
        G.COL=previous
        source_hull=hull([(v.x,v.y) for v in VERTS[key]])
        assert all(inside(p,source_hull) for p in [(x-.535,y-.535),(x+.535,y-.535),(x+.535,y+.535),(x-.535,y+.535)])
    VARIANTS[key]=coll;return coll

def scene_start(label):
    global CURRENT_LABEL,RIBBON_ORDINAL
    CURRENT_LABEL=label;RIBBON_ORDINAL=0
    s=bpy.data.scenes.new(label+' • composition concept');bpy.context.window.scene=s
    G.scene=s;G.COL=bpy.data.collections.new(label+' • editable landscape');s.collection.children.link(G.COL);G.PARENT=None
    terrain(label)
    for b in LAYOUTS[label]['buildings']:
        o=bpy.data.objects.new(label+' • '+b['id']+' • faces its lane',None);s.collection.objects.link(o)
        o.instance_type='COLLECTION';o.instance_collection=composition_asset(b['kind'],b['level'])
        # Hide individual sample forecourt edges inside the continuous communal surface.
        o.location=(*b['xy'],b['ground']-.065*b['scale']);o.rotation_euler[2]=angle(b);o.scale=(b['scale'],)*3
        o['kind']=b['kind'];o['display_level']=b['level'];o['entrance_toward_xy']=b['toward'];o['maximum_stage_hull_checked']=True
        bpy.context.window.scene=s
    return s

def paving_marks(poly,z):
    # Sparse broad colour stones; no dense cobblestone geometry or tiny bevels.
    for iy in range(9):
        for ix in range(11):
            x=-4.0+ix*.63+(iy%2)*.28;y=-2.0+iy*.51
            if not inside((x,y),poly) or boundary_distance((x,y),poly)<.20:continue
            if (ix*3+iy)%5==0:continue
            dx=.26;dy=.19;j=.04*math.sin(ix*7+iy*11)
            points=[(x-dx,y-dy+j,z),(x+dx,y-dy,z),(x+dx-.03,y+dy,z),(x-dx-.02,y+dy+j,z)]
            o=mesh('Court • broad paving colour',points,[(0,1,2,3)],'Stone' if (ix+iy)%3 else 'Path edge');o.visible_shadow=False

def hillside():
    s=scene_start('A')
    plaza=[(-4.1,.2),(-3.30,-1.25),(-1.35,-2.30),(1.24,-1.64),(2.60,.45),(1.83,2.54),(-.52,3.15),(-2.56,2.35),(-3.89,1.47)]
    polygon('A • one irregular common shop court',plaza,.072,'Path',.10)
    paving_marks(plaza,.080)
    ribbon('A • downhill entry alley',[(-1.4,-14,.03,1.28),(-1,-8,.03,1.45),(-2.1,-5.8,.03,1.42),(-2.9,-3.6,.04,1.24),(-2.0,-1.55,.074,1.55)],'Path')
    ribbon('A • workshop lane',[(-2.0,-4.7,-.05,1.20),(-3.9,-5.0,-.27,1.15),(-5.2,-4.96,-.40,1.00)],'Path')
    ribbon('A • cafe threshold',[(-3.96,1.37,.074,1.16),(-2.9,.96,.074,1.45),(-1.50,.62,.074,1.60)],'Path')
    ribbon('A • florist threshold',[(2.88,1.56,.074,1.05),(1.9,1.05,.074,1.12),(.80,.55,.074,1.45)],'Path')
    ribbon('A • plaza to stair bend',[(-.65,1.85,.074,1.34),(-1.53,2.82,.06,1.25),(-2.54,3.92,.055,1.39)],'Path')
    wall('A • old retaining wall west',[(-8.1,5.05),(-5.4,4.85),(-3.4,5.4)],.15,1.58)
    wall('A • old retaining wall east',[(-1.69,6.25),(.2,6.58),(3.40,7.15)],.38,1.58)
    steps()
    ribbon('A • upper winding residential lane',[(-5.38,5.85,1.705,1.04),(-4.0,6.32,1.705,1.23),(-2.3,7.04,1.705,1.27),(-.26,7.43,1.705,1.12),(.65,8.15,1.705,1.12)],'Path')
    ribbon('A • tucked upper cottage lane',[(-6.9,8.3,1.70,.86),(-6.2,7.4,1.70,.91),(-5.8,6.5,1.70,.94),(-5.38,5.85,1.70,1.04)],'Path')
    ribbon('A • lower cottage approach',[(-3.26,-2.07,-.1,.85),(-2.82,-1.97,.02,.93),(-2,-1.55,.07,1.10)],'Path')
    # Shared focal tree and a small low well leave the middle of the court open.
    ring('A • tree stone edging',(-1.75,-1.05,.14),.48,.08,'Wall stone')
    tree(-1.75,-1.05,2.95,'A',hero=True)
    cyl('A • low well stone body',(.34,.24,.33),.44,.52,'Wall stone')
    cyl('A • well water',(.34,.24,.602),.32,.018,'Water deep',thin=True)
    ring('A • well coping',(.34,.24,.61),.38,.085,'Stone')
    bench(-.96,-1.40,.075,-.16);lantern(-3.51,3.35,.08);lantern(.85,7.11,1.67)
    for args in [(-9.6,6.9,4.9,0),(-10.3,9.4,5.5,1),(-8.1,10.9,5.0,0),(-6.7,12.3,4.7,1),
                 (5.8,10.5,4.8,1),(6.9,12.1,5.2,0),(8.2,10.8,4.2,0),(8.4,8.6,4.5,1),
                 (8.8,3.3,4.1,0),(9.4,1.6,3.4,1),(7.5,2.0,3.1,0),
                 (-10.1,-5.7,5.0,1),(-11.0,-3.4,4.1,0),(5.8,-4.7,3.5,1)]:tree(args[0],args[1],args[2],'A',args[3])
    for x,y,ss in [(-7.8,4.2,.85),(3.8,6.8,.8),(5.5,4.6,.9),(5.7,-.9,.65),(-5.3,-6.8,.7),(-7.8,9.9,1.0)]:shrub(x,y,'A',ss)
    for x,y,ss in [(-7.4,4.4,1.1),(-8.1,4.15,.7),(4.3,6.8,1.3),(6.3,5.6,.8),(-7.7,-6.2,.8)]:rock(x,y,'A',ss)
    return s

def creekside():
    s=scene_start('B')
    ribbon('B • shallow continuous creek',[(p.x,p.y,p.z,p.w+1.05) for p in STREAM],'Water',False)
    # The shop court is on one bank. The bridge is a destination, not part of a loop road.
    market=[(-4.17,2.35),(-2.24,3.2),(-1.03,1.70),(-1.36,.85),(-2.30,.02),(-3.5,-.65),(-4.32,-.50)]
    polygon('B • bridgehead market court',market,.066,'Path');paving_marks(market,.075)
    ribbon('B • market approach alley',[(-14,-2.5,.025,1.2),(-10.5,-2.5,.025,1.23),(-8.4,-1.9,.04,1.24),(-6.7,-1.55,.04,1.18),(-4.9,-.65,.06,1.20),(-3.1,-.1,.07,1.30),(-1.45,.48,.07,1.32)],'Path')
    ribbon('B • grocer uphill threshold',[(-5.16,-2.6,.04,.93),(-5.0,-1.9,.04,.98),(-4.8,-1.0,.04,1.04),(-4.9,-.65,.06,1.12)],'Path')
    wall('B • bridgehead stone embankment',[(-3.5,-.65),(-2.30,.02),(-1.36,.85)],-.38,.04)
    ribbon('B • market north bend',[(-2.7,.9,.07,1.4),(-2.15,2.65,.07,1.24),(-2.05,4.05,.07,1.14)],'Path')
    ribbon('B • workshop back lane',[(-2.55,3.13,.065,1.12),(-4.10,3.84,.15,1.0),(-5.80,5.67,.31,.92)],'Path')
    ribbon('B • western cottage alley',[(-7.52,3.03,.16,.84),(-7.2,3.6,.16,.90),(-6.5,4.0,.16,.91),(-5.7,4.1,.16,.97),(-4.10,3.84,.16,1.00)],'Path')
    creek_bridge()
    ribbon('B • residential winding lane',[(1.43,-2.43,.07,1.43),(2.78,-3.35,.17,1.30),(4.31,-3.05,.33,1.21),(5.27,-1.51,.45,1.35),(5.77,.58,.53,1.15),(5.62,2.71,.53,1.08)],'Path')
    ribbon('B • cottage doorstep',[(4.5,-4.15,.34,.92),(3.63,-3.54,.24,1.03),(2.78,-3.35,.17,1.18)],'Path')
    ribbon('B • bookshop turn',[(6.93,-.04,.49,1.02),(6.12,-.22,.49,1.08),(5.48,-.54,.49,1.12)],'Path')
    ribbon('B • upper cottage turn',[(7.31,2.16,.52,.85),(6.7,2.1,.52,.90),(5.7,2.2,.52,1.00)],'Path')
    ribbon('B • home garden approach',[(6.85,4.0,.52,.91),(6.2,3.75,.52,1.0),(5.7,3.2,.52,1.04),(5.62,2.71,.52,1.08)],'Path')
    bench(-2.85,1.76,.07,.2);lantern(-1.50,.92,.05);lantern(4.10,-2.80,.32)
    tree(-3.8,-.36,2.85,'B',hero=True)
    # Interrupted low garden walls turn the residential lane into an inhabited place.
    wall('B • cottage garden wall',[(4.41,-5.20),(3.28,-4.71),(2.88,-4.24)],.25,.70)
    wall('B • home garden wall',[(4.88,4.30),(4.59,3.25)],.44,.88)
    for args in [(-9.7,7.2,4.8,0),(-8.9,9.7,5.3,1),(-6.6,10.9,4.8,0),(-4.9,10.6,3.8,1),
                 (11.9,8.9,5.2,1),(13.7,9.7,4.1,0),(14.8,7.3,4.8,1),(12.8,6.1,5.0,0),
                 (13.8,-1.8,3.7,1),(15.0,-.3,4.6,0),(12.5,-2.9,3.2,0),
                 (10.2,-7.4,3.8,0),(8.6,-8.2,3.4,1),(-10.7,-3.3,4.3,1),(-11.6,-5.0,5.4,0)]:tree(args[0],args[1],args[2],'B',args[3])
    for x,y,ss in [(-4.5,-4.5,.7),(-4.4,-3.8,.65),(2.4,4.6,.72),(3.5,6.6,.8),(1.6,2.3,.7),(-5.4,7.8,.85),(5.0,-5.6,.6)]:shrub(x,y,'B',ss)
    for x,y,ss in [(-4.55,-3.8,.75),(-5.8,-5.7,.6),(1.5,3.5,.7),(2.9,5.9,.85),(3.7,7.5,.7),(5.8,8.3,.8)]:rock(x,y,'B',ss)
    return s

world=bpy.data.worlds.new('Soft daylight • same comparison light');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.69,.77,.84,1);bg.inputs['Strength'].default_value=.35
def configure(s):
    s.world=world;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1;s.render.engine='CYCLES'
    s.cycles.samples=24 if PREVIEW else 64;s.cycles.use_denoising=True
    s.render.resolution_x=1440 if PREVIEW else 1920;s.render.resolution_y=810 if PREVIEW else 1080;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.view_settings.view_transform='AgX';s.view_settings.exposure=.15
    sun=bpy.data.lights.new(s.name+' sun','SUN');sun.energy=1.0;sun.angle=.10;sun.color=(1,.91,.78)
    so=bpy.data.objects.new(sun.name,sun);s.collection.objects.link(so);so.rotation_euler=(.45,-.32,-.48)
    for name,loc,power,size,color in [('Key',(-12,-18,26),4500,12,(1,.88,.73)),('Fill',(16,4,20),2300,18,(.78,.87,1)),('Rim',(-8,22,24),3500,15,(1,.94,.82))]:
        d=bpy.data.lights.new(s.name+' '+name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
        o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,1,0))-o.location).to_track_quat('-Z','Y').to_euler()
    d=bpy.data.cameras.new(s.name+' camera');o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);s.camera=o;d.type='ORTHO'
def camera(s,top=False):
    is_b=s.name.startswith('B')
    target=Vector((0,1.5 if is_b else 3.3,1.5 if is_b else 2.0)) if not top else Vector((0,2,0))
    if top:
        s.camera.location=(0,3,45);s.camera.rotation_euler=(0,0,0);s.camera.data.ortho_scale=35.0
    else:
        s.camera.location=target+Vector((18,-27,24));s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=28.0
SCENES=[hillside(),creekside()]
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    device='GPU' if any(d.type!='CPU' for d in prefs.devices) else 'CPU'
except Exception:device='CPU'
for s in SCENES:configure(s);camera(s);s.cycles.device=device
bpy.context.window.scene=SCENES[0];bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/chagok_layout_v002_concepts.blend'))
# Reopen the actual editable layout before rendering. No whole-town GLB is exported.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/chagok_layout_v002_concepts.blend'))
for label in ('A','B'):
    s=bpy.data.scenes[label+' • composition concept'];bpy.context.window.scene=s
    for top in (False,True):
        camera(s,top);name=label+('_top' if top else '_oblique')+'.png'
        s.render.filepath=str(ROOT/'renders'/(('preview_' if PREVIEW else '')+name))
        bpy.ops.render.render(write_still=True);print('RENDERED',name,flush=True)
assert all(hashlib.sha256((ART/p).read_bytes()).hexdigest()==h for p,h in hashes.items()),'Read-only source asset changed externally'
REPORT['editable_blend_reopened']=True;REPORT['input_files_unchanged']=len(hashes);REPORT['render_device']=device
REPORT['oblique_scale_m']=28.0;REPORT['top_scale_m']=35.0;REPORT['image_aspect']='16:9';REPORT['preview']=PREVIEW
REPORT['composition_variants']=['bookshop: warm plaster, taller upper silhouette and pointed lookout; XY inside original max-stage hull',
                                'bakery: olive/brown roof colour fields on separate in-scene copy']
REPORT['depth_of_field']=False;REPORT['full_game_or_runtime_certified']=False
(ROOT/'reports/palette.json').write_text(json.dumps(palette,indent=2),encoding='utf-8')
(ROOT/'reports/composition_checks.json').write_text(json.dumps(REPORT,indent=2),encoding='utf-8')
print('CONCEPTS_COMPLETE',flush=True)
