"""ChagokTown café upgrade models v003. No lettering, all solid geometry.

Builds editable high/low detail versions of the same three designs, then exports
the low-detail models as one opaque vertex-colour mesh/material per level.
The v001 directory is read-only input for baseline hashes and measurements.
"""
import bpy, math, json, hashlib, struct
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
V1=ROOT.parent/'town_miniature_v001'
for folder in ('blend','exports','renders','reports/reference'):
    (ROOT/folder).mkdir(parents=True,exist_ok=True)
manifest={str(p.relative_to(V1)):hashlib.sha256(p.read_bytes()).hexdigest() for p in V1.rglob('*') if p.is_file()}
manifest_path=ROOT/'reports/v001_preservation.json'
if manifest_path.exists():
    assert json.loads(manifest_path.read_text())==manifest,'v001 changed since the first v003 build'
else:manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
V2=ROOT.parent/'town_cafe_v002'
v2_manifest={str(p.relative_to(V2)):hashlib.sha256(p.read_bytes()).hexdigest() for p in V2.rglob('*') if p.is_file()}
v2_manifest_path=ROOT/'reports/v002_preservation.json'
if v2_manifest_path.exists():assert json.loads(v2_manifest_path.read_text())==v2_manifest
else:v2_manifest_path.write_text(json.dumps(v2_manifest,indent=2),encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene; scene.name='01 • Cafe upgrades'
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
M={}; COL=None; PARENT=None; LOW=False
PALETTE={
 'Cream':'F5E6C8','Butter':'E9CB89','Teal':'427B78','Teal light':'59908A',
 'Teal dark':'315D5B','Wood':'966C4E','Wood light':'BB9065','Dark wood':'624B3C',
 'Ink':'354C4B','Glass':'507D87','Glint':'BFD5CF','Leaf':'78946A',
 'Leaf light':'94AC77','Leaf dark':'58785C','Pink':'DF9BA6','Flower':'F5DEA6',
 'Earth':'675644','Clay':'BA6555','Clay light':'D18468','Stone':'D4C7AD',
 'Brass':'BC945A','Backdrop':'E5DDD0'
}
def linear(h):
    c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)+(1,)
for name,h in PALETTE.items():
    m=bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=linear(h)
    b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value=linear(h); b.inputs['Roughness'].default_value=.68
    M[name]=m
runtime_mat=bpy.data.materials.new('Town • vertex palette • opaque'); runtime_mat.use_nodes=True
runtime_mat.use_backface_culling=True
b=next(n for n in runtime_mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
b.inputs['Roughness'].default_value=.68
v=runtime_mat.node_tree.nodes.new('ShaderNodeVertexColor'); v.layer_name='Palette'
runtime_mat.node_tree.links.new(v.outputs['Color'],b.inputs['Base Color'])

def collection(name):
    c=bpy.data.collections.new(name); scene.collection.children.link(c); return c
def attach(o,name,mat,smooth=False):
    o.name=name
    for c in list(o.users_collection): c.objects.unlink(o)
    COL.objects.link(o)
    if PARENT: o.parent=PARENT
    if mat: o.data.materials.append(M[mat])
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    return o
def bevel(o,w,large=False):
    if not w:return o
    m=o.modifiers.new('Rounded miniature edge','BEVEL'); m.width=w
    m.segments=(2 if large else 1) if LOW else 3
    # Keep smooth custom normals when baking and merging the runtime mesh.
    for p in o.data.polygons:p.use_smooth=True
    m.harden_normals=True
    n=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL'); n.keep_sharp=True
    return o
def box(name,loc,size,mat,edge=.035,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=attach(bpy.context.object,name,mat); o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel(o,min(edge,min(size)*.43),large=min(size)>.17)
    if rot:o.rotation_euler=rot
    return o
def mesh(name,vs,fs,mat,edge=0):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
    o=bpy.data.objects.new(name,me);COL.objects.link(o);o.data.materials.append(M[mat])
    if PARENT:o.parent=PARENT
    return bevel(o,edge)
def cyl(name,loc,r,h,mat,top=None,rot=None,thin=False):
    n=(8 if thin else 12) if LOW else 24
    bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r,radius2=r if top is None else top,depth=h,location=loc)
    o=attach(bpy.context.object,name,mat)
    if LOW and thin:
        # Sub-pixel end bevels on rods cost more than their visible contribution.
        for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    else:bevel(o,min(.02,h*.18,r*.15))
    if rot:o.rotation_euler=rot
    return o
def rod(name,a,b,r,mat):
    d=Vector(b)-Vector(a);o=cyl(name,(Vector(a)+Vector(b))/2,r,d.length,mat,thin=True)
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o
def ellipsoid(name,loc,scale,mat):
    if LOW and ('petal' in name or 'foliage' in name):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=loc)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8 if LOW else 16,ring_count=6 if LOW else 10,radius=1,location=loc)
    o=attach(bpy.context.object,name,mat,True);o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return o
