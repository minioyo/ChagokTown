"""Geometry helpers derived from cafe v003; independent copy for this asset set."""
import bpy, math, struct, json
from mathutils import Vector
scene=bpy.context.scene
COL=None
PARENT=None
LOW=False
M={}
runtime_mat=None
def linear(h):
    c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)+(1,)

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
    # Keep front/back bevels apart on thin glazing; half-depth creates zero-area faces.
    return mesh(name,vs,fs,mat,min(.02,depth*.35))

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

def consolidate(coll,root,asset_id,level):
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
    bpy.ops.object.join();o=bpy.context.object;o.name=asset_id+'_runtime'
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    tri=o.modifiers.new('Explicit runtime triangles','TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=tri.name)
    o['asset_id']=asset_id;o['level']=level;o['text_free']=True
    o['placement_lot_m']=[4.8,4.8]
    o['placement_xy_min']=[-2.4,-3.2];o['placement_xy_max']=[2.4,1.6]
    o['units']='metres';o['front']='-Y'
    root['asset_id']=asset_id
    return o
