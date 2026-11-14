"""Verify that deleting the window backing is the only v002-to-v003 model change."""
import bpy, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
V2=ROOT.parent/'town_cafe_v002'

def capture(path,ignore_backing):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    result={}
    for level in (1,2,3):
        bpy.context.window.scene=bpy.data.scenes[f'EDIT • level {level}']
        bpy.context.view_layer.update()
        dg=bpy.context.evaluated_depsgraph_get()
        objects=[];backings=[]
        for o in bpy.context.scene.objects:
            if o.type!='MESH' or not any(c.name==f'EDIT • cafe level {level}' for c in o.users_collection):continue
            name=re.sub(r'\.\d+$','',o.name)
            if name=='Window • shadow recess':
                backings.append(o.name)
                if ignore_backing:continue
            e=o.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles()
            coords=[tuple(round(x,7) for x in e.matrix_world@v.co) for v in me.vertices]
            # Coordinate-based triangle and material fingerprints ignore Blender's
            # allocation-order suffixes while checking actual geometry and palette.
            faces=sorted((tuple(sorted(coords[i] for i in t.vertices)),me.materials[t.material_index].name) for t in me.loop_triangles)
            mats=sorted((m.name,tuple(round(x,7) for x in m.diffuse_color)) for m in me.materials if m)
            signature=hashlib.sha256(json.dumps([name,faces,mats],ensure_ascii=False).encode()).hexdigest()
            objects.append((name,signature));e.to_mesh_clear()
        result[str(level)]={'objects':sorted(objects),'backings':backings}
    main=bpy.data.scenes['01 • Cafe upgrades']
    result['camera']={'matrix':[list(r) for r in main.camera.matrix_world],'ortho_scale':main.camera.data.ortho_scale}
    result['lights']=sorted((o.name,[list(r) for r in o.matrix_world],o.data.energy,o.data.size,tuple(o.data.color)) for o in main.objects if o.type=='LIGHT')
    result['placements']=sorted((o.name,[list(r) for r in o.matrix_world]) for o in main.objects if o.instance_type=='COLLECTION')
    return result

before=capture(V2/'blend/chagok_cafe_upgrades_v002.blend',True)
after=capture(ROOT/'blend/chagok_cafe_upgrades_v003.blend',False)
report={'levels':{},'camera_unchanged':before['camera']==after['camera'],'lights_unchanged':before['lights']==after['lights'],'placements_unchanged':before['placements']==after['placements']}
for level,count in [('1',2),('2',2),('3',3)]:
    assert len(before[level]['backings'])==count and not after[level]['backings']
    assert before[level]['objects']==after[level]['objects'],f'Unexpected non-backing change in level {level}'
    report['levels'][level]={'removed_backing_count':count,'remaining_semantic_meshes':len(after[level]['objects']),'all_remaining_geometry_materials_transforms_identical':True}
assert report['camera_unchanged'] and report['lights_unchanged'] and report['placements_unchanged']
report['all_passed']=True
(ROOT/'reports/scope_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('SCOPE_VALIDATION_COMPLETE',json.dumps(report),flush=True)