def ring(name,loc,r,tube,mat,rot=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=12 if LOW else 24,minor_segments=4 if LOW else 8,major_radius=r,minor_radius=tube,location=loc)
    o=attach(bpy.context.object,name,mat,True)
    if rot:o.rotation_euler=rot
    return o
def arch(name,x,y,z,w,h,depth,mat):
    n=8 if LOW else 16;r=w/2
    points=[(x-r,z),(x+r,z)]+[(x+r*math.cos(i*math.pi/n),z+h-r+r*math.sin(i*math.pi/n)) for i in range(n+1)]
    k=len(points);vs=[(xx,yy,zz) for yy in (y-depth/2,y+depth/2) for xx,zz in points]
    # X/Z counter-clockwise has normal -Y: the front face must keep that winding.
    fs=[tuple(range(k)),tuple(range(k*2-1,k-1,-1))]+[(i,i+k,(i+1)%k+k,(i+1)%k) for i in range(k)]
    return mesh(name,vs,fs,mat,.02)

def window(x,y,z,w,h,trim='Cream',cross=True):
    # v003: omit the brown backing; retain glazing, ivory/teal frame and sill.
    box('Window • blue glazing',(x,y-.06,z),(w,.06,h),'Glass',.015)
    for dx in (-w/2,w/2):box('Window • jamb',(x+dx,y-.11,z),(.09,.13,h+.12),trim,.022)
    for dz in (-h/2,h/2):box('Window • lintel',(x,y-.11,z+dz),(w+.10,.13,.09),trim,.022)
    box('Window • centre mullion',(x,y-.13,z),(.055,.10,h),trim,.012)
    if cross:box('Window • crossbar',(x,y-.13,z+.07),(w,.10,.055),trim,.012)
    box('Window • painted reflection',(x-w*.24,y-.099,z+.08),(.034,.012,h*.48),'Glint',0,rot=(0,-.28,0))
    box('Window • deep sill',(x,y-.18,z-h/2-.07),(w+.24,.30,.13),'Cream',.035)
def side_window(x,z,w,h):
    before=set(COL.objects);window(0,-x,z,w,h)
    for o in set(COL.objects)-before:
        o.location=Vector((-o.location.y,o.location.x,o.location.z));o.rotation_euler[2]+=math.pi/2
def door(x,y):
    arch('Door • cream arch',x,y,.16,.91,1.70,.18,'Cream')
    arch('Door • teal panel',x,y-.105,.17,.72,1.54,.10,'Teal')
    arch('Door • inset glass',x,y-.17,.91,.51,.64,.035,'Glass')
    box('Door • lower panel',(x,y-.18,.51),(.48,.025,.36),'Teal light',.035)
    box('Door • divider',(x,y-.195,1.07),(.53,.03,.045),'Cream',.008)
    ellipsoid('Door • knob',(x+.235,y-.22,.84),(.047,)*3,'Brass')
    box('Door • step',(x,y-.27,.095),(1.08,.58,.19),'Stone',.055)
def succulent(x,y,z,r=.17,h=.24):
    cyl('Planter • pot',(x,y,z+h/2),r*.76,h,'Clay',top=r)
    ring('Planter • rolled rim',(x,y,z+h-.025),r*.94,.028,'Clay light')
    cyl('Planter • earth',(x,y,z+h-.035),r*.80,.015,'Earth',thin=True)
    for i in range(3):
        a=i*math.tau/3
        o=ellipsoid('Planter • fleshy leaf',(x+math.cos(a)*r*.31,y+math.sin(a)*r*.31,z+h+.12),(r*.40,r*.37,.20),'Leaf light')
        o.rotation_euler=(math.sin(a)*.35,math.cos(a)*.35,0)
