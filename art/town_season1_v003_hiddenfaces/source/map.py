"""Copy v002 scenes and replace building references only. Environment is untouched."""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
import scene_checks as C
manifest=json.loads((ROOT/'reports/manifest.json').read_text());source=F.ART/'town_season1_v002_integrated/blend/integrated_village.blend';source_hash=F.sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source));original={label:bpy.data.scenes['INTEGRATED • '+label] for label in ('beginning','middle','final')}
baseline={label:C.snapshot(scene) for label,scene in original.items()}
library=bpy.data.scenes.new('LIBRARY • optimized 36 GLBs');library.use_fake_user=True;assets={}
for entry in manifest['assets']:
    key=(entry['type'],entry['level']);assets[key]=C.import_asset(F.ART/entry['path'],library,f'OPT ASSET • {key[0]} L{key[1]}')
report={'source_map_sha256':source_hash,'scenes':{}}
for label,scene in original.items():
    optimized=scene.copy();optimized.name='OPTIMIZED • '+label;optimized.use_fake_user=True;scene.use_fake_user=True
    bpy.context.window.scene=optimized;bpy.context.view_layer.update()
    for obj in list(optimized.objects):
        if not obj.get('plot_id'):continue
        assert obj in list(optimized.collection.objects),'Plot unexpectedly belongs to shared environment collection'
        new=obj.copy();new.name='OPT PLOT • '+obj['plot_id'];new.instance_collection=assets[obj['kind'],obj['level']]
        optimized.collection.objects.unlink(obj);optimized.collection.objects.link(new)
    result=C.snapshot(optimized)
    assert result==baseline[label],('Changed environment, camera, lighting, color, or placement',label)
    assert C.snapshot(scene)==baseline[label],('Original scene was changed',label)
    scene.name='ORIGINAL • '+label
    report['scenes'][label]={'environment_sha256':result['environment_sha256'],'presentation_sha256':result['presentation_sha256'],'plot_count':len(result['plots']),
                           'exact_environment_preserved':True,'exact_plot_matrices_preserved':True}
bpy.context.window.scene=bpy.data.scenes['OPTIMIZED • final'];bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/hiddenfaces_review.blend'))
assert F.sha(source)==source_hash
(ROOT/'reports/environment_baseline.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
(ROOT/'reports/map_preservation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
F.protect();print('BUILDING_REFERENCE_ONLY_MAP_COMPLETE',flush=True)
