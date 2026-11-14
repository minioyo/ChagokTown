import sys,bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import scene_common as C
s,library,layout,asset,footprints=C.init(True)
ground,roads,strip=C.terrain(s,layout,footprints)
C.check_layout(s,layout,footprints,'blockout')
C.configure(s,True);C.camera(s)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/season1_blockout.blend'))
s.render.filepath=str(ROOT/'renders/00_max_stage_blockout.png');bpy.ops.render.render(write_still=True)
C.camera(s,top=True);s.render.filepath=str(ROOT/'renders/00_max_stage_blockout_top.png');bpy.ops.render.render(write_still=True)
C.protect();print('BLOCKOUT_COMPLETE',flush=True)