def cup_icon(x,y,z,s=1,disc=True):
    if disc:cyl('Sign • plain medallion',(x,y,z),.28*s,.10*s,'Cream',rot=(math.pi/2,0,0))
    yy=y-.065*s
    box('Sign • cup silhouette',(x-.025*s,yy,z),(.25*s,.045*s,.21*s),'Teal',.043*s)
    ring('Sign • cup handle',(x+.13*s,yy-.006*s,z+.015*s),.065*s,.022*s,'Teal',rot=(math.pi/2,0,0))
    box('Sign • saucer',(x-.018*s,yy,z-.14*s),(.35*s,.045*s,.036*s),'Teal',.012*s)
def awning(center,y,z,width,stripes,depth=.65):
    for i in range(stripes):
        x=center-width/2+(i+.5)*width/stripes;dw=width/stripes
        seg=4 if LOW else 8
        points=[(y-depth*t/seg,z-.12*t/seg-.24*(t/seg)**2) for t in range(seg+1)]
        vs=[(xx,yy,zz) for xx in (x-dw/2,x+dw/2) for yy,zz in points]
        fs=[(j,j+1,seg+2+j,seg+1+j) for j in range(seg)]
        o=mesh('Awning • stripe %02d'%i,vs,fs,'Cream' if i%2==0 else 'Teal')
        m=o.modifiers.new('Fabric thickness','SOLIDIFY');m.thickness=.038
        bevel(o,.012)
        box('Awning • rounded valance',(x,y-depth-.01,z-.43),(dw+.004,.065,.21),'Cream' if i%2==0 else 'Teal',.055)
    for x in (center-width/2+.03,center+width/2-.03):rod('Awning • brace',(x,y,z-.40),(x,y-depth,z-.31),.023,'Wood')
def hip_roof(w,d,z):
    a=w/2+.16;b=d/2+.16;inset=.38
    vs=[(-a,-b,z),(a,-b,z),(a,b,z),(-a,b,z),(-a+inset,-b+inset,z+.46),(a-inset,-b+inset,z+.46),(a-inset,b-inset,z+.46),(-a+inset,b-inset,z+.46)]
    mesh('Roof • soft hipped shell',vs,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'Teal',.055)
    box('Roof • rounded crown',(0,0,z+.46),(w-.40,d-.40,.13),'Teal light',.055)
    for i in range(5):
        x=(i-2)*w*.20
        rod('Roof • front seam',(x,-b+.04,z+.04),(x*.78,-b+inset-.01,z+.50),.018,'Teal light')
def table(x,y,z=0):
    cyl('Terrace • round tabletop',(x,y,z+.63),.32,.085,'Wood light')
    rod('Terrace • pedestal',(x,y,z+.06),(x,y,z+.60),.045,'Teal dark')
    cyl('Terrace • table foot',(x,y,z+.04),.21,.08,'Teal dark')
    for dx in (-.48,.48):
        cyl('Terrace • stool seat',(x+dx,y+.03,z+.35),.16,.08,'Wood light')
        for a in (0,math.tau/3,2*math.tau/3):
            ox=.105*math.cos(a);oy=.105*math.sin(a)
            rod('Terrace • stool leg',(x+dx+ox,y+.03+oy,z+.02),(x+dx+ox*.7,y+.03+oy*.7,z+.32),.023,'Teal dark')
    cyl('Terrace • cup',(x-.05,y,z+.725),.06,.11,'Cream',top=.073)
    cyl('Terrace • coffee',(x-.05,y,z+.783),.058,.005,'Dark wood',thin=True)
def flowerbox(x,y,z,w=.78):
    box('Upper • flowerbox',(x,y,z),(w,.26,.19),'Wood light',.035)
    for i in range(3):
        xx=x+(i-1)*w*.25
        ellipsoid('Upper • foliage',(xx,y,z+.15),(.15,.11,.11),'Leaf')
        for k in range(4):
            a=k*math.tau/4
            ellipsoid('Upper • flower petal',(xx+.055*math.cos(a),y+.055*math.sin(a),z+.25),(.058,.058,.035),'Pink' if i%2 else 'Flower')
