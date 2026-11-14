"""Reopen the authored .blend and render proofs; MODE=preview/hero/individual/set/all."""
import bpy, os, json, math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
MODE=os.environ.get('TOWN_RENDER_MODE','all')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/chagok_town_miniature_v001.blend'))
scene=bpy.context.scene
print('REOPEN_OK',len(bpy.data.objects),'objects',flush=True)
if scene.render.engine=='CYCLES':
    # The saved scene may name a GPU, but device selection is a per-process preference.
    prefs=bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type='OPTIX'; prefs.get_devices()
        available=[d for d in prefs.devices if d.type!='CPU']
        for d in prefs.devices: d.use=d.type!='CPU'
        scene.cycles.device='GPU' if available else 'CPU'
    except Exception: scene.cycles.device='CPU'
    print('RENDER_DEVICE',scene.cycles.device,[(d.name,d.type,d.use) for d in prefs.devices],flush=True)

def aim(loc,target,scale):
    scene.camera.location=loc
    scene.camera.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    scene.camera.data.ortho_scale=scale

def render(name,w,h,samples=48):
    scene.render.resolution_x=w; scene.render.resolution_y=h
    if scene.render.engine=='CYCLES': scene.cycles.samples=samples
    scene.render.filepath=str(ROOT/'renders'/name)
    bpy.ops.render.render(write_still=True)
    print('RENDERED',name,flush=True)

if MODE=='preview':
    render('preview_diorama.png',1100,850,24)
if MODE in ('hero','all'):
    render('01_diorama.png',2000,1550,64)
    aim((-11,-19,12),(0,.2,1.0),15.7)
    render('02_diorama_reverse.png',2000,1550,64)

if MODE in ('individual','set','all'):
    bpy.data.collections['DIORAMA • lane and landscaping'].hide_render=True
    bpy.data.objects['Studio floor'].location.z=-.06
    shot=bpy.data.collections.new('RENDER • isolated models'); scene.collection.children.link(shot)
    assets={o['asset_id']:o for o in bpy.data.objects if o.type=='EMPTY' and 'asset_id' in o}
    def inst(key,loc):
        o=bpy.data.objects.new('Render '+key,None); shot.objects.link(o)
        o.instance_type='COLLECTION'; o.instance_collection=assets[key].users_collection[0]; o.location=loc
        return o
    specs={
        'house':((6,-9,6.8),(0,-.15,1.8),5.9),
        'cafe':((6,-9,6.5),(.1,-.35,1.45),6.0),
        'flower_shop':((6,-9,6.6),(.30,-.25,1.55),5.8),
        'round_tree':((5,-8,5),(0,0,1.45),4.1),
        'wood_bench':((4,-7,4),(0,0,.53),2.55),
        'street_lamp':((5,-8,4.8),(0,0,1.37),3.7),
    }
    if MODE in ('individual','all'):
        for key,settings in specs.items():
            o=inst(key,(0,0,0)); aim(*settings)
            render('asset_'+key+'.png',1100,1100,48)
            bpy.data.objects.remove(o,do_unlink=True)
    if MODE in ('set','all'):
        for key,loc in [('house',(-4,1.35,0)),('cafe',(0,1.35,0)),('flower_shop',(4,1.35,0)),('round_tree',(-3.5,-3,0)),('wood_bench',(0,-3,0)),('street_lamp',(3.5,-3,0))]: inst(key,loc)
        aim((9,-20,16),(0,-.1,1.3),16.7)
        render('03_asset_set.png',2200,1600,64)
print('RENDER_BATCH_COMPLETE',MODE,flush=True)
