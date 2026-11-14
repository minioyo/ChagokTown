"""Original house/florist upgrades. Cafe-v003 palette and single-material GLBs."""
import bpy, bmesh, sys, json, hashlib, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
for d in ('blend','exports','renders','reports'):(ROOT/d).mkdir(parents=True,exist_ok=True)
PREVIOUS=['town_miniature_v001','town_cafe_v002','town_cafe_v003']
def hashes():
    return {str(p.relative_to(ROOT.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in PREVIOUS for p in (ROOT.parent/folder).rglob('*') if p.is_file()}
prior=hashes();mp=ROOT/'reports/previous_versions_sha256.json'
if mp.exists():assert json.loads(mp.read_text())==prior,'Previous assets changed since this set began'
else:mp.write_text(json.dumps(prior,indent=2),encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
import geometry as G
from geometry import box, mesh, cyl, rod, ellipsoid, ring, arch, window, side_window, door, succulent
scene=bpy.context.scene;scene.name='01 • House upgrades'
palette=json.loads((ROOT.parent/'town_cafe_v003/reports/palette.json').read_text())
palette.update({'Apricot':'EDB292','Sage':'A8BCA6','Rose':'CC817B','Glass light':'79A5AA','Plum':'AE7FAD'})
for name,h in palette.items():
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=G.linear(h)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=G.linear(h);p.inputs['Roughness'].default_value=.68
    G.M[name]=m
m=bpy.data.materials.new('Town • vertex palette • opaque');m.use_nodes=True;m.use_backface_culling=True
p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Roughness'].default_value=.68
color=m.node_tree.nodes.new('ShaderNodeVertexColor');color.layer_name='Palette'
m.node_tree.links.new(color.outputs['Color'],p.inputs['Base Color']);G.runtime_mat=m

def begin(key,level,low):
    G.LOW=low;G.COL=G.collection(('LOW' if low else 'EDIT')+' • '+key)
    root=bpy.data.objects.new(key+('_low' if low else '_edit'),None);G.COL.objects.link(root)
    root['level']=level;root['front']='-Y';root['pivot']='building ground centre';G.PARENT=root
    return G.COL,root
def foundation(w,d,h,color):
    box('Foundation • rounded plinth',(0,0,.085),(w+.20,d+.18,.17),'Stone',.065)
    box('Wall • plaster shell',(0,0,(h+.12)/2),(w,d,h-.12),color,.085)
    box('Wall • cream skirting',(0,0,.255),(w+.05,d+.05,.18),'Cream',.035)
def gable(w,d,z,rise,roof_color,tile_color,wall_color):
    half=w/2;depth=d/2
    vs=[(-half+.18,-depth+.18,z-.12),(half-.18,-depth+.18,z-.12),(0,-depth+.18,z+rise-.10),(-half+.18,depth-.18,z-.12),(half-.18,depth-.18,z-.12),(0,depth-.18,z+rise-.10)]
    mesh('Gable • solid plaster',vs,[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)],wall_color,.025)
    a=math.atan2(rise,half);length=math.hypot(half,rise)
    for side in (-1,1):
        box('Roof • thick slope',(side*half/2,0,z+rise/2),(length+.10,d,.14),roof_color,.04,rot=(0,side*a,0))
        for y in (-depth,depth):box('Roof • ivory bargeboard',(side*half/2,y,z+rise/2-.045),(length+.18,.13,.17),'Cream',.03,rot=(0,side*a,0))
        box('Roof • eave fascia',(side*half,0,z-.035),(.13,d+.10,.19),'Cream',.03)
        # Broad shallow tile panels, not dozens of densely bevelled tiny tiles.
        for row in range(3):
            t=(row+.5)/3
            for col in range(5):
                y=-depth+(col+.5)*d/5
                box('Roof • tile panel',(side*half*t,y,z+rise*(1-t)+.085),(length/3+.018,d/5-.018,.035),tile_color if (row+col)%4==0 else roof_color,.0 if G.LOW else .012,rot=(0,side*a,0))
    cyl('Roof • rounded ridge',(0,0,z+rise+.10),.115,d+.12,roof_color,rot=(math.pi/2,0,0))
def round_window(x,y,z,r=.22):
    cyl('Attic • ivory round frame',(x,y,z),r,.105,'Cream',rot=(math.pi/2,0,0))
    cyl('Attic • opaque round glazing',(x,y-.067,z),r*.73,.035,'Glass',rot=(math.pi/2,0,0))
    box('Attic • vertical mullion',(x,y-.095,z),(.042,.03,r*1.42),'Cream',.008)
    box('Attic • horizontal mullion',(x,y-.095,z),(r*1.42,.03,.042),'Cream',.008)
def chimney(x,y,roof_z):
    box('Chimney • apricot stack',(x,y,roof_z+.25),(.36,.39,.72),'Apricot',.035)
    box('Chimney • cream cap',(x,y,roof_z+.62),(.49,.50,.12),'Cream',.025)
    box('Chimney • dark mouth',(x,y,roof_z+.685),(.24,.25,.018),'Dark wood',0)
def small_bench(x,y,z=0,w=.85):
    for yy in (-.08,.08):box('Porch • bench seat slat',(x,y+yy,z+.43),(w,.14,.08),'Wood light',.025)
    box('Porch • bench back',(x,y+.16,z+.64),(w,.08,.16),'Wood light',.025)
    for xx in (-w*.34,w*.34):
        for yy in (-.08,.08):rod('Porch • bench leg',(x+xx,y+yy,z+.015),(x+xx,y+yy,z+.40),.027,'Teal dark')
        rod('Porch • bench back support',(x+xx,y+.14,z+.39),(x+xx,y+.14,z+.72),.025,'Teal dark')
def plant_box(x,y,z,w=.78):
    box('Home • timber planter',(x,y,z),(w,.27,.19),'Wood light',.03)
    for i in range(3):ellipsoid('Home • foliage',(x+(i-1)*w*.25,y,z+.15),(.16,.12,.14),'Leaf light')

def house(level,low):
    key=f'house_level_{level}';coll,root=begin(key,level,low)
    w,d,h=[(2.25,2.10,2.30),(2.60,2.25,2.45),(2.94,2.40,3.43)][level-1]
    y=-d/2-.04
    foundation(w,d,h,'Apricot')
    gable(w+.40,d+.40,h+.03,.78 if level<3 else .92,'Clay','Clay light','Apricot')
    door(.57 if level==1 else .67,y-.015)
    window(-.61 if level==1 else -.67,y-.01,1.35,.70 if level==1 else .84,.82 if level==1 else .91)
    side_window(w/2+.025,1.42,.80 if level==1 else .95,.91)
    if level==1:
        round_window(0,y-.02,2.61,.20)
        succulent(1.32,y-.34,0,.13,.21)
    elif level==2:
        round_window(0,y-.02,2.78,.23)
        chimney(.73,.52,2.89)
        box('Porch • raised deck',(0,y-.40,.065),(2.76,.85,.13),'Stone',.045)
        box('Porch • teal canopy',(0,y-.35,2.05),(2.61,.92,.12),'Teal',.04,rot=(.08,0,0))
        for x in (-1.17,1.17):
            box('Porch • ivory post',(x,y-.66,1.06),(.11,.11,1.96),'Cream',.025)
            rod('Porch • diagonal bracket',(x,y-.17,1.80),(x,y-.61,2.04),.028,'Wood')
        small_bench(-.69,y-.47,.13,.79)
        succulent(1.54,y-.28,0,.17,.27)
        box('Home • plain mailbox',(-1.16,y-.12,.82),(.25,.17,.30),'Teal',.03)
        box('Home • letter slot',(-1.16,y-.212,.88),(.16,.018,.024),'Brass',0)
    else:
        chimney(.91,.52,3.92)
        box('Upper • ivory belt',(0,0,2.44),(w+.12,d+.12,.15),'Cream',.035)
        window(-.65,y-.01,2.98,.62,.56)
        arch('Balcony • ivory doorway',.65,y-.035,2.49,.70,.91,.14,'Cream')
        arch('Balcony • glazed door',.65,y-.13,2.55,.53,.78,.04,'Glass')
        box('Balcony • door mullion',(.65,y-.165,2.94),(.035,.035,.68),'Cream',.008)
        ellipsoid('Balcony • door knob',(.84,y-.19,2.80),(.028,)*3,'Brass')
        side_window(w/2+.025,2.98,.95,.56)
        round_window(0,y-.02,3.78,.20)
        box('Porch • raised deck',(0,y-.40,.065),(3.10,.85,.13),'Stone',.045)
        box('Balcony • slab',(0,y-.30,2.42),(2.63,.73,.14),'Cream',.04)
        for x in (-1.15,1.15):box('Balcony • porch column',(x,y-.55,1.27),(.13,.13,2.28),'Cream',.03)
        for x in (-1.10,-.55,0,.55,1.10):rod('Balcony • baluster',(x,y-.62,2.49),(x,y-.62,2.91),.027,'Teal dark')
        box('Balcony • timber handrail',(0,y-.62,2.93),(2.37,.10,.09),'Wood light',.025)
        for x in (-1.15,1.15):box('Balcony • side handrail',(x,y-.29,2.93),(.09,.65,.09),'Wood light',.025)
        plant_box(-.64,y-.40,2.57,.71)
        small_bench(-.73,y-.45,.13,.83)
        succulent(1.64,y-.29,0,.18,.29)
    bpy.context.view_layer.update();return coll,root

def bloom(x,y,z,color='Pink',s=1):
    rod('Flower • stem',(x,y,z),(x,y,z+.24*s),.014*s,'Leaf dark')
    for i in range(5):
        a=i*math.tau/5
        ellipsoid('Flower • petal',(x+.058*s*math.cos(a),y+.058*s*math.sin(a),z+.26*s),(.063*s,.063*s,.038*s),color)
    ellipsoid('Flower • petal centre',(x,y,z+.28*s),(.034*s,)*3,'Flower')
    for sign in (-1,1):
        leaf=ellipsoid('Flower • foliage',(x+sign*.055*s,y,z+.12*s),(.08*s,.034*s,.035*s),'Leaf')
        leaf.rotation_euler[1]=sign*.25
def bouquet(x,y,z=0,r=.16,h=.23,color='Pink',count=1):
    cyl('Florist • ceramic pot',(x,y,z+h/2),r*.77,h,'Clay',top=r)
    if G.LOW:
        bpy.ops.mesh.primitive_torus_add(major_segments=12,minor_segments=3,major_radius=r*.94,minor_radius=.026,location=(x,y,z+h-.02))
        G.attach(bpy.context.object,'Florist • rolled pot rim','Clay light',True)
    else:ring('Florist • rolled pot rim',(x,y,z+h-.02),r*.94,.026,'Clay light')
    cyl('Florist • pot soil',(x,y,z+h-.028),r*.80,.018,'Earth',thin=True)
    for i in range(count):
        a=i*2.4
        bloom(x+(math.cos(a)*r*.38 if count>1 else 0),y+(math.sin(a)*r*.38 if count>1 else 0),z+h,color,.85+i*.12)
def flower_emblem(x,y,z,s=1):
    cyl('Florist • ivory icon disc',(x,y,z),.27*s,.07,'Cream',rot=(math.pi/2,0,0))
    for i in range(5):
        a=i*math.tau/5
        ellipsoid('Florist • icon petal',(x+.12*s*math.sin(a),y-.055*s,z+.12*s*math.cos(a)),(.09*s,.035*s,.09*s),'Rose')
    ellipsoid('Florist • icon petal centre',(x,y-.09*s,z),(.065*s,.025*s,.065*s),'Flower')
def rose_awning(x,y,z,w):
    previous=set(G.COL.objects)
    G.awning(x,y,z,w,7,.58)
    # Recolour only newly created teal fabric, never unrelated timber supports.
    for o in set(G.COL.objects)-previous:
        for slot in o.material_slots:
            if slot.material==G.M['Teal']:slot.material=G.M['Rose']
def display_stand(x,y,z=.45,w=1.18):
    box('Florist • timber display shelf',(x,y,z),(w,.39,.10),'Wood light',.03)
    for xx in (-w*.42,w*.42):
        for yy in (-.13,.13):box('Florist • shelf leg',(x+xx,y+yy,z/2-.025),(.065,.065,z-.05),'Wood',.014)
    for i,c in enumerate(('Pink','Flower','Plum')):bouquet(x+(i-1)*w*.31,y,z+.05,.145,.21,c)
def greenhouse():
    x=1.85;y=.08
    box('Greenhouse • cream base',(x,y,.22),(.96,2.25,.44),'Cream',.055)
    box('Greenhouse • opaque glass walls',(x,y,1.17),(.87,2.16,1.46),'Glass light',.025)
    for xx in (1.40,2.30):
        for yy in (-1.03,.08,1.19):box('Greenhouse • ivory upright',(xx,yy,1.18),(.065,.07,1.56),'Cream',.014)
    for zz in (.48,1.20,1.92):box('Greenhouse • side rail',(2.32,y,zz),(.065,2.29,.065),'Cream',.014)
    box('Greenhouse • front transom',(x,-1.05,1.20),(.96,.07,.065),'Cream',.014)
    angle=.31
    box('Greenhouse • sloping blue roof',(x,y,2.10),(1.04,2.33,.07),'Glass',.015,rot=(0,angle,0))
    # Glazed wedges close the front/rear space below the sloping roof.
    for yy in (-1.02,1.18):
        profile=[(1.40,1.88),(2.30,1.88),(2.30,1.921),(1.40,2.209)]
        vs=[(xx,plane,zz) for plane in (yy-.025,yy+.025) for xx,zz in profile]
        mesh('Greenhouse • upper glazed infill',vs,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'Glass light',0 if G.LOW else .008)
    for yy in (-1.09,-.32,.47,1.25):box('Greenhouse • roof rafter',(x,yy,2.14),(1.09,.065,.065),'Cream',.014,rot=(0,angle,0))
    for xx,zz in ((1.35,2.30),(2.36,1.99)):box('Greenhouse • eave edge',(xx,y,zz),(.065,2.41,.08),'Cream',.014)

def florist(level,low):
    key=f'florist_level_{level}';coll,root=begin(key,level,low)
    w,d,h=[(2.20,2.00,2.28),(2.58,2.23,2.60),(2.68,2.30,2.75)][level-1]
    y=-d/2-.04
    foundation(w,d,h,'Sage')
    gable(w+.36,d+.36,h+.03,.66 if level==1 else .83,'Teal','Teal light','Sage')
    door(-.59 if level==1 else -.65,y-.015)
    # The painted door stays rose while its opaque glazing and ivory arch stay intact.
    for o in coll.objects:
        if o.name.startswith('Door'):
            for slot in o.material_slots:
                if slot.material in (G.M['Teal'],G.M['Teal light']):slot.material=G.M['Rose']
    window(.56,y-.01,1.30,.67 if level==1 else .86,1.02 if level==1 else 1.15)
    flower_emblem(0,y-.03,h+.30,.87 if level==1 else 1)
    if level<3:side_window(w/2+.025,1.40,.80,.98)
    if level==1:
        box('Florist • low flower ledge',(.55,y-.28,.18),(.88,.42,.36),'Cream',.04)
        bouquet(.30,y-.31,.36,.14,.20,'Pink')
        bouquet(.82,y-.31,.36,.14,.24,'Flower')
    else:
        rose_awning(.57,y-.025,2.14 if level==2 else 2.22,1.48)
        display_stand(.58,y-.43,.48,1.24)
        bouquet(-1.17,y-.46,0,.19,.34,'Flower',2)
        if level==2:succulent(1.48,y-.29,0,.17,.24)
        else:
            greenhouse()
            bouquet(1.88,-1.52,0,.20,.32,'Plum',2)
            # Low shelves of foliage make the greenhouse useful without dense leaves.
            box('Florist • greenhouse display ledge',(1.83,-1.12,.52),(.85,.29,.08),'Wood light',.025)
            for xx in (1.59,1.83,2.07):ellipsoid('Florist • greenhouse foliage',(xx,-1.16,.66),(.13,.10,.15),'Leaf light')
    bpy.context.view_layer.update();return coll,root

def normal_check(coll):
    dg=bpy.context.evaluated_depsgraph_get();closed=0;open_meshes=[]
    for o in coll.objects:
        if o.type!='MESH':continue
        e=o.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles()
        assert all(t.area>1e-12 for t in me.loop_triangles),(o.name,'degenerate source triangle')
        bm=bmesh.new();bm.from_mesh(me)
        if all(edge.is_manifold for edge in bm.edges):
            volume=bm.calc_volume(signed=True)
            assert volume>1e-10,(o.name,'inward or zero-volume solid',volume)
            closed+=1
        else:open_meshes.append(o.name)
        bm.free();e.to_mesh_clear()
    assert not open_meshes,open_meshes
    return {'closed_outward_components':closed,'open_components':0}

EDIT={};RUN={};REPORT={'models':{},'placement_xy_min':[-2.4,-3.2],'placement_xy_max':[2.4,1.6]}
for kind,fn in [('house',house),('florist',florist)]:
    for level in (1,2,3):
        key=f'{kind}_level_{level}'
        hi,hr=fn(level,False);EDIT[key]=hi
        hi_stats=G.stats(hi);hi_normals=normal_check(hi)
        low,lr=fn(level,True)
        dz=G.stats(low)['bounds_min'][2]
        for o in low.objects:
            if o!=lr:o.location.z-=dz
        bpy.context.view_layer.update();low_normals=normal_check(low)
        G.consolidate(low,lr,key,level);RUN[key]=low
        file=ROOT/'exports'/f'{key}.glb';G.export(low,file)
        after=G.stats(low);glb=G.glb_stats(file)
        assert glb['mesh_objects']==glb['primitives']==glb['materials']==1
        assert glb['textures']==0 and glb['all_primitives_have_vertex_color']
        assert after['bounds_min'][0]>=-2.4 and after['bounds_min'][1]>=-3.2
        assert after['bounds_max'][0]<=2.4 and after['bounds_max'][1]<=1.6
        assert after['triangles']<={1:4000,2:6000,3:8000}[level],(key,after['triangles'])
        REPORT['models'][key]={'level':level,'editable':hi_stats,'runtime':after,'glb':glb,'editable_normals':hi_normals,'runtime_source_normals':low_normals,
          'triangle_reduction_percent':round(100*(1-after['triangles']/hi_stats['triangles']),2),
          'initial_triangle_target':{1:4000,2:6000,3:8000}[level]}
        scene.collection.children.unlink(hi);scene.collection.children.unlink(low)
        print('ASSET_COMPLETE',key,json.dumps(REPORT['models'][key]),flush=True)

# Import a read-only copy of the delivered cafe v003 for a common-style proof.
bpy.ops.import_scene.gltf(filepath=str(ROOT.parent/'town_cafe_v003/exports/cafe_level_3.glb'))
cafe_collection=bpy.data.collections.new('REFERENCE • cafe v003 level 3');scene.collection.children.link(cafe_collection)
for o in list(bpy.context.selected_objects):
    for c in list(o.users_collection):c.objects.unlink(o)
    cafe_collection.objects.link(o)
scene.collection.children.unlink(cafe_collection)

G.LOW=True;G.PARENT=None;G.COL=G.collection('STUDIO • lighting');STUDIO=G.COL
box('Studio floor',(0,0,-.065),(150,150,.10),'Backdrop',0)
for name,loc,power,size,color in [('Warm window',(-6,-8,13),1800,8,(1,.86,.72)),('Sky fill',(7,-1,10),1100,7,(.77,.87,1)),('Back rim',(0,7,10),1400,6,(1,.94,.80))]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);STUDIO.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Warm studio');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.65,.72,.78,1);bg.inputs['Strength'].default_value=.35
def configure(s,w=2400,h=1250):
    s.world=world;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
    try:s.render.engine='CYCLES'
    except TypeError:s.render.engine='BLENDER_EEVEE'
    if s.render.engine=='CYCLES':s.cycles.samples=64;s.cycles.use_denoising=True
    s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
    opts=[x.identifier for x in s.view_settings.bl_rna.properties['view_transform'].enum_items]
    if 'AgX' in opts:s.view_settings.view_transform='AgX'
    s.view_settings.exposure=.35
def camera(s,loc=(9,-25,17),target=(0,-.2,1.6),scale=17.8):
    d=bpy.data.cameras.new(s.name+' camera');o=bpy.data.objects.new(s.name+' camera',d);s.collection.objects.link(o)
    o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    d.type='ORTHO';d.ortho_scale=scale;s.camera=o
def row(s,collections):
    right=Vector((24.8,9,0)).normalized()
    for i,c in enumerate(collections):
        o=bpy.data.objects.new(c.name+' display',None);s.collection.objects.link(o)
        o.instance_type='COLLECTION';o.instance_collection=c;o.location=right*((i-1)*5.1)
    configure(s);camera(s)
row(scene,[RUN[f'house_level_{n}'] for n in (1,2,3)])
s=bpy.data.scenes.new('02 • Florist upgrades');s.collection.children.link(STUDIO)
row(s,[RUN[f'florist_level_{n}'] for n in (1,2,3)])
s=bpy.data.scenes.new('03 • Neighborhood style');s.collection.children.link(STUDIO)
row(s,[RUN['house_level_3'],cafe_collection,RUN['florist_level_3']])
for key in RUN:
    for prefix,coll in [('EDIT',EDIT[key]),('RUNTIME',RUN[key])]:
        s=bpy.data.scenes.new(prefix+' • '+key);s.collection.children.link(coll);s.collection.children.link(STUDIO)
        configure(s,1200,1200);camera(s,(7,-11,8),(0,-.25,1.90),6.75)
        s['note']='EDIT has named components. RUNTIME has one mesh/material with COLOR_0.'
bpy.context.window.scene=scene
scene.render.filepath=str(ROOT/'renders/01_house_levels.png')
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
assert not any(o.type=='FONT' for o in bpy.data.objects)
assert not any('shadow recess' in o.name for o in bpy.data.objects)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/chagok_house_florist_v001.blend'))
(ROOT/'reports/model_stats.json').write_text(json.dumps(REPORT,indent=2),encoding='utf-8')
(ROOT/'reports/palette.json').write_text(json.dumps(palette,indent=2),encoding='utf-8')
assert prior==hashes()
print('BUILD_COMPLETE',flush=True)