def umbrella(x,y,z):
    rod('Terrace • umbrella pole',(x,y,.12),(x,y,z+.23),.028,'Wood')
    n=8;vs=[(x,y,z+.25)]+[(x+.77*math.cos(i*math.tau/n),y+.77*math.sin(i*math.tau/n),z-.05) for i in range(n)]
    o=mesh('Terrace • scalloped umbrella',vs,[(0,i+1,(i+1)%n+1) for i in range(n)],'Cream')
    o.data.materials.append(M['Teal light'])
    for p in o.data.polygons:p.material_index=p.index%2;p.use_smooth=True
    m=o.modifiers.new('Canopy thickness','SOLIDIFY');m.thickness=.025
    ellipsoid('Terrace • umbrella finial',(x,y,z+.27),(.05,.05,.06),'Wood')

def build(level,low):
    global COL,PARENT,LOW
    LOW=low;tag='LOW' if low else 'EDIT'
    COL=collection('%s • cafe level %d'%(tag,level))
    PARENT=bpy.data.objects.new('cafe_level_%d_%s'%(level,tag.lower()),None);COL.objects.link(PARENT)
    PARENT['level']=level;PARENT['pivot']='ground centre';PARENT['front']='-Y'
    w,d,h=[(2.50,2.10,2.38),(3.0,2.40,2.63),(3.20,2.50,3.77)][level-1]
    y=-d/2-.04
    box('Foundation • stone plinth',(0,0,.095),(w+.22,d+.20,.19),'Stone',.07)
    box('Wall • butter plaster',(0,0,(h+.13)/2),(w,d,h-.13),'Butter',.085)
    box('Wall • cream skirting',(0,0,.28),(w+.05,d+.05,.20),'Cream',.035)
    box('Roof • cream cornice',(0,0,h),(w+.24,d+.24,.20),'Cream',.06)
    hip_roof(w,d,h+.11)
    dx=.72 if level==1 else 1.0
    door(dx,y-.02)
    window(-.51,y-.01,1.17,1.00 if level==1 else 1.34,1.16 if level==1 else 1.37,trim='Teal dark',cross=False)
    side_window(w/2+.025,1.38,1.00 if level==1 else 1.18,1.06)
    # A pictogram takes the place of all lettering; no FONT objects or text textures.
    if level==1:
        cup_icon(-.48,y-.06,2.10,.70)
        awning(-.51,y-.02,1.94,1.35,5,.49)
        succulent(1.46,y-.29,0,.14,.21)
    else:
        box('Fascia • plain cream band',(0,y-.04,2.32),(2.55,.14,.40),'Cream',.065)
        cup_icon(0,y-.155,2.33,.69,False)
        # Small bean silhouettes, never text, on the central pictogram band.
        for x in (-.36,.36):
            bean=ellipsoid('Fascia • coffee bean',(x,y-.167,2.33),(.07,.025,.105),'Wood')
            bean.rotation_euler[1]=.45 if x>0 else -.45
        awning(0,y-.04,2.08,w-.04,10)
        rod('Sign • hanging arm',(w/2-.06,y,2.49),(w/2+.37,y-.40,2.49),.032,'Dark wood')
        cup_icon(w/2+.30,y-.44,2.19,.95)
        if level==2:
            table(-.85,y-.97)
            succulent(.26,y-.43,0,.16,.25)
        else:
            # A real second floor changes silhouette and scale, not just decoration.
            box('Upper • belt cornice',(0,0,2.64),(w+.18,d+.18,.17),'Cream',.04)
            for x in (-.79,.79):
                arch('Upper • arched surround',x,y-.01,2.83,.83,.78,.16,'Cream')
                arch('Upper • arched glazing',x,y-.105,2.91,.65,.61,.04,'Glass')
                box('Upper • central mullion',(x,y-.14,3.19),(.045,.055,.54),'Cream',.01)
                flowerbox(x,y-.23,2.80)
            side_window(w/2+.035,3.22,.92,.58)
            # Paved terrace remains inside the common 4.8 x 4.8 m placement envelope.
            box('Terrace • patio base',(0,y-.72,.055),(3.52,1.46,.11),'Stone',.06)
            table(-.88,y-.91,.11)
            umbrella(-.88,y-1.04,2.40)
            succulent(1.49,y-.64,.11,.22,.32)
            box('Terrace • seat',(1.03,y-1.19,.49),(.80,.30,.09),'Wood light',.035)
            for x in (.73,1.32):rod('Terrace • seat leg',(x,y-1.19,.11),(x,y-1.19,.46),.04,'Teal dark')
            # One small roof vent adds the final silhouette accent.
            cyl('Roof • vent',(1.02,.63,h+.68),.11,.36,'Teal dark')
            cyl('Roof • vent cap',(1.02,.63,h+.88),.18,.075,'Cream')
    bpy.context.view_layer.update()
    return COL,PARENT

