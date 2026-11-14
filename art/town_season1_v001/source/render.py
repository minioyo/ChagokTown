"""Render only saved imported-GLB scenes, reopening in this fresh process."""
import sys,bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import scene_common as C
preview='--preview' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/season1_map.blend'))
jobs=[('Season 1 • beginning','01_season_beginning','wide'),('Season 1 • middle','02_season_middle','wide'),
      ('Season 1 • final','03_season_final','wide'),('Season 1 • final','04_season_final_top','top'),('Season 1 • final','05_compact_centre_close','close')]
if '--all' in sys.argv:
    jobs += [('LEVELS • '+kind,'06_'+kind+'_levels','levels') for kind in ('cathedral','inn','watermill','farmstead')]
if '--backs' in sys.argv:jobs=[('LEVELS • '+kind,'qa_back_'+kind,'back') for kind in ('cathedral','inn','watermill','farmstead')]
for name,filename,view in jobs:
    scene=bpy.data.scenes[name];bpy.context.window.scene=scene;C.configure(scene,preview)
    if view not in ('levels','back'):C.camera(scene,close=view=='close',top=view=='top')
    else:
        scene.render.resolution_x=2100 if preview else 3000;scene.render.resolution_y=1000 if preview else 1440
        if view=='back':
            target=Vector((0,0,3.4 if 'cathedral' in name else 2.1));scene.camera.location=(-17,32,22);scene.camera.rotation_euler=(target-scene.camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(ROOT/'renders'/(('preview_' if preview else '')+filename+'.png'))
    bpy.ops.render.render(write_still=True);print('RENDERED',filename,flush=True)
C.protect();print('SEASON_RENDERS_COMPLETE',flush=True)
