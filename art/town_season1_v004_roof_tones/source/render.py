"""Fresh paired renders from both actual GLBs, with unchanged cameras and lighting."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
import scene_checks as C
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];batch=args[args.index('--batch')+1];assert batch in ('preview','whole','roofs_a','roofs_b')
manifest=json.loads((ROOT/'reports/manifest.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/roof_tones_review.blend'))
fresh=bpy.data.scenes.new('QA • fresh paired delivered GLBs');assets={'before':{},'after':{}};points={}
for entry in manifest['assets']:
    key=(entry['type'],entry['level'])
    for variant,field in [('before','source_path'),('after','path')]:
        stored=bpy.data.collections[f"{'OPT' if variant=='before' else 'ROOF'} ASSET • {key[0]} L{key[1]}"]
        col=C.import_asset(F.ART/entry[field],fresh,f'QA {variant} • {key}');assert C.runtime_digest(col)==C.runtime_digest(stored),('Stale map model',variant,key)
        assets[variant][key]=col
    d,b,_=F.read(F.ART/entry['path']);p=F.primitive(d);points[key]=F.blender_points(d,F.accessor(d,b,p['attributes']['POSITION']))
for variant,prefix in [('before','BEFORE v003 • '),('after','AFTER roof tones • ')]:
    for label in ('beginning','middle','final'):
        for o in bpy.data.scenes[prefix+label].objects:
            if o.get('plot_id'):o.instance_collection=assets[variant][o['kind'],o['level']]
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type!='CPU'
    gpu=any(d.type!='CPU' for d in prefs.devices)
except Exception:gpu=False
records=[];record_path=ROOT/'reports'/f'renders_{batch}.json'
def render(scene,case,variant,keys,relative):
    scene.render.engine='CYCLES';scene.cycles.device='GPU' if gpu else 'CPU';scene.cycles.samples=64;scene.cycles.use_denoising=True;scene.cycles.use_adaptive_sampling=False;scene.cycles.seed=71;scene.cycles.use_animated_seed=False
    x,y=(2400,1500) if case.startswith('whole_') else (3000,1600);scene.render.resolution_x=x;scene.render.resolution_y=y;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.camera.data.dof.use_dof=False
    bpy.context.window.scene=scene;bpy.context.view_layer.update();presentation=C.presentation(scene)
    placements=sorted([{'id':o.get('plot_id',o.name),'matrix':[list(r) for r in o.matrix_world]} for o in scene.objects if o.instance_type=='COLLECTION'],key=lambda r:r['id'])
    hashes={f'{k}_level_{n}':F.sha(F.ART/next(e['source_path' if variant=='before' else 'path'] for e in manifest['assets'] if e['type']==k and e['level']==n)) for k,n in keys}
    scene.render.filepath=str(ROOT/relative);bpy.ops.render.render(write_still=True)
    records.append({'case':case,'variant':variant,'path':relative,'sha256':F.sha(ROOT/relative),'asset_sha256':hashes,'placements':placements,'presentation':presentation,
                    'presentation_sha256':C.digest(presentation),'samples':64,'seed':71,'adaptive_sampling':False,'denoising':True,'actual_glbs_freshly_imported':True})
    record_path.write_text(json.dumps({'batch':batch,'review_map_sha256':F.sha(ROOT/'blend/roof_tones_review.blend'),'records':records},indent=2),encoding='utf-8');print('FRESH_RENDER',len(records),relative,flush=True)
def whole(label,top=False):
    a=bpy.data.scenes['BEFORE v003 • '+label];b=bpy.data.scenes['AFTER roof tones • '+label]
    if top:a.camera.location=(-1.5,2,55);a.camera.rotation_euler=(0,0,0);a.camera.data.ortho_scale=58
    case='whole_'+label+('_top' if top else '');keys=sorted({(o['kind'],o['level']) for o in a.objects if o.get('plot_id')})
    for variant,scene in [('before',a),('after',b)]:render(scene,case,variant,keys,f'renders/whole/{label}{"_top" if top else ""}_{variant}.png')
    assert records[-1]['presentation_sha256']==records[-2]['presentation_sha256']
def roofs(kinds):
    template=bpy.data.scenes['BEFORE v003 • final'];bpy.context.window.scene=template;bpy.context.view_layer.update();scene=template.copy();scene.name='QA • roof stage row'
    for col in list(scene.collection.children):scene.collection.children.unlink(col)
    for obj in list(scene.collection.objects):
        if obj.type not in ('CAMERA','LIGHT'):scene.collection.objects.unlink(obj)
    cam=scene.camera.copy();cam.data=scene.camera.data.copy();scene.collection.objects.unlink(scene.camera);scene.collection.objects.link(cam);scene.camera=cam
    me=bpy.data.meshes.new('QA neutral ground');me.from_pydata([(-200,-200,-.004),(200,-200,-.004),(200,200,-.004),(-200,200,-.004)],[],[(0,1,2,3)]);me.materials.append(template.objects['Integrated • continuous terrain'].data.materials[0]);scene.collection.objects.link(bpy.data.objects.new('QA neutral ground',me))
    instances=[]
    for n in (1,2,3):
        obj=bpy.data.objects.new(f'QA stage {n}',None);obj.instance_type='COLLECTION';obj.scale=(1,1,1);scene.collection.objects.link(obj);instances.append(obj)
    forward=Vector((-.17,1,-.85)).normalized();q=forward.to_track_quat('-Z','Y');right=q@Vector((1,0,0));up=q@Vector((0,1,0))
    for kind in kinds:
        pp=np.concatenate([points[kind,n] for n in (1,2,3)]);xx=pp@np.array(right);spacing=float(xx.max()-xx.min())+.95;rows=[]
        for n,obj in enumerate(instances,1):obj.location=right*((n-2)*spacing);rows.append(points[kind,n]+np.array(obj.location))
        pp=np.concatenate(rows);xx=pp@np.array(right);yy=pp@np.array(up);zz=pp@np.array(forward);target=right*float((xx.min()+xx.max())/2)+up*float((yy.min()+yy.max())/2)+forward*float((zz.min()+zz.max())/2)
        cam.location=target-forward*45;cam.rotation_euler=q.to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=max(float(xx.max()-xx.min()),float(yy.max()-yy.min())*(3000/1600))*1.08
        for variant in ('before','after'):
            for n,obj in enumerate(instances,1):obj.instance_collection=assets[variant][kind,n]
            render(scene,kind+'_roofs',variant,[(kind,n) for n in (1,2,3)],f'renders/models/{kind}_roofs_{variant}.png')
        assert records[-1]['presentation_sha256']==records[-2]['presentation_sha256']
if batch=='preview':whole('final');roofs(['cathedral'])
elif batch=='whole':whole('beginning');whole('middle');whole('final',True)
elif batch=='roofs_a':roofs(['inn','farmstead','watermill'])
elif batch=='roofs_b':roofs(['bakery','florist','house','town_hall'])
F.protect();print('ROOF_RENDER_BATCH_COMPLETE',batch,len(records),flush=True)
