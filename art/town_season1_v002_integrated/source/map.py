"""Assemble the whole fourteen-plot village from the actual delivered GLBs."""
import bpy,sys,json,hashlib,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import town as T
import lanes
scene,library,before=T.start_scene();asset=T.importer(scene,library)
kinds=sorted(T.FOLDERS)+list(T.NEW)
for kind in kinds:
    for n in (1,2,3):asset(kind,n)
local={k:T.hull([(p.x,p.y) for n in (1,2,3) for p in T.local_points(asset(k,n))]) for k in kinds}
layout=T.plan(local);T.save_metrics(layout,local,'final');T.place(scene,layout,asset)
height,paving,_=T.ground_scene(scene,layout,local,False)
access=lanes.make(layout,asset,height,paving)
import details
details.add(scene,before,layout,local,height)
T.configure(scene);scene['layout_revision']='All fourteen plots released; all world scales 1';scene['access']='42 primary doors across all 3 growth stages'
env=next(c for c in scene.collection.children if c.name.startswith('ENVIRONMENT'))
for n in (1,2):scene.collection.children.unlink(bpy.data.collections[f'ACCESS • level {n} thresholds'])
stages=[('beginning',1,{'home_entry','cafe','bakery','florist','grocer','bookshop','workshop','town_hall'}),
        ('middle',2,{b['id'] for b in layout}-{'home_upper_east','home_upper_west'})]
for label,level,ids in stages:
    stage=bpy.data.scenes.new('INTEGRATED • '+label);stage.world=scene.world
    for obj in scene.objects:
        if obj.type in ('CAMERA','LIGHT'):
            o=obj.copy();o.data=obj.data.copy();stage.collection.objects.link(o)
            if obj==scene.camera:stage.camera=o
    stage.collection.children.link(env);stage.collection.children.link(bpy.data.collections['ACCESS • level 3 thresholds']);stage.collection.children.link(bpy.data.collections[f'ACCESS • level {level} thresholds']);T.place(stage,[b for b in layout if b['id'] in ids],asset,level)
    for key in ('view_transform','look','exposure','gamma'):setattr(stage.view_settings,key,getattr(scene.view_settings,key))
    stage.unit_settings.system='METRIC';stage.unit_settings.scale_length=1;T.configure(stage)
    stage['illustration_only']='8/12/14 plots at L1/L2/L3; this is an art growth study, not game rules'
# Explicit references make unchanged source ownership and later runtime replacement unambiguous.
manifest={'revision':'town_season1_v002_integrated','types':12,'plots':14,'changed_assets':24,'unchanged_assets':12,'instances_world_scale':[1,1,1],
 'assets':[{'type':k,'level':n,'changed':k not in T.NEW,'path':str(T.source_file(k,n).relative_to(T.ART)).replace('\\','/'),
            'sha256':hashlib.sha256(T.source_file(k,n).read_bytes()).hexdigest()} for k in kinds for n in (1,2,3)],'layout':layout}
(ROOT/'reports/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(ROOT/'source/layout.json').write_text(json.dumps(layout,indent=2),encoding='utf-8')
bpy.context.window.scene=scene;bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/integrated_village.blend'))
print('INTEGRATED_MAP_COMPLETE',T.protect(),flush=True)
