"""Patch only RGB float bytes belonging to proven bright roof tile components."""
import bpy,sys,json,struct,copy
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
import roof_scope as R
manifest=json.loads((ROOT/'reports/input_manifest.json').read_text());out=copy.deepcopy(manifest);out.update(revision=ROOT.name,changed_assets=0,unchanged_assets=0)
report={'remaining_patch_contrast_in_linear_rgb':R.REMAINING_CONTRAST,'models':{}};loaded=None
for entry in out['assets']:
    key=f"{entry['type']}_level_{entry['level']}";source=F.ART/entry['path'];assert F.sha(source)==entry['sha256']
    doc,blob,raw=F.read(source);p=F.primitive(doc);points=F.blender_points(doc,F.accessor(doc,blob,p['attributes']['POSITION']));colors=np.array(F.accessor(doc,blob,p['attributes']['COLOR_0']))
    blend=F.ART/entry['editable_blend']
    if blend!=loaded:bpy.ops.wm.open_mainfile(filepath=str(blend));loaded=blend
    result=R.scope(bpy.data.scenes[entry['editable_scene']],points,colors);changed=result['changed']
    triangles=np.array(F.accessor(doc,blob,p['indices']),dtype=np.int64).reshape(-1,3)
    for tri in triangles:
        if not any(int(i) in changed for i in tri):continue
        shared=set(result['owners_per_vertex'][int(tri[0])]).intersection(result['owners_per_vertex'][int(tri[1])],result['owners_per_vertex'][int(tri[2])])
        assert shared and all(result['parts'][j]['base_material'] for j in shared),('Changed triangle leaves patch component',key,tri)
    entry['source_path']=source.relative_to(F.ART).as_posix();entry['source_sha256']=F.sha(source)
    entry['hiddenfaces_mapping']='town_season1_v003_hiddenfaces/'+entry.pop('mapping')
    entry['color_patch_report']='reports/roof_changes.json';entry['changed']=bool(changed)
    if changed:
        ca=doc['accessors'][p['attributes']['COLOR_0']];view=doc['bufferViews'][ca['bufferView']];assert ca['componentType']==5126 and ca['type'] in ('VEC3','VEC4')
        width=F.WIDTH[ca['type']];stride=view.get('byteStride',width*4);start=view.get('byteOffset',0)+ca.get('byteOffset',0)
        json_length=struct.unpack_from('<I',raw,12)[0];bin_start=28+json_length;patched=bytearray(raw)
        for i,rgb in changed.items():struct.pack_into('<3f',patched,bin_start+start+i*stride,*rgb)
        dest=ROOT/'exports'/source.name;dest.write_bytes(patched);entry['path']=dest.relative_to(F.ART).as_posix();entry['sha256']=F.sha(dest);out['changed_assets']+=1
        nd,nb,_=F.read(dest);assert nd==doc and len(patched)==len(raw)
        for semantic,index in p['attributes'].items():
            if semantic!='COLOR_0':assert F.accessor(doc,blob,index,True)==F.accessor(nd,nb,index,True)
        assert F.accessor(doc,blob,p['indices'],True)==F.accessor(nd,nb,p['indices'],True)
    else:out['unchanged_assets']+=1
    components=[r for r in result['parts'] if r['base_material']]
    report['models'][key]={'changed':bool(changed),'source_path':entry['source_path'],'output_path':entry['path'],'source_sha256':entry['source_sha256'],'output_sha256':entry['sha256'],
        'source_blend_sha256':F.sha(blend),'changed_vertex_count':len(changed),'vertices':len(points),'triangles':len(triangles),'max_source_position_match_error_m':result['max_position_match_error_m'],
        'components':components,'source_scene':entry['editable_scene'],'outside_patch_bytes_unchanged':True}
    print('ROOF_ONLY_PATCH',key,len(components),len(changed),flush=True)
(ROOT/'reports/manifest.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
(ROOT/'reports/roof_changes.json').write_text(json.dumps(report,indent=2),encoding='utf-8');F.protect()
print('ROOF_TONES_COMPLETE',out['changed_assets'],out['unchanged_assets'],flush=True)