def stats(coll):
    dg=bpy.context.evaluated_depsgraph_get();points=[];tri=0;verts=0;mats=set();count=0
    for o in coll.objects:
        if o.type!='MESH':continue
        e=o.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles()
        tri+=len(me.loop_triangles);verts+=len(me.vertices);count+=1
        mats.update(m.name for m in me.materials if m)
        points.extend(e.matrix_world@v.co for v in me.vertices);e.to_mesh_clear()
    lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
    return dict(mesh_objects=count,triangles=tri,vertices=verts,materials=len(mats),bounds_min=lo,bounds_max=hi,dimensions=[hi[i]-lo[i] for i in range(3)])

def export(coll,path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in coll.objects:o.select_set(True)
    bpy.context.view_layer.objects.active=next(o for o in coll.objects if o.type=='MESH')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_extras=True,export_cameras=False,export_lights=False)
def glb_stats(path):
    data=path.read_bytes();ln=struct.unpack_from('<I',data,12)[0];j=json.loads(data[20:20+ln])
    ps=[p for m in j.get('meshes',[]) for p in m['primitives']]
    return dict(bytes=len(data),mesh_objects=len(j.get('meshes',[])),primitives=len(ps),
                materials=len(j.get('materials',[])),triangles=sum(j['accessors'][p['indices']]['count']//3 for p in ps),
                vertices=sum(j['accessors'][p['attributes']['POSITION']]['count'] for p in ps),
                textures=len(j.get('textures',[])),all_primitives_have_vertex_color=all('COLOR_0' in p['attributes'] for p in ps))

def consolidate(coll,root,level):
    bpy.ops.object.select_all(action='DESELECT')
    objs=[o for o in coll.objects if o.type=='MESH']
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]
    bpy.ops.object.convert(target='MESH')
    for o in objs:
        attr=o.data.color_attributes.new(name='Palette',type='BYTE_COLOR',domain='CORNER')
        for p in o.data.polygons:
            rgba=o.data.materials[p.material_index].diffuse_color
            for li in p.loop_indices:attr.data[li].color=rgba
            p.material_index=0
        o.data.materials.clear();o.data.materials.append(runtime_mat)
    bpy.ops.object.join();o=bpy.context.object;o.name='cafe_level_%d_runtime'%level
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    tri=o.modifiers.new('Explicit runtime triangles','TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=tri.name)
    o['asset_id']='cafe_level_%d'%level;o['level']=level;o['text_free']=True
    o['placement_lot_m']=[4.8,4.8]
    o['placement_xy_min']=[-2.4,-3.2];o['placement_xy_max']=[2.4,1.6]
    o['units']='metres';o['front']='-Y'
    root['asset_id']='cafe_level_%d'%level
    return o

EDIT={};RUN={};REPORT={'v001_cafe':glb_stats(V1/'exports/cafe.glb'),'levels':{}}
for level in (1,2,3):
    hi,hr=build(level,False);EDIT[level]=hi
    before=stats(hi);ref=ROOT/'reports/reference'/f'cafe_level_{level}_before.glb';export(hi,ref)
    low,lr=build(level,True)
    # Normalize actual evaluated bottom to the shared placement plane.
    dz=stats(low)['bounds_min'][2]
    for o in low.objects:
        if o!=lr:o.location.z-=dz
    bpy.context.view_layer.update();consolidate(low,lr,level);RUN[level]=low
    path=ROOT/'exports'/f'cafe_level_{level}.glb';export(low,path)
    after=stats(low);g=glb_stats(path)
    REPORT['levels'][str(level)]={'before':before,'before_glb':glb_stats(ref),'after':after,'after_glb':g,
       'triangle_reduction_percent':round(100*(1-after['triangles']/before['triangles']),2),
       'bytes_reduction_percent':round(100*(1-g['bytes']/ref.stat().st_size),2)}
    assert g['mesh_objects']==g['materials']==g['primitives']==1
    assert g['all_primitives_have_vertex_color'] and g['textures']==0
    assert after['triangles']<10000,(level,after['triangles'])
    assert after['dimensions'][0]<=4.8 and after['dimensions'][1]<=4.8
    assert after['bounds_min'][0]>=-2.4 and after['bounds_min'][1]>=-3.2
    assert after['bounds_max'][0]<=2.4 and after['bounds_max'][1]<=1.6
    scene.collection.children.unlink(hi);scene.collection.children.unlink(low)
    print('LEVEL_COMPLETE',level,json.dumps(REPORT['levels'][str(level)]),flush=True)

# A clean presentation scene uses only the exact exported low-detail meshes.
PARENT=None;LOW=True;COL=collection('PRESENTATION • runtime comparison')
for level in (1,2,3):
    o=bpy.data.objects.new('Preview level %d'%level,None);COL.objects.link(o)
    o.instance_type='COLLECTION';o.instance_collection=RUN[level]
    # Offset along camera-right so all three ground pivots share one screen baseline.
    right=Vector((24.8,9,0)).normalized();o.location=right*((level-2)*5.1)

STUDIO=collection('STUDIO • lighting');COL=STUDIO
box('Studio floor',(0,0,-.065),(150,150,.10),'Backdrop',0)
def camera(s,name,loc,target,scale):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o)
    o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    d.type='ORTHO';d.ortho_scale=scale;s.camera=o;return o
