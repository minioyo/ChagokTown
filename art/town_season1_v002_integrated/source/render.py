"""Reopen the saved scene and render honest whole-village comparisons."""
import bpy,sys,shutil,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import town as T
from mathutils import Vector
preview='--preview' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/integrated_village.blend'))
map_hash=hashlib.sha256((ROOT/'blend/integrated_village.blend').read_bytes()).hexdigest()
jobs=[('INTEGRATED • beginning','01_beginning','wide'),('INTEGRATED • middle','02_middle','wide'),
 ('INTEGRATED • final','03_final_oblique','wide'),('INTEGRATED • final','04_final_top','top')]
if preview:jobs=jobs[2:]
if '--qa' in sys.argv:
    jobs=[];original=bpy.data.scenes['INTEGRATED • final'];rows=[]
    for kind in T.FOLDERS:
        scene=bpy.data.scenes.new('LEVELS • '+kind);bpy.context.window.scene=scene;scene.world=original.world
        for obj in original.objects:
            if obj.type not in ('CAMERA','LIGHT'):continue
            new=obj.copy();new.data=obj.data.copy();scene.collection.objects.link(new)
            if obj==original.camera:scene.camera=new
        for n in (1,2,3):
            o=bpy.data.objects.new(f'{kind} L{n}',None);scene.collection.objects.link(o);o.instance_type='COLLECTION';o.instance_collection=bpy.data.collections[f'INPUT • {kind}_L{n}'];o.location=((n-2)*4.8,0,0)
        terrain=next(o for o in original.objects if o.name=='Integrated • continuous terrain');ground=terrain.copy();ground.data=terrain.data.copy();scene.collection.objects.link(ground)
        for v in ground.data.vertices:v.co.z=-.006
        for key in ('view_transform','look','exposure','gamma'):setattr(scene.view_settings,key,getattr(original.view_settings,key))
        scene.camera.location=(5,-26,16);scene.camera.rotation_euler=(Vector((0,0,2.7))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=17
        rows.append(scene)
        if '--kind' not in sys.argv or kind==sys.argv[sys.argv.index('--kind')+1]:jobs.append((scene.name,'07_'+kind+'_levels','levels'))
    bpy.data.libraries.write(str(ROOT/'blend/normalized_levels.blend'),set(rows),fake_user=True)
for name,filename,view in jobs:
    scene=bpy.data.scenes[name];bpy.context.window.scene=scene;T.configure(scene,preview)
    if view=='levels':scene.render.resolution_x=2100;scene.render.resolution_y=1100;scene.cycles.samples=40
    if view=='top':T.top_camera(scene)
    scene.render.filepath=str(ROOT/'renders'/f"{'preview_' if preview else ''}{filename}.png")
    bpy.ops.render.render(write_still=True);print('RENDERED',filename,flush=True)
if not preview:
    shutil.copyfile(T.OLD/'renders/03_season_final.png',ROOT/'renders/05_v001_before_oblique.png')
    shutil.copyfile(T.OLD/'renders/04_season_final_top.png',ROOT/'renders/06_v001_before_top.png')
tag='qa' if '--qa' in sys.argv else 'preview' if preview else 'final'
(ROOT/'reports'/f'renders_{tag}.json').write_text(json.dumps({'map_sha256':map_hash,'assets':json.loads((ROOT/'reports/manifest.json').read_text())['assets'],
 'images':[{ 'path':f"renders/{'preview_' if preview else ''}{filename}.png",'sha256':hashlib.sha256((ROOT/'renders'/f"{'preview_' if preview else ''}{filename}.png").read_bytes()).hexdigest()} for _,filename,_ in jobs]},indent=2),encoding='utf-8')
print('INTEGRATED_RENDERS_COMPLETE',T.protect(),flush=True)
