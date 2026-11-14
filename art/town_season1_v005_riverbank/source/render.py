"""Paired genuine scene renders using freshly imported delivered GLBs."""
import bpy, sys, json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
import scene_checks as C
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
batch=args[0] if args else 'preview'
assert batch in ('preview','whole','details')
manifest=json.loads((ROOT/'reports/manifest.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/riverbank_review.blend'))
fresh=bpy.data.scenes.new('QA • freshly imported delivered assets')
assets={}
for entry in manifest['assets']:
    key=(entry['type'],entry['level'])
    col=C.import_asset(F.ART/entry['path'],fresh,f'QA delivered • {key}')
    assert C.runtime_digest(col)==C.runtime_digest(bpy.data.collections[f'ROOF ASSET • {key[0]} L{key[1]}'])
    assets[key]=col
props=C.import_asset(F.ART/manifest['riverbank']['path'],fresh,'QA • delivered riverbank GLB')
for label in ('beginning','middle','final'):
    a=bpy.data.scenes['AFTER roof tones • '+label]
    b=bpy.data.scenes['RIVERBANK v005 • '+label]
    b.collection.children.unlink(bpy.data.collections['RIVERBANK v005 • sparse stones and short grass'])
    b.collection.children.link(props)
    for scene in (a,b):
        for o in scene.objects:
            if o.get('plot_id'):o.instance_collection=assets[o['kind'],o['level']]

prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    gpu=any(d.type!='CPU' for d in prefs.devices)
except Exception:gpu=False
records=[]
record_path=ROOT/'reports'/f'renders_{batch}.json'

def render(scene,case,variant,relative):
    scene.render.engine='CYCLES';scene.cycles.device='GPU' if gpu else 'CPU'
    scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.cycles.use_adaptive_sampling=False
    scene.cycles.seed=71;scene.cycles.use_animated_seed=False
    scene.render.resolution_x,scene.render.resolution_y=(2400,1500) if case.startswith('whole') else (1800,1500)
    scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.camera.data.dof.use_dof=False
    bpy.context.window.scene=scene;bpy.context.view_layer.update()
    presentation=C.presentation(scene)
    scene.render.filepath=str(ROOT/relative)
    bpy.ops.render.render(write_still=True)
    records.append({'case':case,'variant':variant,'path':relative,'sha256':F.sha(ROOT/relative),
                    'presentation':presentation,'presentation_sha256':C.digest(presentation),
                    'samples':64,'seed':71,'actual_glbs_freshly_imported':True,
                    'props_sha256':manifest['riverbank']['sha256'] if variant=='after' else None})
    record_path.write_text(json.dumps({'batch':batch,'review_blend_sha256':F.sha(ROOT/'blend/riverbank_review.blend'),'records':records},indent=2),encoding='utf-8')
    print('RIVERBANK_RENDER',case,variant,flush=True)

def paired(label='final',case='whole_final',target=None,scale=None,top=False):
    for variant,prefix in [('before','AFTER roof tones • '),('after','RIVERBANK v005 • ')]:
        source=bpy.data.scenes[prefix+label]
        scene=source.copy();scene.name='QA '+case+' '+variant
        # Every review camera is a copy; no saved source camera is ever changed.
        cam=scene.camera.copy();cam.data=scene.camera.data.copy();scene.collection.objects.link(cam);scene.camera=cam
        if top:cam.location=(-1.5,2,55);cam.rotation_euler=(0,0,0);cam.data.ortho_scale=58
        elif target is not None:
            orientation=cam.rotation_euler.to_quaternion();forward=orientation@Vector((0,0,-1))
            cam.location=Vector(target)-forward*45;cam.data.ortho_scale=scale
        folder='whole' if case.startswith('whole') else 'details'
        render(scene,case,variant,f'renders/{folder}/{case}_{variant}.png')
        bpy.data.scenes.remove(scene)
    assert records[-1]['presentation_sha256']==records[-2]['presentation_sha256']

if batch=='preview':paired()
elif batch=='whole':
    paired('beginning','whole_beginning');paired('middle','whole_middle');paired('final','whole_final_top',top=True)
else:
    paired(case='riverbank_upper',target=(15.0,5.0,.1),scale=15.5)
    paired(case='riverbank_mill',target=(13.6,-7.7,.5),scale=14.5)
F.protect()
print('RIVERBANK_RENDER_BATCH_COMPLETE',batch,flush=True)