camera(scene,'Comparison camera',(9,-25,17),(0,-.2,1.6),17.8)
for name,loc,power,size,color in [('Warm window',(-6,-8,13),1800,8,(1,.86,.72)),('Sky fill',(7,-1,10),1100,7,(.77,.87,1)),('Back rim',(0,7,10),1400,6,(1,.94,.80))]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);STUDIO.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Warm world');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.65,.72,.78,1);bg.inputs['Strength'].default_value=.35
def configure(s,w=2100,h=1050):
    s.world=world;s.unit_settings.system='METRIC'
    try:s.render.engine='CYCLES'
    except TypeError:s.render.engine='BLENDER_EEVEE'
    if s.render.engine=='CYCLES':s.cycles.samples=64;s.cycles.use_denoising=True
    s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
    options=[i.identifier for i in s.view_settings.bl_rna.properties['view_transform'].enum_items]
    if 'AgX' in options:s.view_settings.view_transform='AgX'
    s.view_settings.exposure=.35
configure(scene)
scene.render.filepath=str(ROOT/'renders/01_cafe_levels.png')
for level in (1,2,3):
    for prefix,coll in [('EDIT',EDIT[level]),('RUNTIME',RUN[level])]:
        s=bpy.data.scenes.new('%s • level %d'%(prefix,level));s.collection.children.link(coll);s.collection.children.link(STUDIO)
        configure(s,1100,1100);camera(s,prefix+' camera '+str(level),(7,-11,8),(0,-.25,1.90),6.75)
        s['notes']='No lettering. EDIT keeps semantic components. RUNTIME is one vertex-colour mesh and material.'
bpy.context.window.scene=scene
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
assert not any(o.type=='FONT' for o in bpy.data.objects)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/chagok_cafe_upgrades_v003.blend'))
(ROOT/'reports/optimization.json').write_text(json.dumps(REPORT,indent=2),encoding='utf-8')
(ROOT/'reports/palette.json').write_text(json.dumps(PALETTE,indent=2),encoding='utf-8')
assert manifest=={str(p.relative_to(V1)):hashlib.sha256(p.read_bytes()).hexdigest() for p in V1.rglob('*') if p.is_file()}
assert v2_manifest=={str(p.relative_to(V2)):hashlib.sha256(p.read_bytes()).hexdigest() for p in V2.rglob('*') if p.is_file()}
print('BUILD_COMPLETE',flush=True)

