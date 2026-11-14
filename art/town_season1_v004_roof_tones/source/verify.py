"""Independently reconstruct roof ownership and prove every non-RGB byte unchanged."""
import bpy,sys,json,struct,math
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
import roof_scope as R
import scene_checks as C
manifest=json.loads((ROOT/'reports/manifest.json').read_text());changes=json.loads((ROOT/'reports/roof_changes.json').read_text());loaded=None;report={'models':{}}
for entry in manifest['assets']:
    key=f"{entry['type']}_level_{entry['level']}";src=F.ART/entry['source_path'];dst=F.ART/entry['path'];assert F.sha(src)==entry['source_sha256'] and F.sha(dst)==entry['sha256']
    a,ab,ar=F.read(src);b,bb,br=F.read(dst);assert a==b and len(ar)==len(br);p=F.primitive(a)
    points=F.blender_points(a,F.accessor(a,ab,p['attributes']['POSITION']));colors=np.array(F.accessor(a,ab,p['attributes']['COLOR_0']))
    blend=F.ART/entry['editable_blend'];assert F.sha(blend)==changes['models'][key]['source_blend_sha256']
    if loaded!=blend:bpy.ops.wm.open_mainfile(filepath=str(blend));loaded=blend
    scope=R.scope(bpy.data.scenes[entry['editable_scene']],points,colors);actual=F.accessor(b,bb,p['attributes']['COLOR_0'],True);original=F.accessor(a,ab,p['attributes']['COLOR_0'],True)
    recorded={i:part for part in changes['models'][key]['components'] for i in part['vertex_ids']};assert set(recorded)==set(scope['changed'])
    ca=a['accessors'][p['attributes']['COLOR_0']];view=a['bufferViews'][ca['bufferView']];width=F.WIDTH[ca['type']];stride=view.get('byteStride',width*4)
    start=28+struct.unpack_from('<I',ar,12)[0]+view.get('byteOffset',0)+ca.get('byteOffset',0);allowed=set()
    for i,(old,new) in enumerate(zip(original,actual)):
        if i in scope['changed']:
            expected=struct.pack('<3f',*scope['changed'][i]);assert new[:12]==expected and new[12:]==old[12:] and expected!=old[:12]
            allowed.update(range(start+i*stride,start+i*stride+12))
        else:assert old==new,(key,'outside-roof color changed',i)
    assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(ar,br))),('Non-roof-RGB byte changed',key)
    for semantic,index in p['attributes'].items():
        if semantic!='COLOR_0':assert F.accessor(a,ab,index,True)==F.accessor(b,bb,index,True)
    assert F.accessor(a,ab,p['indices'],True)==F.accessor(b,bb,p['indices'],True)
    triangles=np.array(F.accessor(a,ab,p['indices']),dtype=np.int64).reshape(-1,3)
    for tri in triangles:
        if not any(int(i) in scope['changed'] for i in tri):continue
        owners=set.intersection(*(set(scope['owners_per_vertex'][int(i)]) for i in tri));assert owners and all(scope['parts'][j]['base_material'] for j in owners)
    report['models'][key]={'changed_vertices':len(scope['changed']),'vertices':len(points),'triangles':len(triangles),'independent_source_component_ownership':True,
        'all_non_roof_rgb_bytes_unchanged':True,'position_normal_indices_and_metadata_bytes_unchanged':True,'source_sha256':F.sha(src),'output_sha256':F.sha(dst)}
    print('INDEPENDENT_ROOF_SCOPE_OK',key,len(scope['changed']),flush=True)
# Reopen the actual saved map before importing the delivered files afresh.
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blend/roof_tones_review.blend'));baseline=json.loads((ROOT/'reports/environment_baseline.json').read_text())
for label in ('beginning','middle','final'):
    for prefix in ('BEFORE v003 • ','AFTER roof tones • '):assert C.digest(C.snapshot(bpy.data.scenes[prefix+label]))==C.digest(baseline[label])
stored={(e['type'],e['level']):C.runtime_digest(bpy.data.collections[f"ROOF ASSET • {e['type']} L{e['level']}"]) for e in manifest['assets']}
stored_before={(e['type'],e['level']):C.runtime_digest(bpy.data.collections[f"OPT ASSET • {e['type']} L{e['level']}"]) for e in manifest['assets']}
fresh=bpy.data.scenes.new('VALIDATE • fresh imports')
for entry in manifest['assets']:
    key=(entry['type'],entry['level']);name=f'{key[0]}_level_{key[1]}'
    for variant,path,expected in [('after',entry['path'],stored[key]),('before',entry['source_path'],stored_before[key])]:
        col=C.import_asset(F.ART/path,fresh,f'VALIDATE • {variant} {name}');assert C.runtime_digest(col)==expected,('Stale map asset',variant,name)
        obj=next(o for o in col.all_objects if o.type=='MESH');me=obj.data;me.calc_loop_triangles()
        assert len(me.materials)==1 and all(t.area>1e-12 for t in me.loop_triangles)
        assert all(math.isfinite(c) and abs(n.vector.length-1)<.001 for n in me.corner_normals for c in n.vector)
        assert all(abs(s-1)<1e-6 for s in obj.matrix_world.to_scale());attr=me.color_attributes.active_color;assert attr and all(abs(c.color[3]-1)<1e-5 for c in attr.data)
        assert len(me.loop_triangles)==report['models'][name]['triangles']
    report['models'][name]['both_actual_glbs_reimported_and_map_matched']=True
    print('PAIRED_REIMPORT_OK',name,flush=True)
report.update(passed=True,models_checked=36,changed_assets=manifest['changed_assets'],unchanged_assets=manifest['unchanged_assets'],
              all_hiddenface_topology_preserved=True,all_environment_and_plot_matrices_preserved=True,protected_inputs_unchanged=F.protect(),
              manifest_sha256=F.sha(ROOT/'reports/manifest.json'),review_map_sha256=F.sha(ROOT/'blend/roof_tones_review.blend'))
(ROOT/'reports/validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('ALL_ROOF_TONE_VALIDATION_COMPLETE',flush=True)
