"""ChagokTown: original bakery/bookshop, built in an isolated output folder."""
import sys, bpy, bmesh, math, json, hashlib
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'source'))
for folder in ('blend', 'exports', 'renders', 'reports'):
    (ROOT / folder).mkdir(exist_ok=True)
PROTECTED = ['town_miniature_v001', 'town_cafe_v002', 'town_cafe_v003', 'town_house_florist_v001']
def protected_hashes():
    paths = [p for folder in PROTECTED for p in (ROOT.parent / folder).rglob('*')
             if p.is_file() and '__pycache__' not in p.parts]
    paths += [ROOT.parents[1] / 'AGENTS.md'] + list((ROOT.parents[1] / 'docs').glob('*.md'))
    return {str(p.relative_to(ROOT.parents[1])): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
before = protected_hashes()
baseline = ROOT / 'reports/protected_files_sha256.json'
if baseline.exists():
    assert json.loads(baseline.read_text()) == before, 'Protected inputs changed since first build'
else:
    baseline.write_text(json.dumps(before, indent=2), encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
import geometry as G
from geometry import box, mesh, cyl, rod, ellipsoid, arch, window, door, succulent
scene = bpy.context.scene
scene.name = '01 • Bakery upgrades'
palette = json.loads((ROOT.parent / 'town_house_florist_v001/reports/palette.json').read_text())
for name, color in palette.items():
    m = bpy.data.materials.new(name); m.use_nodes = True; m.diffuse_color = G.linear(color)
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = G.linear(color)
    p.inputs['Roughness'].default_value = .68
    G.M[name] = m
m = bpy.data.materials.new('Town • opaque vertex palette'); m.use_nodes = True
m.use_backface_culling = True
p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
p.inputs['Roughness'].default_value = .68
p.inputs['Metallic'].default_value = 0
vc = m.node_tree.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Palette'
m.node_tree.links.new(vc.outputs['Color'], p.inputs['Base Color']); G.runtime_mat = m

def begin(key, level):
    # Editable components use exactly the delivered geometry, without a redundant dense variant.
    G.LOW = True
    G.COL = G.collection('EDIT • ' + key)
    G.PARENT = bpy.data.objects.new(key + '_root', None); G.COL.objects.link(G.PARENT)
    G.PARENT['level'] = level; G.PARENT['front'] = '-Y'; G.PARENT['units'] = 'metres'
    return G.COL, G.PARENT

def shell(x, y, w, d, h, color):
    box('Foundation • stone plinth', (x,y,.085), (w+.18,d+.18,.17), 'Stone', .065)
    box('Wall • plaster shell', (x,y,(h+.12)/2), (w,d,h-.12), color, .075)
    box('Wall • ivory skirting', (x,y,.25), (w+.04,d+.04,.17), 'Cream', .035)

def gable(x,y,w,d,z,rise,color,tile_color,wall_color,across=False,tiles=True):
    """Closed plaster gable with broad tiles. across rotates ridge to X for bakery."""
    old = set(G.COL.objects)
    a = math.atan2(rise,w/2); length = math.hypot(w/2,rise)
    hw = w/2-.15; hd = d/2-.15
    vs = [(-hw,-hd,z-.12),(hw,-hd,z-.12),(0,-hd,z+rise-.09),
          (-hw,hd,z-.12),(hw,hd,z-.12),(0,hd,z+rise-.09)]
    mesh('Gable • closed plaster infill',vs,[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)],wall_color,.018)
    for side in (-1,1):
        box('Roof • thick slope',(side*w/4,0,z+rise/2),(length+.10,d,.15),color,.04,rot=(0,side*a,0))
        for yy in (-d/2,d/2):
            box('Roof • ivory bargeboard',(side*w/4,yy,z+rise/2-.055),(length+.17,.13,.17),'Cream',.026,rot=(0,side*a,0))
        box('Roof • ivory eave',(side*w/2,0,z-.04),(.13,d+.12,.18),'Cream',.026)
        if tiles:
            for row in range(3):
                t = (row+.5)/3
                for col in range(4):
                    box('Roof • broad tile',(side*w/2*t,-d/2+(col+.5)*d/4,z+rise*(1-t)+.086),
                        (length/3+.01,d/4-.016,.032),tile_color if (row+col)%5==0 else color,0,rot=(0,side*a,0))
    cyl('Roof • rounded ridge',(0,0,z+rise+.10),.105,d+.12,color,rot=(math.pi/2,0,0))
    for o in set(G.COL.objects)-old:
        if across:
            o.location = Vector((-o.location.y,o.location.x,o.location.z)); o.rotation_euler[2] += math.pi/2
        o.location.x += x; o.location.y += y

def side_window(x,y,z,w,h,cross=True):
    old = set(G.COL.objects); window(0,-x,z,w,h,cross=cross)
    for o in set(G.COL.objects)-old:
        o.location = Vector((-o.location.y,o.location.x+y,o.location.z)); o.rotation_euler[2] += math.pi/2

def back_window(x,y,z,w,h):
    old = set(G.COL.objects); window(x,-y,z,w,h)
    for o in set(G.COL.objects)-old:
        o.location.x = -o.location.x; o.location.y = -o.location.y; o.rotation_euler[2] += math.pi

def loaf(x,y,z,s=1,icon=False):
    ellipsoid('Bread • golden loaf',(x,y,z),(.29*s,.075*s if icon else .14*s,.15*s),'Wood light')
    for dx in (-.12,0,.12):
        box('Bread • pale score',(x+dx*s,y-.071*s if icon else y-.025*s,z+.06*s if icon else z+.136*s),
            (.035*s,.016*s if icon else .16*s,.14*s if icon else .012*s),'Cream',.003,
            rot=(0,-.32,0) if icon else (0,0,-.28))

def bread_emblem(x,y,z,s=1):
    box('Bakery • ivory picture plaque',(x,y,z),(.80*s,.10,.49*s),'Cream',.075)
    loaf(x,y-.09,z,s,True)

def book_emblem(x,y,z,s=1):
    # An open book in relief. Covers, two blank page masses and the centre binding are geometry.
    for side in (-1,1):
        box('Book icon • teal cover',(x+side*.20*s,y,z),(.43*s,.085,.47*s),'Teal',.025,rot=(0,-side*.16,0))
        box('Book icon • blank pages',(x+side*.19*s,y-.057,z+.025*s),(.36*s,.042,.40*s),'Cream',.014,rot=(0,-side*.16,0))
    rod('Book icon • binding',(x,y-.09,z-.19*s),(x,y-.09,z+.22*s),.018*s,'Butter')

def canopy(x,y,z,w,color,depth=.6):
    # Reuse safe fabric geometry, recolour only the freshly created teal fabric.
    old = set(G.COL.objects); G.awning(x,y,z,w,5,depth)
    for o in set(G.COL.objects)-old:
        for slot in o.material_slots:
            if slot.material == G.M['Teal']: slot.material = G.M[color]

def bench(x,y,z=0,w=.85):
    box('Reading seat • cushion',(x,y,z+.43),(w,.39,.12),'Apricot',.04)
    box('Reading seat • timber back',(x,y+.19,z+.66),(w,.075,.24),'Wood light',.025)
    for dx in (-w*.36,w*.36):
        for dy in (-.12,.12):
            rod('Reading seat • leg',(x+dx,y+dy,z+.015),(x+dx,y+dy,z+.39),.027,'Teal dark')
        rod('Reading seat • back support',(x+dx,y+.18,z+.40),(x+dx,y+.18,z+.78),.024,'Teal dark')

def book(x,y,z,w=.12,h=.29,color='Rose',lean=0):
    old = set(G.COL.objects)
    box('Book • blank page block',(0,0,h/2),(w*.72,.17,h*.86),'Cream',.008)
    for dx in (-w/2,w/2):
        box('Book • plain cover',(dx,0,h/2),(.025,.20,h),color,.006)
    box('Book • plain spine',(0,-.105,h/2),(w+.025,.035,h),color,.008)
    for o in set(G.COL.objects)-old:
        # Pivot the whole closed book as a group, preserving closed component meshes.
        v = o.location.copy(); o.location.x = math.cos(lean)*v.x+math.sin(lean)*v.z+x
        o.location.y += y; o.location.z = -math.sin(lean)*v.x+math.cos(lean)*v.z+z
        o.rotation_euler[1] = lean

def book_cart(x,y,z=0):
    box('Book cart • lower shelf',(x,y,z+.22),(1.05,.40,.09),'Wood light',.025)
    box('Book cart • upper shelf',(x,y,z+.68),(1.05,.40,.09),'Wood light',.025)
    for dx in (-.47,.47):
        box('Book cart • side',(x+dx,y,z+.47),(.075,.37,.67),'Wood light',.02)
        for dy in (-.13,.13):
            cyl('Book cart • wheel',(x+dx,y+dy,z+.10),.075,.055,'Teal dark',rot=(math.pi/2,0,0),thin=True)
    for i,c in enumerate(('Teal','Rose','Butter','Plum','Apricot')):
        book(x+(i-2)*.15,y-.01,z+.27,.105,.27+(i%2)*.04,c)
    for i,c in enumerate(('Rose','Teal','Butter')):
        book(x+(i-1)*.25,y-.015,z+.725,.14,.29,c,(i-1)*.09)

def bread_counter(x,y,z=0,w=1.22):
    box('Bread stand • timber counter',(x,y,z+.57),(w,.45,.10),'Wood light',.025)
    box('Bread stand • lower shelf',(x,y,z+.23),(w,.37,.08),'Wood light',.02)
    for dx in (-w*.40,w*.40):
        for dy in (-.14,.14):
            box('Bread stand • leg',(x+dx,y+dy,z+.29),(.065,.065,.54),'Wood',.014)
    box('Bread stand • cream tray',(x,y,z+.64),(w-.10,.35,.045),'Cream',.015)
    for dx in (-w*.22,w*.22): loaf(x+dx,y,z+.73,.66)

def bakery(level):
    key=f'bakery_level_{level}'; coll,root=begin(key,level)
    x,w,d,h = [(0,2.30,1.96,2.34),(0,2.96,2.18,2.53),(-.39,2.46,2.34,3.65)][level-1]
    front=-d/2-.035
    shell(x,0,w,d,h,'Butter')
    # Crosswise gable keeps its broad warm roof distinct from the cafe's hipped teal roof.
    gable(x,0,d+.38,w+.42,h+.025,.63 if level<3 else .69,'Clay','Clay light','Butter',across=True)
    dx=x-w*.29; wx=x+w*.22; ww=w*.43
    door(dx,front-.015)
    window(wx,front,1.15,ww,.91,cross=False)
    bread_emblem(wx if level==1 else x+.15,front-.15,2.11 if level<3 else 2.19,.77 if level==1 else .92)
    side_window(x+w/2+.02,.05,1.25,.84,.87)
    back_window(-x,d/2+.025,1.35,.80,.79)
    if level==1:
        # Tiny bread shapes sit on the outside display ledge, not hidden behind opaque glass.
        loaf(wx,front-.22,.71,.48)
        succulent(1.30,front-.32,0,.13,.21)
    else:
        box('Forecourt • stone deck',(-.05,front-.74,.055),(3.25 if level==2 else 3.63,1.51,.11),'Stone',.045)
        canopy(wx,front-.08,2.02,ww+.26,'Clay light',.62)
        bread_counter(wx,front-.98,.11,1.15)
        succulent(-1.59,front-.40,.11,.14,.23)
        if level==2:
            box('Bakery • side chimney',(1.08,.64,2.99),(.34,.37,.81),'Apricot',.035)
            box('Bakery • chimney cap',(1.08,.64,3.42),(.46,.48,.12),'Cream',.025)
            box('Bakery • chimney mouth',(1.08,.64,3.486),(.23,.25,.016),'Dark wood',0)
        else:
            box('Upper bakery • ivory belt',(x,0,2.49),(w+.10,d+.08,.13),'Cream',.028)
            arch('Upper bakery • cream arch',x,front-.04,2.65,1.08,.83,.14,'Cream')
            arch('Upper bakery • opaque baking loft window',x,front-.13,2.72,.86,.65,.045,'Glass')
            box('Upper bakery • mullion',(x,front-.17,3.04),(.05,.045,.59),'Cream',.009)
            box('Upper bakery • sill',(x,front-.19,2.62),(1.27,.31,.12),'Cream',.03)
            side_window(x+w/2+.02,.03,3.03,.84,.68)
            back_window(-x,d/2+.025,3.03,.84,.68)
            # Attached baking wing, lower roof and a stout chimney create a new silhouette.
            ax,ay=1.43,.13
            shell(ax,ay,1.12,1.83,1.85,'Apricot')
            box('Bakehouse • thick shed roof',(ax,ay,1.94),(1.34,2.04,.16),'Clay light',.04,rot=(.13,0,0))
            for xx in (ax-.65,ax+.65):
                box('Bakehouse • ivory side fascia',(xx,ay,1.91),(.10,2.08,.16),'Cream',.025,rot=(.13,0,0))
            # Closed wall infill reaches the sloping roof at front and rear.
            box('Bakehouse • full upper infill',(ax,ay,1.78),(1.12,1.83,.43),'Apricot',.02,rot=(.13,0,0))
            arch('Bakehouse • ivory oven window',ax,-.835,.48,.76,1.01,.13,'Cream')
            arch('Bakehouse • dark oven glazing',ax,-.92,.56,.56,.83,.045,'Teal dark')
            for zz in (.76,.91):box('Bakehouse • brass oven rail',(ax,-.954,zz),(.40,.025,.04),'Brass',.006)
            box('Bakehouse • chimney',(1.62,.64,2.38),(.45,.46,1.70),'Apricot',.04)
            box('Bakehouse • ivory chimney cap',(1.62,.64,3.25),(.61,.62,.14),'Cream',.03)
            box('Bakehouse • chimney mouth',(1.62,.64,3.327),(.30,.31,.018),'Dark wood',0)
            succulent(1.68,-1.61,.11,.15,.24)
    bpy.context.view_layer.update();return coll,root

def bookshop(level):
    key=f'bookshop_level_{level}';coll,root=begin(key,level)
    w,d,h,rise=[(2.13,2.00,2.29,.86),(2.57,2.20,2.42,1.00),(2.89,2.34,3.10,1.30)][level-1]
    front=-d/2-.035
    shell(0,0,w,d,h,'Sage')
    gable(0,0,w+.38,d+.38,h+.025,rise,'Teal dark','Teal','Sage')
    door(w*.27,front-.015)
    window(-w*.255,front,1.18,.83 if level==1 else 1.01,.96,cross=False)
    side_window(w/2+.025,.02,1.38,.84,.88)
    back_window(0,d/2+.025,1.38,.82,.87)
    if level<3:
        book_emblem(0,front-.10,h+.37,.78)
    if level>=2:
        box('Reading porch • stone deck',(0,front-.82,.055),(3.15,1.70,.11),'Stone',.045)
        # Solid little porch roof, unlike the fabric awnings of the cafe and bakery.
        box('Reading porch • broad canopy',(0,front-.35,2.17),(2.98,.95,.14),'Teal',.04,rot=(.11,0,0))
        box('Reading porch • ivory front edge',(0,front-.81,2.12),(3.02,.10,.15),'Cream',.025)
        for xx in (-1.35,1.35):
            box('Reading porch • ivory post',(xx,front-.72,1.10),(.10,.10,1.98),'Cream',.022)
            rod('Reading porch • bracket',(xx,front-.68,1.84),(xx,front-.34,2.10),.027,'Wood light')
        book_cart(-.72,front-.95,.11)
        bench(.76,front-1.28,.11,.89)
        if level==3:
            # A closed, projecting front reading bay fills the attic rather than floating on the roof.
            box('Reading loft • projecting wall',(0,front-.14,3.08),(1.73,.44,1.12),'Sage',.035)
            gable(0,front-.15,1.99,.77,3.64,.48,'Teal','Teal light','Sage',tiles=False)
            window(0,front-.40,3.12,1.35,.78,cross=True)
            box('Reading loft • supported sill',(0,front-.51,2.64),(1.93,.39,.15),'Cream',.035)
            book_emblem(0,front-.65,2.38,.67)
            side_window(w/2+.025,.05,2.66,.84,.59)
            back_window(0,d/2+.025,2.68,.84,.59)
            # A visible blank closed book on the seat and a modest planter finish the nook.
            box('Reading seat • resting book cover',(.83,front-1.29,.645),(.30,.22,.035),'Rose',.007,rot=(0,0,.17))
            box('Reading seat • resting blank pages',(.83,front-1.29,.669),(.26,.20,.026),'Cream',.006,rot=(0,0,.17))
            succulent(1.74,front-.90,0,.16,.25)
    bpy.context.view_layer.update();return coll,root

def check_components(coll):
    dg=bpy.context.evaluated_depsgraph_get();count=0
    for o in coll.objects:
        if o.type!='MESH':continue
        e=o.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles()
        assert all(t.area>1e-12 for t in me.loop_triangles),(o.name,'degenerate source triangle')
        assert all(math.isfinite(c) for n in me.corner_normals for c in n.vector),o.name
        assert all(abs(n.vector.length-1)<.001 for n in me.corner_normals),(o.name,'non-unit source normal')
        bm=bmesh.new();bm.from_mesh(me)
        assert all(edge.is_manifold for edge in bm.edges),(o.name,'open source solid')
        assert bm.calc_volume(signed=True)>1e-10,(o.name,'inward source solid')
        # Consistent oriented shared edges catches locally reversed faces too.
        assert all(edge.is_contiguous for edge in bm.edges),(o.name,'inconsistent source face winding')
        bm.free();e.to_mesh_clear();count+=1
    return {'closed_outward_components':count,'open_components':0,'degenerate_triangles':0,'finite_unit_corner_normals':True}

EDIT={};RUN={};REPORT={'models':{},'placement_xy_min':[-2.4,-3.2],'placement_xy_max':[2.4,1.6]}
for kind,fn in [('bakery',bakery),('bookshop',bookshop)]:
    for level in (1,2,3):
        key=f'{kind}_level_{level}'
        coll,root=fn(level);EDIT[key]=coll
        component_check=check_components(coll);editable_stats=G.stats(coll)
        low=G.collection('LOW • '+key)
        lr=root.copy();lr.name=key+'_runtime_root';low.objects.link(lr)
        for source in list(coll.objects):
            if source.type!='MESH':continue
            obj=source.copy();obj.data=source.data.copy();low.objects.link(obj);obj.parent=lr
        # Both editable and runtime share exact metre-scale geometry, ground and local root.
        assert abs(editable_stats['bounds_min'][2])<1e-5
        G.consolidate(low,lr,key,level);RUN[key]=low
        path=ROOT/'exports'/f'{key}.glb';G.export(low,path)
        runtime=G.stats(low);glb=G.glb_stats(path)
        assert glb['mesh_objects']==glb['materials']==glb['primitives']==1
        assert glb['textures']==0 and glb['all_primitives_have_vertex_color']
        assert runtime['triangles']<={1:4000,2:6000,3:8000}[level],(key,runtime['triangles'])
        assert runtime['bounds_min'][0]>=-2.4 and runtime['bounds_min'][1]>=-3.2
        assert runtime['bounds_max'][0]<=2.4 and runtime['bounds_max'][1]<=1.6,(key,runtime)
        REPORT['models'][key]={'level':level,'editable':editable_stats,'runtime':runtime,'glb':glb,
            'source_geometry':component_check,'initial_triangle_target':{1:4000,2:6000,3:8000}[level]}
        scene.collection.children.unlink(coll);scene.collection.children.unlink(low)
        print('ASSET_COMPLETE',key,runtime['triangles'],flush=True)

bpy.ops.import_scene.gltf(filepath=str(ROOT.parent/'town_cafe_v003/exports/cafe_level_3.glb'))
cafe=bpy.data.collections.new('REFERENCE • cafe v003');scene.collection.children.link(cafe)
for o in list(bpy.context.selected_objects):
    for c in list(o.users_collection):c.objects.unlink(o)
    cafe.objects.link(o)
scene.collection.children.unlink(cafe)
G.PARENT=None;G.COL=G.collection('STUDIO • lighting');STUDIO=G.COL
box('Studio floor',(0,0,-.065),(150,150,.10),'Backdrop',0)
for name,loc,power,size,color in [('Warm window',(-6,-8,13),1800,8,(1,.86,.72)),('Sky fill',(7,-1,10),1100,7,(.77,.87,1)),('Back rim',(0,7,10),1400,6,(1,.94,.80))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    o=bpy.data.objects.new(name,data);STUDIO.objects.link(o);o.location=loc
    o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Warm studio');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.65,.72,.78,1);bg.inputs['Strength'].default_value=.35
def configure(s,w=2400,h=1250):
    s.world=world;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
    s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=True
    s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
    if 'AgX' in [x.identifier for x in s.view_settings.bl_rna.properties['view_transform'].enum_items]:s.view_settings.view_transform='AgX'
    s.view_settings.exposure=.35
def camera(s,loc=(9,-25,17),target=(0,-.2,1.7),scale=17.8):
    data=bpy.data.cameras.new(s.name+' camera');o=bpy.data.objects.new(s.name+' camera',data);s.collection.objects.link(o)
    o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO';data.ortho_scale=scale;s.camera=o
def row(s,collections):
    right=Vector((24.8,9,0)).normalized()
    for i,coll in enumerate(collections):
        o=bpy.data.objects.new(coll.name+' display',None);s.collection.objects.link(o)
        o.instance_type='COLLECTION';o.instance_collection=coll;o.location=right*((i-1)*5.1)
    configure(s);camera(s)
row(scene,[RUN[f'bakery_level_{n}'] for n in (1,2,3)])
s=bpy.data.scenes.new('02 • Bookshop upgrades');s.collection.children.link(STUDIO)
row(s,[RUN[f'bookshop_level_{n}'] for n in (1,2,3)])
s=bpy.data.scenes.new('03 • Neighborhood style');s.collection.children.link(STUDIO)
row(s,[RUN['bakery_level_3'],cafe,RUN['bookshop_level_3']])
for key in RUN:
    for prefix,coll in [('EDIT',EDIT[key]),('RUNTIME',RUN[key])]:
        s=bpy.data.scenes.new(prefix+' • '+key);s.collection.children.link(coll);s.collection.children.link(STUDIO)
        configure(s,1200,1200);camera(s,(7,-11,8),(0,-.3,2.0),6.8)
        s['note']='Named editable components and exact corresponding vertex-colour runtime mesh.'
bpy.context.window.scene=scene
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
assert not any(o.type=='FONT' or 'shadow recess' in o.name for o in bpy.data.objects)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/chagok_sol_bakery_bookshop_v001.blend'))
(ROOT/'reports/model_stats.json').write_text(json.dumps(REPORT,indent=2),encoding='utf-8')
(ROOT/'reports/palette.json').write_text(json.dumps(palette,indent=2),encoding='utf-8')
assert before==protected_hashes()
print('BUILD_COMPLETE',flush=True)
