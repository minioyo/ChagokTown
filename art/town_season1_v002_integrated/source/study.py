"""First whole-village study using unit-scale existing-model copies."""
import sys,bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import town as T
scene,library,before=T.start_scene();asset=T.importer(scene,library,True)
local={kind:T.hull([(p.x,p.y) for level in (1,2,3) for p in T.local_points(asset(kind,level))]) for kind in set(t[1] for t in T.TARGETS)}
layout=T.plan(local);T.save_metrics(layout,local,'study');T.place(scene,layout,asset);T.ground_scene(scene,layout,local);T.configure(scene,True)
scene['note']='Whole fourteen plots at unit scale. Existing copies are massing inputs; door/storey corrections follow after this composition review.'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/whole_village_study.blend'))
scene.render.filepath=str(ROOT/'renders/00_whole_village_study_oblique.png');bpy.ops.render.render(write_still=True)
T.top_camera(scene);scene.render.filepath=str(ROOT/'renders/00_whole_village_study_top.png');bpy.ops.render.render(write_still=True)
(ROOT/'source/study_layout.json').write_text(json.dumps(layout,indent=2),encoding='utf-8');T.protect();print('WHOLE_VILLAGE_STUDY_COMPLETE',flush=True)
