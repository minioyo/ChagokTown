"""Read-only validation in a fresh Blender process of the delivered blend."""
import bpy,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
layouts=json.loads((ROOT/'reports/display_layouts.json').read_text())
calibration=json.loads((ROOT/'reports/calibration.json').read_text())
metrics=json.loads((ROOT/'reports/density_metrics.json').read_text())
names={'Baseline':'Baseline • v002 A','Compact':'Compact • same eight models','Dense':'Dense • sixteen existing copies'}
summaries={};baseline=None
for label,name in names.items():
    scene=bpy.data.scenes[name];bpy.context.window.scene=scene;bpy.context.view_layer.update()
    objects={o.name.split(' • ')[1]:o for o in scene.objects if o.type=='EMPTY' and o.instance_type=='COLLECTION' and o.get('kind')}
    assert set(objects)=={b['id'] for b in layouts[label]}
    assert (scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage)==(1920,1080,100)
    assert scene.cycles.samples==64 and not scene.camera.data.dof.use_dof
    assert abs(scene.camera.data.ortho_scale-28)<1e-6
    assert max(abs(x-y) for a,b in zip(scene.camera.matrix_world,calibration['camera_matrix']) for x,y in zip(a,b))<1e-6
    if baseline is None:baseline=objects
    for building in layouts[label]:
        obj=objects[building['id']]
        assert math.dist(obj.location[:2],building['xy'])<1e-5
        assert abs(obj.location.z-(building['ground']-.065*building['scale']))<1e-5
        assert all(abs(s-building['scale'])<1e-6 for s in obj.scale)
        if building.get('source_id'):assert obj.instance_collection==baseline[building['source_id']].instance_collection
    trees=sum(o.type=='MESH' and o.name.startswith('Tree • warm trunk') for o in scene.objects)
    assert trees==metrics[label]['tree_count']
    summaries[label]={'models':len(objects),'trees':trees,'saved_oblique_camera_matches':True,'render_resolution':[1920,1080],'samples':64}
(ROOT/'reports/independent_blend_reopen.json').write_text(json.dumps({'passed':True,'blend':bpy.data.filepath,'scenes':summaries},indent=2),encoding='utf-8')
completion=json.loads((ROOT/'reports/completion.json').read_text());completion['independent_blend_reopen_passed']=True
(ROOT/'reports/completion.json').write_text(json.dumps(completion,indent=2),encoding='utf-8')
print('INDEPENDENT_BLEND_REOPEN_PASSED',flush=True)
