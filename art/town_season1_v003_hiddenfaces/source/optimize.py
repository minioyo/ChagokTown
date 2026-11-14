"""Extend the audit's strict-inside convex cull to all 36 stage-specific assets."""
import bpy,sys,json,gzip,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'source'));sys.dont_write_bytecode=True
import glb as F
import solids
source=json.loads((ROOT/'reports/input_manifest.json').read_text());epsilon=5e-5
retain_path=ROOT/'source/retain_triangles.json';retain=json.loads(retain_path.read_text()) if retain_path.exists() else {}
report={'method':'Only all three vertices strictly inside one proven opaque closed outward convex same-stage component; 0.05mm margin.',
        'epsilon_m':epsilon,'no_camera_or_terrain_occluders':True,'models':{}}
manifest={**source,'revision':'town_season1_v003_hiddenfaces','optimization':'strictly hidden triangles only','changed_assets':36,'unchanged_assets':0,'assets':[]}
loaded=None
for entry in source['assets']:
    key=f"{entry['type']}_level_{entry['level']}";path=F.ART/entry['path'];assert F.sha(path)==entry['sha256']
    doc,blob,raw=F.read(path);p=F.primitive(doc)
    positions=np.array(F.accessor(doc,blob,p['attributes']['POSITION']),dtype=np.float64);points=F.blender_points(doc,positions)
    indices=np.array(F.accessor(doc,blob,p['indices']),dtype=np.int64).reshape(-1,3);triangles=points[indices]
    blend=F.ART/entry['editable_blend']
    if blend!=loaded:bpy.ops.wm.open_mainfile(filepath=str(blend));loaded=blend
    scene=bpy.data.scenes[entry['editable_scene']];occluders,component_checks=solids.collect(scene,points)
    lo=triangles.min(axis=1);hi=triangles.max(axis=1);owner=np.full(len(indices),-1,dtype=np.int32)
    for number,o in enumerate(occluders):
        lower=np.array(o['lower']);upper=np.array(o['upper']);normals=np.array(o['normals']);offsets=np.array(o['offsets'])
        eligible=np.flatnonzero((owner<0)&np.all(lo>=lower+epsilon,axis=1)&np.all(hi<=upper-epsilon,axis=1))
        for start in range(0,len(eligible),256):
            batch=eligible[start:start+256];inside=np.all(triangles[batch]@normals.T<offsets-epsilon,axis=(1,2));owner[batch[inside]]=number
    explicitly_retained=retain.get(key,[])
    for i in explicitly_retained:assert 0<=i<len(indices);owner[i]=-1
    kept_ids=np.flatnonzero(owner<0).tolist();kept=indices[kept_ids].tolist();used=sorted(set(i for tri in kept for i in tri));assert used and kept
    out,outblob,output=F.compact(doc,blob,kept,used);outp=F.primitive(out)
    for semantic,new_index in outp['attributes'].items():
        old_values=F.accessor(doc,blob,p['attributes'][semantic],True);new_values=F.accessor(out,outblob,new_index,True)
        assert new_values==[old_values[i] for i in used],(key,semantic)
    for field in ('nodes','materials','scenes','scene','asset','extras','extensionsUsed','extensionsRequired','extensions','samplers'):
        assert doc.get(field)==out.get(field),(key,field)
    outpath=ROOT/'exports'/f'{key}.glb';outpath.write_bytes(output)
    proof={'source_glb_sha256':entry['sha256'],'output_glb_sha256':F.sha(outpath),'source_blend_sha256':F.sha(blend),'editable_scene':entry['editable_scene'],
           'new_to_old_vertex':used,'kept_original_triangle_ids':kept_ids,'removed_triangles':[[int(i),int(owner[i])] for i in np.flatnonzero(owner>=0)],'occluders':occluders}
    with gzip.open(ROOT/'reports/mappings'/f'{key}.json.gz','wt',encoding='utf-8') as stream:json.dump(proof,stream,separators=(',',':'))
    by_owner={o['name']:int(np.sum(owner==i)) for i,o in enumerate(occluders) if np.any(owner==i)}
    report['models'][key]={'type':entry['type'],'level':entry['level'],'triangles_before':len(indices),'triangles_after':len(kept),'vertices_before':len(points),'vertices_after':len(used),
                          'bytes_before':len(raw),'bytes_after':len(output),'removed_triangles':len(indices)-len(kept),'attribute_bytes_preserved':True,'source_sha256':entry['sha256'],
                          'output_sha256':F.sha(outpath),'component_checks':component_checks,'by_occluder':by_owner,'explicitly_retained_triangle_count':len(explicitly_retained)}
    manifest['assets'].append({**entry,'changed':True,'source_path':entry['path'],'source_sha256':entry['sha256'],'path':outpath.relative_to(F.ART).as_posix(),'sha256':F.sha(outpath),
                               'mapping':f'reports/mappings/{key}.json.gz'})
    print('OPTIMIZED',key,len(indices),'->',len(kept),'vertices',len(points),'->',len(used),flush=True)
    (ROOT/'reports/optimization.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert len(report['models'])==36
fields=('triangles_before','triangles_after','vertices_before','vertices_after','bytes_before','bytes_after')
report['all_fourteen_plots_by_stage']={str(n):{field:sum(report['models'][f"{b['kind']}_level_{n}"][field] for b in source['layout']) for field in fields} for n in (1,2,3)}
report['unique_types_by_stage']={str(n):{field:sum(v[field] for v in report['models'].values() if v['level']==n) for field in fields} for n in (1,2,3)}
report['protected_inputs_unchanged']=F.protect()
(ROOT/'reports/optimization.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(ROOT/'reports/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('ALL_STAGE_OPTIMIZATION_COMPLETE',report['all_fourteen_plots_by_stage'],flush=True)
