"""Fresh source/candidate GLB comparisons; no image-exists render cache."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
import scene_checks as C
manifest=json.loads((ROOT/'reports/manifest.json').read_text());batch=sys.argv[sys.argv.index('--batch')+1] if '--batch' in sys.argv else 'whole'
assert batch in ('whole','buildings_a','buildings_b','buildings_c')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/hiddenfaces_review.blend'))
# Initialize the original imported library before comparing its stored transforms.
old_library=bpy.data.scenes.get('LIBRARY • imported runtime GLBs')
if old_library:bpy.context.window.scene=old_library;bpy.context.view_layer.update()
old_collections={(o['kind'],o['level']):o.instance_collection for label in ('beginning','middle','final') for o in bpy.data.scenes['ORIGINAL • '+label].objects if o.get('plot_id')}
old_digests={key:C.runtime_digest(col) for key,col in old_collections.items()}
fresh=bpy.data.scenes.new('QA • fresh original 36 GLBs');original={};optimized={};points={};source_reimport={}
for entry in manifest['assets']:
    key=(entry['type'],entry['level']);original[key]=C.import_asset(F.ART/entry['source_path'],fresh,f'QA SOURCE • {key}')
    optimized[key]=bpy.data.collections[f'OPT ASSET • {key[0]} L{key[1]}']
    if key in old_digests:assert C.runtime_digest(original[key])==old_digests[key],('Stored original GLB is stale',key)
    source_reimport[f'{key[0]}_level_{key[1]}']=F.sha(F.ART/entry['source_path'])
    d,b,_=F.read(F.ART/entry['source_path']);p=F.primitive(d);points[key]=F.blender_points(d,F.accessor(d,b,p['attributes']['POSITION']))
for label in ('beginning','middle','final'):
    for obj in bpy.data.scenes['ORIGINAL • '+label].objects:
        if obj.get('plot_id'):obj.instance_collection=original[obj['kind'],obj['level']]
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type!='CPU'
    gpu=any(d.type!='CPU' for d in prefs.devices)
except Exception:gpu=False
record_path=ROOT/'reports'/f'renders_{batch}.json';records=[]

def configure(scene,x,y,seed=71):
    scene.render.engine='CYCLES';scene.cycles.device='GPU' if gpu else 'CPU';scene.cycles.samples=64;scene.cycles.use_denoising=True
    scene.cycles.seed=seed;scene.cycles.use_animated_seed=False;scene.cycles.use_adaptive_sampling=False
    scene.render.resolution_x=x;scene.render.resolution_y=y;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.camera.data.dof.use_dof=False

def render(scene,relative,variant,assets,case,seed=71):
    x,y=(2400,1500) if case.startswith('whole_') else (3000,1600)
    configure(scene,x,y,seed);bpy.context.window.scene=scene;bpy.context.view_layer.update()
    current={f'{k}_level_{n}':F.sha(F.ART/next(e['source_path'] if variant!='optimized' else e['path'] for e in manifest['assets'] if e['type']==k and e['level']==n)) for k,n in assets}
    placements=sorted([{'id':o.get('plot_id',o.name),'matrix':[list(r) for r in o.matrix_world]} for o in scene.objects if o.instance_type=='COLLECTION'],key=lambda r:r['id'])
    presentation=C.presentation(scene);signature={'case':case,'assets':current,'placements':placements,'presentation':presentation,'samples':64,'seed':seed,'adaptive_sampling':False,'denoising':True,
        'source_environment_sha256':json.loads((ROOT/'reports/environment_baseline.json').read_text())['final']['environment_sha256']}
    path=ROOT/relative;scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    records.append({'case':case,'variant':variant,'path':relative,'sha256':F.sha(path),'input_signature':signature,'input_signature_sha256':C.digest(signature),
                    'camera_lighting_color_signature':C.digest(presentation),'source_reimported_actual_glbs':True})
    record_path.write_text(json.dumps({'batch':batch,'review_map_sha256':F.sha(ROOT/'blend/hiddenfaces_review.blend'),'original_source_glbs':source_reimport,'records':records},indent=2),encoding='utf-8')
    print('FRESH_RENDER',len(records),relative,flush=True)

if batch=='whole':
    for label in ('beginning','middle','final'):
        a=bpy.data.scenes['ORIGINAL • '+label];b=bpy.data.scenes['OPTIMIZED • '+label]
        keys=sorted({(o['kind'],o['level']) for o in a.objects if o.get('plot_id')})
        render(a,f'renders/whole/{label}_original.png','original',keys,'whole_'+label)
        render(b,f'renders/whole/{label}_optimized.png','optimized',keys,'whole_'+label)
        assert records[-1]['camera_lighting_color_signature']==records[-2]['camera_lighting_color_signature']
    render(bpy.data.scenes['ORIGINAL • final'],'renders/whole/final_noise_control.png','noise_control',keys,'whole_final',172)
    a=bpy.data.scenes['ORIGINAL • final'];b=bpy.data.scenes['OPTIMIZED • final']
    # Both share the same camera. This temporary review view is never saved into the map.
    a.camera.location=(-1.5,2,55);a.camera.rotation_euler=(0,0,0);a.camera.data.ortho_scale=58
    render(a,'renders/whole/final_top_original.png','original',keys,'whole_final_top')
    render(b,'renders/whole/final_top_optimized.png','optimized',keys,'whole_final_top')
    assert records[-1]['camera_lighting_color_signature']==records[-2]['camera_lighting_color_signature']
else:
    kinds=sorted({e['type'] for e in manifest['assets']});part={'buildings_a':0,'buildings_b':1,'buildings_c':2}[batch];kinds=kinds[part*4:part*4+4]
    template=bpy.data.scenes['ORIGINAL • final'];bpy.context.window.scene=template;bpy.context.view_layer.update()
    scene=template.copy();scene.name='QA • three-stage close row'
    for col in list(scene.collection.children):scene.collection.children.unlink(col)
    for obj in list(scene.collection.objects):
        if obj.type not in ('CAMERA','LIGHT'):scene.collection.objects.unlink(obj)
    cam=scene.camera.copy();cam.data=scene.camera.data.copy();scene.collection.objects.unlink(scene.camera);scene.collection.objects.link(cam);scene.camera=cam
    me=bpy.data.meshes.new('QA neutral ground');me.from_pydata([(-200,-200,-.004),(200,-200,-.004),(200,200,-.004),(-200,200,-.004)],[],[(0,1,2,3)]);me.materials.append(template.objects['Integrated • continuous terrain'].data.materials[0])
    ground=bpy.data.objects.new('QA neutral ground',me);scene.collection.objects.link(ground)
    instances=[]
    for n in (1,2,3):
        obj=bpy.data.objects.new(f'QA stage {n}',None);obj.instance_type='COLLECTION';obj.scale=(1,1,1);scene.collection.objects.link(obj);instances.append(obj)
    bearings={'front':(.17,-1),'back':(-.17,1),'side':(1,.12)}
    for kind in kinds:
        for view,(bx,by) in bearings.items():
            forward=Vector((-bx,-by,-.66)).normalized();q=forward.to_track_quat('-Z','Y');right=q@Vector((1,0,0));up=q@Vector((0,1,0))
            all_points=np.concatenate([points[kind,n] for n in (1,2,3)]);projection=all_points@np.array(right);spacing=float(projection.max()-projection.min())+.95
            pp=[]
            for n,obj in enumerate(instances,1):obj.location=right*((n-2)*spacing);pp.append(points[kind,n]+np.array(obj.location))
            pp=np.concatenate(pp);xx=pp@np.array(right);yy=pp@np.array(up);zz=pp@np.array(forward)
            target=right*float((xx.min()+xx.max())/2)+up*float((yy.min()+yy.max())/2)+forward*float((zz.min()+zz.max())/2)
            cam.location=target-forward*45;cam.rotation_euler=q.to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=max(float(xx.max()-xx.min()),float(yy.max()-yy.min())*(3000/1600))*1.08
            keys=[(kind,n) for n in (1,2,3)];case=kind+'_'+view
            for variant,assets in [('original',original),('optimized',optimized)]:
                for n,obj in enumerate(instances,1):obj.instance_collection=assets[kind,n]
                render(scene,f'renders/models/{case}_{variant}.png',variant,keys,case)
            assert records[-1]['camera_lighting_color_signature']==records[-2]['camera_lighting_color_signature']
            if view=='front' and kind in ('cafe','cathedral','florist','watermill'):
                for n,obj in enumerate(instances,1):obj.instance_collection=original[kind,n]
                render(scene,f'renders/models/{case}_noise_control.png','noise_control',keys,case,172)
F.protect();print('COMPARISON_BATCH_COMPLETE',batch,len(records),flush=True)
