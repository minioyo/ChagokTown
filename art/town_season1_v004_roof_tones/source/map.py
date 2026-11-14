"""Keep the v003 map intact; copy stage scenes and replace asset references only."""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
import scene_checks as C
manifest=json.loads((ROOT/'reports/manifest.json').read_text());source=F.ART/'town_season1_v003_hiddenfaces/blend/hiddenfaces_review.blend';source_hash=F.sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source));before={label:bpy.data.scenes['OPTIMIZED • '+label] for label in ('beginning','middle','final')}
baseline={label:C.snapshot(scene) for label,scene in before.items()}
for label in before:bpy.data.scenes['ORIGINAL • '+label].name='ARCHIVE v002 • '+label
bpy.data.scenes['LIBRARY • optimized 36 GLBs'].name='LIBRARY • v003 baseline 36'
library=bpy.data.scenes.new('LIBRARY • roof tones 36 GLBs');library.use_fake_user=True;assets={}
for entry in manifest['assets']:
    key=(entry['type'],entry['level']);assets[key]=C.import_asset(F.ART/entry['path'],library,f'ROOF ASSET • {key[0]} L{key[1]}')
report={'source_map_sha256':source_hash,'scenes':{}}
for label,scene in before.items():
    scene.name='BEFORE v003 • '+label;scene.use_fake_user=True;after=scene.copy();after.name='AFTER roof tones • '+label;after.use_fake_user=True
    for obj in list(after.objects):
        if not obj.get('plot_id'):continue
        assert obj in list(after.collection.objects)
        new=obj.copy();new.name='ROOF PLOT • '+obj['plot_id'];new.instance_collection=assets[obj['kind'],obj['level']]
        after.collection.objects.unlink(obj);after.collection.objects.link(new)
    result=C.snapshot(after);assert C.digest(result)==C.digest(baseline[label]);assert C.digest(C.snapshot(scene))==C.digest(baseline[label])
    report['scenes'][label]={'environment_sha256':result['environment_sha256'],'presentation_sha256':result['presentation_sha256'],'plots':len(result['plots']),'environment_and_placements_unchanged':True}
bpy.context.window.scene=bpy.data.scenes['AFTER roof tones • final'];bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/roof_tones_review.blend'))
(ROOT/'reports/environment_baseline.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
(ROOT/'reports/map_preservation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');assert F.sha(source)==source_hash;F.protect()
print('ROOF_TONE_MAP_COMPLETE',flush=True)
