"""Assemble imported GLBs into the seasonal map and four upgrade comparison rows."""
import sys,bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import scene_common as C
import geometry as G
import models as M
import access as A
preview='--preview' in sys.argv
final,library,layout,asset,footprints=C.init(False)
for kind in M.BUILDERS:
    for level in (1,2,3):asset(kind,level)
ground,roads,strip=C.terrain(final,layout,footprints)
assert not C.check_layout(final,layout,footprints,'final'),'Maximum-stage footprints collide'
G.PARENT=None;G.scene=final;G.COL=next(c for c in final.collection.children if c.name.startswith('SEASON • geography'))

# Connect each primary entrance to actual shared paving. New authored routes are
# terrain colour; short links follow actual current building meshes.
doors={'cafe':(1,-1.75),'house':(.67,-1.66),'florist':(-.65,-1.63),'bakery':(-1.1034,-1.66),
       'bookshop':(.7803,-1.64),'workshop':(-1.0,-1.65),'grocer':(0,-1.65),'town_hall':(0,-1.65),**M.DOORS}
bvh=A.terrain_bvh(final);obstacles=A.building_bvhs(final);candidates=A.road_candidates(final);access_report={}
for b in layout:
    local=doors[b['kind']];start=C.transform_xy(b,local);lead=C.transform_xy(b,(local[0],local[1]-.85))
    half_width=min(.25,.30*b['scale']);height=min(.65,.85*b['scale'])
    path=A.connection(start,candidates,bvh,obstacles,half_width,height,lead=lead)
    if math.dist(path[0],path[-1])>.06:strip('Season • doorstep '+b['id'],path,half_width*2+.1)
    access_report[b['id']]={'local_primary_door':local,'path_xy':path,'three_ray_half_width':half_width,'ray_height':height,'clear':True}
(ROOT/'reports/entrance_access.json').write_text(json.dumps(access_report,indent=2),encoding='utf-8')
(ROOT/'reports/path_network.json').write_text(json.dumps({'authored_routes':[{'name':name,'nodes_xy':points,'width_m':width} for name,points,width in roads],
    'door_connectors':access_report,'inherited_compact_paving':[o.name for o in final.objects if o.type=='MESH' and any(m and (m.name=='Path' or m.name.startswith('Path.')) for m in o.data.materials) and not o.name.startswith('Season')],
    'scope':'visual prototype connections; no engine navigation bake'},indent=2),encoding='utf-8')

def duplicate(name,ids,level):
    bpy.context.window.scene=final;bpy.ops.scene.new(type='FULL_COPY');scene=bpy.context.scene;scene.name=name
    for obj in list(C.models_in(scene)):
        key=C.identity(obj)
        if key not in ids:bpy.data.objects.remove(obj,do_unlink=True);continue
        b=next(b for b in layout if b['id']==key);obj.instance_collection=asset(b['kind'],level);obj['display_level']=level
    return scene
start_ids={'cafe','bakery','home','workshop','cathedral','inn','watermill','farmstead'}
start=duplicate('Season 1 • beginning',start_ids,1)
middle=duplicate('Season 1 • middle',{b['id'] for b in layout if b['kind'] not in ('grocer','town_hall')},2)
for scene in (start,middle,final):C.configure(scene,preview);C.camera(scene)

# Reimported level rows use one metre scale and identical cameras within each row.
studio=bpy.data.collections.new('STUDIO • upgrade comparisons')
bpy.context.window.scene=library;library.collection.children.link(studio);G.scene=library;G.COL=studio;G.PARENT=None
G.box('Studio • continuous neutral floor',(0,0,-.085),(160,160,.16),'Backdrop',0)
for name,loc,energy,size,color in [('Warm large window',(-10,-14,18),2400,10,(1,.88,.73)),('Sky fill',(10,-2,14),1700,9,(.78,.88,1)),('Roof rim',(0,12,16),2100,8,(1,.95,.83))]:
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=color
    obj=bpy.data.objects.new(name,data);studio.objects.link(obj);obj.location=loc;obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Season studio • warm neutral');world.use_nodes=True;bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.65,.72,.78,1);bg.inputs['Strength'].default_value=.4
for kind in M.BUILDERS:
    scene=bpy.data.scenes.new('LEVELS • '+kind);scene.collection.children.link(studio);scene.world=world
    data=bpy.data.cameras.new(kind+' comparison camera');cam=bpy.data.objects.new(kind+' comparison camera',data);scene.collection.objects.link(cam);scene.camera=cam
    cam.location=(17,-32,22);target=Vector((0,0,3.4 if kind=='cathedral' else 2.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=32 if kind=='cathedral' else (35 if kind=='farmstead' else 31)
    right=Vector((32,17,0)).normalized();spacing=10.3 if kind=='farmstead' else 9.1
    for i in (1,2,3):
        obj=bpy.data.objects.new(f'{kind} • level {i} • actual GLB',None);scene.collection.objects.link(obj);obj.instance_type='COLLECTION';obj.instance_collection=asset(kind,i);obj.location=right*((i-2)*spacing)
    C.configure(scene,preview);scene.render.resolution_x=2100 if preview else 3000;scene.render.resolution_y=1000 if preview else 1440

def triangle_count(col):
    count=0;dg=bpy.context.evaluated_depsgraph_get()
    for obj in col.all_objects:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();count+=len(me.loop_triangles);ev.to_mesh_clear()
    return count
summary={}
for scene in (start,middle,final):
    bpy.context.window.scene=scene;bpy.context.view_layer.update();models=C.models_in(scene)
    model_triangles=sum(triangle_count(o.instance_collection) for o in models)
    environment=0;dg=bpy.context.evaluated_depsgraph_get()
    for obj in scene.objects:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();environment+=len(me.loop_triangles);ev.to_mesh_clear()
    summary[scene.name]={'buildings':len(models),'building_triangles':model_triangles,'environment_triangles':environment,'total_scene_triangles':model_triangles+environment,
                         'camera_matrix':[list(r) for r in scene.camera.matrix_world],'ortho_scale':scene.camera.data.ortho_scale,
                         'level_assignments':{C.identity(o):o['display_level'] for o in models}}
(ROOT/'reports/scene_stats.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
(ROOT/'source/layout.json').write_text(json.dumps(layout,indent=2),encoding='utf-8')
bpy.context.window.scene=final
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/season1_map.blend'))
C.protect();print('SEASON_MAP_COMPLETE',flush=True)
