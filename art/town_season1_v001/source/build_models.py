"""Produce named-component originals and twelve actual vertex-colour GLBs."""
import bpy,bmesh,sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import geometry as G
import models as M
import scene_common as C
bpy.ops.wm.read_factory_settings(use_empty=True)
work=bpy.context.scene;work.name='LIBRARY • twelve runtime assets';G.scene=work;palette=M.materials()
report={'models':{},'proportion_standard':M.PROPORTIONS,'type_lots_xy':M.LOTS}

def check(coll):
    dg=bpy.context.evaluated_depsgraph_get();count=0
    for obj in coll.objects:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
        assert all(t.area>1e-12 for t in me.loop_triangles),(obj.name,'degenerate triangle')
        assert all(math.isfinite(c) for n in me.corner_normals for c in n.vector),(obj.name,'non-finite normals')
        assert all(abs(n.vector.length-1)<.001 for n in me.corner_normals),(obj.name,'non-unit normal')
        bm=bmesh.new();bm.from_mesh(me)
        assert all(e.is_manifold and e.is_contiguous for e in bm.edges),(obj.name,'open/inward edge')
        assert bm.calc_volume(signed=True)>1e-10,(obj.name,'inward volume')
        bm.free();ev.to_mesh_clear();count+=1
    return {'closed_outward_components':count,'degenerate_triangles':0,'finite_unit_corner_normals':True}

for kind,fn in M.BUILDERS.items():
    for level in (1,2,3):
        key=f'{kind}_level_{level}';scene=bpy.data.scenes.new('EDIT • '+key);bpy.context.window.scene=scene
        coll,root=fn(level,True);bpy.context.view_layer.update();component_checks=check(coll);edit_stats=G.stats(coll)
        low=G.collection('RUNTIME • '+key);lr=root.copy();lr.name=key+' • runtime ground root';low.objects.link(lr)
        for source in list(coll.objects):
            if source.type!='MESH':continue
            obj=source.copy();obj.data=source.data.copy();low.objects.link(obj);obj.parent=lr
        obj=G.consolidate(low,lr,key,level)
        obj['placement_xy_min']=M.LOTS[kind][0];obj['placement_xy_max']=M.LOTS[kind][1]
        obj['placement_lot_m']=[M.LOTS[kind][1][i]-M.LOTS[kind][0][i] for i in range(2)]
        obj['door_panel_standard_m']=[.8,1.6];obj['floor_pitch_m']=2.0
        path=ROOT/'exports'/f'{key}.glb';G.export(low,path)
        runtime=G.stats(low);glb=G.glb_stats(path)
        assert glb['mesh_objects']==glb['materials']==glb['primitives']==1 and glb['textures']==0 and glb['all_primitives_have_vertex_color']
        assert runtime['triangles']<={1:4000,2:6000,3:8000}[level],(key,runtime['triangles'])
        assert abs(runtime['bounds_min'][2])<1e-5,(key,runtime['bounds_min'])
        for i in range(2):
            assert runtime['bounds_min'][i]>=M.LOTS[kind][0][i]-1e-5 and runtime['bounds_max'][i]<=M.LOTS[kind][1][i]+1e-5,(key,runtime,M.LOTS[kind])
        report['models'][key]={'type':kind,'level':level,'editable':edit_stats,'runtime':runtime,'glb':glb,'source_checks':component_checks,'budget':{1:4000,2:6000,3:8000}[level]}
        scene.collection.children.unlink(low);work.collection.children.link(low)
        if scene.camera is None:
            data=bpy.data.cameras.new(key+' edit camera');cam=bpy.data.objects.new(key+' edit camera',data);scene.collection.objects.link(cam);scene.camera=cam
        scene.camera.location=(12,-18,14);scene.camera.rotation_euler=(__import__('mathutils').Vector((0,0,2.4))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.type='ORTHO';scene.camera.data.ortho_scale=15
        C.configure(scene,True)
        print('MODEL_COMPLETE',key,runtime['triangles'],flush=True)
        (ROOT/'reports/model_stats.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.context.window.scene=bpy.data.scenes['EDIT • cathedral_level_3']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blend/season1_models.blend'))
(ROOT/'reports/palette.json').write_text(json.dumps(palette,indent=2),encoding='utf-8')
C.protect();print('TWELVE_MODELS_COMPLETE',flush=True)
